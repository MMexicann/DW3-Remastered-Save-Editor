"""Reordering conserves the exact original equipped weapon multiset."""
import os
from pathlib import Path
import struct
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.game_registry import get_game
from koei_editor.games.dw3.models import SaveError
from koei_editor.shared import verified_editor as backend
from tests.test_dw8_affinity import procedural_weapons


def procedural_equipment():
    original = backend.decode(procedural_weapons(), 'dw8xl')
    payload = bytearray(original.payload)
    for officer, pair in enumerate(((0, 1), (0, 0), (0, 2), (0, 3), (0, 65535), (1, 0))):
        struct.pack_into('<HH', payload, 0x7fc9 + officer * 0x48 + 0x30, *pair)
    inner = backend.byte_cipher(bytes(payload), original.format.inner_seed)
    return (struct.pack('<HH', backend.word_sum(inner), original.seed)
            + backend.word_cipher(inner, original.seed)
            + bytes([(sum(payload) & 255) ^ (backend.mix_word(original.seed) & 255)]))


class DW8WeaponOrderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = backend.decode(procedural_equipment(), 'dw8xl')

    def test_only_distinct_pairs_of_existing_qualified_weapons_get_controls(self):
        mapping = backend.field_map(self.document)
        self.assertTrue({'officer_0_first_weapon', 'officer_5_first_weapon'} <= mapping.keys())
        for slot in range(1, 5):
            self.assertNotIn(f'officer_{slot}_first_weapon', mapping)
        self.assertEqual(tuple(value for value, _ in backend.field_options(self.document, 'officer_0_first_weapon')), (1, 2))
        self.assertEqual(backend.serialize(self.document, {}), self.document.raw)

    def test_swap_is_atomic_surgical_and_does_not_change_weapon_records_or_other_officers(self):
        document = self.document
        field = backend.field_map(document)['officer_0_first_weapon']
        changes = backend.stage(document, {}, field.id, 2)
        reopened = backend.decode(backend.serialize(document, changes), 'dw8xl')
        expected = bytearray(document.payload)
        struct.pack_into('<HH', expected, field.offset, 1, 0)
        self.assertEqual(reopened.payload, bytes(expected))
        self.assertEqual(backend.progression(reopened, 1)['weapon_slots'], (2, 1))
        self.assertEqual(backend.progressions(reopened)[1:], backend.progressions(document)[1:])
        self.assertEqual(backend.weapons(reopened), backend.weapons(document))
        self.assertEqual(backend.bodyguards(reopened), backend.bodyguards(document))
        self.assertEqual(reopened.seed, document.seed)

    def test_third_weapon_duplicates_unknown_fields_and_non_integer_edits_rejected(self):
        for value in (0, 3, 1831, 65536, True, '2', 2.0):
            with self.subTest(value=value), self.assertRaises(SaveError):
                backend.stage(self.document, {}, 'officer_0_first_weapon', value)
        for changes in ({'officer_0_second_weapon': 1}, {'officer_1_first_weapon': 2}):
            with self.assertRaises(SaveError):
                backend.serialize(self.document, changes)

    def test_order_is_excluded_from_max_and_original_assignment_unstages_pair(self):
        self.assertEqual(backend.limit_values(self.document, {}, ['officer_0_first_weapon']), {})
        self.assertEqual(backend.maximums(self.document, {}, 'Weapon order'), {})
        changes = backend.stage(self.document, {}, 'officer_0_first_weapon', 2)
        self.assertEqual(backend.stage(self.document, changes, 'officer_0_first_weapon', 1), {})
        self.assertEqual(backend.maximums(self.document, changes, 'Weapon order'), changes)

    @unittest.skipUnless(os.environ.get('DW8XL_SAVE_COPY'), 'Private native DW8 XL copy not configured.')
    def test_genuine_copy_unchanged_and_original_equipped_pair_swap(self):
        document = backend.read_save(Path(os.environ['DW8XL_SAVE_COPY']), 'dw8xl')
        fields = [field for field in backend.fields_for(document) if field.group == 'Weapon order']
        self.assertTrue(fields)
        self.assertEqual(backend.serialize(document, {}), document.raw)
        field = fields[0]
        changes = backend.stage(document, {}, field.id, field.opened_slots[1])
        reopened = backend.decode(backend.serialize(document, changes), 'dw8xl')
        self.assertEqual(backend.progression(reopened, field.slot)['weapon_slots'], field.opened_slots[::-1])
        allowed = set(range(field.offset, field.offset + 4))
        self.assertLessEqual({i for i, (old, new) in enumerate(zip(document.payload, reopened.payload)) if old != new}, allowed)
        self.assertEqual(backend.weapons(reopened), backend.weapons(document))

    def test_gui_choices_stage_both_references_undo_review_and_safe_copy(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.addCleanup(root.destroy)
        root.withdraw()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'copy.dat'
            source.write_bytes(self.document.raw)
            editor = get_game('dw8xl').create_editor(root, root)
            with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                editor.open()
            self.assertEqual(editor.backup.read_bytes(), source.read_bytes())
            editor.group.set('Weapon order')
            editor.refresh()
            editor.fields.selection_set('officer_0_first_weapon')
            editor.selected()
            self.assertEqual(len(editor.value_choice.cget('values')), 2)
            editor.choice_value.set(editor.value_choice.cget('values')[1])
            editor.selected_choice()
            editor.apply_selected()
            self.assertEqual(editor.changes, {'officer_0_first_weapon': 2})
            editor.review()
            editor.revert_selected()
            self.assertEqual(editor.changes, {})
            editor.undo()
            self.assertEqual(editor.changes, {'officer_0_first_weapon': 2})
            editor.save_to(Path(folder) / 'edited.dat')
            self.assertEqual(backend.progression(editor.document, 1)['weapon_slots'], (2, 1))
            self.assertEqual(source.read_bytes(), self.document.raw)


if __name__ == '__main__':
    unittest.main()
