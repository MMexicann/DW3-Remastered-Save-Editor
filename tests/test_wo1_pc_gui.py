"""Original PC GUI workflows; procedural and genuine bytes remain distinct."""
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.wo1_pc.wo1_editor import Editor
from koei_editor.games.wo1_pc import wo1_parser as backend
from tests.test_wo1_pc_format import procedural_raw


class OrochiPCGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / 'wo1-copy.dat'
        self.errors = []
        errors = patch('koei_editor.shared.verified_gui.messagebox.showerror',
                       side_effect=lambda *args: self.errors.append(args))
        errors.start()
        self.addCleanup(errors.stop)

    def open_copy(self, raw):
        self.source.write_bytes(raw)
        editor = Editor(self.root)
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename',
                   return_value=str(self.source)):
            editor.open()
        self.assertEqual(self.errors, [])
        return editor

    def test_apply_review_undo_filtered_max_inspector_backup_save(self):
        raw = procedural_raw()
        editor = self.open_copy(raw)
        editor.group.set('Resources')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('stock_exp',))
        editor.fields.selection_set('stock_exp')
        editor.value.set('3000')
        editor.apply_selected()
        self.assertEqual(editor.changes, {'stock_exp': 3000})
        editor.max_visible()
        self.assertEqual(editor.changes, {'stock_exp': 3000})
        editor.review()
        self.assertTrue(any(isinstance(child, tk.Toplevel) for child in self.root.winfo_children()))
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.group.set('Weapon attributes')
        editor.search.set('Flame (ID 0)')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('officer_0_weapon_0_attribute_0_level',))
        editor.max_visible()
        self.assertEqual(editor.changes, {'officer_0_weapon_0_attribute_0_level': 10})
        editor.search.set('Rage (ID 14)')
        editor.refresh()
        editor.max_visible()
        self.assertNotIn('officer_0_weapon_0_attribute_14_level', editor.changes)
        editor.show_inspector()
        self.assertEqual([len(table.rows) for table in editor.presentation.inspection_tables(editor.document)],
                         [79, 632])
        editor.apply_theme('Dark')
        editor.apply_theme('Light')
        destination = Path(self.folder.name) / 'edited.dat'
        with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename',
                   return_value=str(destination)):
            editor.save_as()
        self.assertEqual(self.errors, [])
        updated = backend.read_save(destination)
        self.assertEqual(backend.field_map(updated)['officer_0_weapon_0_attribute_0_level'].value(updated.payload), 10)
        self.assertEqual(backend.field_map(updated)['officer_0_weapon_0_attribute_14_level'].value(updated.payload), 99)
        self.assertEqual(self.source.read_bytes(), raw)
        self.assertEqual(editor.backup.read_bytes(), raw)

    @unittest.skipUnless(os.environ.get('WO1_NATIVE_SAVES'), 'Private original PC fixtures not supplied')
    def test_genuine_original_pc_resource_edit_review_undo_backup_save(self):
        inputs = list(Path(os.environ['WO1_NATIVE_SAVES']).glob('*.dat'))
        self.assertTrue(inputs)
        raw = inputs[0].read_bytes()
        editor = self.open_copy(raw)
        editor.group.set('Resources')
        editor.refresh()
        editor.fields.selection_set('stock_exp')
        original = backend.field_map(editor.document)['stock_exp'].value(raw)
        target = 100 if original != 100 else 101
        editor.value.set(str(target))
        editor.apply_selected()
        self.assertEqual(editor.changes, {'stock_exp': target})
        editor.review()
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.value.set(str(target))
        editor.apply_selected()
        destination = Path(self.folder.name) / 'genuine-edited.dat'
        with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename',
                   return_value=str(destination)):
            editor.save_as()
        self.assertEqual(self.errors, [])
        result = destination.read_bytes()
        self.assertEqual(backend.field_map(backend.decode(result))['stock_exp'].value(result), target)
        allowed = set(range(backend.STOCK_EXP_OFFSET, backend.STOCK_EXP_OFFSET + 4)) | set(range(0x24160, 0x24164))
        self.assertLessEqual({i for i, (a, b) in enumerate(zip(raw, result)) if a != b}, allowed)
        self.assertEqual(editor.backup.read_bytes(), raw)
        self.assertEqual(self.source.read_bytes(), raw)
        self.assertEqual(inputs[0].read_bytes(), raw)
