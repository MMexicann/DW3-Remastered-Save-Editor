"""GUI workflows using procedural SW4 DX data, without publishing saves."""
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from tests.test_samurai4dx_format import procedural_raw
from samurai4dx_editor import Editor
import samurai4dx_parser as parser


class Samurai4DXGuiTests(unittest.TestCase):
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

    def test_named_weapon_search_apply_review_undo_save_and_inspection(self):
        editor = self.editor
        editor.group.set('Weapons')
        editor.search.set('Blaze level')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('weapon_0_0_skill_0_rank', 'weapon_0_1_skill_0_rank'))
        editor.fields.selection_set('weapon_0_0_skill_0_rank')
        editor.value.set('5')
        editor.apply_selected()
        self.assertEqual(editor.changes, {'weapon_0_0_skill_0_rank': 5})
        editor.review()
        self.assertTrue(any(isinstance(child, tk.Toplevel) for child in self.root.winfo_children()))
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.stage_values({'weapon_0_0_skill_0_rank': 5, 'weapon_0_0_skill_0_active': 1})
        editor.show_inspector()
        tables = editor.presentation.inspection_tables(editor.document)
        self.assertTrue(any('Blaze' in str(row) for table in tables for row in table.rows))
        editor.apply_theme('Dark')
        editor.apply_theme('Light')
        destination = Path(self.folder.name) / 'edited.dat'
        editor.save_to(destination)
        self.assertFalse(self.errors)
        self.assertEqual(self.source.read_bytes(), self.raw)
        self.assertTrue(editor.backup.exists())
        edited = parser.read_save(destination)
        self.assertEqual(parser.field_map(edited)['weapon_0_0_skill_0_rank'].value(edited.payload), 5)
        self.assertEqual(parser.field_map(edited)['weapon_0_0_skill_0_active'].value(edited.payload), 1)

    def test_invalid_equipment_and_visible_max_preserve_unknown_flags(self):
        editor = self.editor
        editor.stage_values({'officer_0_equipped_weapon': 7})
        self.assertEqual(len(self.errors), 1)
        self.assertEqual(editor.changes, {})
        editor.group.set('Officers')
        editor.search.set('')
        editor.refresh()
        editor.max_visible()
        self.assertEqual(editor.changes, {})
        editor.group.set('Unlocks')
        editor.refresh()
        editor.max_visible()
        self.assertEqual(len(editor.changes), parser.OFFICER_COUNT)
        changed = parser.changed_payload(editor.document, editor.changes)
        self.assertEqual(changed[parser.OFFICER_BASE + 0x3F], 0xA5)
        editor.undo()
        self.assertEqual(editor.changes, {})
