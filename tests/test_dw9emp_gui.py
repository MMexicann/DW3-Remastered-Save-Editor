"""DW9 Empires GUI checks using procedural data; no game-load claim."""
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.dw9emp.dw9emp_editor import Editor
from koei_editor.games.dw9emp import dw9emp_parser as backend
from tests.test_dw9emp_format import procedural_raw


class DW9EmpGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / 'system-copy.bin'
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

    def test_quantity_search_apply_review_undo_max_inspection_and_save_as(self):
        editor = self.editor
        self.assertEqual(len(editor.fields.get_children()), 3)
        editor.group.set('Inventory quantities')
        editor.search.set('Item ID 799')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('item_799_quantity',))
        editor.fields.selection_set('item_799_quantity')
        editor.value.set('45')
        editor.apply_selected()
        self.assertEqual(editor.changes, {'item_799_quantity': 45})
        editor.review()
        self.assertTrue(any(isinstance(child, tk.Toplevel)
                            for child in self.root.winfo_children()))
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.max_visible()
        self.assertEqual(editor.changes, {})
        editor.stage_values({'item_799_quantity': 45})
        editor.max_visible()
        self.assertEqual(editor.changes, {'item_799_quantity': 45})
        editor.show_inspector()
        tables = editor.presentation.inspection_tables(editor.document)
        self.assertEqual([len(table.rows) for table in tables], [800, 900])
        self.assertEqual(tables[1].rows[0][1], 'Test Officer')
        editor.apply_theme('Dark')
        editor.apply_theme('Light')
        destination = Path(self.folder.name) / 'edited.bin'
        with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename',
                   return_value=str(destination)):
            editor.save_as()
        self.assertEqual(self.errors, [])
        edited = backend.read_save(destination)
        self.assertEqual(backend.field_map(edited)['item_799_quantity'].value(edited.payload), 45)
        offset = backend.ITEM_BASE + 2 * 799
        self.assertEqual(edited.raw[:offset], self.raw[:offset])
        self.assertEqual(edited.raw[offset + 2:], self.raw[offset + 2:])
        self.assertEqual(self.source.read_bytes(), self.raw)
        self.assertTrue(editor.backup.exists())
        self.assertEqual(editor.backup.read_bytes(), self.raw)
