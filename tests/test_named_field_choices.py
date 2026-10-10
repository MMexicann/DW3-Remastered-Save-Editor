"""Named choices stage native values through the same safe scalar workflow."""
import tempfile
import tkinter as tk
from tkinter import ttk
import unittest
from pathlib import Path
from unittest.mock import patch

from koei_editor.application import Application
from koei_editor.games.dw6 import dw6_parser
from tests.test_dw6_format import procedural_raw
from koei_editor.shared.table_tools import copy_selected, sort_table


class NamedChoiceGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / 'copy.dat'
        self.source.write_bytes(procedural_raw())
        self.app = Application(self.root, persist_preferences=False)
        self.editor = self.app.select_game('dw6')
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(self.source)):
            self.editor.open()

    def tearDown(self):
        if hasattr(self, 'root'):
            self.root.destroy()

    def test_choice_stage_undo_switch_save_and_unknown_bytes(self):
        editor = self.editor
        key = 'officer_0_weapon_0_element'
        editor.fields.selection_set(key)
        editor.selected()
        self.assertEqual(tuple(editor.value_choice.cget('values')),
                         ('0 · Fire', '1 · Ice', '2 · Lightning', '3 · No element'))
        self.assertEqual(editor.value_choice.winfo_manager(), 'pack')
        editor.choice_value.set('1 · Ice')
        editor.selected_choice()
        editor.apply_selected()
        self.assertEqual(editor.changes, {key: 1})
        self.assertIn('Ice', str(editor.fields.item(key)['values']))
        self.app.select_game('dw7xl')
        self.app.select_game('dw6')
        self.assertEqual(editor.changes, {key: 1})
        editor.undo()
        self.assertFalse(editor.changes)
        editor.choice_value.set('2 · Lightning')
        editor.selected_choice()
        editor.apply_selected()
        original = self.source.read_bytes()
        target = Path(self.folder.name) / 'edited.dat'
        editor.save_to(target)
        field = dw6_parser.field_map(editor.document)[key]
        reopened = target.read_bytes()
        self.assertEqual(field.value(reopened), 2)
        self.assertEqual(reopened[:field.offset], original[:field.offset])
        self.assertEqual(reopened[field.offset + field.size:], original[field.offset + field.size:])
        self.assertEqual(self.source.read_bytes(), original)
        self.assertTrue(editor.backup.exists())

    def test_mixed_choices_use_numeric_entry_and_invalid_batch_is_atomic(self):
        editor = self.editor
        editor.fields.selection_set(('officer_0_weapon_0_element', 'officer_1_unlocked'))
        editor.selected()
        self.assertEqual(editor.value_entry.winfo_manager(), 'pack')
        self.assertFalse(editor.value_choice.winfo_manager())
        editor.value.set('2')
        with patch('koei_editor.shared.verified_gui.messagebox.showerror') as error:
            editor.apply_selected()
        error.assert_called_once()
        self.assertFalse(editor.changes)
        self.assertFalse(editor.history)

    def test_inspector_filter_keeps_sort_order_and_copies_only_visible_rows(self):
        self.editor.show_inspector()
        dialog = next(child for child in self.root.winfo_children()
                      if isinstance(child, tk.Toplevel))
        notebook = next(child for child in dialog.winfo_children()
                        if isinstance(child, ttk.Notebook))
        horses = next(self.root.nametowidget(tab) for tab in notebook.tabs()
                      if notebook.tab(tab, 'text') == 'Horses')
        tools, body = (child for child in horses.winfo_children()
                       if isinstance(child, ttk.Frame))
        query = next(child for child in tools.winfo_children()
                     if isinstance(child, ttk.Entry))
        view = next(child for child in body.winfo_children()
                    if isinstance(child, ttk.Treeview))
        rows = {view.set(row, 'Record'): row for row in view.get_children()}
        view.selection_set((rows['Horse slot 1'], rows['Horse slot 2']))
        sort_table(view, 'Record', reverse=True)
        ordered = view.get_children()
        query.insert(0, 'horse slot')
        self.assertEqual(view.get_children(), ordered)
        query.delete(0, 'end')
        query.insert(0, 'horse 341')
        self.assertEqual(view.get_children(), (rows['Horse slot 1'],))
        self.assertTrue(copy_selected(view))
        copied = self.root.clipboard_get()
        self.assertIn('Horse slot 1', copied)
        self.assertNotIn('Horse slot 2', copied)
        query.delete(0, 'end')
        self.assertEqual(view.get_children(), ordered)
        self.assertEqual(set(view.selection()), {rows['Horse slot 1'], rows['Horse slot 2']})
        self.assertEqual(self.editor.changes, {})


if __name__ == '__main__':
    unittest.main()
