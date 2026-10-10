"""Bounds and existing-record qualification for native progression fields."""
import unittest

import koei_editor.games.origins.origins_progression as progression


class ProgressionTests(unittest.TestCase):
    def test_revision_layouts_and_formed_bonds(self):
        for revision, peace_base in progression.PEACE_BASES.items():
            with self.subTest(revision=revision):
                payload = bytearray(0x271660)
                bond = progression.BOND_BASES[revision] + 7 * 5
                payload[bond] = 2
                payload[bond + 2:bond + 4] = (4).to_bytes(2, 'little')
                fields = {q['id']: q for q in progression.progression_specs(payload, revision)}
                self.assertEqual(len(fields), 15 + len(progression.BATTLE_HISTORY_IDS))
                self.assertEqual(fields['peace_12']['offset'], peace_base + 24)
                self.assertEqual(fields['peace_12']['maximum'], 10000)
                self.assertEqual(fields['bond_7_level']['offset'], bond)
                self.assertEqual(fields['bond_7_level']['minimum'], 1)
                self.assertEqual(fields['bond_7_training']['offset'], bond + 2)
                self.assertFalse(fields['bond_7_training']['maxable'])

    def test_history_qualifies_catalogue_ids_only_and_preserves_unusual_bytes(self):
        for revision, base in progression.HISTORY_BASES.items():
            with self.subTest(revision=revision):
                payload = bytearray(0x271660)
                payload[base + 0] = 1
                payload[base + 19] = 2
                before = bytes(payload)
                fields = {q['id']: q for q in progression.progression_specs(payload, revision)}
                history = [q for q in fields.values() if q['group'] == 'Battle clear history']
                self.assertEqual(len(history), len(progression.BATTLE_HISTORY_IDS) - 1)
                self.assertEqual(fields['battle_history_0']['offset'], base)
                self.assertEqual(fields['battle_history_68']['offset'], base + 68)
                self.assertEqual(fields['battle_history_0']['maximum'], 1)
                self.assertEqual(fields['battle_history_0']['minimum'], 1)
                self.assertEqual(fields['battle_history_68']['minimum'], 0)
                self.assertFalse(fields['battle_history_0']['maxable'])
                self.assertNotIn('battle_history_19', fields)
                self.assertNotIn('battle_history_16', fields)
                self.assertNotIn('battle_history_70', fields)
                self.assertEqual(bytes(payload), before)

    def test_native_history_setter_does_not_allow_reset_of_original_clear(self):
        from koei_editor.games.origins.origins_parser import Field
        from koei_editor.games.dw3.models import SaveError
        payload = bytearray(0x271660)
        payload[progression.HISTORY_BASES[29]] = 1
        history = next(q for q in progression.progression_specs(payload, 29)
                       if q['id'] == 'battle_history_0')
        field = Field(**history)
        field.validate(1)
        with self.assertRaises(SaveError):
            field.validate(0)

    def test_verified_names_and_dynamic_or_placeholder_id_fallback(self):
        payload = bytearray(0x271660)
        for index in (0, 47, 48, 49, 99, 100):
            payload[progression.BOND_BASES[29] + index * 5] = 1
        fields = {q['id']: q for q in progression.progression_specs(payload, 29)}
        self.assertTrue(fields['peace_0']['label'].startswith('Sili Province'))
        self.assertTrue(fields['peace_12']['label'].startswith('Jiaozhi'))
        self.assertTrue(fields['bond_0_level']['label'].startswith('Xiahou Dun'))
        self.assertTrue(fields['bond_48_level']['label'].startswith('Zhuhe'))
        self.assertTrue(fields['bond_99_level']['label'].startswith('Yuanhua'))
        for index in (47, 49, 100):
            self.assertTrue(fields[f'bond_{index}_level']['label'].startswith(f'Bond ID {index}'))

    def test_unusual_values_preserved_and_not_exposed(self):
        payload = bytearray(0x271660)
        base = progression.BOND_BASES[29]
        payload[base] = 6
        payload[base + 5] = 1
        payload[base + 7:base + 9] = (1000).to_bytes(2, 'little')
        peace = progression.PEACE_BASES[29]
        payload[peace:peace + 2] = (10001).to_bytes(2, 'little')
        before = bytes(payload)
        fields = {q['id']: q for q in progression.progression_specs(payload, 29)}
        self.assertNotIn('bond_0_level', fields)
        self.assertNotIn('bond_1_training', fields)
        self.assertNotIn('peace_0', fields)
        self.assertIn('bond_1_level', fields)
        self.assertEqual(bytes(payload), before)

    def test_unknown_revision_and_short_body(self):
        self.assertEqual(progression.progression_specs(bytes(10), 29), [])
        self.assertEqual(progression.progression_specs(bytes(0x271660), 30), [])


if __name__ == '__main__':
    unittest.main()
