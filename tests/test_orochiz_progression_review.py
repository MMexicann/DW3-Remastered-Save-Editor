"""Independent equipment/EXP safety review; no game execution or player data."""
import os
from pathlib import Path
import struct
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.orochiz import orochiz_codec as codec
from koei_editor.games.orochiz import orochiz_parser as parser
from tests.test_orochiz_equipment import equipment_raw


def progressed_raw():
    raw = bytearray(equipment_raw())
    raw[0xC] = 1
    struct.pack_into('<I', raw, 0x1C, 1000)
    return codec.encode(raw)


class OrochiProgressionIndependentTests(unittest.TestCase):
    def test_combined_selector_exp_and_weapon_edits_preserve_all_dependencies(self):
        document = parser.decode(progressed_raw())
        changes = {'officer_0_equipped_weapon': 3, 'officer_0_exp_within_level': 1639,
                   'officer_0_weapon_2_attack_bonus': 20}
        output = parser.decode(parser.serialize(document, changes))
        before = parser.officers(document)
        for index, (original, edited) in enumerate(zip(before, parser.officers(output))):
            expected = dict(original)
            if index == 0:
                expected.update(exp=1639, equipped_slot=2)
            self.assertEqual(edited, expected)
        for index, (original, edited) in enumerate(zip(parser.weapons(document), parser.weapons(output))):
            expected = dict(original)
            if index == 2:
                expected['bonus'] = 20
            self.assertEqual(edited, expected)
        mapping = parser.field_map(document)
        allowed = {offset for key in changes for offset in range(mapping[key].offset,
                                                                 mapping[key].offset + mapping[key].size)}
        allowed.update(range(codec.CHECKSUM_OFFSET, codec.CHECKSUM_OFFSET + 4))
        self.assertLessEqual({i for i, (a, b) in enumerate(zip(document.raw, output.raw)) if a != b}, allowed)
        self.assertEqual(parser.maximums(document, {}, 'Officer growth'), {})
        self.assertEqual(parser.maximums(document, {}, 'Equipment'), {})

    def test_manual_groups_cannot_hide_invalid_pending_changes_during_max(self):
        document = parser.decode(progressed_raw())
        for pending in ({'officer_0_exp_within_level': 799}, {'officer_0_exp_within_level': 1640},
                        {'officer_0_equipped_weapon': 2}, {'officer_0_equipped_weapon': True},
                        {'officer_0_weapon_2_attribute_slots': -1}, {'unmapped_story': 1}):
            for group in ('Equipment', 'Officer growth', None):
                with self.subTest(pending=pending, group=group), self.assertRaises(SaveError):
                    parser.maximums(document, pending, group)

    def test_unusual_equipped_mask_capacity_and_growth_records_survive_resource_max(self):
        raw = bytearray(progressed_raw())
        raw[0xD] = 255
        raw[0xC] = 255
        raw[0x1C:0x20] = b'\xFF' * 4
        weapon = 0x20 + 2 * 24
        struct.pack_into('<H', raw, weapon + 2, 0x8000)
        raw[weapon + 6] = 255
        document = parser.decode(codec.encode(raw))
        self.assertNotIn('officer_0_exp_within_level', parser.field_map(document))
        self.assertNotIn('officer_0_equipped_weapon', parser.field_map(document))
        self.assertNotIn('officer_0_weapon_2_attack_bonus', parser.field_map(document))
        output = parser.decode(parser.serialize(document, parser.maximums(document, {}, 'Resources')))
        self.assertEqual(output.raw[0xC:0xE], document.raw[0xC:0xE])
        self.assertEqual(output.raw[0x1C:0x20], document.raw[0x1C:0x20])
        self.assertEqual(output.raw[weapon:weapon + 24], document.raw[weapon:weapon + 24])

    @unittest.skipUnless(os.environ.get('OROCHIZ_GROWTH_SAVE'), 'No private progressed native Orochi Z copy')
    def test_genuine_growth_and_selector_combination_preserves_officer_stats_and_inventory(self):
        path = Path(os.environ['OROCHIZ_GROWTH_SAVE'])
        raw = path.read_bytes()
        document = parser.decode(raw)
        mapping = parser.field_map(document)
        selected = next(field for field in mapping.values()
                        if field.id.endswith('_exp_within_level')
                        and f'officer_{field.slot - 1}_equipped_weapon' in mapping)
        key = f'officer_{selected.slot - 1}_equipped_weapon'
        choices = parser.field_options(document, key)
        value = next(value for value, _ in choices if value != mapping[key].value(raw))
        changes = {selected.id: selected.maximum, key: value}
        output = parser.decode(parser.serialize(document, changes))
        self.assertEqual(parser.weapons(output), parser.weapons(document))
        for original, edited in zip(parser.officers(document), parser.officers(output)):
            expected = dict(original)
            if original['id'] == selected.slot - 1:
                expected.update(exp=selected.maximum, equipped_slot=value - 1)
            self.assertEqual(edited, expected)
        self.assertEqual(path.read_bytes(), raw)

    @unittest.skipUnless(os.environ.get('OROCHIZ_NATIVE_SAVE'), 'No private native Orochi Z copy')
    def test_genuine_maximum_level_attachment_has_no_exp_write_or_level_repair(self):
        path = Path(os.environ['OROCHIZ_NATIVE_SAVE'])
        raw = path.read_bytes()
        document = parser.decode(raw)
        maxed = [row for row in parser.officers(document) if row['stored_level'] == 98]
        if not maxed:
            self.skipTest('This explicit native copy has no final-level officers')
        fields = parser.field_map(document)
        for row in maxed:
            self.assertNotIn(f"officer_{row['id']}_exp_within_level", fields)
        output = parser.decode(parser.serialize(document, parser.maximums(document, {}, 'Weapons')))
        self.assertEqual(parser.officers(output), parser.officers(document))
        self.assertEqual(path.read_bytes(), raw)
