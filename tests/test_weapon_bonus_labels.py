"""Exercise weapon stat labels through selection, staging and change review."""
from copy import deepcopy
from pathlib import Path
import sys
import tkinter as tk
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gui
from models import Change


class WeaponBonusLabelTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.editor = gui.Editor(self.root, persist_preferences=False)
        self.editor.document = object()

    def tearDown(self):
        self.root.destroy()

    def test_officer_selection_stages_stat_choice_with_original_id(self):
        g = self.editor
        skills = [{'id': 10, 'value': 1}] + [{'id': None, 'value': 0} for _ in range(8)]
        row = {'owned': True, 'array': 'WeaponDataArray', 'weapon_id': 6,
               'data_id': 36, 'metadata': {'name': 'Test Weapon', 'base_power': 10},
               'blue_limit': 6, 'blue_minimum': 0, 'skills': skills,
               'editable': True, 'element_editable': False, 'attr': 3, 'elements': 0}
        original = deepcopy(row)
        g.weapons.insert('', 'end', iid='regular:36', text='Test Weapon')
        g.weapon_rows['regular:36'] = row
        g.weapons.selection_set('regular:36')
        with patch.object(gui.weapon_editor, 'state', return_value=row), \
             patch.object(gui.weapon_editor, 'original_skills', return_value=skills), \
             patch.object(gui.weapon_editor, 'allowed_elements', return_value={'None': 0}), \
             patch.object(g, 'stage_many') as stage, \
             patch.object(gui.messagebox, 'showerror') as error:
            g.select_weapon()
            self.assertEqual(g.weapon_bonus_names[0].get(), 'Luck')
            self.assertNotIn('Seven Star Orb', g.weapon_bonus_boxes[0].cget('values'))
            self.assertEqual(g.weapon_bonus_choices['Life'], 3)
            self.assertEqual(g.weapon_bonus_choices['Musou'], 2)
            self.assertEqual(g.weapon_bonus_choices['Mounted Defense'], 9)
            g.weapon_bonus_names[0].set('Attack')
            g.weapon_bonus_values[0].set('1')
            g.apply_weapon_rolls()
            error.assert_not_called()
            change = stage.call_args.args[0][0]
            self.assertEqual(change, Change('weapon_roll', 36, 'Skills',
                                           [{'id': 4, 'value': 1}] + skills[1:]))
            self.assertEqual(g.review_change(change)[2:], ('Luck +1', 'Attack +1'))
        self.assertEqual(row, original)
        self.assertFalse(g.changes)

    def test_bodyguard_selection_stages_stat_choice_with_original_id(self):
        g = self.editor
        weapon_id = next(i for i, row in gui.GUARD_WEAPONS.items()
                         if 0 in row['allowed_skill_ids'] and 2 in row['allowed_skill_ids'])
        metadata = gui.GUARD_WEAPONS[weapon_id]
        life = metadata['allowed_values_by_guard_item_id']['0'][0]
        attack = metadata['allowed_values_by_guard_item_id']['2'][0]
        row = {'weapon_id': weapon_id, 'skills': [{'id': 0, 'value': life}],
               'editable': True}
        original = deepcopy(row)
        g.guard_weapons.insert('', 'end', iid='slot:0', text='Test Guard Weapon')
        g.guard_weapons.selection_set('slot:0')
        with patch.object(gui.guard_editor, 'weapon_state', return_value=[row]), \
             patch.object(g, 'original_value', return_value=row['skills']), \
             patch.object(g, 'stage_many') as stage, \
             patch.object(gui.messagebox, 'showerror') as error:
            g.select_guard_weapon()
            self.assertEqual(g.guard_bonus_items[0].get(), 'Life')
            self.assertNotIn('BG Peacock Urn', g.guard_bonus_boxes[0].cget('values'))
            g.guard_bonus_items[0].set('Attack')
            g.guard_bonus_values[0].set(str(attack))
            g.apply_guard_bonuses()
            error.assert_not_called()
            change = stage.call_args.args[0][0]
            self.assertEqual(change, Change('guard_weapon_slot', 0, 'Skills',
                                           [{'id': 2, 'value': attack}]))
            self.assertEqual(g.review_change(change)[2:],
                             (f'Life +{life}', f'Attack +{attack}'))
        self.assertEqual(row, original)
        self.assertFalse(g.changes)

    def test_item_and_rare_effect_names_remain_item_names(self):
        g = self.editor
        with patch.object(g, 'item_rows', return_value=[(10, gui.ITEMS[10])]), \
             patch.object(g, 'value', return_value=1), \
             patch.object(g, 'select_item'):
            g.refresh_items()
            self.assertEqual(g.items.item('10', 'text'), 'Seven Star Orb')
        with patch.object(gui.guard_editor, 'item_state',
                          return_value={0: {'value': 1, 'owned': True}}), \
             patch.object(g, 'select_guard_item'):
            g.refresh_guard_items()
            self.assertEqual(g.guard_items.item('0', 'text'), gui.GUARD_ITEMS[0]['name'])
        with patch.object(g, 'original_value', return_value=False):
            self.assertEqual(g.review_change(Change('item', 10, 'Owned', True))[0],
                             'Seven Star Orb')
            self.assertEqual(g.review_change(Change('guard_item', 0, 'Owned', True))[0],
                             gui.GUARD_ITEMS[0]['name'])
        for item_id in gui.weapon_editor.RARE_ITEMS:
            self.assertEqual(g.describe_skill(gui.ITEMS[item_id], 0),
                             gui.ITEMS[item_id]['name'])
        self.assertEqual(gui.ITEMS[10]['name'], 'Seven Star Orb')
        self.assertEqual(gui.ITEMS[3]['name'], 'Peacock Urn')


if __name__ == '__main__':
    unittest.main()
