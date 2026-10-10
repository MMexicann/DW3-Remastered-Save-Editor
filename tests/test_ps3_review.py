"""Independent PS3 safety checks; all public inputs are procedural."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.dw7_ps3 import parser as dw7
from koei_editor.games.sw4_ps3 import parser as sw4
from tests.test_ps3_expansion import fixture
from tests import test_ps3_expansion as ps3_fixtures


class PS3IndependentReviewTests(unittest.TestCase):
    def test_conflicting_destination_and_changed_source_context_reject_writes(self):
        for backend, correct in ((dw7, 'BLUS30690-SAVEDATA'), (sw4, 'NPUB31564-00')):
            with tempfile.TemporaryDirectory() as folder, self.subTest(game=backend.GAME_ID):
                root = Path(folder)
                source_folder = root / 'source'
                destination_folder = root / 'destination'
                source_folder.mkdir()
                destination_folder.mkdir()
                source = source_folder / 'copy.bin'
                raw = fixture(backend)
                source.write_bytes(raw)
                source_metadata = source_folder / 'PARAM.SFO'
                source_metadata.write_bytes(ps3_fixtures.PS3ContextTests.metadata(correct))
                document = backend.read_save(source)
                backup = backend.backup(document)
                destination_metadata = destination_folder / 'PARAM.SFO'
                destination_metadata.write_bytes(ps3_fixtures.PS3ContextTests.metadata('NPJB00534-00'))
                destination = destination_folder / 'edited.bin'
                with self.assertRaises(SaveError):
                    backend.save_as(document, {'gold': 123}, destination)
                with self.assertRaises(SaveError):
                    backend.restore(backup, destination)
                self.assertFalse(destination.exists())
                destination_metadata.write_bytes(ps3_fixtures.PS3ContextTests.metadata(correct))
                source_metadata.write_bytes(ps3_fixtures.PS3ContextTests.metadata('NPJB00534-00'))
                with self.assertRaises(SaveError):
                    backend.save_as(document, {'gold': 123}, destination)
                self.assertFalse(destination.exists())
                self.assertEqual(source.read_bytes(), raw)
                source_metadata.write_bytes(ps3_fixtures.PS3ContextTests.metadata(correct))
                backend.save_as(document, {'gold': 123}, destination)
                self.assertEqual(backend.field_map(backend.read_save(destination))['gold'].value(destination.read_bytes()), 123)

    def test_dw7_nonzero_upper_power_speed_bytes_are_not_editable(self):
        raw = bytearray(fixture(dw7))
        # Apollo byte patches qualify only the normal zero-upper-byte encoding.
        raw[0x14BD] = 0xA5
        raw[0x14BF + 61 * 0x80] = 0x7F
        document = dw7.decode(bytes(raw))
        fields = dw7.field_map(document)
        self.assertNotIn('officer_0_power', fields)
        self.assertNotIn('officer_61_speed', fields)
        for key in ('officer_0_power', 'officer_61_speed'):
            with self.subTest(key=key), self.assertRaises(SaveError):
                dw7.stage(document, {}, key, 100)
        output = dw7.serialize(document, {'gold': 123})
        self.assertEqual(output[0x14BD:0x14BF], bytes(raw[0x14BD:0x14BF]))
        offset = 0x14BF + 61 * 0x80
        self.assertEqual(output[offset:offset + 2], bytes(raw[offset:offset + 2]))

    def test_manual_bounds_never_max_higher_values_and_unstage_original(self):
        for backend in (dw7, sw4):
            with self.subTest(game=backend.GAME_ID):
                raw = bytearray(fixture(backend))
                for field in backend.FORMAT.fields:
                    raw[field.offset:field.offset + field.size] = ((1 << (field.size * 8)) - 1).to_bytes(field.size, 'big')
                raw = backend.seal(bytes(raw))
                document = backend.decode(raw)
                self.assertTrue(all(not field.maxable for field in backend.fields_for(document)))
                self.assertEqual(backend.maximums(document, {}), {})
                self.assertEqual(backend.serialize(document, {}), raw)
                field = backend.field_map(document)['gold']
                changes = backend.stage(document, {}, field.id, 123)
                self.assertEqual(backend.maximums(document, changes), changes)
                self.assertEqual(backend.stage(document, changes, field.id, field.value(raw)), {})
                encoded = backend.serialize(document, changes)
                allowed = set(range(field.offset, field.offset + field.size))
                for offset in getattr(backend, 'CHECKSUM_OFFSETS', ()):
                    allowed.update(range(offset, offset + 4))
                touched = {index for index, (before, after) in enumerate(zip(raw, encoded)) if before != after}
                self.assertLessEqual(touched, allowed)

    def test_sw4_proficiencies_cannot_edit_without_matching_exp_dependencies(self):
        document = sw4.decode(fixture(sw4))
        for key in ('officer_0_proficiency_0', 'officer_0_proficiency_1',
                    'officer_0_proficiency_2', 'officer_55_proficiency_0'):
            with self.subTest(key=key), self.assertRaises(SaveError):
                sw4.stage(document, {}, key, 20)
        encoded = sw4.serialize(document, {'gold': 20})
        self.assertEqual(encoded[0xC44:0xC48], document.raw[0xC44:0xC48])
        self.assertEqual(encoded[0xC2A:0xC3A], document.raw[0xC2A:0xC3A])

    def test_checksum_covered_unknown_bytes_reject_and_uncovered_tail_preserves(self):
        raw = bytearray(fixture(sw4))
        # The native d-section checksum term is multiplied by a-section sum.
        # Use a nonzero a-section as genuine exports do; zero would cancel d.
        raw[8] = 1
        raw = sw4.seal(bytes(raw))
        for offset in (0x10, 0x100, 0xD00, 0x8000, 0x10000, 0x50000):
            altered = bytearray(raw)
            altered[offset] ^= 0x5A
            with self.subTest(offset=hex(offset)), self.assertRaises(SaveError):
                sw4.decode(bytes(altered))
        # Native section checksums deliberately do not cover the capacity tail.
        altered = bytearray(raw)
        altered[-53:] = bytes(range(53))
        document = sw4.decode(bytes(altered))
        encoded = sw4.serialize(document, {'gold': 123})
        self.assertEqual(encoded[-53:], bytes(range(53)))

    def test_forged_foreign_snapshot_rejects_before_any_output(self):
        for backend in (dw7, sw4):
            with tempfile.TemporaryDirectory() as folder, self.subTest(game=backend.GAME_ID):
                source = Path(folder) / 'copy.bin'
                source.write_bytes(fixture(backend))
                document = backend.read_save(source)
                foreign = replace(document, format=replace(document.format, id='foreign'))
                for operation in (lambda: backend.backup(foreign),
                                  lambda: backend.maximums(foreign, {}),
                                  lambda: backend.save_as(foreign, {}, Path(folder) / 'foreign.bin')):
                    with self.assertRaises(SaveError):
                        operation()
                self.assertFalse((Path(folder) / 'foreign.bin').exists())

    def test_restore_rechecks_exact_replaced_bytes_after_manifest_rehash(self):
        for backend in (dw7, sw4):
            with tempfile.TemporaryDirectory() as folder, self.subTest(game=backend.GAME_ID):
                source = Path(folder) / 'copy.bin'
                source.write_bytes(fixture(backend))
                document = backend.read_save(source)
                backup = backend.backup(document)
                real_restore = backend.restore_snapshot
                destination = Path(folder) / 'restore.bin'

                def swap_then_restore(*args, **kwargs):
                    altered = b'junk' + document.raw[4:]
                    backup.write_bytes(altered)
                    manifest = backup.with_suffix('.json')
                    metadata = json.loads(manifest.read_text(encoding='utf-8'))
                    metadata['sha256'] = hashlib.sha256(altered).hexdigest()
                    manifest.write_text(json.dumps(metadata), encoding='utf-8')
                    return real_restore(*args, **kwargs)

                with patch.object(backend, 'restore_snapshot', side_effect=swap_then_restore):
                    with self.assertRaises(SaveError):
                        backend.restore(backup, destination)
                self.assertFalse(destination.exists())
