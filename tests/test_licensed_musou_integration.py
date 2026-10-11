"""Explicit console dispatch and retained scalar sessions with generated inputs."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.game_registry import get_game
from koei_editor.games.gundam1_ps3 import parser as gundam
from koei_editor.games.kens_rage1_ps3 import parser as rage1
from koei_editor.games.kens_rage2_ps3 import parser as rage2
from tests.test_gundam1_ps3 import fixture as gundam_fixture, metadata as gundam_metadata
from tests.test_kens_rage1_ps3 import procedural_save as rage1_fixture, metadata as rage1_metadata
from tests.test_kens_rage2_ps3 import procedural_save as rage2_fixture, metadata as rage2_metadata

CASES = ((gundam, gundam_fixture, gundam_metadata),
         (rage1, rage1_fixture, rage1_metadata),
         (rage2, rage2_fixture, rage2_metadata))


class LicensedDispatchTests(unittest.TestCase):
    def test_selected_adapter_rejects_other_native_profiles_without_fallback(self):
        for backend, fixture, _metadata in CASES:
            game = get_game(backend.GAME_ID)
            adapter = game.get_scalar_adapter()
            for other, other_fixture, _ in CASES:
                if other is backend:
                    continue
                with self.subTest(selected=game.id, input=other.GAME_ID), self.assertRaises(SaveError):
                    adapter.decode(other_fixture())
            with patch.object(backend, 'read_save') as read:
                with self.assertRaises(SaveError):
                    game.read_save('signed-container.zip')
                read.assert_not_called()
            self.assertEqual(adapter.get_format().id, backend.GAME_ID)


@unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'A graphical display is required')
class LicensedSessionTests(unittest.TestCase):
    def test_registered_open_switch_review_undo_and_theme_retains_each_pending_edit(self):
        import tkinter as tk
        from tkinter import ttk
        from koei_editor.application import Application

        root = tk.Tk()
        self.addCleanup(root.destroy)
        root.withdraw()
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            app = Application(root, preferences_path=folder / 'preferences.json')
            opened = []
            for backend, fixture, metadata in CASES:
                copies = folder / backend.GAME_ID
                copies.mkdir()
                source = copies / 'DATA.BIN'
                raw = fixture()
                source.write_bytes(raw)
                (copies / 'PARAM.SFO').write_bytes(metadata())
                editor = app.select_game(backend.GAME_ID)
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                    editor.open()
                candidates = [f for f in backend.fields_for(editor.document)
                              if f.value(raw) != f.maximum]
                self.assertTrue(candidates)
                field = candidates[0]
                editor.stage_values({field.id: field.maximum})
                opened.append((backend, editor, field, source, raw))
            app.select_game('dw3')
            app.apply_theme('Dark')
            for backend, editor, field, source, raw in opened:
                self.assertIs(app.select_game(backend.GAME_ID), editor)
                self.assertEqual(editor.changes, {field.id: field.maximum})
                self.assertEqual(editor.theme_name.get(), 'Dark')
                editor.review()
                review = next(w for w in root.winfo_children() if isinstance(w, tk.Toplevel))
                def trees(widget):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Treeview):
                            yield child
                        yield from trees(child)
                self.assertEqual(len(next(trees(review)).get_children()), 1)
                review.destroy()
                editor.undo()
                self.assertEqual(editor.changes, {})
                self.assertEqual(source.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
