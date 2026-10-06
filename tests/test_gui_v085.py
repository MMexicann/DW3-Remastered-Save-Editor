"""GUI regression checks against immutable, explicitly supplied save copies."""
from pathlib import Path
import sys
import tkinter as tk
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
import gui
import bodyguard_customization as customization
import officer_weapon_editor as weapons
import bodyguard_editor as guards
import collection_editor as collections
import musou_slots
from models import Change, fields
from save_parser import read_save, parse_bytes
from save_writer import serialize

WORKSPACE = PROJECT.parents[1]
FIXTURE = WORKSPACE / 'work/original-upload/GameStatusData.sav'
REPORT = WORKSPACE / 'work/received-v034/report-2-dd54eb37ba5d.sav'


@unittest.skipUnless(FIXTURE.exists() and REPORT.exists(), 'Private supplied copies are required.')
class GuiRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = read_save(FIXTURE)
        cls.report = read_save(REPORT)

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.editor = gui.Editor(self.root)
        self.errors = []
        self.error_patch = patch.object(gui.messagebox, 'showerror', side_effect=lambda *a, **k: self.errors.append(a))
        self.confirm_patch = patch.object(gui.messagebox, 'askyesno', return_value=True)
        self.error_patch.start()
        self.confirm_patch.start()
        self.load(self.original)

    def load(self, document):
        self.editor.document = document
        self.editor.changes = {}
        self.editor.history = []
        self.editor.set_loaded(True)
        self.editor.refresh()

    def tearDown(self):
        self.confirm_patch.stop()
        self.error_patch.stop()
        self.root.destroy()

    def test_customization_unlock_review_undo_and_serialization(self):
        g = self.editor
        g.unlock_guard_customization()
        self.assertFalse(self.errors)
        self.assertEqual(len(g.changes), 6)
        self.assertEqual(g.review_change(Change('guard_customization', 2, 'AppearanceUnlocked', True)),
                         ('Bodyguard Nanman Male', 'Available', 'No', 'Yes'))
        edited = parse_bytes(serialize(g.document, list(g.changes.values()))[0])
        state = customization.customization_state(edited)
        self.assertTrue(all(row['unlocked'] for family in ('appearances', 'outfits') for row in state[family]))
        self.assertEqual(edited.properties['EngiClearCharaArray']['value'], g.document.properties['EngiClearCharaArray']['value'])
        g.undo()
        self.assertFalse(g.changes)

    def test_max_items_keeps_reported_high_values(self):
        self.load(self.report)
        g = self.editor
        g.max_items()
        self.assertFalse(self.errors)
        for index, row in g.editable_item_rows():
            if row['kind'] != 'normal':
                continue
            target = weapons.max_item_value(self.report, index)
            self.assertEqual(g.value('item', index, 'Value'), target)
        g.max_guard_items()
        self.assertFalse(self.errors)
        states = guards.item_state(self.report, list(g.changes.values()))
        for index, row in guards.GUARD_ITEMS.items():
            if row['kind'] == 'normal':
                self.assertEqual(states[index]['value'], guards.max_item_value(self.report, index))
        edited = parse_bytes(serialize(self.report, list(g.changes.values()))[0])
        self.assertEqual(fields(edited.records('EquipItemDataArray')[0])['Value']['value'], 50)
        self.assertEqual(edited.properties['EngiClearCharaArray']['value'], self.report.properties['EngiClearCharaArray']['value'])

    def test_apply_existing_high_item_does_not_reject_or_lower_it(self):
        self.load(self.report)
        g = self.editor
        g.items.selection_set('0')
        g.select_item()
        self.assertIn('Normal drop maximum: 20', g.item_detail.get())
        g.apply_item()
        self.assertFalse(self.errors)
        self.assertFalse(g.changes)
        g.item_value.set('51')
        g.apply_item()
        self.assertEqual(len(self.errors), 1)
        self.assertFalse(g.changes)

    def test_max_recovers_original_high_from_pending_lower_value(self):
        self.load(self.report)
        g = self.editor
        self.assertTrue(g.stage_many([Change('item', 0, 'Value', 1)]))
        g.max_items()
        self.assertFalse(self.errors)
        self.assertEqual(g.value('item', 0, 'Value'), 50)
        self.assertNotIn(('item', 0, 'Value'), g.changes)

    def test_movies_unlock_without_changing_other_options_or_story(self):
        g = self.editor
        g.unlock_movies()
        self.assertFalse(self.errors)
        edited = parse_bytes(serialize(g.document, list(g.changes.values()))[0])
        state = collections.collection_state(edited)
        self.assertEqual(state['movies']['owned'], state['movies']['total'])
        self.assertEqual(edited.properties['EngiSaveDataArray']['value'], self.original.properties['EngiSaveDataArray']['value'])
        self.assertEqual(edited.properties['EngiClearCharaArray']['value'], self.original.properties['EngiClearCharaArray']['value'])
        g.undo()
        self.assertFalse(g.changes)

    def test_remove_run_preview_review_undo_and_write(self):
        g = self.editor
        slots = musou_slots.slot_state(self.original)
        active = next(row for row in slots['slots'] if row['active'] and row['editable'])
        g.musou_saves_tree.selection_set(str(active['index']))
        g.select_musou_save()
        g.remove_musou_save()
        self.assertFalse(self.errors)
        self.assertEqual(musou_slots.slot_state(g.document, list(g.changes.values()))['active_count'], slots['active_count'] - 1)
        change = g.changes['musou_slot', active['index'], 'Remove']
        self.assertIn('Remove saved run', g.review_change(change))
        edited = parse_bytes(serialize(g.document, list(g.changes.values()))[0])
        self.assertEqual(musou_slots.slot_state(edited)['active_count'], slots['active_count'] - 1)
        self.assertEqual(edited.properties['PCSaveDataArray']['value'], self.original.properties['PCSaveDataArray']['value'])
        self.assertEqual(edited.properties['EngiClearCharaArray']['value'], self.original.properties['EngiClearCharaArray']['value'])
        self.assertEqual(len(edited.records('EngiSaveDataArray')), len(self.original.records('EngiSaveDataArray')))
        g.undo()
        self.assertFalse(g.changes)
        self.assertEqual(musou_slots.slot_state(g.document)['active_count'], slots['active_count'])

    def test_cancelled_run_removal_keeps_pending_batch(self):
        g = self.editor
        g.max_elixirs()
        before = g.changes.copy()
        with patch.object(gui.messagebox, 'askyesno', return_value=False):
            g.remove_all_musou_saves()
        self.assertEqual(g.changes, before)
        self.assertFalse(self.errors)


if __name__ == '__main__':
    unittest.main()
