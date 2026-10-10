"""All-Stars copy editor GUI safety; no game binary is executed."""
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.stars.stars_editor import Editor
from koei_editor.games.stars import stars_parser as backend
from tests.test_stars_format import procedural_raw


class StarsGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.source = Path(self.temporary.name) / 'copy.bin'
        self.source.write_bytes(procedural_raw())
        self.editor = Editor(self.root)
        self.errors = []
        errors = patch('koei_editor.shared.verified_gui.messagebox.showerror',
                       side_effect=lambda *args: self.errors.append(args))
        errors.start()
        self.addCleanup(errors.stop)
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(self.source)):
            self.editor.open()
        self.assertEqual(self.errors, [])

    def test_search_edit_max_review_undo_history_theme_safe_save(self):
        editor = self.editor
        editor.search.set('slot_3_gold')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('slot_3_gold',))
        editor.fields.selection_set('slot_3_gold')
        editor.value.set('12345')
        editor.apply_selected()
        self.assertEqual(editor.changes, {'slot_3_gold': 12345})
        editor.review()
        self.assertTrue(any(isinstance(child, tk.Toplevel) for child in self.root.winfo_children()))
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.max_visible()
        self.assertEqual(editor.changes, {'slot_3_gold': 9_999_999})
        editor.search.set('slot_1_gold')
        editor.refresh()
        editor.max_visible()
        self.assertEqual(editor.changes, {'slot_3_gold': 9_999_999})
        editor.show_inspector()
        tables = editor.presentation.inspection_tables(editor.document)
        self.assertEqual(tuple(table.title for table in tables), ('Campaign gold', 'Materials', 'System history'))
        self.assertTrue(any('Lifetime earned gold' in row[0] for row in tables[2].rows))
        editor.group.set('Materials')
        editor.search.set('slot_0_material_0')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('slot_0_material_0',))
        editor.fields.selection_set('slot_0_material_0')
        editor.value.set('321')
        editor.apply_selected()
        editor.max_visible()
        self.assertEqual(editor.changes['slot_0_material_0'], 321)
        editor.apply_theme('Dark')
        editor.apply_theme('Light')
        destination = Path(self.temporary.name) / 'edited.bin'
        with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename', return_value=str(destination)):
            editor.save_as()
        self.assertEqual(self.errors, [])
        self.assertEqual(self.source.read_bytes(), procedural_raw())
        decoded = backend.read_save(destination)
        self.assertEqual(backend.FIELDS[3].value(decoded.payload), 9_999_999)
        self.assertEqual(backend.field_map(decoded)['slot_0_material_0'].value(decoded.payload), 321)
        self.assertEqual(decoded.payload[:0x79B66], editor.document.payload[:0x79B66])
        self.assertTrue(list((self.source.parent / 'WarriorsEditorBackups').glob('*.bin')))
