"""Actual Tk copy workflows; no console reimport or game execution."""
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.ayesha_ps3 import parser
from koei_editor.games.ayesha_ps3.editor import Editor
from tests.test_ayesha_ps3 import procedural_save


class AyeshaWorkflow:
    fixture = staticmethod(procedural_save)

    def test_stack_search_review_undo_inspect_manual_no_max_copy_backup_restore(self):
        try: root = tk.Tk()
        except tk.TclError as error: self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy);root.withdraw()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'copy.bin';raw = self.fixture();source.write_bytes(raw)
            errors = []
            with patch('koei_editor.shared.verified_gui.messagebox.showerror', side_effect=lambda *args: errors.append(args)), \
                    patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                editor = Editor(root);editor.open();self.assertFalse(errors)
                field = next(f for f in parser.fields_for(editor.document) if f.group.endswith(' stacks'))
                editor.group.set(field.group);editor.search.set(field.label);editor.refresh()
                self.assertIn(field.id, editor.fields.get_children())
                editor.fields.selection_set(field.id);editor.value.set('1');editor.apply_selected()
                self.assertEqual(editor.changes, {field.id: 1});editor.max_visible()
                self.assertEqual(editor.changes, {field.id: 1});editor.review();editor.undo()
                self.assertEqual(editor.changes, {})
                editor.fields.selection_set(field.id);editor.value.set('1');editor.apply_selected();editor.show_inspector()
                self.assertEqual([t.title for t in editor.presentation.inspection_tables(editor.document)],
                                 ['Existing inventory records', 'Memory-related words'])
                editor.apply_theme('Dark');editor.apply_theme('Light')
                editor.save_to(Path(folder) / 'edited.bin');self.assertFalse(errors)
                self.assertEqual(source.read_bytes(), raw);self.assertTrue(editor.backup.exists())
                self.assertEqual(parser.restore(editor.backup, Path(folder) / 'restored.bin').read_bytes(), raw)
                self.assertEqual(field.value(parser.read_save(Path(folder) / 'edited.bin').payload), 1)


class ProceduralAyeshaGuiTests(AyeshaWorkflow, unittest.TestCase): pass


@unittest.skipUnless(os.environ.get('AYESHA_PS3_SAVE_COPIES'), 'No private native decrypted PS3 copy')
class GenuineAyeshaGuiTests(AyeshaWorkflow, unittest.TestCase):
    fixture = staticmethod(lambda: Path(os.environ['AYESHA_PS3_SAVE_COPIES'].split(os.pathsep)[1]).read_bytes())
