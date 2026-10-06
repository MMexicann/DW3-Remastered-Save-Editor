"""Public bodyguard-rule regressions using shipped metadata, without a save.

These boundary cases protect the native shared-point budget, separate automatic
progression gates, and tier-specific weapon rolls. No game installation or
private player fixture is needed to run this module.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bodyguard_growth as growth
import bodyguard_editor as equipment
from models import SaveError


class BodyguardGrowthRules(unittest.TestCase):
    def test_shared_budget_progression_boundaries(self):
        cases = {0: 0, 999: 0, 1000: 1, 1999: 1, 2000: 2,
                 22999: 9, 23000: 10, 80999: 21, 81000: 22,
                 86999: 22, 87000: 23, 92999: 23, 93000: 24,
                 99998: 24, 99999: 25}
        for merit, expected in cases.items():
            with self.subTest(merit=merit):
                self.assertEqual(growth.budget(merit), expected)

    def test_six_displayed_levels_do_not_all_spend_points(self):
        levels = [6, 7, 7, 3, 3, 3]
        self.assertEqual(growth.validate_growth(92222, levels), tuple(levels))
        self.assertEqual(growth.spent(levels), 23)
        self.assertEqual(growth.budget(92222), 23)
        self.assertEqual(growth.spent([6, 7, 7, 0, 3, 0]), 23)
        with self.assertRaises(ValueError):
            growth.validate_growth(92222, [7, 7, 7, 3, 3, 3])

    def test_individual_maxima_exceed_the_legitimate_shared_cap(self):
        self.assertEqual(growth.spent([11, 11, 11, 3, 3, 3]), 36)
        with self.assertRaises(ValueError):
            growth.validate_growth(99999, [11, 11, 11, 3, 3, 3])
        growth.validate_growth(99999, [11, 11, 0, 3, 3, 3])

    def test_count_and_bow_gates_are_separate_from_ai_gates(self):
        cases = [(24999, 0, 0, 0), (25000, 1, 1, 0),
                 (29999, 1, 1, 0), (30000, 1, 1, 1),
                 (49999, 1, 1, 1), (50000, 2, 2, 1),
                 (59999, 2, 2, 1), (60000, 2, 2, 2),
                 (74999, 2, 2, 2), (75000, 3, 3, 2),
                 (89999, 3, 3, 2), (90000, 3, 3, 3)]
        for merit, count, bow, ai in cases:
            with self.subTest(merit=merit):
                caps = growth.earned_caps(merit)
                self.assertEqual((caps[3], caps[4], caps[5]), (count, bow, ai))
                growth.validate_growth(merit, [0, 0, 0, count, bow, ai])
                for index in (3, 4, 5):
                    if caps[index] < 3:
                        early = [0] * 6
                        early[index] = caps[index] + 1
                        with self.assertRaises(ValueError):
                            growth.validate_growth(merit, early)

    def test_automatic_levels_preserve_allocations_and_inputs(self):
        original = [6, 6, 7, 0, 3, 0]
        result = growth.automatic_levels(99999, original)
        self.assertEqual(original, [6, 6, 7, 0, 3, 0])
        self.assertEqual(result, [6, 6, 7, 3, 3, 3])
        # Lowering Merit is safe only when the allocated budget remains valid.
        self.assertEqual(growth.automatic_levels(0, [0, 0, 0, 3, 0, 3]), [0] * 6)
        with self.assertRaises(ValueError):
            growth.automatic_levels(0, original)

    def test_presets_spend_earned_points_without_overspending(self):
        # Include both sides of each allocation, Count, Bow and AI threshold.
        boundaries = set(growth.BUDGET_THRESHOLDS)
        boundaries.update((25000, 30000, 50000, 60000, 75000, 90000))
        merits = sorted(boundaries | {value - 1 for value in boundaries if value})
        for merit in merits:
            for mode in growth.PRESET_NAMES:
                with self.subTest(merit=merit, mode=mode):
                    levels = growth.safe_preset(merit, mode)
                    growth.validate_growth(merit, levels)
                    self.assertEqual(growth.spent(levels), growth.budget(merit))
                    caps = growth.earned_caps(merit)
                    self.assertEqual((levels[3], levels[4], levels[5]), (caps[3], caps[4], caps[5]))
        self.assertEqual(growth.safe_preset(), [8, 7, 7, 3, 3, 3])
        for mode, index in [('life', 0), ('attack', 1), ('defense', 2)]:
            self.assertEqual(growth.safe_preset(99999, mode)[index], 11)
        with self.assertRaises(ValueError):
            growth.safe_preset(99999, 'unknown')

    def test_growth_base_stats_and_percentage_units(self):
        # Native HP_Special plus the Bow/Moveset HP_Add produces BOTH outputs.
        base = growth.derive_stats([0] * 6)
        self.assertEqual((base['base_hp'], base['base_musou']), (150, 150))
        self.assertEqual((base['base_attack'], base['base_defense']), (40, 40))
        stats = growth.derive_stats([6, 7, 7, 3, 3, 3])
        self.assertEqual((stats['base_hp'], stats['base_musou']), (240, 240))
        self.assertEqual((stats['base_attack'], stats['base_defense']), (110, 110))
        self.assertEqual(stats['member_count'], 9)  # Native capacity field, not a follower-count claim.
        self.assertEqual(stats['bow_percent'], 80)
        self.assertEqual(stats['motion_level'], 2)
        self.assertEqual((stats['move'], stats['shift_move'], stats['jump']), (140, 88, 150))
        self.assertEqual(growth.derive_stats([11, 0, 0, 0, 0, 0])['base_hp'], 260)
        self.assertEqual(growth.derive_stats([11, 0, 0, 0, 3, 0])['base_hp'], 290)

    def test_malformed_growth_values_fail_explicitly(self):
        for merit in (-1, 100000, True, False, 99999.0, '99999', None):
            with self.subTest(merit=merit), self.assertRaises(ValueError):
                growth.budget(merit)
        for levels in ([0] * 5, [0] * 7, [True, 0, 0, 0, 0, 0],
                       [0, 0, 0, 0, 0, 1.0], [12, 0, 0, 0, 0, 0],
                       [0, -1, 0, 0, 0, 0], None, '000000'):
            with self.subTest(levels=levels), self.assertRaises(ValueError):
                growth.validate_growth(99999, levels)


class BodyguardEquipmentRules(unittest.TestCase):
    def test_item_limits_are_independent_of_officer_items(self):
        expected = [40, 40, 25, 25, 15, 15, 15, 15, 15]
        self.assertEqual([equipment.GUARD_ITEMS[index]['max_value'] for index in range(9)], expected)
        self.assertTrue(all(equipment.GUARD_ITEMS[index]['kind'] == 'normal' for index in range(9)))
        self.assertEqual(equipment.GUARD_ITEMS[9]['kind'], 'rare')
        self.assertEqual(equipment.GUARD_ITEMS[9]['max_value'], 0)

    def test_every_family_has_three_distinct_tiers(self):
        self.assertEqual(set(equipment.GUARD_WEAPONS), set(range(173, 188)))
        self.assertEqual(len(equipment.FAMILY_NAMES), 5)
        for family in range(5):
            rows = sorted((row for row in equipment.GUARD_WEAPONS.values() if row['family_index'] == family), key=lambda row: row['tier'])
            self.assertEqual([row['tier'] for row in rows], [1, 2, 3])
            self.assertEqual([row['base_power'] for row in rows][1:], [15, 20])
            self.assertIn(rows[0]['base_power'], (7, 8))

    def test_melee_and_ranged_bonus_eligibility(self):
        # Normal Attack/Reach apply to melee; Bow Attack applies to ranged.
        for row in equipment.GUARD_WEAPONS.values():
            allowed = set(row['allowed_skill_ids'])
            self.assertNotIn(9, allowed)  # Healing Scroll cannot be a weapon bonus.
            if row['family_index'] < 3:
                self.assertIn(2, allowed)
                self.assertIn(7, allowed)
                self.assertNotIn(4, allowed)
            else:
                self.assertIn(4, allowed)
                self.assertNotIn(2, allowed)
                self.assertNotIn(7, allowed)

    def test_generated_values_are_discrete_and_tier_limited(self):
        self.assertEqual(equipment.validate_skills(173, [{'id': 0, 'value': 15}]), [{'id': 0, 'value': 15}])
        self.assertEqual(equipment.validate_skills(175, [{'id': 0, 'value': 30}]), [{'id': 0, 'value': 30}])
        self.assertEqual(equipment.validate_skills(184, [{'id': 4, 'value': 10}]), [{'id': 4, 'value': 10}])
        invalid = [(173, [{'id': 0, 'value': 30}]), (175, [{'id': 0, 'value': 29}]),
                   (175, [{'id': 0, 'value': 2}]), (175, [{'id': 4, 'value': 10}]),
                   (184, [{'id': 2, 'value': 20}]), (184, [{'id': 4, 'value': 15}]),
                   (175, [{'id': 9, 'value': 0}])]
        for weapon_id, skills in invalid:
            with self.subTest(weapon_id=weapon_id, skills=skills), self.assertRaises(SaveError):
                equipment.validate_skills(weapon_id, skills)

    def test_max_profiles_are_legal_and_return_independent_copies(self):
        for weapon_id in equipment.GUARD_WEAPONS:
            profile = equipment.max_skills(weapon_id)
            self.assertEqual(len(profile), 3)
            self.assertEqual(equipment.validate_skills(weapon_id, profile), profile)
            original = equipment.max_skills(weapon_id)
            profile[0]['value'] = 999
            profile.clear()
            self.assertEqual(equipment.max_skills(weapon_id), original)

    def test_stock_empty_bonuses_and_upgraded_fallback(self):
        # Initial tier-one stock can be bare; dropped upgraded weapons cannot.
        self.assertEqual(equipment.validate_skills(173, []), [])
        for weapon_id in (174, 175, 183, 184, 186, 187):
            with self.subTest(weapon_id=weapon_id), self.assertRaises(SaveError):
                equipment.validate_skills(weapon_id, [])

    def test_duplicate_excess_or_malformed_bonuses_are_refused(self):
        invalid = [[{'id': 0, 'value': 30}] * 2,
                   [{'id': 0, 'value': 30}, {'id': 1, 'value': 30}, {'id': 2, 'value': 20}, {'id': 3, 'value': 20}],
                   [{'id': True, 'value': 1}], [{'id': 0, 'value': True}],
                   [{'id': 0, 'value': 30.0}], [{'id': 0}],
                   [{'id': 0, 'value': 30, 'extra': 1}], [None], None]
        for skills in invalid:
            with self.subTest(skills=skills), self.assertRaises(SaveError):
                equipment.validate_skills(175, skills)
        for weapon_id in (175.0, True, '175', None, [], 999):
            with self.subTest(weapon_id=weapon_id), self.assertRaises(SaveError):
                equipment.validate_skills(weapon_id, [{'id': 0, 'value': 30}])


if __name__ == '__main__':
    unittest.main()
