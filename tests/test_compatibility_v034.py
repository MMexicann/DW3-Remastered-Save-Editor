"""Dynamic tagged-array and historical-growth compatibility regressions.

Player fixtures remain private, optional workspace copies. Binary edge cases
are constructed in memory; no supplied file or installed-game save is changed.
"""
from pathlib import Path
import hashlib
import struct
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / 'tests'))
import bodyguard_editor as guard
import bodyguard_growth as growth
from models import Change, SaveError, fields
from save_codec import encrypt
from save_parser import ARRAY_LAYOUTS, parse_bytes, read_save
from save_writer import serialize
from test_bodyguards import edited_fixture_bytes, enum_bytes, record_bytes, tag_bytes

ORIGINAL = WORKSPACE / 'work/original-upload/GameStatusData.sav'
REPORTS = WORKSPACE / 'work/received-v034'


class SavedGrowthContractTests(unittest.TestCase):
    def test_historical_bow_growth_does_not_require_reearning_it(self):
        levels = [0, 1, 11, 1, 3, 1]
        self.assertEqual(growth.spent(levels), growth.budget(45228))
        self.assertEqual(growth.validate_saved_growth(45228, levels), tuple(levels))
        with self.assertRaises(ValueError):
            growth.validate_growth(45228, levels)
        self.assertEqual(growth.advance_automatic_levels(99999, levels), [0, 1, 11, 3, 3, 3])
        self.assertEqual(levels, [0, 1, 11, 1, 3, 1])

    def test_saved_profile_still_requires_known_six_level_representation(self):
        for levels in ([0] * 5, [0] * 7, [0, 0, 0, 0, 4, 0], [12, 0, 0, 0, 0, 0]):
            with self.subTest(levels=levels), self.assertRaises(ValueError):
                growth.validate_saved_growth(99999, levels)


@unittest.skipUnless(ORIGINAL.exists(), 'The explicitly supplied workspace fixture is required.')
class TaggedArrayCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hash = hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
        cls.document = read_save(ORIGINAL)

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == cls.hash

    def reshaped(self, name, count):
        prop = self.document.properties[name]
        if ARRAY_LAYOUTS[name] is None:
            values = prop['value']['values']
            payload = struct.pack('<i', count) + bytes(values[i % len(values)] for i in range(count))
        else:
            records = self.document.records(name)
            payload = struct.pack('<i', count) + b''.join(
                record_bytes(self.document, name, min(i, len(records) - 1)) for i in range(count))
        return parse_bytes(edited_fixture_bytes(self.document, [(prop, payload)]))

    def test_every_supported_top_array_uses_its_saved_length(self):
        for name in ARRAY_LAYOUTS:
            original_count = self.document.properties[name]['value']['count']
            for count in (0, 1, original_count + 1):
                with self.subTest(name=name, count=count):
                    document = self.reshaped(name, count)
                    self.assertEqual(document.properties[name]['value']['count'], count)
                    self.assertEqual(serialize(document)[0], document.encrypted)

    def test_unique_inventory_expansion_to_104_preserves_unchanged_bytes(self):
        document = self.reshaped('UniqueWeaponDataArray', 104)
        self.assertEqual(len(document.records('UniqueWeaponDataArray')), 104)
        self.assertEqual(serialize(document)[0], document.encrypted)

    def test_unrelated_merit_edit_preserves_expanded_future_inventory(self):
        document = self.reshaped('GuardEquipItemDataArray', 12)
        edited = parse_bytes(serialize(document, [Change('officer', 0, 'SPoint', 99998)])[0])
        self.assertEqual(tag_bytes(document, document.properties['GuardEquipItemDataArray']),
                         tag_bytes(edited, edited.properties['GuardEquipItemDataArray']))
        self.assertEqual(set(guard.item_state(document)), set(range(10)))

    def test_record_count_mismatch_and_negative_count_are_not_compatibility(self):
        for name in ARRAY_LAYOUTS:
            prop = self.document.properties[name]
            original = self.document.plaintext[prop['data_offset']:prop['data_offset'] + prop['data_size']]
            for count in (-1, prop['value']['count'] + 1, prop['value']['count'] - 1):
                with self.subTest(name=name, count=count), self.assertRaises(SaveError):
                    parse_bytes(edited_fixture_bytes(self.document, [(prop, struct.pack('<i', count) + original[4:])]))

    def test_nonboolean_unlock_byte_is_rejected(self):
        prop = self.document.properties['CanUseCharaArray']
        payload = bytearray(self.document.plaintext[prop['data_offset']:prop['data_offset'] + prop['data_size']])
        payload[4] = 2
        with self.assertRaises(SaveError):
            parse_bytes(edited_fixture_bytes(self.document, [(prop, bytes(payload))]))

    def test_noneditable_boolean_arrays_still_require_real_boolean_bytes(self):
        prop = self.document.properties['TutorialPlayedFlagArray']
        payload = bytearray(self.document.plaintext[prop['data_offset']:prop['data_offset'] + prop['data_size']])
        payload[4] = 3
        with self.assertRaises(SaveError):
            parse_bytes(edited_fixture_bytes(self.document, [(prop, bytes(payload))]))

    def test_unchanged_unknown_family_ref_does_not_block_another_equipment_choice(self):
        prop = fields(self.document.records('GuardDataArray')[0])['MemberWeapon']
        original = list(prop['value']['values'])
        original[0] = 999
        document = parse_bytes(edited_fixture_bytes(self.document, [
            (prop, struct.pack('<i10i', 10, *original))]))
        choices = list(original)
        choices[1] = -1
        edited = parse_bytes(serialize(document, [Change('bodyguard', 0, 'MemberWeapon', choices)])[0])
        self.assertEqual(guard.team_state(edited, 0)['MemberWeapon'][0], 999)
        self.assertEqual(guard.team_state(edited, 0)['MemberWeapon'][1], -1)
        # Introducing a new unknown reference in another family is rejected.
        choices[2] = 999
        with self.assertRaises(SaveError):
            serialize(document, [Change('bodyguard', 0, 'MemberWeapon', choices)])

    def test_unknown_enum_member_is_preserved_but_wrong_namespace_is_rejected(self):
        prop = fields(self.document.records('GuardWeaponDataArray')[0])['WeaponID']
        unknown = parse_bytes(edited_fixture_bytes(self.document, [(prop, enum_bytes('EWeaponID::FutureSword'))]))
        self.assertTrue(unknown.compatibility_warnings)
        self.assertEqual(serialize(unknown)[0], unknown.encrypted)
        state = guard.weapon_state(unknown)[0]
        self.assertFalse(state['empty'])
        self.assertFalse(state['editable'])
        with self.assertRaises(SaveError):
            parse_bytes(edited_fixture_bytes(self.document, [(prop, enum_bytes('OtherWeaponID::FutureSword'))]))

    def test_saved_item_values_outside_edit_limits_are_not_erased(self):
        prop = fields(self.document.records('EquipItemDataArray')[0])['Value']
        document = parse_bytes(edited_fixture_bytes(self.document, [(prop, struct.pack('<i', 1234))]))
        self.assertTrue(document.compatibility_warnings)
        edited = parse_bytes(serialize(document, [Change('officer', 0, 'SPoint', 99998)])[0])
        self.assertEqual(fields(edited.records('EquipItemDataArray')[0])['Value']['value'], 1234)
        self.assertEqual(serialize(document, [Change('item', 0, 'Value', 1234)])[0], document.encrypted)
        with self.assertRaises(SaveError):
            serialize(document, [Change('item', 0, 'Value', 1235)])

    def test_unknown_growth_shape_is_view_only_and_survives_unrelated_edit(self):
        prop = fields(self.document.records('GuardDataArray')[0])['BGLevels']
        payload = struct.pack('<i7i', 7, 0, 0, 0, 0, 0, 0, 1)
        document = parse_bytes(edited_fixture_bytes(self.document, [(prop, payload)]))
        self.assertTrue(document.compatibility_warnings)
        self.assertFalse(guard.team_state(document, 0)['growth_editable'])
        self.assertEqual(serialize(document)[0], document.encrypted)
        edited = parse_bytes(serialize(document, [Change('officer', 0, 'SPoint', 99998)])[0])
        self.assertEqual(tag_bytes(document, document.properties['GuardDataArray']),
                         tag_bytes(edited, edited.properties['GuardDataArray']))

    def test_engine_patch_number_is_descriptive_but_new_serialization_is_rejected(self):
        # GVAS begins at 4; three format ints precede the engine UInt16 triplet.
        plain = bytearray(self.document.plaintext)
        struct.pack_into('<H', plain, 24, 2)
        document = parse_bytes(encrypt(bytes(plain)))
        self.assertEqual(document.parsed['header']['engine'], [5, 6, 2])
        self.assertTrue(document.compatibility_warnings)
        self.assertEqual(serialize(document)[0], document.encrypted)
        struct.pack_into('<i', plain, 16, 1018)
        with self.assertRaises(SaveError):
            parse_bytes(encrypt(bytes(plain)))


@unittest.skipUnless(REPORTS.exists() and len(list(REPORTS.glob('*.sav'))) == 2,
                     'The two explicitly supplied reporter saves are required.')
class ReportedCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = sorted(REPORTS.glob('*.sav'))
        cls.hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in cls.inputs}
        cls.documents = [read_save(p) for p in cls.inputs]

    @classmethod
    def tearDownClass(cls):
        for path, digest in cls.hashes.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest

    def test_both_player_reports_open_and_roundtrip_without_any_change(self):
        for document in self.documents:
            with self.subTest(source=document.source.name):
                raw, audit = serialize(document)
                self.assertEqual(raw, document.encrypted)
                self.assertEqual(audit['plaintext_changes'], [])

    def test_104_unique_slots_and_six_teams_are_detected_from_the_save(self):
        document = self.documents[1]
        self.assertEqual(len(document.records('UniqueWeaponDataArray')), 104)
        self.assertEqual(len(document.records('GuardDataArray')), 6)

    def test_historical_growth_report_accepts_merit_increase_and_preserves_bow(self):
        document = self.documents[0]
        edited = parse_bytes(serialize(document, [Change('bodyguard', 3, 'SPoint', 99999)])[0])
        state = guard.team_state(edited, 3)
        self.assertEqual(state['SPoint'], 99999)
        self.assertEqual(state['BGLevels'], [0, 1, 11, 3, 3, 3])
        for index in range(3):
            self.assertEqual(record_bytes(document, 'GuardDataArray', index),
                             record_bytes(edited, 'GuardDataArray', index))

    def test_historical_read_compatibility_does_not_allow_illegal_new_allocations(self):
        document = self.documents[0]
        for levels in ([11, 11, 11, 3, 3, 3], [0, 2, 11, 1, 3, 1]):
            with self.subTest(levels=levels), self.assertRaises(SaveError):
                serialize(document, [Change('bodyguard', 3, 'BGLevels', levels)])


if __name__ == '__main__':
    unittest.main()
