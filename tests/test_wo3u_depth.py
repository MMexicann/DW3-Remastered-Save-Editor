"""WO3 native item ownership/equipment and separate upgrade balance regressions."""
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.wo3u import wo3u_equipment as eq
from koei_editor.games.wo3u import wo3u_parser as backend
from koei_editor.games.wo3u.wo3u_editor import Editor
from tests.test_wo3u_format import procedural_raw


def depth_raw():
    raw = bytearray(procedural_raw())
    base = backend.OFFICER_BASE
    raw[base + 38:base + 44] = bytes((0, 1, 255, 255, 255, 255))
    raw[base + 44] = 2
    raw[base + 52:base + 54] = (50).to_bytes(2, 'little')
    raw[base + 62] = 1
    raw[eq.ITEM_OWNERSHIP_OFFSET:eq.ITEM_OWNERSHIP_OFFSET + 8] = ((1 << 0) | (1 << 1) | (1 << 2) | (1 << 28)).to_bytes(8, 'little')
    raw[eq.ITEM_RANK_OFFSET:eq.ITEM_RANK_OFFSET + 128] = bytes(128)
    for identity in (0, 1, 2, 3, 28):
        raw[eq.ITEM_RANK_OFFSET + 2 * identity:eq.ITEM_RANK_OFFSET + 2 * identity + 2] = (1).to_bytes(2, 'little')
    return bytes(raw)


class WO3DepthTests(unittest.TestCase):
    def test_equipment_choice_is_surgical_and_preserves_acquisition(self):
        document = backend.decode(depth_raw())
        key = 'officer_0_equipped_item_0'
        options = dict(backend.field_options(document, key))
        self.assertEqual(set(options), {0, 1, 2, 255})
        for value in (2, 255):
            pending = backend.stage(document, {}, key, value)
            expected = bytearray(document.raw)
            expected[backend.OFFICER_BASE + 38] = value
            self.assertEqual(backend.serialize(document, pending), expected)
            self.assertEqual(backend.stage(document, pending, key, 0), {})
            self.assertEqual(len(backend.review(document, pending)), 1)
        for value in (True, -1, 3, 28, 64, 256):
            with self.subTest(value=value), self.assertRaises(SaveError):
                backend.stage(document, {}, key, value)
        self.assertEqual(backend.maximums(document, {}, 'Equipment'), {})
        self.assertEqual(backend.limit_values(document, {}, [key]), {})

    def test_duplicate_guard_checks_complete_staged_equipment(self):
        document = backend.decode(depth_raw())
        first, second = 'officer_0_equipped_item_0', 'officer_0_equipped_item_1'
        with self.assertRaises(SaveError):
            backend.stage(document, {}, first, 1)
        cleared = backend.stage(document, {}, second, 255)
        pending = backend.stage(document, cleared, first, 1)
        expected = bytearray(document.raw)
        expected[backend.OFFICER_BASE + 38:backend.OFFICER_BASE + 40] = bytes((1, 255))
        self.assertEqual(backend.serialize(document, pending), expected)
        # Direct batches cannot bypass the staged dependency guard.
        with self.assertRaises(SaveError):
            backend.serialize(document, {first: 2, second: 2})
        # Unstaging a clear must not make the remaining edit incoherent.
        with self.assertRaises(SaveError):
            backend.stage(document, pending, second, 1)
        invalid = {first: 1}
        for operation in (
                lambda: backend.stage(document, invalid, first, 0),
                lambda: backend.limit_values(document, invalid, [first]),
                lambda: backend.maximums(document, invalid, 'Equipment')):
            with self.assertRaises(SaveError):
                operation()

    def test_unknown_dormant_unowned_and_duplicate_layouts_preserve_equipment(self):
        for relative, value in ((38, 64), (38, 3), (39, 0), (40, 2), (44, 7), (44, 1)):
            raw = bytearray(depth_raw())
            raw[backend.OFFICER_BASE + relative] = value
            document = backend.decode(raw)
            self.assertNotIn('officer_0_equipped_item_0', backend.field_map(document))
            changed = backend.serialize(document, backend.maximums(document, {}))
            self.assertEqual(changed[backend.OFFICER_BASE + 38:backend.OFFICER_BASE + 45],
                             raw[backend.OFFICER_BASE + 38:backend.OFFICER_BASE + 45])

    def test_upgrade_balance_is_separate_from_promotion_and_allocations(self):
        document = backend.decode(depth_raw())
        key = 'officer_0_upgrade_stones'
        for value in (0, 891):
            pending = backend.stage(document, {}, key, value)
            expected = bytearray(document.raw)
            expected[backend.OFFICER_BASE + 52:backend.OFFICER_BASE + 54] = value.to_bytes(2, 'little')
            self.assertEqual(backend.serialize(document, pending), expected)
            self.assertEqual(backend.stage(document, pending, key, 50), {})
        for value in (True, -1, 892):
            with self.assertRaises(SaveError):
                backend.stage(document, {}, key, value)
        self.assertEqual(backend.maximums(document, {}, 'Upgrade stones'), {})
        for promotion, balance in ((0, 50), (10, 50), (1, 892), (9, 65535)):
            raw = bytearray(depth_raw())
            raw[backend.OFFICER_BASE + 62] = promotion
            raw[backend.OFFICER_BASE + 52:backend.OFFICER_BASE + 54] = balance.to_bytes(2, 'little')
            document = backend.decode(raw)
            self.assertNotIn(key, backend.field_map(document))
            self.assertEqual(backend.serialize(document, {}), raw)
        self.assertNotIn('officer_145_upgrade_stones', backend.field_map(backend.decode(depth_raw())))


@unittest.skipUnless(os.environ.get('WO3U_SAVE_COPY'), 'Private native WO3 copy unavailable')
class NativeWO3DepthTests(unittest.TestCase):
    def test_native_new_systems_surgical_and_original_immutable(self):
        document = backend.read_save(os.environ['WO3U_SAVE_COPY'])
        fields = [field for field in backend.fields_for(document)
                  if field.group in ('Equipment', 'Upgrade stones')]
        self.assertTrue(any(field.group == 'Equipment' for field in fields))
        self.assertTrue(any(field.group == 'Upgrade stones' for field in fields))
        pending = {}
        expected = bytearray(document.raw)
        for field in fields:
            value = 255 if field.group == 'Equipment' else max(0, field.value(document.payload) - 1)
            pending = backend.stage(document, pending, field.id, value)
            expected[field.offset:field.offset + field.size] = field.encoded(value)
        self.assertEqual(backend.serialize(document, pending), expected)
        self.assertEqual(Path(document.source).read_bytes(), document.raw)
        self.assertEqual(document.raw, document.payload)

    def test_native_gui_choices_review_undo_backup_save_and_restore(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        original = Path(os.environ['WO3U_SAVE_COPY'])
        raw = original.read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'copy.bin'
            source.write_bytes(raw)
            editor = Editor(root)
            with patch('koei_editor.shared.verified_gui.messagebox.showerror') as errors:
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                    editor.open()
                field = next(field for field in backend.fields_for(editor.document) if field.group == 'Equipment')
                editor.group.set('Equipment')
                editor.search.set(field.id)
                editor.refresh()
                editor.fields.selection_set(field.id)
                editor.selected()
                self.assertTrue(editor._choice_values)
                editor.choice_value.set('255 · Unequipped')
                editor.selected_choice()
                editor.apply_selected()
                self.assertEqual(editor.changes, {field.id: 255})
                editor.max_visible()
                self.assertEqual(editor.changes, {field.id: 255})
                editor.review()
                editor.undo()
                self.assertEqual(editor.changes, {})
                stone = next(field for field in backend.fields_for(editor.document) if field.group == 'Upgrade stones')
                editor.stage_values({field.id: 255, stone.id: max(0, stone.value(raw) - 1)})
                expected = backend.serialize(editor.document, editor.changes)
                destination = Path(folder) / 'edited.bin'
                editor.save_to(destination)
                self.assertEqual(destination.read_bytes(), expected)
                self.assertEqual(editor.backup.read_bytes(), raw)
                restored = Path(folder) / 'restored.bin'
                backend.restore(editor.backup, restored)
                self.assertEqual(restored.read_bytes(), raw)
                self.assertEqual(source.read_bytes(), raw)
                errors.assert_not_called()
        self.assertEqual(original.read_bytes(), raw)
