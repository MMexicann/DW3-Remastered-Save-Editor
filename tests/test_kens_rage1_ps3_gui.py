"""Real Tk resource-edit workflow, with opt-in genuine exports."""
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.kens_rage1_ps3 import parser
from koei_editor.games.kens_rage1_ps3.editor import Editor
from tests.test_kens_rage1_ps3 import metadata, procedural_save


class KenRage1GuiTests(unittest.TestCase):
    def run_workflow(self, raw):
        try: root = tk.Tk()
        except tk.TclError as error: self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy);root.withdraw()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'DATA.BIN';source.write_bytes(raw)
            (source.parent / 'PARAM.SFO').write_bytes(metadata())
            errors = []
            with patch('koei_editor.shared.verified_gui.messagebox.showerror', side_effect=lambda *args: errors.append(args)), \
                    patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                editor = Editor(root);editor.open();self.assertFalse(errors)
                field = parser.fields_for(editor.document)[0]
                editor.group.set(field.group);editor.search.set(field.label);editor.refresh()
                self.assertIn(field.id, editor.fields.get_children())
                editor.fields.selection_set(field.id);editor.value.set('123');editor.apply_selected()
                self.assertEqual(editor.changes, {field.id: 123})
                editor.max_visible();self.assertEqual(editor.changes, {field.id: 123})
                editor.review();editor.undo();self.assertEqual(editor.changes, {})
                editor.fields.selection_set(field.id);editor.value.set('123');editor.apply_selected()
                editor.show_inspector();self.assertEqual(len(parser.inspection_rows(editor.document)), 8)
                editor.apply_theme('Dark');editor.apply_theme('Light')
                editor.save_to(source.parent / 'edited.bin');self.assertFalse(errors)
                self.assertTrue(editor.backup.exists())
                self.assertEqual(source.read_bytes(), raw)
                self.assertEqual(field.value(parser.read_save(source.parent / 'edited.bin').payload), 123)
                self.assertEqual(parser.restore(editor.backup, source.parent / 'restored.bin').read_bytes(), raw)

    def test_procedural_gui(self):
        self.run_workflow(procedural_save())

    def test_genuine_gui(self):
        copies = os.environ.get('KENS_RAGE1_PS3_SAVE_COPIES')
        if not copies: self.skipTest('No genuine copied decrypted US/EU gameplay exports')
        for filename in copies.split(os.pathsep):
            doc = parser.read_save(filename)
            self.run_workflow(doc.raw)
