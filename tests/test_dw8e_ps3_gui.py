"""DW8E procedural SYSTEM GUI workflow; no game execution."""
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.dw8e_ps3.editor import Editor
from koei_editor.games.dw8e_ps3 import parser as backend
from tests.test_dw8e_ps3_horses import procedural_raw
from tests import test_ps3_expansion as context_tests


class DW8EmpiresGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / 'APP.BIN'
        self.source.write_bytes(procedural_raw())
        (self.source.parent / 'PARAM.SFO').write_bytes(context_tests.PS3ContextTests.metadata('NPUB31656-SYSTEM'))
        self.editor = Editor(self.root)
        self.errors = []
        errors = patch('koei_editor.shared.verified_gui.messagebox.showerror',
                       side_effect=lambda *args: self.errors.append(args))
        errors.start()
        self.addCleanup(errors.stop)
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(self.source)):
            self.editor.open()
        self.assertEqual(self.errors, [])

    def test_new_head_choice_witnessed_positions_apply_undo_and_save(self):
        editor = self.editor
        editor.fields.selection_set('horse_0_head')
        editor.selected()
        self.assertEqual(set(editor._choice_values.values()), {1, 3})
        editor.choice_value.set(next(label for label, value in editor._choice_values.items() if value == 3))
        editor.selected_choice()
        editor.apply_selected()
        self.assertEqual(editor.changes, {'horse_0_head': 3})
        editor.review()
        editor.revert_selected()
        self.assertEqual(editor.changes, {})
        editor.undo()
        self.assertEqual(editor.changes, {'horse_0_head': 3})
        before = self.source.read_bytes()
        editor.save_to(self.source.with_name('head-edited.bin'))
        self.assertEqual(self.errors, [])
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(backend.field_map(editor.document)['horse_0_head'].value(editor.document.payload), 3)
        self.assertEqual(backend.restore(editor.backup, self.source.with_name('head-restored.bin')).read_bytes(), before)

    def test_existing_named_body_apply_review_undo_max_inspection_save_backup(self):
        editor = self.editor
        editor.search.set('Final Horse')
        editor.refresh()
        self.assertEqual(set(editor.fields.get_children()),
                         {f'horse_149_{key}' for key, _, _ in backend.SLIDERS})
        editor.fields.selection_set('horse_149_body')
        editor.selected()
        editor.value.set('4')
        editor.apply_selected()
        self.assertEqual(editor.changes, {'horse_149_body': 4})
        editor.review()
        self.assertTrue(any(isinstance(child, tk.Toplevel) for child in self.root.winfo_children()))
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.max_visible()
        self.assertEqual(editor.changes, {})
        editor.max_selected()
        self.assertEqual(editor.changes, {})
        editor.fields.selection_set('horse_149_body')
        editor.value.set('4')
        editor.apply_selected()
        editor.show_inspector()
        table, = editor.presentation.inspection_tables(editor.document)
        self.assertEqual(len(table.rows), 150)
        self.assertEqual(table.rows[-1][1], 'Final Horse')
        before = self.source.read_bytes()
        other_folder = self.source.parent / 'other-output'
        other_folder.mkdir()
        rejected_destination = other_folder / 'edited.bin'
        editor.save_to(rejected_destination)
        self.assertEqual(len(self.errors), 1)
        self.assertFalse(rejected_destination.exists())
        self.assertEqual(editor.changes, {'horse_149_body': 4})
        self.errors.clear()
        destination = self.source.with_name('edited.bin')
        editor.save_to(destination)
        self.assertEqual(self.errors, [])
        self.assertEqual(self.source.read_bytes(), before)
        self.assertTrue(editor.backup.exists())
        result = backend.read_save(destination)
        offset = backend.field_map(result)['horse_149_body'].offset
        opened = backend.decode(before)
        self.assertEqual(result.payload[offset], 4)
        self.assertEqual(result.payload[:offset], opened.payload[:offset])
        self.assertEqual(result.payload[offset + 1:], opened.payload[offset + 1:])

        restored = self.source.with_name('restored.bin')
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(editor.backup)), \
             patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename', return_value=str(restored)), \
             patch('koei_editor.shared.verified_gui.messagebox.askyesno', return_value=True):
            editor.restore()
        self.assertEqual(self.errors, [])
        self.assertEqual(restored.read_bytes(), before)
        editor.apply_theme('Dark')
        self.assertEqual(editor.theme_name.get(), 'Dark')

    @unittest.skipUnless(os.environ.get('DW8E_PS3_SYSTEM_COPY'), 'Private genuine US PS3 SYSTEM not supplied')
    def test_genuine_copied_system_gui_save_backup_restore(self):
        private_source = Path(os.environ['DW8E_PS3_SYSTEM_COPY'])
        backend._context(private_source, required=True)
        raw = private_source.read_bytes()
        source = self.source.with_name('genuine-copy.bin')
        source.write_bytes(raw)
        editor = self.editor
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
            editor.open()
        self.assertEqual(self.errors, [])
        field = backend.fields_for(editor.document)[0]
        value = (field.value(editor.document.payload) + 1) % 5
        editor.stage_values({field.id: value})
        editor.review()
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.stage_values({field.id: value})
        destination = source.with_name('genuine-edited.bin')
        editor.save_to(destination)
        self.assertEqual(self.errors, [])
        self.assertEqual(source.read_bytes(), raw)
        self.assertEqual(private_source.read_bytes(), raw)
        self.assertEqual(backend.field_map(backend.read_save(destination))[field.id].value(
            backend.read_save(destination).payload), value)
        snapshot = editor.backup
        restored = source.with_name('genuine-restored.bin')
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(snapshot)), \
             patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename', return_value=str(restored)), \
             patch('koei_editor.shared.verified_gui.messagebox.askyesno', return_value=True):
            editor.restore()
        self.assertEqual(self.errors, [])
        self.assertEqual(restored.read_bytes(), raw)
