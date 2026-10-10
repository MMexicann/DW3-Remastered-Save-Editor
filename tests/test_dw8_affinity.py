"""Procedural/native-file affinity safety tests; no game-load claim."""
import os
from pathlib import Path
import struct
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

import koei_editor.shared.verified_editor as editor
from koei_editor.games.dw3.models import SaveError
from tests.test_verified_editors import synthetic_raw


def procedural_weapons():
    document = editor.decode(synthetic_raw('dw8xl'), 'dw8xl')
    payload = bytearray(document.payload)
    for index, state, identity, affinity in ((0, 1, 7, 0), (1, 3, 12, 2),
                                            (2, 0, 17, 1), (3, 1, 65535, 1),
                                            (4, 1, 15, 255)):
        offset = editor.DW8_WEAPON_BASE + index * editor.DW8_WEAPON_STRIDE
        payload[offset] = state
        payload[offset+2:offset+4] = identity.to_bytes(2, 'little')
        payload[offset+4] = affinity
        payload[offset+5:offset+18] = bytes((70, 7, 255, 255, 255, 255, 255, 4, 0, 0, 0, 0, 0))
    inner = editor.byte_cipher(bytes(payload), document.format.inner_seed)
    return (struct.pack('<HH', editor.word_sum(inner), document.seed)
            + editor.word_cipher(inner, document.seed)
            + bytes([(sum(payload) & 255) ^ (editor.mix_word(document.seed) & 255)]))


class DW8AffinityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = editor.decode(procedural_weapons(), 'dw8xl')

    def test_only_observed_affinities_on_existing_qualified_records_are_editable(self):
        keys = set(editor.field_map(self.document))
        self.assertTrue({'weapon_0_affinity', 'weapon_1_affinity'} <= keys)
        self.assertTrue({'weapon_2_affinity', 'weapon_3_affinity', 'weapon_4_affinity'}.isdisjoint(keys))
        for value in (0, 1, 2):
            changes = editor.stage(self.document, {}, 'weapon_0_affinity', value)
            reopened = editor.decode(editor.serialize(self.document, changes), 'dw8xl')
            expected = bytearray(self.document.payload)
            expected[editor.DW8_WEAPON_BASE+4] = value
            self.assertEqual(reopened.payload, bytes(expected))
        for value in (-1, 3, 255, True, '1', 1.0):
            with self.assertRaises(SaveError):
                editor.stage(self.document, {}, 'weapon_0_affinity', value)

    def test_all_max_actions_exclude_affinity_choices(self):
        changes = editor.maximums(self.document, {})
        self.assertFalse(any(key.endswith('_affinity') for key in changes))
        self.assertEqual(editor.maximums(self.document, {}, 'Weapon affinity'), {})
        self.assertEqual(editor.limit_values(self.document, {}, ['weapon_0_affinity']), {})
        original = editor.stage(self.document, {}, 'weapon_0_affinity', 1)
        self.assertEqual(editor.maximums(self.document, original, 'Weapon affinity'), original)
        self.assertEqual(editor.stage(self.document, original, 'weapon_0_affinity', 0), {})

    @unittest.skipUnless(os.environ.get('DW8XL_SAVE_COPY'), 'Private genuine DW8 PC fixture not configured.')
    def test_genuine_weapon_affinity_only_roundtrip_preserves_other_weapon_properties(self):
        document = editor.read_save(Path(os.environ['DW8XL_SAVE_COPY']), 'dw8xl')
        self.assertEqual(editor.serialize(document, {}), document.raw)
        field = next(field for field in editor.fields_for(document) if field.group == 'Weapon affinity')
        old = field.value(document.payload)
        changes = editor.stage(document, {}, field.id, (old + 1) % 3)
        reopened = editor.decode(editor.serialize(document, changes), 'dw8xl')
        differences = {i for i, pair in enumerate(zip(document.payload, reopened.payload)) if pair[0] != pair[1]}
        self.assertEqual(differences, {field.offset})
        before, after = editor.weapon(document, field.slot), editor.weapon(reopened, field.slot)
        before.pop('affinity'); after.pop('affinity')
        self.assertEqual(before, after)
        self.assertEqual(editor.progressions(document), editor.progressions(reopened))
        self.assertEqual(editor.bodyguards(document), editor.bodyguards(reopened))

    @unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'A graphical display is required.')
    def test_gui_search_stage_undo_review_backup_and_save_as(self):
        import koei_editor.games.dw8xl.dw8xl_editor as dw8xl_editor
        import koei_editor.shared.verified_gui as verified_gui
        root = tk.Tk()
        root.withdraw()
        try:
            workspace = dw8xl_editor.Editor(root)
            with tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / 'dw8-copy.dat'
                raw = procedural_weapons()
                source.write_bytes(raw)
                with patch.object(verified_gui.filedialog, 'askopenfilename', return_value=str(source)), \
                        patch.object(verified_gui.messagebox, 'showerror') as errors:
                    workspace.open()
                    errors.assert_not_called()
                self.assertEqual(workspace.backup.read_bytes(), raw)
                workspace.group.set('Weapon affinity')
                workspace.search.set('0001')
                workspace.refresh()
                self.assertEqual(workspace.fields.get_children(), ('weapon_0_affinity',))
                workspace.fields.selection_set('weapon_0_affinity')
                workspace.selected()
                self.assertIn('Max excludes', workspace.selection_info.get())
                workspace.max_selected()
                self.assertEqual(workspace.changes, {})
                workspace.value.set('1')
                workspace.apply_selected()
                self.assertEqual(workspace.changes, {'weapon_0_affinity':1})
                workspace.undo()
                self.assertEqual(workspace.changes, {})
                workspace.value.set('2')
                workspace.apply_selected()
                workspace.review()
                destination = Path(folder) / 'dw8-edited.dat'
                with patch.object(verified_gui.filedialog, 'asksaveasfilename', return_value=str(destination)), \
                        patch.object(verified_gui.messagebox, 'showerror') as errors:
                    workspace.save_as()
                    errors.assert_not_called()
                self.assertEqual(editor.weapon(workspace.document, 1)['affinity'], 2)
                self.assertEqual(source.read_bytes(), raw)
                self.assertEqual(workspace.changes, {})
        finally:
            root.destroy()


if __name__ == '__main__':
    unittest.main()
