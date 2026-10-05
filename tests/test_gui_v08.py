"""Elixir GUI interactions and short-window form accessibility."""
from pathlib import Path
import struct
import sys
import tkinter as tk
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / 'tests'))
import gui
import progression_editor as progression
import save_writer
from save_parser import read_save, parse_bytes
from test_bodyguards import edited_fixture_bytes

FIXTURE = PROJECT.parents[1] / 'work/original-upload/GameStatusData.sav'


@unittest.skipUnless(FIXTURE.exists(), 'Private supplied fixture is required.')
class ElixirGuiRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = read_save(FIXTURE)

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.editor = gui.Editor(self.root)
        self.errors = []
        self.error_patch = patch.object(gui.messagebox, 'showerror', side_effect=lambda *a, **k: self.errors.append(a))
        self.confirm_patch = patch.object(gui.messagebox, 'askyesno', return_value=True)
        self.error_patch.start()
        self.confirm_patch.start()
        self.editor.document = self.source
        self.editor.set_loaded(True)
        self.editor.refresh()

    def tearDown(self):
        self.confirm_patch.stop()
        self.error_patch.stop()
        self.root.destroy()

    def test_manual_max_review_undo_and_discard(self):
        g = self.editor
        saved = self.source.properties['BeansNum']['value']
        self.assertEqual(g.author_label.cget('text'), 'Made by Mexican')
        self.assertEqual(int(g.elixir_input.get()), saved)
        g.elixir_input.set('17'); g.apply_elixirs()
        change = g.changes['progression', 0, 'HuanglongElixirs']
        self.assertEqual(g.review_change(change), ('Huanglong Elixirs', 'Final balance', saved, 17))
        g.max_elixirs()
        self.assertEqual(int(g.elixir_input.get()), 999)
        g.undo()
        self.assertEqual(int(g.elixir_input.get()), 17)
        g.discard()
        self.assertFalse(g.changes)
        self.assertEqual(int(g.elixir_input.get()), saved)
        self.assertFalse(self.errors)

    def test_invalid_entry_preserves_pending_batch_and_history(self):
        g = self.editor
        g.max_elixirs()
        before, history = g.changes.copy(), list(g.history)
        for value in ('', '-1', '1000', '1.5', 'abc'):
            g.elixir_input.set(value); g.apply_elixirs()
            self.assertEqual(g.changes, before)
            self.assertEqual(g.history, history)
        self.assertEqual(len(self.errors), 5)

    def test_reset_to_saved_balance_overrides_pending_story_reward(self):
        g = self.editor
        route = next(row['officer_id'] for row in progression.progression_state(self.source)['officers']
                     if row['can_clear'] and not row['cleared'])
        g.stage_many(progression.musou_clear_changes(self.source, route))
        saved = self.source.properties['BeansNum']['value']
        self.assertEqual(int(g.elixir_input.get()), min(999, saved + 3))
        g.elixir_input.set(str(saved)); g.apply_elixirs()
        self.assertIn(('progression', 0, 'HuanglongElixirs'), g.changes)
        edited = parse_bytes(save_writer.serialize(self.source, list(g.changes.values()))[0])
        self.assertEqual(edited.properties['BeansNum']['value'], saved)
        self.assertTrue(edited.properties['EngiClearCharaArray']['value']['values'][route])
        g.undo()
        self.assertEqual(int(g.elixir_input.get()), min(999, saved + 3))
        self.assertFalse(self.errors)

    def test_unusual_counter_disables_editing_without_disabling_officers(self):
        document = parse_bytes(edited_fixture_bytes(self.source, [(self.source.properties['BeansNum'], struct.pack('<i', 1000))]))
        g = self.editor
        g.document = document; g.set_loaded(True); g.refresh()
        for widget in (g.elixir_entry, g.elixir_apply_button, g.elixir_max_button):
            self.assertEqual(str(widget.cget('state')), 'disabled')
        self.assertIn('outside', g.elixir_note.get())
        g.inputs['Attack'].set('149'); g.apply_officer()
        self.assertFalse(self.errors)
        edited = parse_bytes(save_writer.serialize(document, list(g.changes.values()))[0])
        self.assertEqual(edited.properties['BeansNum']['value'], 1000)

    def test_long_forms_have_scrollable_content(self):
        self.root.update_idletasks()
        self.assertGreaterEqual(len(self.editor.scroll_areas), 7)
        for canvas, content in self.editor.scroll_areas:
            self.assertEqual(canvas.winfo_reqheight(), 200)
            self.assertTrue(canvas.cget('scrollregion'))
        # Controls no longer impose a thousand-pixel minimum window height.
        self.assertLess(self.root.winfo_reqheight(), 790)


if __name__ == '__main__':
    unittest.main()
