"""DW8E procedural SYSTEM GUI workflow; no game execution."""
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.dw8e.dw8e_editor import Editor
from koei_editor.games.dw8e import dw8e_parser as backend
from tests.test_dw8e_horses import procedural_raw


class DW8EmpiresGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / 'SystemSave-copy.dat'
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

    def test_existing_named_body_apply_review_undo_max_inspection_save_backup(self):
        editor = self.editor
        editor.search.set('Final Horse')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('horse_149_body',))
        editor.fields.selection_set('horse_149_body')
        editor.selected()
        editor.value.set('4')
        editor.apply_selected()
        self.assertEqual(editor.changes, {'horse_149_body': 4})
        editor.review()
        self.assertTrue(any(isinstance(child, tk.Toplevel) for child in self.root.winfo_children()))
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.max_visible()
        self.assertEqual(editor.changes, {})
        editor.max_selected()
        self.assertEqual(editor.changes, {})
        editor.fields.selection_set('horse_149_body')
        editor.value.set('4')
        editor.apply_selected()
        editor.show_inspector()
        table, = editor.presentation.inspection_tables(editor.document)
        self.assertEqual(len(table.rows), 150)
        self.assertEqual(table.rows[-1][1], 'Final Horse')
        before = self.source.read_bytes()
        destination = self.source.with_name('edited.dat')
        editor.save_to(destination)
        self.assertEqual(self.errors, [])
        self.assertEqual(self.source.read_bytes(), before)
        self.assertTrue(editor.backup.exists())
        result = backend.read_save(destination)
        offset = backend.field_map(result)['horse_149_body'].offset
        opened = backend.decode(before)
        self.assertEqual(result.payload[offset], 4)
        self.assertEqual(result.payload[:offset], opened.payload[:offset])
        self.assertEqual(result.payload[offset + 1:], opened.payload[offset + 1:])
