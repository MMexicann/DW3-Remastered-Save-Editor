"""Independent lexical and dependency audit; generated files are not player saves."""
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.fatal_frame2_remake import parser
from tests.test_fatal_frame2_remake import make_raw, procedural_raw, system_json


class FatalFrame2IndependentAuditTests(unittest.TestCase):
    def test_escaped_path_and_opaque_tokens_survive_resource_reduction(self):
        encoded = json.dumps(system_json(), separators=(',', ':')).encode()
        encoded = encoded.replace(b'"SystemPlayerRecordData"', b'"SystemPlayerRecordD\\u0061ta"')
        encoded = encoded.replace(b'"shop_point_":123456', b'"shop_po\\u0069nt_" : 123456', 1)
        encoded = encoded[:-1] + (b', "Unmapped" : {"shop_point_":777, "negative_zero":-0, '
                                  b'"scientific":1.2300e+03,"quoted":"shop_point_ 123456",'
                                  b'"escaped":"\\u002f"}}')
        document = parser.decode(make_raw(system_json(), json_bytes=encoded))
        field, = parser.fields_for(document)
        output = parser.changed_payload(document, {'photo_points': 7})
        self.assertEqual(output, document.payload[:field.offset] + b'     7' +
                         document.payload[field.offset + field.size:])
        for literal in (b'"shop_point_":777', b'"negative_zero":-0', b'1.2300e+03', b'"\\u002f"'):
            self.assertIn(literal, output)
        reopened = parser.decode(parser.serialize(document, {'photo_points': 7}))
        self.assertEqual(reopened.payload, output)
        # Reopening a shorter, whitespace-padded number discovers its real span.
        second = parser.changed_payload(reopened, {'photo_points': 1})
        self.assertEqual(len(second), len(output))
        self.assertEqual(second[-9:], output[-9:])

    def test_alias_duplicates_and_non_integer_spellings_are_rejected(self):
        encoded = json.dumps(system_json(), separators=(',', ':')).encode()
        for replacement in (b'"shop_point_":true', b'"shop_point_":123456.0',
                            b'"shop_point_":1.23456e5',
                            b'"shop_point_":123456,"shop_po\\u0069nt_":7'):
            raw = make_raw(system_json(), json_bytes=encoded.replace(b'"shop_point_":123456', replacement, 1))
            with self.subTest(replacement=replacement), self.assertRaises(SaveError):
                document = parser.decode(raw)
                parser.fields_for(document)

    def test_malformed_pending_maps_and_equal_mutable_snapshots_cannot_stage(self):
        document = parser.decode(procedural_raw())
        for changes in ({'unknown': 1}, {'photo_points': True}, {'photo_points': 123457}, [], None):
            for operation in (lambda: parser.stage(document, changes, 'photo_points', 7),
                              lambda: parser.limit_values(document, changes, ('photo_points',)),
                              lambda: parser.maximums(document, changes)):
                with self.subTest(changes=changes), self.assertRaises(SaveError):
                    operation()
        for name in ('raw', 'payload', 'header'):
            forged = replace(document, **{name: bytearray(getattr(document, name))})
            for operation in (lambda: parser.fields_for(forged),
                              lambda: parser.maximums(forged, {}),
                              lambda: parser.serialize(forged, {})):
                with self.subTest(name=name), self.assertRaises(SaveError):
                    operation()

    def test_unlocks_gameplay_and_foreign_currency_paths_do_not_grant_ownership(self):
        document = parser.decode(procedural_raw())
        self.assertEqual(tuple(parser.field_map(document)), ('photo_points',))
        self.assertFalse(parser.field_map(document)['photo_points'].maxable)
        self.assertEqual(parser.limit_values(document, {}, ('photo_points',)), {})
        for key in ('sen', 'senki', 'shop_point_', 'ghost_list_unlock_data_', 'costume_mio'):
            with self.subTest(key=key), self.assertRaises(SaveError):
                parser.stage(document, {}, key, 1)
        self.assertEqual(parser.serialize(document, {'photo_points': 123456}), document.raw)


@unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'A graphical display is required')
class FatalFrame2IndependentGuiTests(unittest.TestCase):
    def test_system_resource_open_undo_review_save_backup_restore(self):
        import tkinter as tk
        from koei_editor.games.fatal_frame2_remake.editor import Editor
        root = tk.Tk()
        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as folder:
                folder = Path(folder)
                source, target, restored = (folder / name for name in ('source.bin', 'edited.bin', 'restored.bin'))
                raw = procedural_raw()
                source.write_bytes(raw)
                editor = Editor(root)
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)), \
                     patch('koei_editor.shared.verified_gui.messagebox.showerror') as errors:
                    editor.open()
                    errors.assert_not_called()
                field, = parser.fields_for(editor.document)
                editor.fields.selection_set(field.id)
                editor.value.set('0')
                editor.apply_selected()
                self.assertEqual(editor.changes, {'photo_points': 0})
                editor.undo()
                self.assertEqual(editor.changes, {})
                editor.value.set('0')
                editor.apply_selected()
                editor.review()
                next(widget for widget in root.winfo_children() if isinstance(widget, tk.Toplevel)).destroy()
                editor.apply_theme('Dark')
                with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename', return_value=str(target)), \
                     patch('koei_editor.shared.verified_gui.messagebox.showerror') as errors:
                    editor.save_as()
                    errors.assert_not_called()
                self.assertEqual(parser.fields_for(parser.read_save(target))[0].value(editor.document.payload), 0)
                self.assertEqual(source.read_bytes(), raw)
                backups = list((folder / 'UniversalEditorBackups').glob('*.bin'))
                self.assertTrue(backups)
                self.assertEqual(backups[0].read_bytes(), raw)
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(backups[0])), \
                     patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename', return_value=str(restored)), \
                     patch('koei_editor.shared.verified_gui.messagebox.showerror') as errors:
                    editor.restore()
                    errors.assert_not_called()
                self.assertEqual(restored.read_bytes(), raw)
                self.assertEqual(editor.changes, {})
        finally:
            root.destroy()


if __name__ == '__main__':
    unittest.main()
