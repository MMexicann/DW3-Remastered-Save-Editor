"""Procedural Orochi Z GUI workflow; no Windows game-load claim."""
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.orochiz.orochiz_editor import Editor
from koei_editor.games.orochiz import orochiz_parser as backend
from tests.test_orochiz_format import procedural_raw


class OrochiZGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / 'orochiz-copy.dat'
        self.raw = procedural_raw()
        self.source.write_bytes(self.raw)
        self.editor = Editor(self.root)
        self.errors = []
        errors = patch('koei_editor.shared.verified_gui.messagebox.showerror',
                       side_effect=lambda *args: self.errors.append(args))
        errors.start()
        self.addCleanup(errors.stop)
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename',
                   return_value=str(self.source)):
            self.editor.open()
        self.assertEqual(self.errors, [])

    def test_resources_and_weapon_search_apply_review_undo_max_inspection_save(self):
        editor = self.editor
        editor.group.set('Resources')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('stock_exp',))
        editor.fields.selection_set('stock_exp')
        editor.value.set('3000')
        editor.apply_selected()
        self.assertEqual(editor.changes, {'stock_exp': 3000})
        editor.review()
        self.assertTrue(any(isinstance(child, tk.Toplevel)
                            for child in self.root.winfo_children()))
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.group.set('Officer attack')
        editor.search.set('officer_95_base_attack')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('officer_95_base_attack',))
        editor.fields.selection_set('officer_95_base_attack')
        editor.value.set('104')
        editor.apply_selected()
        self.assertEqual(editor.changes, {'officer_95_base_attack': 104})
        editor.max_visible()
        self.assertEqual(editor.changes, {'officer_95_base_attack': 461})
        editor.undo()
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.group.set('Weapon attributes')
        editor.search.set('Attribute ID 0 level')
        editor.refresh()
        self.assertIn('officer_0_weapon_0_attribute_0_level', editor.fields.get_children())
        self.assertEqual(len(editor.fields.get_children()), 2)
        editor.max_visible()
        self.assertEqual(editor.changes, {'officer_0_weapon_0_attribute_0_level': 10})
        editor.search.set('Attribute ID 14 level')
        editor.refresh()
        editor.max_visible()
        self.assertNotIn('officer_0_weapon_0_attribute_14_level', editor.changes)
        editor.show_inspector()
        self.assertEqual([len(table.rows) for table in editor.presentation.inspection_tables(editor.document)],
                         [96, 768])
        editor.apply_theme('Dark')
        editor.apply_theme('Light')
        destination = Path(self.folder.name) / 'edited.dat'
        with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename',
                   return_value=str(destination)):
            editor.save_as()
        self.assertEqual(self.errors, [])
        updated = backend.read_save(destination)
        self.assertEqual(backend.field_map(updated)['officer_0_weapon_0_attribute_0_level'].value(updated.payload), 10)
        self.assertEqual(backend.field_map(updated)['officer_0_weapon_0_attribute_14_level'].value(updated.payload), 20)
        self.assertEqual(self.source.read_bytes(), self.raw)
        self.assertTrue(editor.backup.exists())
        self.assertEqual(editor.backup.read_bytes(), self.raw)
