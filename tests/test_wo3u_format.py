"""Procedural safety regressions; optional genuine sample remains private."""
from dataclasses import replace
import os
from pathlib import Path
import tempfile
import unittest

from models import SaveError
import wo3u_parser as parser


def procedural_raw():
    # This deliberately patterned buffer is not a playable or genuine save.
    raw = bytearray((index * 17 + 3) & 255 for index in range(parser.SAVE_SIZE))
    raw[:4] = parser.SIGNATURE
    for index in range(parser.SERIALIZED_OFFICER_COUNT):
        offset = parser.OFFICER_BASE + index * parser.OFFICER_STRIDE
        raw[offset - 10:offset - 6] = bytes.fromhex('a86d7f7f')
        for stat in range(5):
            raw[offset + stat * 2:offset + stat * 2 + 2] = (100 + index).to_bytes(2, 'little')
    for index in range(parser.WEAPON_COUNT):
        offset = parser.WEAPON_BASE + index * parser.WEAPON_STRIDE
        raw[offset - 4:offset] = bytes.fromhex('28627f7f')
        raw[offset:offset + 3] = b'\xff\xff\xff'
        raw[offset + 4:offset + 12] = b'\xff' * 8
    offset = parser.WEAPON_BASE
    raw[offset:offset + 3] = b'\x02\x00\x02'
    raw[offset + 4:offset + 6] = bytes([5, 31])
    raw[offset + 12:offset + 14] = bytes([2, 1])
    return bytes(raw)


class WO3FormatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = procedural_raw()
        cls.document = parser.decode(cls.raw)

    def test_noop_is_byte_exact(self):
        self.assertEqual(parser.serialize(self.document, {}), self.raw)

    def test_title_size_and_platform_rejection(self):
        for raw in (b'', self.raw[:-1], self.raw + b'0', b'\0' * len(self.raw),
                    b'MZ\0\0' + self.raw[4:]):
            with self.subTest(length=len(raw)), self.assertRaises(SaveError):
                parser.decode(raw)
        with self.assertRaises(SaveError):
            parser.decode(self.raw, 'wo3_ps3')

    def test_record_revision_corruption_rejected(self):
        for offset in (parser.OFFICER_BASE - 10,
                       parser.OFFICER_BASE + 149 * parser.OFFICER_STRIDE - 10,
                       parser.WEAPON_BASE - 4,
                       parser.WEAPON_BASE + 2319 * parser.WEAPON_STRIDE - 4):
            raw = bytearray(self.raw)
            raw[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(SaveError):
                parser.decode(raw)

    def test_aslr_fragments_are_preserved_and_supported(self):
        raw = bytearray(self.raw)
        for count, base, stride in ((150, parser.OFFICER_BASE - 10, parser.OFFICER_STRIDE),
                                    (2320, parser.WEAPON_BASE - 4, parser.WEAPON_STRIDE)):
            for index in range(count):
                raw[base + index * stride + 2:base + index * stride + 4] = b'\x12\x34'
        document = parser.decode(raw)
        self.assertEqual(parser.serialize(document, {}), raw)
        edited = parser.serialize(document, {'officer_0_attack': 500})
        self.assertEqual(edited[parser.WEAPON_BASE - 4:parser.WEAPON_BASE], b'\x28\x62\x12\x34')

    def test_targeted_edit_changes_only_proven_bytes(self):
        for key in ('growth_points', 'gems', 'officer_0_attack', 'officer_144_speed',
                    'orb_57', 'material_6_144', 'weapon_0_slots', 'weapon_0_rank_0'):
            field = parser.field_map(self.document)[key]
            changes = parser.stage(self.document, {}, key, field.maximum)
            raw = parser.serialize(self.document, changes)
            touched = {index for index, pair in enumerate(zip(self.raw, raw)) if pair[0] != pair[1]}
            self.assertLessEqual(touched, set(range(field.offset, field.offset + field.size)))
            self.assertEqual(field.value(parser.decode(raw).payload), field.maximum)
            self.assertEqual(self.document.raw, self.raw)

    def test_staging_is_immutable_and_can_unstage(self):
        pending = {}
        changes = parser.stage(self.document, pending, 'officer_0_attack', 500)
        self.assertEqual(pending, {})
        self.assertEqual(changes, {'officer_0_attack': 500})
        self.assertEqual(parser.stage(self.document, changes, 'officer_0_attack', 100), {})
        self.assertEqual([(field.id, old, new) for field, old, new in parser.review(self.document, changes)],
                         [('officer_0_attack', 100, 500)])

    def test_fields_do_not_rewrite_empty_internal_or_unknown_records(self):
        keys = parser.field_map(self.document)
        self.assertNotIn('officer_145_attack', keys)
        self.assertNotIn('weapon_1_slots', keys)
        self.assertNotIn('weapon_0_rank_2', keys)
        raw = bytearray(self.raw)
        raw[parser.WEAPON_BASE + 4] = 222
        document = parser.decode(raw)
        self.assertNotIn('weapon_0_rank_0', parser.field_map(document))
        edited = parser.serialize(document, parser.maximums(document, {}))
        self.assertEqual(edited[parser.WEAPON_BASE + 4], 222)
        offset = parser.OFFICER_BASE + 145 * parser.OFFICER_STRIDE
        self.assertEqual(edited[offset:offset + 5 * parser.OFFICER_STRIDE], raw[offset:offset + 5 * parser.OFFICER_STRIDE])

    def test_zero_rank_and_unproven_resource_caps_are_excluded_from_bulk(self):
        raw = bytearray(self.raw)
        raw[parser.WEAPON_BASE + 12] = 0
        document = parser.decode(raw)
        self.assertNotIn('weapon_0_rank_0', parser.field_map(document))
        maximums = parser.maximums(document, {})
        self.assertNotIn('growth_points', maximums)
        self.assertNotIn('gems', maximums)
        self.assertFalse(any(key.startswith(('orb_', 'material_')) for key in maximums))

    def test_binary_and_ranked_attributes_have_distinct_limits(self):
        keys = parser.field_map(self.document)
        self.assertEqual(keys['weapon_0_rank_0'].maximum, 10)
        self.assertEqual(keys['weapon_0_rank_1'].maximum, 1)
        with self.assertRaises(SaveError):
            parser.stage(self.document, {}, 'weapon_0_rank_1', 10)

    def test_slot_reduction_preserves_existing_attributes(self):
        with self.assertRaises(SaveError):
            parser.stage(self.document, {}, 'weapon_0_slots', 1)
        changes = parser.stage(self.document, {}, 'weapon_0_slots', 8)
        self.assertEqual(parser.serialize(self.document, changes)[parser.WEAPON_BASE + 4:parser.WEAPON_BASE + 20],
                         self.raw[parser.WEAPON_BASE + 4:parser.WEAPON_BASE + 20])

    def test_slot_expansion_does_not_activate_dormant_attributes(self):
        raw = bytearray(self.raw)
        raw[parser.WEAPON_BASE + 7] = 222
        raw[parser.WEAPON_BASE + 15] = 0
        document = parser.decode(raw)
        field = parser.field_map(document)['weapon_0_slots']
        self.assertFalse(field.maxable)
        self.assertNotIn(field.id, parser.maximums(document, {}, group='Weapons'))
        with self.assertRaises(SaveError):
            parser.stage(document, {}, field.id, 4)
        changes = parser.stage(document, {}, field.id, 3)
        edited = parser.serialize(document, changes)
        self.assertEqual(edited[parser.WEAPON_BASE + 2], 3)
        self.assertEqual(edited[parser.WEAPON_BASE + 4:parser.WEAPON_BASE + 20],
                         raw[parser.WEAPON_BASE + 4:parser.WEAPON_BASE + 20])

    def test_max_preserves_higher_existing_values_and_unknowns(self):
        raw = bytearray(self.raw)
        raw[parser.OFFICER_BASE:parser.OFFICER_BASE + 2] = (5000).to_bytes(2, 'little')
        raw[parser.WEAPON_BASE + 12] = 200
        raw[0xE944] = 200
        document = parser.decode(raw)
        maximums = parser.maximums(document, {})
        for key in ('officer_0_health', 'weapon_0_rank_0', 'orb_0'):
            self.assertNotIn(key, maximums)
        self.assertEqual(parser.serialize(document, maximums)[parser.WEAPON_BASE + 12], 200)

    def test_wrong_fields_bounds_and_mutated_snapshot_rejected(self):
        for key, value in [('officer_0_attack', True), ('officer_0_attack', -1),
                           ('officer_0_attack', 1000), ('weapon_0_slots', 9),
                           ('__unknown', 2)]:
            with self.subTest(key=key, value=value), self.assertRaises(SaveError):
                parser.stage(self.document, {}, key, value)
        with self.assertRaises(SaveError):
            parser.serialize(replace(self.document, payload=self.raw[:-1] + b'X'), {})
        with self.assertRaises(SaveError):
            parser.serialize(replace(self.document, format=replace(parser.FORMAT, id='wo3_ps3')), {})

    def test_backup_save_as_restore_and_changed_source_safety(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            source = folder / 'copy.bin'
            source.write_bytes(self.raw)
            document = parser.read_save(source)
            backup = parser.backup(document)
            self.assertEqual(backup.read_bytes(), self.raw)
            edited = parser.save_as(document, {'officer_0_attack': 500}, folder / 'edited.bin')
            self.assertEqual(source.read_bytes(), self.raw)
            self.assertEqual(parser.field_map(edited)['officer_0_attack'].value(edited.payload), 500)
            with self.assertRaises(FileExistsError):
                parser.save_as(document, {}, edited.source)
            restored = parser.restore(backup, folder / 'restored.bin')
            self.assertEqual(restored.read_bytes(), self.raw)
            source.write_bytes(self.raw[:-1] + b'X')
            with self.assertRaises(SaveError):
                parser.save_as(document, {}, folder / 'changed.bin')
            self.assertFalse((folder / 'changed.bin').exists())

    def test_progression_is_read_only(self):
        rows = parser.inspection_rows(self.document)
        self.assertEqual(len([row for row in rows if row['group'] == 'Progression']), 150)
        self.assertTrue(any('Verity' in row['value'] for row in rows if row['group'] == 'Weapons'))
        for key in ('officer_0_level', 'officer_0_promotions', 'officer_0_experience', 'story_complete'):
            with self.assertRaises(SaveError):
                parser.stage(self.document, {}, key, 1)


@unittest.skipUnless(os.environ.get('WO3U_SAVE_COPY'), 'Private native Steam WO3 copy unavailable')
class NativeWO3Tests(unittest.TestCase):
    def test_copied_native_roundtrip_and_targeted_edit(self):
        document = parser.read_save(os.environ['WO3U_SAVE_COPY'])
        self.assertEqual(parser.serialize(document, {}), document.raw)
        field = parser.field_map(document)['officer_0_attack']
        value = 998 if field.value(document.payload) == 999 else 999
        changes = parser.stage(document, {}, field.id, value)
        edited = parser.serialize(document, changes)
        self.assertEqual(field.value(parser.decode(edited).payload), value)
        self.assertTrue(all(old == new for index, (old, new) in enumerate(zip(document.raw, edited))
                            if not field.offset <= index < field.offset + field.size))
        self.assertEqual(Path(document.source).read_bytes(), document.raw)
