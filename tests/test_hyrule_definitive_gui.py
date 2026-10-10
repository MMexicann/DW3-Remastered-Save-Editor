"""Shared Tk copy workflow for the separate Switch Definitive Edition adapter."""
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.hyrule_definitive import parser
from koei_editor.games.hyrule_definitive.editor import Editor
from tests.test_hyrule_definitive import procedural_raw


class DefinitiveGuiTests(unittest.TestCase):
    def test_named_search_apply_review_undo_readonly_inspector_backup_save(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        root.withdraw()
        self.addCleanup(root.destroy)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'copy.bin'
            source.write_bytes(procedural_raw())
            editor = Editor(root)
            errors = []
            with patch('koei_editor.shared.verified_gui.messagebox.showerror', side_effect=lambda *args: errors.append(args)):
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                    editor.open()
                editor.group.set('Material inventory')
                editor.search.set('Metal Plate')
                editor.refresh()
                self.assertEqual(editor.fields.get_children(), ('material_1afe',))
                editor.max_visible()
                self.assertEqual(editor.changes, {})
                editor.fields.selection_set('material_1afe')
                editor.value.set('30')
                editor.apply_selected()
                self.assertEqual(editor.changes, {'material_1afe': 30})
                editor.review()
                self.assertTrue(any(isinstance(child, tk.Toplevel) for child in root.winfo_children()))
                editor.undo()
                self.assertEqual(editor.changes, {})
                editor.fields.selection_set('material_1afe')
                editor.value.set('30')
                editor.apply_selected()
                editor.show_inspector()
                tables = editor.presentation.inspection_tables(editor.document)
                self.assertIn('Weapons', tuple(table.title for table in tables))
                self.assertTrue(any('Burning Frame' in str(row) for table in tables for row in table.rows))
                rows = tables[0].rows
                self.assertTrue(any('Link: EXP' in str(row) for row in rows))
                self.assertTrue(any('Fairy food' in str(row) for row in rows))
                editor.apply_theme('Dark')
                editor.apply_theme('Light')
                destination = source.with_name('edited.bin')
                editor.save_to(destination)
                self.assertEqual(errors, [])
                self.assertEqual(source.read_bytes(), procedural_raw())
                self.assertTrue(editor.backup.exists())
                written = parser.read_save(destination)
                self.assertEqual(parser.field_map(written)['material_1afe'].value(written.raw), 30)
