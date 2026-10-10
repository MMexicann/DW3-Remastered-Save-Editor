"""DW6 procedural GUI workflows; these do not run or validate the game."""
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.dw6.dw6_editor import Editor
from koei_editor.games.dw6 import dw6_parser as backend
from tests.test_dw6_format import procedural_raw


class DW6GuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / 'copy.dat'
        self.source.write_bytes(procedural_raw())
        self.editor = Editor(self.root)
        self.errors = []
        errors = patch('koei_editor.shared.verified_gui.messagebox.showerror',
                       side_effect=lambda *args: self.errors.append(args))
        errors.start()
        self.addCleanup(errors.stop)
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(self.source)):
            self.editor.open()
        self.assertEqual(self.errors, [])

    def test_named_search_separate_unlocks_max_undo_review_inspection_save(self):
        editor = self.editor
        editor.group.set('Unlocks')
        editor.search.set('Xu Huang')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('officer_19_unlocked',))
        editor.max_visible()
        self.assertEqual(editor.changes, {})
        editor.unlock_all()
        self.assertEqual(len(editor.changes), 40)
        self.assertFalse(any(key.startswith('horse') for key in editor.changes))
        editor.review()
        self.assertTrue(any(isinstance(child, tk.Toplevel) for child in self.root.winfo_children()))
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.group.set('Horses')
        editor.search.set('horse_0_speed')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('horse_0_speed',))
        editor.fields.selection_set('horse_0_speed')
        editor.value.set('400')
        editor.apply_selected()
        self.assertEqual(editor.changes, {'horse_0_speed': 400})
        editor.max_visible()
        self.assertEqual(editor.changes, {'horse_0_speed': 500})
        editor.search.set('horse_1_speed')
        editor.refresh()
        editor.max_visible()
        self.assertEqual(editor.changes, {'horse_0_speed': 500})
        editor.show_inspector()
        tables = editor.presentation.inspection_tables(editor.document)
        self.assertEqual(tuple(table.title for table in tables), ('Officers', 'Weapons', 'Horses'))
        self.assertEqual(len(tables[0].rows), 41)
        editor.apply_theme('Dark')
        editor.apply_theme('Light')
        destination = Path(self.folder.name) / 'edited.dat'
        with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename', return_value=str(destination)):
            editor.save_as()
        self.assertEqual(self.errors, [])
        self.assertEqual(self.source.read_bytes(), procedural_raw())
        written = backend.read_save(destination)
        self.assertEqual(backend.field_map(written)['horse_0_speed'].value(written.payload), 500)
        self.assertEqual(backend.field_map(written)['officer_19_unlocked'].value(written.payload), 0)
        self.assertTrue(list((Path(self.folder.name) / 'WarriorsEditorBackups').glob('*.dat')))
