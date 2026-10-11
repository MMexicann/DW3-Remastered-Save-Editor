"""Real Tk workflow using a clearly labelled procedural collection fixture."""
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.kens_rage2_ps3 import parser
from koei_editor.games.kens_rage2_ps3.editor import Editor
from tests.test_kens_rage2_ps3 import procedural_save, metadata


class KenRage2GuiTests(unittest.TestCase):
    def test_unlock_review_undo_inspector_no_max_backup_save_restore(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy);root.withdraw()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'DATA.BIN';raw = procedural_save();source.write_bytes(raw)
            (source.parent / 'PARAM.SFO').write_bytes(metadata())
            errors = []
            with patch('koei_editor.shared.verified_gui.messagebox.showerror', side_effect=lambda *args: errors.append(args)), \
                    patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                editor = Editor(root);editor.open();self.assertFalse(errors)
                field = parser.fields_for(editor.document)[0]
                editor.group.set(field.group);editor.search.set(field.label);editor.refresh()
                self.assertIn(field.id, editor.fields.get_children())
                editor.fields.selection_set(field.id);editor.value.set('1');editor.apply_selected()
                self.assertEqual(editor.changes, {field.id: 1})
                editor.max_visible();self.assertEqual(editor.changes, {field.id: 1})
                editor.review();editor.undo();self.assertEqual(editor.changes, {})
                editor.fields.selection_set(field.id);editor.value.set('1');editor.apply_selected()
                editor.show_inspector();self.assertEqual(len(parser.inspection_rows(editor.document)), 271)
                editor.apply_theme('Dark');editor.apply_theme('Light')
                editor.save_to(Path(folder) / 'edited.bin');self.assertFalse(errors)
                self.assertEqual(source.read_bytes(), raw)
                self.assertTrue(editor.backup.exists())
                self.assertEqual(parser.restore(editor.backup, Path(folder) / 'restored.bin').read_bytes(), raw)
                self.assertEqual(field.value(parser.read_save(Path(folder) / 'edited.bin').payload), 1)


class GenuineKenRage2GuiTests(unittest.TestCase):
    def test_genuine_open_inspection_unchanged_save_backup_restore(self):
        import os
        copies = os.environ.get('KENS_RAGE2_PS3_SAVE_COPIES')
        if not copies:
            self.skipTest('No copied genuine decrypted EU exports')
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy);root.withdraw()
        for sample in copies.split(os.pathsep):
            original = Path(sample);parser.validate_context(original)
            with self.subTest(sample=original.parent.name), tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / 'DATA.BIN';raw = original.read_bytes();source.write_bytes(raw)
                # Only generated identity metadata is used in the temporary GUI workspace.
                (source.parent / 'PARAM.SFO').write_bytes(metadata())
                errors = []
                with patch('koei_editor.shared.verified_gui.messagebox.showerror', side_effect=lambda *args: errors.append(args)), \
                        patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                    editor = Editor(root);editor.open();editor.show_inspector()
                    self.assertEqual(editor.changes, {});self.assertFalse(errors)
                    editor.save_to(source.parent / 'unchanged.bin');self.assertFalse(errors)
                    self.assertEqual((source.parent / 'unchanged.bin').read_bytes(), raw)
                    self.assertEqual(source.read_bytes(), raw)
                    self.assertEqual(parser.restore(editor.backup, source.parent / 'restored.bin').read_bytes(), raw)
