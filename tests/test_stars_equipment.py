"""Native own-pool Hero Card references; no game executable is run."""
import os
from pathlib import Path
import struct
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.stars import stars_parser as parser, stars_codec as codec
from tests.test_stars_format import procedural_raw


def equipment_raw(selected=21):
    raw = procedural_raw()
    payload = bytearray(codec.decode(raw)[0])
    slot = parser._slot_base(0)
    for hero in range(parser.HERO_COUNT):
        struct.pack_into('<i', payload, slot + parser.HERO_BASE + hero * parser.HERO_STRIDE
                         + parser.EQUIPPED_CARD_OFFSET, -1)
    for index in range(parser.CARD_COUNT):
        struct.pack_into('<h', payload, parser._card_offset(0, index), -1)
    for index, identity in ((21, 42), (24, 71), (41, 123), (2000, 999)):
        struct.pack_into('<h', payload, parser._card_offset(0, index), identity)
    struct.pack_into('<i', payload, slot + parser.HERO_BASE + parser.HERO_STRIDE
                     + parser.EQUIPPED_CARD_OFFSET, selected)
    return codec.encode(raw, bytes(payload))


class CardEquipmentTests(unittest.TestCase):
    def test_existing_own_pool_choices_change_only_four_reference_bytes(self):
        raw = equipment_raw()
        document = parser.decode(raw)
        key = 'slot_0_hero_1_equipped_card'
        field = parser.field_map(document)[key]
        self.assertEqual(parser.field_options(document, key),
                         ((21, 'Card record 22 (card ID 42)'), (24, 'Card record 25 (card ID 71)')))
        self.assertFalse(field.maxable)
        changes = parser.stage(document, {}, key, 24)
        output = parser.serialize(document, changes)
        expected = bytearray(document.payload)
        struct.pack_into('<I', expected, field.offset, 24)
        self.assertEqual(output, codec.encode(raw, bytes(expected)))
        self.assertEqual(parser.stage(document, changes, key, 21), {})
        self.assertEqual(parser.review(document, changes), [(field, 21, 24)])
        self.assertEqual(parser.maximums(document, {}, 'Hero cards'), {})
        self.assertEqual(parser.inspection_rows(document), parser.inspection_rows(parser.decode(output)))

    def test_cross_owner_empty_special_gift_unknown_and_typed_values_rejected(self):
        document = parser.decode(equipment_raw())
        key = 'slot_0_hero_1_equipped_card'
        for value in (-1, 20, 25, 41, 2000, 2200, True, 24.0, '24'):
            for action in (lambda: parser.stage(document, {}, key, value),
                           lambda: parser.serialize(document, {key: value}),
                           lambda: parser.review(document, {key: value}),
                           lambda: parser.maximums(document, {key: value})):
                with self.subTest(value=value), self.assertRaises(SaveError):
                    action()

    def test_unusual_original_references_and_single_or_invalid_pool_read_only(self):
        for selected in (-1, 20, 41, 2000, 2200):
            document = parser.decode(equipment_raw(selected))
            self.assertNotIn('slot_0_hero_1_equipped_card', parser.field_map(document))
            self.assertEqual(parser.serialize(document, {}), document.raw)
        for identity in (-1, 2000, 32767):
            raw = equipment_raw()
            payload = bytearray(codec.decode(raw)[0])
            struct.pack_into('<h', payload, parser._card_offset(0, 24), identity)
            document = parser.decode(codec.encode(raw, bytes(payload)))
            self.assertNotIn('slot_0_hero_1_equipped_card', parser.field_map(document))
        raw = equipment_raw()
        payload = bytearray(codec.decode(raw)[0])
        struct.pack_into('<h', payload, parser._slot_base(0) + parser.ACTIVE_HERO_OFFSET, -1)
        self.assertNotIn('slot_0_hero_1_equipped_card', parser.field_map(parser.decode(codec.encode(raw, bytes(payload)))))

    def test_inventory_inspector_retains_numeric_unknown_properties(self):
        document = parser.decode(equipment_raw())
        rows = [row for row in parser.inspection_rows(document) if row['group'] == 'Hero cards']
        first_slot = [row for row in rows if row['label'].startswith('Campaign slot 1 /')]
        self.assertEqual(len(first_slot), 4)
        self.assertTrue(any('Friendship-gift pool (read only)' in row['value'] for row in first_slot))
        self.assertTrue(any('card ID 71' in row['value'] for row in first_slot))


@unittest.skipUnless(os.environ.get('STARS_NATIVE_SAVE'), 'Private native All-Stars copy unavailable')
class NativeCardEquipmentTests(unittest.TestCase):
    def test_all_native_hero_selections_and_own_pool_choices_surgical(self):
        path = Path(os.environ['STARS_NATIVE_SAVE'])
        raw = path.read_bytes()
        document = parser.decode(raw)
        self.assertEqual(parser.serialize(document, {}), raw)
        count = 0
        for field in parser.fields_for(document):
            if field.group != 'Hero cards':
                continue
            slot, hero = divmod(field.slot - 1, parser.HERO_COUNT)
            for value, _label in parser.field_options(document, field.id):
                self.assertTrue(hero * 20 <= value < (hero + 1) * 20)
                output = parser.serialize(document, parser.stage(document, {}, field.id, value))
                expected = bytearray(document.payload)
                struct.pack_into('<I', expected, field.offset, value)
                self.assertEqual(codec.decode(output)[0], bytes(expected))
                # Encrypted block reconstruction must preserve all other campaigns,
                # global history, seeds and padding.
                self.assertEqual(output, codec.encode(raw, bytes(expected)))
                count += 1
        self.assertGreater(count, 0)
        self.assertEqual(path.read_bytes(), raw)

    def test_native_tk_dropdown_apply_undo_review_max_and_saved_copy(self):
        from koei_editor.games.stars.stars_editor import Editor
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        raw = Path(os.environ['STARS_NATIVE_SAVE']).read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            source, destination = Path(folder) / 'copy.bin', Path(folder) / 'edited.bin'
            source.write_bytes(raw)
            editor = Editor(root)
            errors = []
            with patch('koei_editor.shared.verified_gui.messagebox.showerror', side_effect=lambda *args: errors.append(args)), \
                 patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                editor.open()
                field = next(field for field in parser.fields_for(editor.document) if field.group == 'Hero cards')
                editor.group.set('Hero cards')
                editor.search.set(field.id)
                editor.refresh()
                editor.fields.selection_set(field.id)
                editor.selected()
                choices = parser.field_options(editor.document, field.id)
                value, label = next((value, label) for value, label in choices if value != field.value(editor.document.payload))
                editor.choice_value.set(next(text for text, number in editor._choice_values.items() if number == value))
                editor.selected_choice()
                editor.apply_selected()
                self.assertEqual(editor.changes, {field.id: value})
                editor.review()
                editor.undo()
                self.assertEqual(editor.changes, {})
                editor.max_visible()
                self.assertEqual(editor.changes, {})
                editor.choice_value.set(next(text for text, number in editor._choice_values.items() if number == value))
                editor.selected_choice()
                editor.apply_selected()
                editor.show_inspector()
                self.assertTrue(any(table.title == 'Hero cards' for table in editor.presentation.inspection_tables(editor.document)))
                with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename', return_value=str(destination)):
                    editor.save_as()
            self.assertEqual(errors, [])
            self.assertEqual(source.read_bytes(), raw)
            expected = bytearray(parser.decode(raw).payload)
            struct.pack_into('<I', expected, field.offset, value)
            self.assertEqual(parser.read_save(destination).payload, bytes(expected))
            self.assertTrue(list((source.parent / 'WarriorsEditorBackups').glob('*.bin')))
