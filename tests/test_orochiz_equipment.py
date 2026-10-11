"""Qualified own-pool references, including optional privately supplied native saves."""
import os
from pathlib import Path
import struct
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.orochiz import orochiz_codec as codec
from koei_editor.games.orochiz import orochiz_parser as parser
from tests.test_orochiz_format import procedural_raw


def equipment_raw():
    raw = bytearray(procedural_raw())
    raw[parser.OFFICER_BASE + 1] = 0
    second = parser._weapon_offset(0, 2)
    struct.pack_into('<HHHBB', raw, second, 35, 0, 0, 0, 12)
    return codec.encode(raw)


class EquippedWeaponTests(unittest.TestCase):
    def test_choices_only_include_existing_qualified_same_officer_weapons(self):
        document = parser.decode(equipment_raw())
        key = 'officer_0_equipped_weapon'
        field = parser.field_map(document)[key]
        self.assertEqual(field.value(document.payload), 1)
        self.assertFalse(field.maxable)
        self.assertEqual(parser.field_options(document, key),
                         ((1, 'Weapon slot 1 (ID 2)'), (3, 'Weapon slot 3 (ID 35)')))
        changed = parser.stage(document, {}, key, 3)
        output = parser.serialize(document, changed)
        expected = bytearray(document.raw)
        expected[parser.OFFICER_BASE + 1] = 2
        self.assertEqual(output, codec.encode(expected))
        self.assertEqual(parser.stage(document, changed, key, 1), {})
        self.assertEqual([(field.id, before, after) for field, before, after
                          in parser.review(document, changed)], [(key, 1, 3)])
        self.assertEqual(parser.maximums(document, {}, 'Equipment'), {})

    def test_empty_unknown_and_cross_officer_choices_rejected_in_every_path(self):
        document = parser.decode(equipment_raw())
        key = 'officer_0_equipped_weapon'
        for value in (0, 2, 8, 9, True, 3.0, '3'):
            for operation in (lambda: parser.stage(document, {}, key, value),
                              lambda: parser.serialize(document, {key: value}),
                              lambda: parser.review(document, {key: value}),
                              lambda: parser.maximums(document, {key: value})):
                with self.subTest(value=value), self.assertRaises(SaveError):
                    operation()
        # Officer 96's occupied slot 8 is not a valid officer 1 reference.
        self.assertEqual(parser.weapons(document)[-1]['id'], 380)

    def test_unusual_equipped_or_weapon_layouts_stay_read_only(self):
        for pointer, identity, mask, capacity in ((255, 35, 0, 0), (1, 35, 0, 0),
                                                 (0, 414, 0, 0), (0, 415, 0, 0),
                                                 (0, 35, 0x8000, 8), (0, 35, 3, 1),
                                                 (0, 35, 0, 9)):
            raw = bytearray(equipment_raw())
            raw[parser.OFFICER_BASE + 1] = pointer
            second = parser._weapon_offset(0, 2)
            struct.pack_into('<HH', raw, second, identity, mask)
            raw[second + 6] = capacity
            document = parser.decode(codec.encode(raw))
            with self.subTest(pointer=pointer, identity=identity, mask=mask, capacity=capacity):
                self.assertNotIn('officer_0_equipped_weapon', parser.field_map(document))
                self.assertEqual(parser.serialize(document, {}), document.raw)

    def test_reference_change_preserves_progression_base_stats_and_entire_inventory(self):
        document = parser.decode(equipment_raw())
        updated = parser.decode(parser.serialize(document, {'officer_0_equipped_weapon': 3}))
        self.assertEqual(parser.weapons(updated), parser.weapons(document))
        for before, after in zip(parser.officers(document), parser.officers(updated)):
            expected = dict(before)
            if before['id'] == 0:
                expected['equipped_slot'] = 2
            self.assertEqual(after, expected)


@unittest.skipUnless(os.environ.get('OROCHIZ_NATIVE_SAVE'), 'Private native Orochi Z copy unavailable')
class NativeEquippedTests(unittest.TestCase):
    def test_all_native_pool_choices_change_only_reference_and_integrity(self):
        path = Path(os.environ['OROCHIZ_NATIVE_SAVE'])
        raw = path.read_bytes()
        document = parser.decode(raw)
        count = 0
        for field in parser.fields_for(document):
            if not field.id.endswith('_equipped_weapon'):
                continue
            for value, _label in parser.field_options(document, field.id):
                output = parser.serialize(document, parser.stage(document, {}, field.id, value))
                expected = bytearray(raw)
                expected[field.offset] = value - 1
                self.assertEqual(output, codec.encode(expected))
                self.assertEqual(parser.weapons(parser.decode(output)), parser.weapons(document))
                count += 1
        self.assertGreater(count, 0)
        self.assertEqual(path.read_bytes(), raw)

    def test_native_tk_choice_apply_review_undo_and_saved_copy(self):
        from koei_editor.games.orochiz.orochiz_editor import Editor
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        raw = Path(os.environ['OROCHIZ_NATIVE_SAVE']).read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'save.dat'
            source.write_bytes(raw)
            editor = Editor(root)
            errors = []
            with patch('koei_editor.shared.verified_gui.messagebox.showerror',
                       side_effect=lambda *args: errors.append(args)):
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                    editor.open()
                field = next(field for field in parser.fields_for(editor.document)
                             if field.id.endswith('_equipped_weapon'))
                value = next(value for value, _label in parser.field_options(editor.document, field.id)
                             if value != field.value(raw))
                editor.group.set('Equipment')
                editor.search.set(field.id)
                editor.refresh()
                editor.fields.selection_set(field.id)
                editor.selected()
                self.assertTrue(editor._choice_values)
                label = next(label for label, number in editor._choice_values.items() if number == value)
                editor.choice_value.set(label)
                editor.selected_choice()
                editor.apply_selected()
                self.assertEqual(editor.changes, {field.id: value})
                editor.review()
                editor.undo()
                self.assertEqual(editor.changes, {})
                editor.stage_values({field.id: value})
                expected = parser.serialize(editor.document, editor.changes)
                destination = Path(folder) / 'equipped.dat'
                editor.save_to(destination)
                self.assertEqual(parser.read_save(destination).raw, expected)
                self.assertEqual(source.read_bytes(), raw)
                self.assertEqual(editor.backup.read_bytes(), raw)
            self.assertEqual(errors, [])
