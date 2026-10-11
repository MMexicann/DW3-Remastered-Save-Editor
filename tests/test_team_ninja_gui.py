"""Real Tk copy workflows; procedural and private native evidence are separate."""
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.game_registry import get_game
from tests.test_nioh3_format import procedural_raw
from tests.test_ninja_gaiden_ii import procedural_story


class CopyWorkflow:
    def test_search_stack_review_undo_themes_save_backup_restore_and_rejection(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        game = get_game(self.game_id)
        adapter = game.get_scalar_adapter()
        raw = self.fixture_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = folder / ('source-copy' + game.extension)
            source.write_bytes(raw)
            editor = game.create_editor(root, root)
            errors = []
            with patch('koei_editor.shared.verified_gui.messagebox.showerror',
                       side_effect=lambda *args: errors.append(args)), \
                    patch('koei_editor.shared.verified_gui.messagebox.showinfo'):
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename',
                           return_value=str(source)):
                    editor.open()
                self.assertEqual(errors, [])
                field = next(field for field in adapter.fields_for(editor.document)
                             if field.size <= 2 and field.maximum > 1)
                opened = field.value(editor.document.payload)
                editor.search.set(field.id)
                editor.refresh()
                self.assertEqual(editor.fields.get_children(), (field.id,))
                editor.fields.selection_set(field.id)
                editor.value.set(str(opened - 1))
                editor.apply_selected()
                pending = {field.id: opened - 1}
                self.assertEqual(editor.changes, pending)
                editor.max_selected()
                editor.max_visible()
                self.assertEqual(editor.changes, pending)
                editor.review()
                self.assertEqual([(f.id, before, after) for f, before, after in
                                  adapter.review(editor.document, editor.changes)],
                                 [(field.id, opened, opened - 1)])
                self.assertTrue(any(isinstance(child, tk.Toplevel)
                                    for child in root.winfo_children()))
                editor.undo()
                self.assertEqual(editor.changes, {})
                editor.fields.selection_set(field.id)
                editor.value.set(str(opened - 1))
                editor.apply_selected()
                self.assertEqual(editor.changes, pending)
                resource = next(resource for resource in adapter.fields_for(editor.document)
                                if resource.group in ('Resources', 'Balances') and resource.size >= 4
                                and resource.value(editor.document.payload) > 0)
                resource_opened = resource.value(editor.document.payload)
                editor.search.set(resource.id)
                editor.refresh()
                editor.fields.selection_set(resource.id)
                editor.value.set(str(resource_opened - 1))
                editor.apply_selected()
                pending[resource.id] = resource_opened - 1
                editor.max_visible()
                self.assertEqual(editor.changes, pending)
                editor.review()
                self.assertEqual({row.id for row, _before, _after in
                                  adapter.review(editor.document, editor.changes)}, set(pending))
                editor.show_inspector()
                self.assertTrue(editor.presentation.inspection_tables(editor.document))
                editor.apply_theme('Dark')
                editor.apply_theme('Light')
                editor.make_backup()
                snapshot = editor.backup
                self.assertEqual(snapshot.read_bytes(), raw)
                destination = folder / ('edited-copy' + game.extension)
                with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename',
                           return_value=str(destination)):
                    editor.save_as()
                self.assertEqual(errors, [])
                self.assertEqual(editor.changes, {})
                self.assertEqual(editor.document.source.resolve(), destination.resolve())
                saved = adapter.read_save(destination)
                self.assertEqual(field.value(saved.payload), opened - 1)
                self.assertEqual(resource.value(saved.payload), resource_opened - 1)
                self.assertEqual(source.read_bytes(), raw)
                self.assertEqual(snapshot.read_bytes(), raw)
                restored = folder / ('restored-copy' + game.extension)
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename',
                           return_value=str(snapshot)), \
                        patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename',
                              return_value=str(restored)):
                    editor.restore()
                self.assertEqual(errors, [])
                self.assertEqual(restored.read_bytes(), raw)
                before = destination.read_bytes()
                editor.save_to(source)
                self.assertEqual(len(errors), 1)
                self.assertEqual(source.read_bytes(), raw)
                self.assertEqual(destination.read_bytes(), before)
                destination.write_bytes(before[:-1] + bytes([before[-1] ^ 1]))
                rejected = folder / ('changed-source' + game.extension)
                editor.save_to(rejected)
                self.assertEqual(len(errors), 2)
                self.assertFalse(rejected.exists())


class Nioh3ProceduralGuiTests(CopyWorkflow, unittest.TestCase):
    game_id = 'nioh3'

    def fixture_bytes(self):
        return procedural_raw()


class NGIIProceduralGuiTests(CopyWorkflow, unittest.TestCase):
    game_id = 'ninjagaiden2_x360'

    def fixture_bytes(self):
        return procedural_story()


@unittest.skipUnless(os.environ.get('NIOH3_SAVE_COPY'), 'Private native Nioh 3 USER copy not selected.')
class Nioh3NativeGuiTests(CopyWorkflow, unittest.TestCase):
    game_id = 'nioh3'

    def fixture_bytes(self):
        # Validate the external input before copying it to the temporary workflow.
        return get_game(self.game_id).read_save(os.environ['NIOH3_SAVE_COPY']).raw


@unittest.skipUnless(os.environ.get('NGII_SAVE_COPY'), 'Private native NGII story copy not selected.')
class NGIINativeGuiTests(CopyWorkflow, unittest.TestCase):
    game_id = 'ninjagaiden2_x360'

    def fixture_bytes(self):
        return get_game(self.game_id).read_save(os.environ['NGII_SAVE_COPY']).raw
