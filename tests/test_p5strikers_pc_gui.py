"""Real Tk save-copy workflows; procedural and optional genuine PC exports."""
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.p5strikers_pc import parser
from koei_editor.games.p5strikers_pc.editor import Editor
from tests.test_p5strikers_pc import procedural_save


class PCGuiWorkflow:
    fixture = staticmethod(procedural_save)

    def test_named_stack_search_review_undo_max_copy_backup_restore(self):
        try: root = tk.Tk()
        except tk.TclError as error: self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'pc-copy.bin'; raw = self.fixture(); source.write_bytes(raw)
            editor = Editor(root)
            errors = []
            with patch('koei_editor.shared.verified_gui.messagebox.showerror', side_effect=lambda *args: errors.append(args)), \
                    patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                editor.open()
                self.assertFalse(errors)
                fields = parser.fields_for(editor.document)
                field = next(field for field in fields if field.group == 'Consumables')
                value = 2 if field.value(editor.document.payload) != 2 else 3
                editor.group.set(field.group); editor.search.set(field.label); editor.refresh()
                self.assertIn(field.id, editor.fields.get_children())
                editor.fields.selection_set(field.id); editor.value.set(str(value)); editor.apply_selected()
                self.assertEqual(editor.changes, {field.id: value})
                editor.max_visible(); self.assertEqual(editor.changes, {field.id: value})
                editor.review(); self.assertTrue(any(isinstance(child, tk.Toplevel) for child in root.winfo_children()))
                editor.undo(); self.assertEqual(editor.changes, {})
                editor.fields.selection_set(field.id); editor.value.set(str(value)); editor.apply_selected()
                editor.show_inspector()
                self.assertEqual([table.title for table in editor.presentation.inspection_tables(editor.document)],
                                 ['Save-slot resources', 'Named ordinary item stacks', 'Character growth', 'Held Persona records'])
                editor.apply_theme('Dark'); editor.apply_theme('Light')
                destination = Path(folder) / 'edited.bin'; editor.save_to(destination)
                self.assertFalse(errors)
                self.assertEqual(source.read_bytes(), raw)
                self.assertTrue(editor.backup.exists())
                restored = parser.restore(editor.backup, Path(folder) / 'restored.bin')
                self.assertEqual(restored.read_bytes(), raw)
                self.assertEqual(field.value(parser.read_save(destination).payload), value)


class ProceduralPCGuiTests(PCGuiWorkflow, unittest.TestCase):
    pass


@unittest.skipUnless(os.environ.get('P5S_PC_SAVE_COPIES'), 'No private complete PC player save')
class GenuinePCGuiTests(PCGuiWorkflow, unittest.TestCase):
    fixture = staticmethod(lambda: Path(os.environ['P5S_PC_SAVE_COPIES'].split(os.pathsep)[0]).read_bytes())
