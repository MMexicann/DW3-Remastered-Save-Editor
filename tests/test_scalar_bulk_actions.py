"""Relative and selective-revert actions use native backend staging atomically."""
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from koei_editor.game_registry import get_game
from koei_editor.shared import verified_editor as backend
from tests.test_verified_editors import synthetic_raw


class ScalarBulkActionsTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def open_editor(self, game_id='dw8xl', raw=None):
        game = get_game(game_id)
        source = Path(self.folder.name) / ('copied-save' + game.extension)
        source.write_bytes(synthetic_raw(game_id) if raw is None else raw)
        editor = game.create_editor(self.root, self.root)
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)), \
                patch('koei_editor.shared.verified_gui.messagebox.showerror') as errors:
            editor.open()
            errors.assert_not_called()
        self.assertEqual(editor.backup.read_bytes(), source.read_bytes())
        return editor

    def adjust(self, editor, delta):
        with patch('koei_editor.shared.verified_gui.simpledialog.askinteger', return_value=delta):
            editor.adjust_selected()

    def test_relative_batch_uses_pending_values_preserves_hidden_edits_and_saves_surgically(self):
        editor = self.open_editor()
        editor.stage_values({'gold': 321})
        keys = ('officer_0_attack', 'officer_0_defense')
        editor.group.set('Officers')
        editor.search.set('record 1')
        editor.refresh()
        # Selection is by stable native ID, even after filtering and refresh.
        editor.search.set('')
        editor.fields.selection_set(keys)
        self.adjust(editor, -7)
        self.assertEqual(editor.changes, {'gold': 321, keys[0]: 43, keys[1]: 43})
        self.adjust(editor, 2)
        self.assertEqual(editor.changes, {'gold': 321, keys[0]: 45, keys[1]: 45})
        editor.undo()
        self.assertEqual(editor.changes, {'gold': 321, keys[0]: 43, keys[1]: 43})
        editor.review()
        document = editor.document
        expected = editor.adapter.changed_payload(document, editor.changes)
        destination = Path(self.folder.name) / 'edited.dat'
        editor.save_to(destination)
        self.assertEqual(editor.document.payload, expected)
        self.assertEqual(document.source.read_bytes(), document.raw)
        allowed = {at for key in ('gold',) + keys
                   for at in range(backend.field_map(document)[key].offset,
                                   backend.field_map(document)[key].offset + backend.field_map(document)[key].size)}
        self.assertLessEqual({i for i, (old, new) in enumerate(zip(document.payload, expected)) if old != new}, allowed)

    def test_one_out_of_range_target_rejects_entire_batch_and_keeps_undo_history(self):
        editor = self.open_editor()
        editor.stage_values({'gold': 321, 'officer_0_defense': 1499})
        before, history = dict(editor.changes), list(editor.history)
        editor.fields.selection_set(('officer_0_attack', 'officer_0_defense'))
        with patch('koei_editor.shared.verified_gui.messagebox.showerror') as error:
            self.adjust(editor, 5)
        error.assert_called_once()
        self.assertEqual(editor.changes, before)
        self.assertEqual(editor.history, history)

    def test_cancel_zero_and_empty_selection_do_not_add_undo_steps(self):
        editor = self.open_editor()
        editor.fields.selection_set('officer_0_attack')
        self.adjust(editor, None)
        self.adjust(editor, 0)
        editor.fields.selection_remove(*editor.fields.selection())
        with patch('koei_editor.shared.verified_gui.simpledialog.askinteger') as dialog:
            editor.adjust_selected()
            editor.revert_selected()
        dialog.assert_not_called()
        self.assertEqual((editor.changes, editor.history), ({}, []))

    def test_selective_revert_restores_unusual_opened_value_and_is_undoable(self):
        original = backend.decode(synthetic_raw('dw8xl'), 'dw8xl')
        payload = bytearray(original.payload)
        payload[0x7fd5:0x7fd7] = (2500).to_bytes(2, 'little')
        inner = backend.byte_cipher(bytes(payload), original.format.inner_seed)
        raw = (backend.struct.pack('<HH', backend.word_sum(inner), original.seed)
               + backend.word_cipher(inner, original.seed)
               + bytes([(sum(payload) & 255) ^ (backend.mix_word(original.seed) & 255)]))
        editor = self.open_editor(raw=raw)
        editor.stage_values({'gold': 321, 'officer_0_attack': 100})
        before = dict(editor.changes)
        editor.fields.selection_set('officer_0_attack')
        editor.revert_selected()
        self.assertEqual(editor.changes, {'gold': 321})
        self.assertEqual(backend.field_map(editor.document)['officer_0_attack'].value(editor.document.payload), 2500)
        editor.undo()
        self.assertEqual(editor.changes, before)

    def test_named_choices_cannot_be_changed_by_arithmetic(self):
        from tests.test_dw6_format import procedural_raw
        editor = self.open_editor('dw6', procedural_raw())
        editor.fields.selection_set('officer_0_weapon_0_element')
        with patch('koei_editor.shared.verified_gui.messagebox.showerror') as error, \
                patch('koei_editor.shared.verified_gui.simpledialog.askinteger') as dialog:
            editor.adjust_selected()
        error.assert_called_once()
        dialog.assert_not_called()
        self.assertEqual((editor.changes, editor.history), ({}, []))

    def test_mixed_text_and_numeric_revert_preserves_other_pending_names(self):
        from tests.test_three_hopes import procedural_hopes
        editor = self.open_editor('three_hopes', procedural_hopes())
        editor.stage_values({'gold': 123, 'shez_name': 'Navi', 'byleth_name': 'Robin'})
        before = dict(editor.changes)
        editor.fields.selection_set(('gold', 'shez_name'))
        with patch('koei_editor.shared.verified_gui.messagebox.showerror') as error, \
                patch('koei_editor.shared.verified_gui.simpledialog.askinteger') as dialog:
            editor.adjust_selected()
        error.assert_called_once()
        dialog.assert_not_called()
        self.assertEqual(editor.changes, before)
        editor.revert_selected()
        self.assertEqual(editor.changes, {'byleth_name': 'Robin'})
        editor.undo()
        self.assertEqual(editor.changes, before)

    def test_relative_edits_respect_backend_decrease_only_rules(self):
        from tests.test_three_hopes import procedural_hopes
        editor = self.open_editor('three_hopes', procedural_hopes())
        editor.fields.selection_set('gold')
        with patch('koei_editor.shared.verified_gui.messagebox.showerror') as error:
            self.adjust(editor, 1)
        error.assert_called_once()
        self.assertEqual((editor.changes, editor.history), ({}, []))
        self.adjust(editor, -45)
        self.assertEqual(editor.changes, {'gold': 12300})

    def test_reverting_a_whole_loadout_validates_final_state_without_transient_duplicates(self):
        from tests.test_hyrule_fire_emblem_depth import instruction_slot
        editor = self.open_editor('three_houses', instruction_slot())
        first, third = 'character:0:ability:0', 'character:0:ability:2'
        editor.stage_values({first: 240})
        editor.stage_values({third: 2})
        before = dict(editor.changes)
        editor.fields.selection_set(first)
        with patch('koei_editor.shared.verified_gui.messagebox.showerror') as error:
            editor.revert_selected()
        error.assert_called_once()  # Restoring only one slot would duplicate ID 2.
        self.assertEqual(editor.changes, before)
        editor.fields.selection_set((first, third))
        with patch('koei_editor.shared.verified_gui.messagebox.showerror') as error:
            editor.revert_selected()
        error.assert_not_called()
        self.assertEqual(editor.changes, {})
        editor.undo()
        self.assertEqual(editor.changes, before)


if __name__ == '__main__':
    unittest.main()
