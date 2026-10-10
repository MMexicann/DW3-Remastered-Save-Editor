"""Wo Long shared GUI safety; procedural data and no game execution."""
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.wolong.wolong_editor import Editor
from koei_editor.games.wolong import wolong_parser as backend
from tests.test_wolong_format import procedural_payload


class WolongGuiTests(unittest.TestCase):
    def test_search_edit_manual_no_max_review_undo_inspection_safe_save(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'copy.bin'
            source.write_bytes(procedural_payload())
            editor = Editor(root)
            errors = []
            with patch('koei_editor.shared.verified_gui.messagebox.showerror', side_effect=lambda *args: errors.append(args)), \
                    patch('koei_editor.shared.verified_gui.messagebox.showinfo'), \
                    patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                editor.open()
                self.assertEqual(errors, [])
                editor.search.set('Copper')
                editor.refresh()
                self.assertEqual(editor.fields.get_children(), ('sen',))
                editor.fields.selection_set('sen')
                editor.value.set('12345')
                editor.apply_selected()
                self.assertEqual(editor.changes, {'sen': 12345})
                editor.max_visible()
                self.assertEqual(editor.changes, {'sen': 12345})
                editor.review()
                editor.undo()
                self.assertEqual(editor.changes, {})
                editor.group.set('Stored stacks')
                editor.search.set('key 0x000001C8')
                editor.refresh()
                self.assertEqual(editor.fields.get_children(), ('storage_items_8_num',))
                editor.fields.selection_set('storage_items_8_num')
                editor.value.set('10')
                editor.apply_selected()
                self.assertEqual(editor.changes, {'storage_items_8_num': 10})
                editor.show_inspector()
                self.assertEqual(tuple(table.title for table in editor.presentation.inspection_tables(editor.document)),
                                 ('Inventory', 'Companions', 'Progression', 'Profile'))
                editor.apply_theme('Dark')
                editor.apply_theme('Light')
                destination = Path(directory) / 'edited.bin'
                with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename', return_value=str(destination)):
                    editor.save_as()
                self.assertEqual(errors, [])
                self.assertEqual(source.read_bytes(), procedural_payload())
                reopened = backend.read_save(destination)
                self.assertEqual(backend.field_map(reopened)['storage_items_8_num'].value(reopened.payload), 10)
                self.assertTrue(list((source.parent / 'WarriorsEditorBackups').glob('*.bin')))
