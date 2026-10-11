"""Original PC selector edits preserve own-family identity and native integrity."""
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.wo1_pc import wo1_codec as codec
from koei_editor.games.wo1_pc import wo1_parser as backend
from koei_editor.games.wo1_pc.wo1_editor import Editor
from tests.test_wo1_pc_format import procedural_raw


def equipped_raw():
    raw = bytearray(procedural_raw())
    raw[backend.OFFICER_BASE + 1] = 0
    offset = backend._weapon_offset(0, 1)
    raw[offset:offset + backend.WEAPON_STRIDE] = bytes(backend.WEAPON_STRIDE)
    raw[offset:offset + 2] = (3).to_bytes(2, 'little')
    return codec.encode(raw)


class OriginalPCEquipmentTests(unittest.TestCase):
    def test_selector_changes_only_byte_and_native_checksum(self):
        document = backend.decode(equipped_raw())
        key = 'officer_0_equipped_weapon'
        self.assertEqual(dict(backend.field_options(document, key)), {1: 'Weapon slot 1 (ID 2)', 2: 'Weapon slot 2 (ID 3)'})
        pending = backend.stage(document, {}, key, 2)
        expected = bytearray(document.raw)
        expected[backend.OFFICER_BASE + 1] = 1
        expected = codec.encode(expected)
        self.assertEqual(backend.serialize(document, pending), expected)
        self.assertEqual(backend.stage(document, pending, key, 1), {})
        self.assertFalse(backend.field_map(document)[key].maxable)
        self.assertEqual(backend.maximums(document, {}, 'Equipment'), {})
        for value in (True, 0, 3, 8, 9):
            with self.assertRaises(SaveError):
                backend.stage(document, {}, key, value)
        with self.assertRaises(SaveError):
            backend.serialize(document, {key: 8})

    def test_unknown_original_and_cross_family_targets_stay_read_only(self):
        raw = bytearray(equipped_raw())
        for value in (2, 255):
            raw[backend.OFFICER_BASE + 1] = value
            document = backend.decode(codec.encode(raw))
            self.assertNotIn('officer_0_equipped_weapon', backend.field_map(document))
        raw = bytearray(equipped_raw())
        offset = backend._weapon_offset(0, 1)
        raw[offset:offset + 2] = (4).to_bytes(2, 'little')
        document = backend.decode(codec.encode(raw))
        self.assertNotIn('officer_0_equipped_weapon', backend.field_map(document))

    @unittest.skipUnless(os.environ.get('WO1_NATIVE_SAVES'), 'Private original PC copies unavailable')
    def test_genuine_selectors_are_surgical_on_qualified_existing_pools(self):
        count = 0
        for source in Path(os.environ['WO1_NATIVE_SAVES']).glob('*.dat'):
            document = backend.read_save(source)
            self.assertEqual(backend.serialize(document, {}), document.raw)
            for field in backend.fields_for(document):
                if field.group != 'Equipment':
                    continue
                count += 1
                value = next(value for value, _ in backend.field_options(document, field.id)
                             if value != field.value(document.payload))
                expected = bytearray(document.raw)
                expected[field.offset] = value - 1
                self.assertEqual(backend.serialize(document, backend.stage(document, {}, field.id, value)),
                                 codec.encode(expected))
            self.assertEqual(source.read_bytes(), document.raw)
        self.assertGreater(count, 0)

    @unittest.skipUnless(os.environ.get('WO1_NATIVE_SAVES'), 'Private original PC copies unavailable')
    def test_genuine_selector_gui_review_undo_backup_save_restore(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        original = next(path for path in Path(os.environ['WO1_NATIVE_SAVES']).glob('*.dat')
                        if any(field.group == 'Equipment'
                               for field in backend.fields_for(backend.read_save(path))))
        raw = original.read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'copy.dat'
            source.write_bytes(raw)
            editor = Editor(root)
            with patch('koei_editor.shared.verified_gui.messagebox.showerror') as errors:
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename',
                           return_value=str(source)):
                    editor.open()
                field = next(field for field in backend.fields_for(editor.document)
                             if field.group == 'Equipment')
                value, label = next((value, label) for value, label in
                                    backend.field_options(editor.document, field.id)
                                    if value != field.value(raw))
                editor.group.set('Equipment')
                editor.search.set(field.id)
                editor.refresh()
                self.assertIn('Equipment', editor.group_selector['values'])
                editor.fields.selection_set(field.id)
                editor.selected()
                editor.choice_value.set(f'{value} · {label}')
                editor.selected_choice()
                editor.apply_selected()
                self.assertEqual(editor.changes, {field.id: value})
                editor.max_visible()
                self.assertEqual(editor.changes, {field.id: value})
                editor.review()
                editor.undo()
                self.assertEqual(editor.changes, {})
                editor.fields.selection_set(field.id)
                editor.selected()
                editor.choice_value.set(f'{value} · {label}')
                editor.selected_choice()
                editor.apply_selected()
                destination = Path(folder) / 'edited.dat'
                with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename',
                           return_value=str(destination)):
                    editor.save_as()
                self.assertEqual(errors.call_count, 0)
                expected = bytearray(raw)
                expected[field.offset] = value - 1
                self.assertEqual(destination.read_bytes(), codec.encode(expected))
                self.assertEqual(editor.backup.read_bytes(), raw)
                restored = backend.restore(editor.backup, Path(folder) / 'restored.dat')
                self.assertEqual(restored.read_bytes(), raw)
            self.assertEqual(source.read_bytes(), raw)
        self.assertEqual(original.read_bytes(), raw)
