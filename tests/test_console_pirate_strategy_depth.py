"""Equipment/appearance dependency checks; optional native copies remain private."""
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.gundam1_ps3 import parser as gundam
from koei_editor.games.dw8e_ps3 import parser as horses
from tests.test_gundam1_ps3 import fixture, metadata
from tests.test_dw8e_ps3_horses import procedural_raw, procedural_envelope


def equipped_fixture():
    data = bytearray(fixture())
    for _, _, offset in gundam.PILOTS:
        data[offset + 23:offset + 29] = bytes([14, 15, 16, 17, 8, 3])
        # Skill 35 is deliberately unlearned. Unknown high bits remain set.
        data[offset + 29:offset + 34] = bytes.fromhex('ffffffffa7')
    return gundam.seal(bytes(data))


class ConsoleDepthTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / 'copy.bin'
        self.source.write_bytes(equipped_fixture())
        (self.folder / 'PARAM.SFO').write_bytes(metadata())
        self.document = gundam.read_save(self.source)

    def assert_surgical(self, before, after, offsets, integrity=()):
        touched = {i for i, (a, b) in enumerate(zip(before, after)) if a != b}
        self.assertLessEqual(touched, set(offsets) | set(integrity))
        self.assertTrue(touched & set(offsets))

    def test_equipped_fields_options_and_each_independent_slot(self):
        doc = self.document
        fields = [field for field in gundam.fields_for(doc)
                  if isinstance(field, gundam.EquippedField)]
        self.assertEqual(len(fields), 24)
        integrity = {i for offset in gundam.CHECKSUM_OFFSETS for i in range(offset, offset + 4)}
        for field in fields:
            with self.subTest(field=field.id):
                options = dict(gundam.field_options(doc, field.id))
                self.assertIn(18, options)
                for invalid in (3, 8, 35):
                    self.assertNotIn(invalid, options)
                changes = gundam.stage(doc, {}, field.id, 18)
                output = gundam.serialize(doc, changes)
                self.assertEqual(field.value(gundam.decode(output).payload), 18)
                self.assert_surgical(doc.raw, output, [field.offset], integrity)
                self.assertEqual(gundam.stage(doc, changes, field.id, field.value(doc.payload)), {})
                self.assertEqual(gundam.maximums(doc, changes), changes)
        self.assertEqual(self.source.read_bytes(), doc.raw)

    def test_equipment_swaps_atomic_review_and_original_unstage(self):
        doc = self.document
        changes = gundam.stage(doc, {}, 'amuro_equipped_0', 15)
        self.assertEqual(changes, {'amuro_equipped_0': 15, 'amuro_equipped_1': 14})
        self.assertEqual(len(gundam.review(doc, changes)), 2)
        reopened = gundam.decode(gundam.serialize(doc, changes))
        offset = gundam.PILOTS[0][2]
        self.assertEqual(reopened.payload[offset + 23:offset + 29], bytes([15, 14, 16, 17, 8, 3]))
        self.assertEqual(gundam.stage(doc, changes, 'amuro_equipped_0', 14), {})
        # A replacement followed by an occupied-slot swap preserves all four
        # distinct choices and can return to the original equipment atomically.
        replaced = gundam.stage(doc, {}, 'amuro_equipped_0', 18)
        swapped = gundam.stage(doc, replaced, 'amuro_equipped_1', 18)
        self.assertEqual(swapped, {'amuro_equipped_0': 15, 'amuro_equipped_1': 18})
        self.assertEqual(gundam.stage(doc, swapped, 'amuro_equipped_1', 15), {'amuro_equipped_0': 18})

    def test_unlearned_inherent_duplicate_ambiguous_and_invalid_rejected(self):
        doc = self.document
        for value in (-1, 36, 35, 3, 8, True, 1.0, '18'):
            with self.subTest(value=value), self.assertRaises(SaveError):
                gundam.stage(doc, {}, 'amuro_equipped_0', value)
        for pending in (None, [], {'amuro_equipped_0': 15}, {'amuro_equipped_0': 35},
                        {'amuro_equipped_9': 18}):
            with self.subTest(pending=pending), self.assertRaises(SaveError):
                gundam.serialize(doc, pending)
        # A newly staged learning flag does not create an equipment option.
        learned = gundam.stage(doc, {}, 'amuro_skill_35', 1)
        with self.assertRaises(SaveError):
            gundam.stage(doc, learned, 'amuro_equipped_0', 35)
        for relative, value in ((23, 15), (24, 3), (27, 35), (16, 250)):
            raw = bytearray(doc.raw)
            raw[gundam.PILOTS[0][2] + relative] = value
            raw = gundam.seal(bytes(raw))
            ambiguous = gundam.decode(raw)
            self.assertNotIn('amuro_equipped_0', gundam.field_map(ambiguous))
            self.assertEqual(gundam.serialize(ambiguous, {}), raw)

    def test_equipment_backup_restore_and_source_protection(self):
        doc = self.document
        backup = gundam.backup(doc)
        result = gundam.save_as(doc, {'amuro_equipped_3': 18}, self.folder / 'edited.bin')
        self.assertEqual(gundam.field_map(result)['amuro_equipped_3'].value(result.payload), 18)
        restored = gundam.restore(backup, self.folder / 'restored.bin')
        self.assertEqual(restored.read_bytes(), doc.raw)
        self.assertEqual(self.source.read_bytes(), doc.raw)
        self.source.write_bytes(b'damaged')
        with self.assertRaises(SaveError):
            gundam.save_as(doc, {'amuro_equipped_3': 18}, self.folder / 'changed-source.bin')

    def test_all_seven_horse_sliders_and_individual_unknown_preservation(self):
        doc = horses.decode(procedural_raw())
        for relative in range(0x10, 0x17):
            raw = bytearray(doc.payload)
            raw[horses.HORSE_BASE + relative] = 250
            unusual = horses.decode(procedural_envelope(bytes(raw)))
            fields = horses.field_map(unusual)
            key = horses.SLIDERS[relative - 0x10][0]
            self.assertNotIn(f'horse_0_{key}', fields)
            self.assertEqual(sum(field.slot == 1 for field in fields.values()), 6)
            self.assertEqual(horses.serialize(unusual, {}), unusual.raw)
            other = next(field for field in fields.values() if field.slot == 1)
            value = next(value for value, _ in horses.field_options(unusual, other.id)
                         if value != other.value(raw))
            edited = horses.decode(horses.serialize(unusual, {other.id: value}))
            self.assertEqual(edited.payload[horses.HORSE_BASE + relative], 250)
            self.assert_surgical(unusual.payload, edited.payload, [other.offset])
        for field in horses.fields_for(doc):
            for value, _ in horses.field_options(doc, field.id):
                changes = horses.stage(doc, {}, field.id, value)
                reopened = horses.decode(horses.serialize(doc, changes))
                self.assertEqual(field.value(reopened.payload), value)
            if not field.id.endswith('_body'):
                unwitnessed = next(value for value in range(5)
                                   if value not in dict(horses.field_options(doc, field.id)))
                with self.assertRaises(SaveError):
                    horses.stage(doc, {}, field.id, unwitnessed)

    def test_actual_tk_equipment_selector_swap_review_undo_save_restore(self):
        from koei_editor.games.gundam1_ps3.editor import Editor
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        editor = Editor(root)
        errors = []
        with patch('koei_editor.shared.verified_gui.messagebox.showerror',
                   side_effect=lambda *args: errors.append(args)), \
             patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(self.source)):
            editor.open()
            editor.group.set('Equipped skills')
            editor.search.set('Amuro')
            editor.refresh()
            self.assertEqual(len(editor.fields.get_children()), 4)
            editor.fields.selection_set('amuro_equipped_0')
            editor.selected()
            self.assertTrue(editor._choice_values)
            choice = next(label for label, value in editor._choice_values.items() if value == 15)
            editor.choice_value.set(choice)
            editor.selected_choice()
            editor.apply_selected()
            self.assertEqual(editor.changes, {'amuro_equipped_0': 15, 'amuro_equipped_1': 14})
            editor.review()
            editor.fields.selection_set(('amuro_equipped_0', 'amuro_equipped_1'))
            editor.revert_selected()
            self.assertEqual(editor.changes, {})
            editor.undo()
            self.assertEqual(editor.changes, {'amuro_equipped_0': 15, 'amuro_equipped_1': 14})
            editor.undo()
            self.assertEqual(editor.changes, {})
            editor.max_visible()
            self.assertEqual(editor.changes, {})
            editor.stage_values({'amuro_equipped_0': 18})
            editor.save_to(self.folder / 'gui-edited.bin')
            self.assertEqual(errors, [])
            self.assertEqual(self.source.read_bytes(), self.document.raw)
            self.assertEqual(gundam.field_map(editor.document)['amuro_equipped_0'].value(editor.document.payload), 18)
            restored = gundam.restore(editor.backup, self.folder / 'gui-restored.bin')
            self.assertEqual(restored.read_bytes(), self.document.raw)

    @unittest.skipUnless(os.environ.get('GUNDAM1_PS3_COPIES'), 'Private native Gundam copies not supplied')
    def test_native_tk_equipment_choices_save_backup_restore(self):
        from koei_editor.games.gundam1_ps3.editor import Editor
        paths = sorted(Path(os.environ['GUNDAM1_PS3_COPIES']).glob('*/*/DATA.BIN.decrypted'))
        self.assertTrue(paths)
        private_source = paths[0]
        original = private_source.read_bytes()
        native = gundam.decode(original, source=private_source)
        self.source.write_bytes(original)
        (self.folder / 'PARAM.SFO').write_bytes(gundam.identity_metadata(native.native_directory))
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        editor = Editor(root)
        errors = []
        with patch('koei_editor.shared.verified_gui.messagebox.showerror',
                   side_effect=lambda *args: errors.append(args)), \
             patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(self.source)):
            editor.open()
            field = next(field for field in gundam.fields_for(editor.document)
                         if isinstance(field, gundam.EquippedField))
            offset = gundam.PILOTS[field.slot - 1][2]
            selected = native.payload[offset + 23:offset + 27]
            value = next(value for value, _ in gundam.field_options(native, field.id) if value not in selected)
            editor.group.set('Equipped skills')
            editor.refresh()
            editor.fields.selection_set(field.id)
            editor.selected()
            choice = next(label for label, number in editor._choice_values.items() if number == value)
            editor.choice_value.set(choice)
            editor.selected_choice()
            editor.apply_selected()
            editor.review()
            editor.undo()
            self.assertEqual(editor.changes, {})
            editor.stage_values({field.id: value})
            editor.save_to(self.folder / 'native-gui-edited.bin')
            self.assertEqual(errors, [])
            self.assertEqual(field.value(editor.document.payload), value)
            self.assertEqual(gundam.restore(editor.backup, self.folder / 'native-gui-restored.bin').read_bytes(), original)
            self.assertEqual(self.source.read_bytes(), original)
            self.assertEqual(private_source.read_bytes(), original)

    @unittest.skipUnless(os.environ.get('GUNDAM1_PS3_COPIES'), 'Private native Gundam copies not supplied')
    def test_native_every_equipment_slot_dependency_and_surgical_checksum(self):
        paths = sorted(Path(os.environ['GUNDAM1_PS3_COPIES']).glob('*/*/DATA.BIN.decrypted'))
        self.assertEqual(len(paths), 4)
        integrity = {i for offset in gundam.CHECKSUM_OFFSETS for i in range(offset, offset + 4)}
        count = 0
        for source in paths:
            raw = source.read_bytes()
            doc = gundam.decode(raw, source=source)
            self.assertEqual(gundam.serialize(doc, {}), raw)
            for field in gundam.fields_for(doc):
                if not isinstance(field, gundam.EquippedField):
                    continue
                offset = gundam.PILOTS[field.slot - 1][2]
                equipped = doc.payload[offset + 23:offset + 27]
                replacement = next((value for value, _ in gundam.field_options(doc, field.id)
                                    if value not in equipped), None)
                self.assertIsNotNone(replacement)
                changes = gundam.stage(doc, {}, field.id, replacement)
                output = gundam.serialize(doc, changes)
                reopened = gundam.decode(output, source=source)
                self.assertEqual(field.value(reopened.payload), replacement)
                self.assert_surgical(raw, output, [field.offset], integrity)
                self.assertEqual(reopened.payload[offset + 27:offset + 36], doc.payload[offset + 27:offset + 36])
                count += 1
            self.assertEqual(source.read_bytes(), raw)
        self.assertEqual(count, 80)


if __name__ == '__main__':
    unittest.main()
