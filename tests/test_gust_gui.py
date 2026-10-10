"""Registered Gust/FF2 GUI workflows, with distinct optional native inputs.

Public fixture factories are procedural. Optional environment variables select
private reviewed copies; none of these tests establishes actual game loading.
"""
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.game_registry import get_game


class GustGuiTests(unittest.TestCase):
    def exercise(self, game_id, raw):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as name:
                folder = Path(name)
                game = get_game(game_id)
                source = folder / ('input-copy' + game.extension)
                target = folder / ('edited-copy' + game.extension)
                restored = folder / ('restored-copy' + game.extension)
                source.write_bytes(raw)
                editor = game.create_editor(root, root)
                with patch('koei_editor.shared.verified_gui.messagebox.showerror') as errors:
                    with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename',
                               return_value=str(source)):
                        editor.open()
                    errors.assert_not_called()
                    self.assertEqual(editor.document.raw, raw)
                    self.assertEqual(editor.backup.read_bytes(), raw)
                    fields = editor.adapter.fields_for(editor.document)
                    # Exercise quality rather than a second currency-only path
                    # when this adapter has a qualified occupied quality record.
                    fields = sorted(fields, key=lambda field: ('quality' not in field.id, field.id))
                    for field in fields:
                        original = field.value(editor.document.payload)
                        value = field.minimum if original != field.minimum else field.maximum
                        if value != original:
                            break
                    else:
                        self.skipTest('This native snapshot has no alterable qualified field.')
                    editor.group.set(field.group)
                    editor.search.set(field.id)
                    editor.refresh()
                    self.assertIn(field.id, editor.fields.get_children())
                    editor.fields.selection_set(field.id)
                    editor.value.set(str(value))
                    editor.apply_selected()
                    self.assertEqual(editor.changes, {field.id: value})
                    editor.max_visible()
                    self.assertEqual(editor.changes, {field.id: value})
                    editor.review()
                    self.assertTrue(any(isinstance(child, tk.Toplevel)
                                        for child in root.winfo_children()))
                    editor.undo()
                    self.assertEqual(editor.changes, {})
                    editor.value.set(str(value))
                    editor.apply_selected()
                    editor.show_inspector()
                    self.assertTrue(editor.presentation.inspection_tables(editor.document))
                    editor.apply_theme('Dark')
                    editor.apply_theme('Light')
                    editor.make_backup()
                    snapshot = editor.backup
                    self.assertEqual(snapshot.read_bytes(), raw)
                    with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename',
                               return_value=str(target)):
                        editor.save_as()
                    errors.assert_not_called()
                    self.assertEqual(editor.changes, {})
                    reopened = game.read_save(target)
                    self.assertEqual(field.value(reopened.payload), value)
                    self.assertEqual(source.read_bytes(), raw)
                    with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename',
                               return_value=str(snapshot)), \
                         patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename',
                               return_value=str(restored)):
                        editor.restore()
                    errors.assert_not_called()
                    self.assertEqual(restored.read_bytes(), raw)
                    self.assertEqual(game.read_save(restored).raw, raw)
        finally:
            root.destroy()

    def test_registered_procedural_sophie_quality_workflow(self):
        from tests.test_sophie_format import fixture
        self.exercise('atelier_sophie', fixture())

    def test_registered_procedural_ryza2_quality_workflow(self):
        from tests.test_ryza_format import procedural_raw
        self.exercise('atelier_ryza2', procedural_raw())

    def test_registered_procedural_ff2_system_workflow(self):
        from tests.test_fatal_frame2_remake import procedural_raw
        self.exercise('fatal_frame2_remake', procedural_raw())

    def native(self, game_id, variable):
        source = os.environ.get(variable)
        if not source:
            self.skipTest(f'Private native input {variable} is not configured.')
        # Read through the registered copy-only parser before making a temporary
        # GUI test copy, so a live/cloud path never becomes a test input.
        self.exercise(game_id, get_game(game_id).read_save(Path(source)).raw)

    def test_native_sophie_quality_workflow(self):
        self.native('atelier_sophie', 'SOPHIE_SAVE_COPY')

    def test_native_ryza2_quality_workflow(self):
        self.native('atelier_ryza2', 'RYZA2_SAVE_COPY')

    def test_native_ff2_system_workflow(self):
        self.native('fatal_frame2_remake', 'FATAL_FRAME2_SYSTEM_COPY')
