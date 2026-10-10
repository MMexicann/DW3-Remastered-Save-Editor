"""PW4 copy workflow with procedural data; no game-load claim."""
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from tests.test_pw4_format import procedural_raw
from pw4_editor import Editor
import pw4_parser as parser


class PW4GuiTests(unittest.TestCase):
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
        self.raw = procedural_raw()
        self.source.write_bytes(self.raw)
        self.editor = Editor(self.root)
        self.errors = []
        errors = patch('verified_gui.messagebox.showerror', side_effect=lambda *args: self.errors.append(args))
        errors.start()
        self.addCleanup(errors.stop)
        with patch('verified_gui.filedialog.askopenfilename', return_value=str(self.source)):
            self.editor.open()
        self.assertFalse(self.errors)

    def test_search_coin_apply_review_undo_visible_max_inspect_theme_and_save(self):
        editor = self.editor
        editor.group.set('Owned coins')
        editor.search.set('007')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('coin_7_quantity',))
        editor.fields.selection_set('coin_7_quantity')
        editor.value.set('27')
        editor.apply_selected()
        self.assertEqual(editor.changes, {'coin_7_quantity': 27})
        editor.review()
        self.assertTrue(any(isinstance(child, tk.Toplevel) for child in self.root.winfo_children()))
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.max_visible()
        self.assertEqual(editor.changes, {'coin_7_quantity': 999})
        editor.search.set('399')
        editor.refresh()
        editor.max_visible()
        self.assertEqual(editor.changes, {'coin_7_quantity': 999})
        editor.show_inspector()
        tables = editor.presentation.inspection_tables(editor.document)
        self.assertEqual(tables[-1].rows[1], ('Coin ID 007', 0, 300, 22, '0x05'))
        editor.apply_theme('Dark')
        editor.apply_theme('Light')
        destination = Path(self.folder.name) / 'edited.dat'
        editor.save_to(destination)
        self.assertFalse(self.errors)
        self.assertEqual(self.source.read_bytes(), self.raw)
        self.assertTrue(editor.backup.exists())
        edited = parser.read_save(destination)
        self.assertEqual(parser.field_map(edited)['coin_7_quantity'].value(edited.payload), 999)
        self.assertEqual(parser.coins(edited)[1]['earned'], 300)
        self.assertEqual(parser.coins(edited)[1]['spent'], 22)
        self.assertEqual(parser.coins(edited)[1]['flags'], 5)
