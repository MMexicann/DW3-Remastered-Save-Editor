"""Nioh 2 source-only inspection; procedural data is not a valid game save."""
from dataclasses import replace
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import koei_editor.research.nioh2.nioh2_parser as inspector
from koei_editor.shared import copy_storage
from koei_editor.games.dw3.models import SaveError


@lru_cache(maxsize=1)
def procedural_raw():
    # Distinctive unknown bytes make every unsupported mutation detectable.
    # Native body checksum bytes are deliberately unqualified: the parser must
    # never turn this inspection fixture into an editable or playable save.
    raw = bytearray((index * 41 + 17) & 255 for index in range(2715432))
    raw[:8] = b'NIOHUSR\0'
    raw[8:12] = bytes.fromhex('00020321')
    raw[0x14:0x18] = (328).to_bytes(4, 'little')
    raw[0x18:0x1C] = (2715104).to_bytes(4, 'little')
    raw[0x150:0x154] = bytes.fromhex('00020321')
    for offset in (0x7B93C, 0x7B9DA, 0x7B9DC, 0xED0A2):
        raw[offset] = 1
    raw[0x7B8D0:0x7B8D8] = (1234567890123).to_bytes(8, 'little')
    raw[0x7B8D8:0x7B8E0] = (456789).to_bytes(8, 'little')
    raw[0x1C4904:0x1C4906] = (330).to_bytes(2, 'little')
    raw[0x1C4908:0x1C490C] = (330).to_bytes(4, 'little')
    for offset, value in ((0x1C490C, 133), (0x1C4910, 60), (0x1C4914, 10),
                          (0x1C4918, 12), (0x1C491C, 19), (0x1C4920, 71),
                          (0x1C4924, 32), (0x1C4928, 35)):
        raw[offset:offset + 2] = value.to_bytes(2, 'little')
    raw[0x1C4A8C:0x1C4A90] = (112814).to_bytes(4, 'little')
    return bytes(raw)


class Nioh2InspectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.folder = Path(self.temporary.name)
        self.source = self.folder / 'copy.bin'
        self.source.write_bytes(procedural_raw())
        self.document = inspector.read_save(self.source)

    def tearDown(self):
        self.temporary.cleanup()

    def test_source_only_has_no_writable_fields_or_gameplay_caps(self):
        self.assertEqual(inspector.fields_for(self.document), ())
        self.assertEqual(inspector.field_map(self.document), {})
        self.assertEqual(inspector.maximums(self.document, {}), {})
        self.assertEqual(inspector.limit_values(self.document, {}, []), {})
        self.assertFalse(inspector.FORMAT.sample_verified)
        self.assertIn('checksums have not been validated', inspector.FORMAT.note)
        self.assertEqual(len(inspector.INSPECTION_FIELDS), 20)
        self.assertEqual(inspector.INSPECTION_MAP['gold'].storage_maximum, 2**64 - 1)

    def test_published_scalar_widths_and_values_are_inspection_only(self):
        fields = inspector.INSPECTION_MAP
        self.assertEqual(fields['amrita'].value(self.document.payload), 1234567890123)
        self.assertEqual(fields['gold'].value(self.document.payload), 456789)
        self.assertEqual(fields['level'].value(self.document.payload), 330)
        self.assertEqual(fields['constitution'].value(self.document.payload), 133)
        self.assertEqual(fields['courage'].value(self.document.payload), 35)
        self.assertEqual(fields['sword'].value(self.document.payload), 112814)
        with self.assertRaises(TypeError):
            fields['unsupported'] = fields['gold']

    def test_noop_preserves_flags_header_account_unknown_and_checksum_bytes(self):
        self.assertEqual(inspector.serialize(self.document, {}), procedural_raw())
        self.assertEqual(inspector.changed_payload(self.document, {}), procedural_raw())
        self.assertEqual(inspector.review(self.document, {}), [])
        self.assertEqual(self.document.raw, self.document.payload)
        self.assertEqual([self.document.payload[offset] for offset in inspector.INTEGRITY_FLAG_OFFSETS],
                         [1, 1, 1, 1])
        self.assertEqual(self.source.read_bytes(), procedural_raw())

    def test_every_edit_and_checksum_bypass_is_rejected(self):
        for key in (*inspector.INSPECTION_MAP, 'disable_integrity', 'account', 'checksum', 'raw_byte'):
            for operation in (
                    lambda: inspector.stage(self.document, {}, key, 1),
                    lambda: inspector.serialize(self.document, {key: 1}),
                    lambda: inspector.changed_payload(self.document, {key: 1}),
                    lambda: inspector.review(self.document, {key: 1}),
                    lambda: inspector.maximums(self.document, {key: 1}),
                    lambda: inspector.limit_values(self.document, {}, [key])):
                with self.subTest(key=key), self.assertRaisesRegex(SaveError, 'read only'):
                    operation()
        with self.assertRaises(SaveError):
            inspector.serialize(self.document, [])

    def test_disabled_flags_do_not_make_checksums_or_edits_supported(self):
        raw = bytearray(procedural_raw())
        for offset in inspector.INTEGRITY_FLAG_OFFSETS:
            raw[offset] = 0
        document = inspector.decode(raw)
        self.assertEqual(inspector.serialize(document, {}), bytes(raw))
        with self.assertRaisesRegex(SaveError, 'read only'):
            inspector.serialize(document, {'gold': 123})

    def test_inspection_rows_state_native_integrity_limitation_without_account_data(self):
        rows = inspector.inspection_rows(self.document)
        self.assertEqual(len(rows), 27)
        self.assertIn('read only', rows[0]['value'])
        self.assertEqual(rows[1]['value'], '21030200')
        self.assertEqual(rows[2]['value'], 'Native decrypted')
        self.assertEqual([row['value'] for row in rows if row['label'] == 'Level'],
                         ['330 (read only)'])
        self.assertFalse(any('account' in row['label'].lower() for row in rows))

    def test_wrong_title_revision_inner_marker_size_and_flags_rejected(self):
        for data in (b'', bytes(2715432), procedural_raw()[:-1], procedural_raw() + b'\0'):
            with self.assertRaises(SaveError):
                inspector.decode(data)
        for offset, replacement in ((0, b'NIOHSYS\0'), (8, bytes.fromhex('00120917')),
                                    (8, bytes.fromhex('00030321')),
                                    (0x150, bytes.fromhex('00120917')),
                                    (0x14, (344).to_bytes(4, 'little')),
                                    (0x18, (2715103).to_bytes(4, 'little')),
                                    (0x7B93C, b'\x02')):
            raw = bytearray(procedural_raw())
            raw[offset:offset + len(replacement)] = replacement
            with self.subTest(offset=offset), self.assertRaises(SaveError):
                inspector.decode(raw)
        for game_id in ('nioh', 'nioh3', 'dw8xl', 'wolong', 'sopffo'):
            with self.assertRaises(SaveError):
                inspector.decode(procedural_raw(), game_id)

    def test_body_checksums_are_explicitly_not_claimed_validated(self):
        # Unknown checksum coverage means inspection cannot detect this mutation.
        # It still cannot write, repair or disable integrity on the altered file.
        raw = bytearray(procedural_raw())
        raw[0x148] ^= 1
        document = inspector.decode(raw)
        self.assertFalse(document.format.sample_verified)
        self.assertEqual(inspector.serialize(document, {}), bytes(raw))
        with self.assertRaises(SaveError):
            inspector.stage(document, {}, 'level', 400)

    def test_forged_payload_format_representation_and_snapshot_rejected(self):
        for document in (replace(self.document, payload=b'bad'),
                         replace(self.document, encrypted=True),
                         replace(self.document, format=replace(inspector.FORMAT, sample_verified=True)),
                         replace(self.document, raw=bytearray(self.document.raw)),
                         replace(self.document, payload=bytearray(self.document.payload)),
                         replace(self.document, encrypted=0),
                         replace(self.document, raw=self.document.raw[:-1])):
            with self.assertRaises(SaveError):
                inspector.serialize(document, {})

    def test_restore_validates_exact_bytes_after_backup_changes(self):
        snapshot = inspector.backup(self.document)
        destination = self.folder / 'restored.bin'
        damaged = bytearray(procedural_raw())
        damaged[8] ^= 1
        damaged = bytes(damaged)

        def replace_before_read(*args, **kwargs):
            # Model replacement after any earlier validation, together with a
            # matching manifest: checksum/hash checks alone do not prove title.
            snapshot.write_bytes(damaged)
            metadata_path = snapshot.with_suffix('.json')
            metadata = json.loads(metadata_path.read_text())
            metadata['sha256'] = hashlib.sha256(damaged).hexdigest()
            metadata_path.write_text(json.dumps(metadata))
            return copy_storage.restore_snapshot(*args, **kwargs)

        with patch.object(inspector, 'restore_snapshot', side_effect=replace_before_read):
            with self.assertRaisesRegex(SaveError, 'title|revision'):
                inspector.restore(snapshot, destination)
        self.assertFalse(destination.exists())
        self.assertEqual(self.source.read_bytes(), procedural_raw())

    def test_unchanged_copy_backup_and_restore_are_byte_exact(self):
        snapshot = inspector.backup(self.document)
        metadata = json.loads(snapshot.with_suffix('.json').read_text())
        self.assertEqual(metadata['game_id'], 'nioh2')
        self.assertEqual(snapshot.read_bytes(), procedural_raw())
        copied = inspector.save_as(self.document, {}, self.folder / 'copied.bin')
        self.assertEqual(copied.raw, procedural_raw())
        restored = inspector.restore(snapshot, self.folder / 'restored.bin')
        self.assertEqual(restored.read_bytes(), procedural_raw())
        self.assertEqual(self.source.read_bytes(), procedural_raw())
        with self.assertRaisesRegex(SaveError, 'read only'):
            inspector.save_as(self.document, {'gold': 123}, self.folder / 'edited.bin')
        self.assertFalse((self.folder / 'edited.bin').exists())

    def test_existing_destinations_never_overwritten(self):
        snapshot = inspector.backup(self.document)
        existing = self.folder / 'existing.bin'
        existing.write_bytes(b'keep')
        for destination in (existing, self.source):
            before = destination.read_bytes()
            with self.assertRaises(FileExistsError):
                inspector.save_as(self.document, {}, destination)
            with self.assertRaises(FileExistsError):
                inspector.restore(snapshot, destination)
            self.assertEqual(destination.read_bytes(), before)

    def test_source_change_and_wrong_game_backup_manifest_rejected(self):
        snapshot = inspector.backup(self.document)
        metadata_path = snapshot.with_suffix('.json')
        metadata = json.loads(metadata_path.read_text())
        metadata['game_id'] = 'nioh'
        metadata_path.write_text(json.dumps(metadata))
        with self.assertRaises(SaveError):
            inspector.restore(snapshot, self.folder / 'restored.bin')
        self.source.write_bytes(procedural_raw()[:-1])
        with self.assertRaisesRegex(SaveError, 'changed on disk'):
            inspector.save_as(self.document, {}, self.folder / 'copied.bin')
        self.assertFalse((self.folder / 'copied.bin').exists())

    def test_source_changed_during_backup_is_rejected_before_copy(self):
        destination = self.folder / 'copied.bin'
        original_backup = inspector.backup

        def replaced_during_backup(document):
            result = original_backup(document)
            replacement = bytearray(document.raw)
            replacement[-1] ^= 1
            self.source.write_bytes(replacement)
            return result

        with patch.object(inspector, 'backup', replaced_during_backup):
            with self.assertRaisesRegex(SaveError, 'changed on disk'):
                inspector.save_as(self.document, {}, destination)
        self.assertFalse(destination.exists())
        backups = tuple((self.folder / 'WarriorsEditorBackups').glob('*.bin'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), self.document.raw)

    def test_suffix_live_and_resolved_alias_paths_rejected(self):
        wrong = self.folder / 'copy.dat'
        wrong.write_bytes(procedural_raw())
        with self.assertRaises(SaveError):
            inspector.read_save(wrong)
        with self.assertRaises(SaveError):
            inspector.save_as(self.document, {}, self.folder / 'out.dat')
        live = self.folder / 'KoeiTecmo' / 'Nioh2' / 'Savedata'
        live.mkdir(parents=True)
        source = live / 'SAVEDATA.BIN'
        source.write_bytes(procedural_raw())
        with self.assertRaises(SaveError):
            inspector.read_save(source)
        with self.assertRaises(SaveError):
            inspector.save_as(self.document, {}, live / 'copied.bin')
        with self.assertRaises(SaveError):
            inspector._copy_path(r'C:\Users\Player\Documents\KoeiTecmo\Nioh2\Savedata\SAVEDATA.BIN')
        alias = self.folder / 'alias.bin'
        try:
            alias.symlink_to(source)
        except (OSError, NotImplementedError):
            return
        with self.assertRaises(SaveError):
            inspector.read_save(alias)


@unittest.skipUnless(os.environ.get('NIOH2_SAVE_COPY'), 'No explicit Nioh 2 PC user save copy provided')
class ExplicitNioh2SampleInspectionTests(unittest.TestCase):
    def test_native_sample_noop_and_readonly_contract(self):
        document = inspector.read_save(os.environ['NIOH2_SAVE_COPY'])
        self.assertEqual(inspector.serialize(document, {}), document.raw)
        self.assertEqual(inspector.fields_for(document), ())
        self.assertEqual(len(inspector.inspection_rows(document)), 27)
        for field in inspector.INSPECTION_FIELDS:
            self.assertEqual(field.value(document.payload), int.from_bytes(
                document.payload[field.offset:field.offset + field.size], 'little'))
        with self.assertRaisesRegex(SaveError, 'read only'):
            inspector.serialize(document, {'gold': 12345})

    def test_native_unchanged_copy_backup_restore_preserves_retained_flags(self):
        document = inspector.read_save(os.environ['NIOH2_SAVE_COPY'])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'native-copy.bin'
            source.write_bytes(document.raw)
            working = inspector.read_save(source)
            snapshot = inspector.backup(working)
            copied = inspector.save_as(working, {}, root / 'copied.bin')
            restored = inspector.restore(snapshot, root / 'restored.bin')
            self.assertEqual(snapshot.read_bytes(), document.raw)
            self.assertEqual(copied.raw, document.raw)
            self.assertEqual(restored.read_bytes(), document.raw)
            self.assertEqual(source.read_bytes(), document.raw)
            self.assertEqual([copied.payload[o] for o in inspector.INTEGRITY_FLAG_OFFSETS],
                             [document.payload[o] for o in inspector.INTEGRITY_FLAG_OFFSETS])


if __name__ == '__main__':
    unittest.main()
