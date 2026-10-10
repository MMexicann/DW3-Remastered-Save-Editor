"""EXP edits deliberately stay inside an already progressed native level."""
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


class GrowthBandTests(unittest.TestCase):
    def test_curve_and_every_progressed_level_band(self):
        thresholds = parser.LEVEL_EXP_THRESHOLDS
        self.assertEqual(len(thresholds), 99)
        self.assertEqual((thresholds[0], thresholds[1], thresholds[49], thresholds[98]),
                         (0, 800, 86240, 219520))
        self.assertEqual(tuple(thresholds[n + 1] - thresholds[n] for n in range(98)),
                         tuple(min(800 + 40 * n, 2720) for n in range(98)))
        for level in range(1, 98):
            raw = bytearray(procedural_raw())
            raw[parser.OFFICER_BASE] = level
            struct.pack_into('<I', raw, parser.OFFICER_BASE + 16, thresholds[level])
            document = parser.decode(codec.encode(raw))
            field = parser.field_map(document)['officer_0_exp_within_level']
            with self.subTest(level=level):
                self.assertEqual((field.minimum, field.maximum),
                                 (thresholds[level], thresholds[level + 1] - 1))
                self.assertFalse(field.maxable)
                output = parser.serialize(document, {field.id: field.maximum})
                expected = bytearray(document.raw)
                struct.pack_into('<I', expected, field.offset, field.maximum)
                self.assertEqual(output, codec.encode(expected))
                for value in (field.minimum - 1, field.maximum + 1, True, 1.5):
                    with self.assertRaises(SaveError):
                        parser.stage(document, {}, field.id, value)
                self.assertEqual(parser.maximums(document, {}, 'Officer growth'), {})

    def test_unprogressed_final_unknown_or_inconsistent_records_not_repaired(self):
        for level, experience in ((0, 0), (0, 799), (98, 219520), (98, 220000),
                                  (99, 220000), (255, 0), (1, 799), (1, 1640),
                                  (50, 0xFFFFFFFF)):
            raw = bytearray(procedural_raw())
            raw[parser.OFFICER_BASE] = level
            struct.pack_into('<I', raw, parser.OFFICER_BASE + 16, experience)
            document = parser.decode(codec.encode(raw))
            with self.subTest(level=level, experience=experience):
                self.assertNotIn('officer_0_exp_within_level', parser.field_map(document))
                output = parser.serialize(document, parser.maximums(document, {}))
                self.assertEqual(output[parser.OFFICER_BASE], level)
                self.assertEqual(int.from_bytes(output[parser.OFFICER_BASE + 16:parser.OFFICER_BASE + 20],
                                               'little'), experience)

    def test_review_unstage_and_other_progression_dependencies_preserved(self):
        raw = bytearray(procedural_raw())
        raw[parser.OFFICER_BASE] = 1
        struct.pack_into('<I', raw, parser.OFFICER_BASE + 16, 1000)
        document = parser.decode(codec.encode(raw))
        key = 'officer_0_exp_within_level'
        changes = parser.stage(document, {}, key, 1639)
        self.assertEqual(parser.stage(document, changes, key, 1000), {})
        self.assertEqual([(field.id, before, after) for field, before, after
                          in parser.review(document, changes)], [(key, 1000, 1639)])
        output = parser.decode(parser.serialize(document, changes))
        self.assertEqual(parser.weapons(output), parser.weapons(document))
        self.assertEqual(output.raw[parser.STOCK_EXP_OFFSET:parser.STOCK_EXP_OFFSET + 4],
                         document.raw[parser.STOCK_EXP_OFFSET:parser.STOCK_EXP_OFFSET + 4])
        before = dict(parser.officers(document)[0])
        before['exp'] = 1639
        self.assertEqual(parser.officers(output)[0], before)


@unittest.skipUnless(os.environ.get('OROCHIZ_GROWTH_SAVE'), 'Private progressed native Orochi Z copy unavailable')
class NativeGrowthTests(unittest.TestCase):
    def test_existing_progressed_officers_native_surgery_preserves_all_dependencies(self):
        path = Path(os.environ['OROCHIZ_GROWTH_SAVE'])
        raw = path.read_bytes()
        document = parser.decode(raw)
        fields = [field for field in parser.fields_for(document) if field.id.endswith('_exp_within_level')]
        self.assertTrue(fields)
        for field in fields:
            for value in (field.minimum, field.maximum):
                output = parser.serialize(document, parser.stage(document, {}, field.id, value))
                expected = bytearray(raw)
                expected[field.offset:field.offset + 4] = value.to_bytes(4, 'little')
                self.assertEqual(output, codec.encode(expected))
                self.assertEqual(parser.weapons(parser.decode(output)), parser.weapons(document))
                for before, after in zip(parser.officers(document), parser.officers(parser.decode(output))):
                    expected_officer = dict(before)
                    if before['id'] == field.slot - 1:
                        expected_officer['exp'] = value
                    self.assertEqual(after, expected_officer)
        self.assertEqual(path.read_bytes(), raw)

    def test_native_growth_gui_preserves_level_and_source_with_backup(self):
        from koei_editor.games.orochiz.orochiz_editor import Editor
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        raw = Path(os.environ['OROCHIZ_GROWTH_SAVE']).read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'growth-copy.dat'
            source.write_bytes(raw)
            editor = Editor(root)
            errors = []
            with patch('koei_editor.shared.verified_gui.messagebox.showerror',
                       side_effect=lambda *args: errors.append(args)):
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                    editor.open()
                field = next(field for field in parser.fields_for(editor.document)
                             if field.id.endswith('_exp_within_level'))
                editor.group.set('Officer growth')
                editor.search.set(field.id)
                editor.refresh()
                editor.fields.selection_set(field.id)
                editor.value.set(str(field.maximum))
                editor.apply_selected()
                self.assertEqual(editor.changes, {field.id: field.maximum})
                editor.max_visible()
                self.assertEqual(editor.changes, {field.id: field.maximum})
                editor.review()
                editor.undo()
                self.assertEqual(editor.changes, {})
                editor.stage_values({field.id: field.maximum})
                expected = parser.serialize(editor.document, editor.changes)
                destination = Path(folder) / 'growth.dat'
                editor.save_to(destination)
                self.assertEqual(parser.read_save(destination).raw, expected)
                self.assertEqual(source.read_bytes(), raw)
                self.assertEqual(editor.backup.read_bytes(), raw)
            self.assertEqual(errors, [])
