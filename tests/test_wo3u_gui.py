"""Shared GUI workflow checks with generated WO3 data, never player saves."""
from pathlib import Path
import tempfile
import tkinter as tk
from unittest.mock import patch
import unittest

from tests.test_wo3u_format import procedural_raw
from wo3u_editor import Editor
import wo3u_parser as parser


class WO3GuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / 'copy.bin'
        self.raw = procedural_raw()
        self.source.write_bytes(self.raw)
        self.editor = Editor(self.root)
        self.errors = []
        error = patch('verified_gui.messagebox.showerror', side_effect=lambda *args: self.errors.append(args))
        error.start()
        self.addCleanup(error.stop)
        with patch('verified_gui.filedialog.askopenfilename', return_value=str(self.source)):
            self.editor.open()
        self.assertFalse(self.errors)
        self.assertEqual(self.editor.save_extension, '.bin')

    def test_search_apply_review_undo_and_save_as(self):
        editor = self.editor
        editor.group.set('Officers')
        editor.search.set('Officer 1 Attack')
        editor.refresh()
        self.assertTrue(editor.fields.exists('officer_0_attack'))
        editor.fields.selection_set('officer_0_attack')
        editor.value.set('500')
        editor.apply_selected()
        self.assertEqual(editor.changes, {'officer_0_attack': 500})
        editor.review()
        self.assertTrue(any(isinstance(child, tk.Toplevel) for child in self.root.winfo_children()))
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.stage_values({'officer_0_attack': 500})
        destination = Path(self.folder.name) / 'edited.bin'
        editor.save_to(destination)
        self.assertFalse(self.errors)
        self.assertEqual(self.source.read_bytes(), self.raw)
        self.assertTrue(editor.backup.exists())
        edited = parser.read_save(destination)
        self.assertEqual(parser.field_map(edited)['officer_0_attack'].value(edited.payload), 500)

    def test_weapon_search_binary_attribute_and_inspector(self):
        editor = self.editor
        editor.group.set('Weapons')
        editor.search.set('Verity')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('weapon_0_rank_1',))
        editor.fields.selection_set('weapon_0_rank_1')
        editor.value.set('10')
        editor.apply_selected()
        self.assertEqual(len(self.errors), 1)
        self.assertEqual(editor.changes, {})
        editor.show_inspector()
        tables = editor.presentation.inspection_tables(editor.document)
        self.assertEqual([table.title for table in tables], ['Progression', 'Weapons', 'Resources'])
        self.assertTrue(any('Verity' in str(row) for row in tables[1].rows))
        editor.apply_theme('Dark')
        editor.apply_theme('Light')
