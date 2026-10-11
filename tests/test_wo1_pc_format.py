"""Original Warriors Orochi PC procedural and optional genuine-file checks."""
from dataclasses import replace
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.wo1_pc import wo1_codec as codec
from koei_editor.games.wo1_pc import wo1_parser as backend
from tests.scalar_contract import ScalarContractTests


@lru_cache(maxsize=1)
def procedural_raw():
    raw = bytearray((index * 23 + 11) & 255 for index in range(codec.SAVE_SIZE))
    struct.pack_into('<H', raw, 4, codec.REVISION)
    struct.pack_into('<I', raw, 8, 3000)  # Observed header, not a native integrity gate.
    for officer in range(backend.OFFICER_COUNT):
        start = backend.OFFICER_BASE + officer * backend.OFFICER_STRIDE
        raw[start] = officer % 99
        for weapon in range(backend.WEAPON_COUNT):
            offset = backend._weapon_offset(officer, weapon)
            raw[offset:offset + backend.WEAPON_STRIDE] = bytes(backend.WEAPON_STRIDE)
            struct.pack_into('<H', raw, offset, backend.EMPTY_WEAPON)
    first = backend._weapon_offset(0, 0)
    struct.pack_into('<HHBB', raw, first, 2, (1 << 0) | (1 << 5) | (1 << 14), 3, 7)
    raw[first + 6] = 2
    raw[first + 11] = 3  # Unqualified enum five is preserved.
    raw[first + 20] = 98  # Real early player save uses displayed rank 99.
    last = backend._weapon_offset(78, 7)
    struct.pack_into('<HHBB', raw, last, 315, 0, 0, 0)
    struct.pack_into('<I', raw, backend.STOCK_EXP_OFFSET, 347)
    return codec.encode(raw)


class OrochiPCFormatTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / 'wo1-copy.dat'
        self.source.write_bytes(procedural_raw())
        self.document = backend.read_save(self.source)

    def test_original_profile_revision_integrity_and_foreign_editions(self):
        raw = procedural_raw()
        self.assertEqual(backend.serialize(self.document, {}), raw)
        for bad in (None, [], memoryview(raw), b'', raw[:-1], raw + b'\0', bytes(len(raw))):
            with self.subTest(kind=type(bad).__name__), self.assertRaises(SaveError):
                codec.decode(bad)
        from tests.test_orochiz_format import procedural_raw as orochiz_raw
        from tests.test_sw2_pc_format import procedural_raw as sw2_raw
        for foreign in (orochiz_raw(), sw2_raw(), b'PSU\0' + raw):
            with self.assertRaises(SaveError):
                codec.decode(foreign)
        for offset in (4, 1000, codec.CHECKSUM_OFFSET, codec.CHECKSUM_OFFSET + 3):
            changed = bytearray(raw)
            changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(SaveError):
                codec.decode(changed)
        changed = bytearray(raw)
        changed[:4] = b'\x12\x34\x56\x78'
        changed[6:8] = b'\xa5\x5a'
        changed[8:12] = b'\xfe\xca\xad\x0b'
        changed[-28:] = bytes(range(28))
        changed = codec.encode(changed)
        self.assertEqual(codec.decode(changed), changed)
        saved = backend.serialize(backend.decode(changed), {'stock_exp': 2000})
        self.assertEqual(saved[:4], changed[:4])
        self.assertEqual(saved[6:12], changed[6:12])
        self.assertEqual(saved[-28:], changed[-28:])

    def test_existing_own_family_fields_and_rank_encoding(self):
        fields = backend.field_map(self.document)
        self.assertEqual(len(fields), 7)
        key = 'officer_0_weapon_0_attribute_0_level'
        self.assertEqual(fields[key].value(self.document.payload), 3)
        self.assertEqual(fields['officer_0_weapon_0_attribute_14_level'].value(self.document.payload), 99)
        for unknown in ('officer_0_weapon_0_attribute_5_level', 'officer_0_weapon_1_attack_bonus',
                        'officer_0_weapon_0_id', 'officer_0_level', 'officer_0_exp',
                        'officer_0_proficiency', 'officer_0_skill', 'story_clear'):
            with self.subTest(key=unknown), self.assertRaises(SaveError):
                backend.stage(self.document, {}, unknown, 1)
        pending = backend.stage(self.document, {}, key, 10)
        result = backend.serialize(self.document, pending)
        self.assertEqual(result[fields[key].offset], 9)
        self.assertEqual(backend.stage(self.document, pending, key, 3), {})

    def test_max_preserves_higher_values_resources_and_unqualified_effects(self):
        raw = self.document.raw
        maximum = backend.maximums(self.document, {})
        self.assertEqual(maximum, {'officer_0_weapon_0_attribute_0_level': 10})
        result = backend.serialize(self.document, maximum)
        first = backend._weapon_offset(0, 0)
        self.assertEqual(result[first:first + 6], raw[first:first + 6])
        self.assertEqual(result[first + 11], raw[first + 11])
        self.assertEqual(result[first + 20], 98)
        self.assertEqual(result[backend.STOCK_EXP_OFFSET:backend.STOCK_EXP_OFFSET + 4],
                         raw[backend.STOCK_EXP_OFFSET:backend.STOCK_EXP_OFFSET + 4])
        key = 'officer_0_weapon_0_attribute_14_level'
        pending = backend.stage(self.document, {}, key, 10)
        self.assertEqual(backend.stage(self.document, pending, key, 99), {})

    def test_capacity_dependencies_unknown_mask_and_cross_family_are_preserved(self):
        first = backend._weapon_offset(0, 0)
        for offset, value in ((first + 4, 2), (first + 4, 9), (first + 3, 0x80), (first, 4)):
            raw = bytearray(self.document.raw)
            raw[offset] = value
            doc = backend.decode(codec.encode(raw))
            self.assertFalse(any(field.id.startswith('officer_0_weapon_0_')
                                 for field in backend.fields_for(doc)))
            result = backend.serialize(doc, backend.maximums(doc, {}))
            self.assertEqual(result[first:first + backend.WEAPON_STRIDE], raw[first:first + backend.WEAPON_STRIDE])
        for value in (2, 9, -1, True, 3.0, '4'):
            with self.subTest(value=value), self.assertRaises(SaveError):
                backend.stage(self.document, {}, 'officer_0_weapon_0_attribute_slots', value)

    def test_surgical_manual_storage_bounds_and_batch_atomicity(self):
        cases = {'stock_exp': 0xFFFFFFFF, 'officer_0_weapon_0_attack_bonus': 255,
                 'officer_0_weapon_0_attribute_slots': 8, 'officer_78_weapon_7_attack_bonus': 1}
        fields = backend.field_map(self.document)
        for key, value in cases.items():
            result = backend.serialize(self.document, backend.stage(self.document, {}, key, value))
            self.assertEqual(fields[key].value(backend.decode(result).payload), value)
            allowed = set(range(fields[key].offset, fields[key].offset + fields[key].size)) | set(
                range(codec.CHECKSUM_OFFSET, codec.CHECKSUM_OFFSET + 4))
            self.assertLessEqual({i for i, (a, b) in enumerate(zip(self.document.raw, result)) if a != b}, allowed)
        for changes in ({'ghost': 1}, {'stock_exp': -1}, {'stock_exp': True}, [], None):
            with self.subTest(changes=changes), self.assertRaises(SaveError):
                backend.stage(self.document, changes, 'stock_exp', 100)
        for key in (None, [], {}, True):
            with self.subTest(key=key), self.assertRaises(SaveError):
                backend.stage(self.document, {}, key, 100)
        with self.assertRaises(SaveError):
            backend.stage(self.document, {}, 'stock_exp', 0x100000000)
        with self.assertRaises(SaveError):
            backend.stage(self.document, {}, 'officer_0_weapon_0_attack_bonus', 256)
        self.assertEqual(self.source.read_bytes(), self.document.raw)

    def test_forged_snapshots_review_backups_restore_and_source_change(self):
        doc = self.document
        for forged in (replace(doc, raw=bytearray(doc.raw)), replace(doc, payload=bytearray(doc.payload)),
                       replace(doc, format=replace(doc.format)),
                       replace(doc, payload=doc.payload[:-1] + b'\0')):
            with self.assertRaises(SaveError):
                backend.serialize(forged, {})
        self.assertEqual([(f.id, old, new) for f, old, new in backend.review(doc, {'stock_exp': 1000})],
                         [('stock_exp', 347, 1000)])
        saved = backend.save_as(doc, {'stock_exp': 1000}, self.folder / 'edited.dat')
        self.assertEqual(backend.field_map(saved)['stock_exp'].value(saved.payload), 1000)
        backup = backend.backup(doc)
        self.assertEqual(backend.restore(backup, self.folder / 'restored.dat').read_bytes(), doc.raw)
        with self.assertRaises(FileExistsError):
            backend.save_as(doc, {}, saved.source)
        self.source.write_bytes(doc.raw[:-1] + b'\0')
        with self.assertRaises(SaveError):
            backend.save_as(doc, {}, self.folder / 'changed.dat')
        self.assertFalse((self.folder / 'changed.dat').exists())
        corrupted = bytearray(backup.read_bytes())
        corrupted[100] ^= 1
        backup.write_bytes(corrupted)
        manifest = backup.with_suffix('.json')
        metadata = json.loads(manifest.read_text())
        metadata['sha256'] = hashlib.sha256(corrupted).hexdigest()
        manifest.write_text(json.dumps(metadata))
        with self.assertRaises(SaveError):
            backend.restore(backup, self.folder / 'corrupt.dat')
        self.assertFalse((self.folder / 'corrupt.dat').exists())

    @unittest.skipUnless(os.environ.get('WO1_NATIVE_SAVES'), 'Private original PC fixtures not supplied')
    def test_genuine_unchanged_and_every_qualified_field_surgical(self):
        count = 0
        paths = list(Path(os.environ['WO1_NATIVE_SAVES']).glob('*.dat'))
        self.assertTrue(paths, 'The supplied genuine fixture directory contains no .dat copies.')
        for path in paths:
            raw = path.read_bytes()
            doc = backend.decode(raw)
            self.assertEqual(backend.serialize(doc, {}), raw)
            for field in backend.fields_for(doc):
                original = field.value(raw)
                choices = backend.field_options(doc, field.id)
                value = (next(choice for choice, _ in choices if choice != original)
                         if choices else
                         field.minimum if original != field.minimum else field.maximum)
                result = backend.serialize(doc, {field.id: value})
                self.assertEqual(field.value(backend.decode(result).payload), value)
                allowed = set(range(field.offset, field.offset + field.size)) | set(
                    range(codec.CHECKSUM_OFFSET, codec.CHECKSUM_OFFSET + 4))
                self.assertLessEqual({i for i, (a, b) in enumerate(zip(raw, result)) if a != b}, allowed)
                self.assertEqual(backend.stage(doc, {field.id: value}, field.id, original), {})
                count += 1
            maximum = backend.maximums(doc, {})
            edited = backend.serialize(doc, maximum)
            for field in backend.fields_for(doc):
                if not field.maxable or field.value(raw) > field.maximum:
                    self.assertNotIn(field.id, maximum)
                    self.assertEqual(field.value(edited), field.value(raw))
            self.assertEqual(path.read_bytes(), raw)
        self.assertGreater(count, 0)


class OrochiPCScalarContract(ScalarContractTests, unittest.TestCase):
    game_id = 'wo1'
    payload_integrity_offsets = frozenset(range(codec.CHECKSUM_OFFSET, codec.CHECKSUM_OFFSET + 4))

    def fixture_bytes(self):
        return procedural_raw()
