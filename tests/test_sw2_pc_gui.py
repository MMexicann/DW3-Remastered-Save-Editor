"""Actual Tk workflows; procedural and optional genuine PC files stay distinct."""
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.application import Application
from koei_editor.games.sw2 import sw2_parser as backend
from koei_editor.games.sw2.sw2_editor import Editor
from tests.test_sw2_pc_format import procedural_raw


class SW2GuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.area = tempfile.TemporaryDirectory()
        self.addCleanup(self.area.cleanup)
        self.folder = Path(self.area.name)
        self.source = self.folder / 'input-copy.dat'
        self.raw = procedural_raw()
        self.source.write_bytes(self.raw)
        self.app = Application(self.root, preferences_path=self.folder / 'preferences.json')
        self.assertIn('sw2', self.app.game_buttons)
        self.editor = self.app.select_game('sw2')
        self.assertIsInstance(self.editor, Editor)
        self.errors = []
        errors = patch('koei_editor.shared.verified_gui.messagebox.showerror',
                       side_effect=lambda *args: self.errors.append(args))
        errors.start()
        self.addCleanup(errors.stop)
        self.open_copy(self.source)

    def open_copy(self, source):
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
            self.editor.open()
        self.assertEqual(self.errors, [])

    def workflow(self):
        editor = self.editor
        raw = self.source.read_bytes()
        editor.group.set('Resources')
        editor.search.set('money')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('money',))
        original = backend.field_map(editor.document)['money'].value(editor.document.payload)
        value = original - 1 if original else 1
        editor.fields.selection_set('money')
        editor.value.set(str(value))
        editor.apply_selected()
        self.assertEqual(editor.changes, {'money': value})
        editor.max_visible()
        self.assertEqual(editor.changes, {'money': value})
        editor.review()
        self.assertTrue(any(isinstance(child, tk.Toplevel) for child in self.root.winfo_children()))
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.stage_values({'money': value})
        self.app.show_library()
        self.assertIs(self.app.select_game('sw2'), editor)
        self.assertEqual(editor.changes, {'money': value})
        self.app.apply_theme('Dark')
        self.app.apply_theme('Light')
        editor.show_inspector()
        tables = editor.presentation.inspection_tables(editor.document)
        self.assertEqual(tuple(table.title for table in tables), ('Officers', 'Weapons', 'Guards'))
        self.assertEqual(len(tables[0].rows), 26)
        self.assertEqual(len(tables[2].rows), 54)
        backup = editor.backup
        self.assertEqual(backup.read_bytes(), raw)
        destination = self.folder / 'edited.dat'
        with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename', return_value=str(destination)):
            editor.save_as()
        self.assertEqual(self.errors, [])
        self.assertEqual(self.source.read_bytes(), raw)
        self.assertEqual(editor.changes, {})
        edited = backend.read_save(destination)
        self.assertEqual(backend.field_map(edited)['money'].value(edited.payload), value)
        restored = self.folder / 'restored.dat'
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(backup)), \
             patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename', return_value=str(restored)):
            editor.restore()
        self.assertEqual(self.errors, [])
        self.assertEqual(restored.read_bytes(), raw)

    def test_registered_card_open_search_review_undo_theme_inspection_save_and_restore(self):
        self.workflow()

    def test_optional_genuine_pc_copy_gui_workflow(self):
        path = os.environ.get('SW2_PC_SAVE_COPY')
        if not path:
            self.skipTest('SW2_PC_SAVE_COPY genuine original PC copy not supplied.')
        original = Path(path).read_bytes()
        self.source.write_bytes(original)
        self.open_copy(self.source)
        self.workflow()
        self.assertEqual(Path(path).read_bytes(), original)
