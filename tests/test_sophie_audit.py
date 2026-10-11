"""Independent original-PC record/preservation audit using procedural bytes."""
from dataclasses import replace
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.sophie import parser
from tests.test_sophie_format import fixture


class SophieIndependentAuditTests(unittest.TestCase):
    def test_all_fields_preserve_opaque_bytes_and_float_neighbours(self):
        document = parser.decode(fixture())
        fields = parser.fields_for(document)
        changes = {field.id: field.minimum for field in fields}
        output = parser.serialize(document, changes)
        allowed = {field.offset + byte for field in fields for byte in range(field.size)}
        self.assertEqual(len(output), len(document.raw))
        self.assertTrue(all(a == b or offset in allowed
                            for offset, (a, b) in enumerate(zip(document.raw, output))))
        for field in fields:
            self.assertEqual(field.value(output), changes[field.id])
        self.assertEqual(parser.maximums(document, changes), changes)
        for field in fields:
            self.assertFalse(field.maxable)

    def test_nonfinite_fractional_empty_and_working_records_are_inspection_only(self):
        original = parser.decode(fixture())
        pools, *_ = parser._structure(original.payload)
        for key, _label, base, _count, editable in pools:
            payload = bytearray(original.payload)
            for index, quality in enumerate((float('nan'), float('inf'), -1.0, 12.25, 2**24)):
                offset = base + index * parser.RECORD_SIZE
                struct.pack_into('>HHf', payload, offset, 900 + index, 500 + index, quality)
            document = parser.decode(bytes(payload))
            mapping = parser.field_map(document)
            for index in range(5):
                self.assertNotIn(f'{key}_{index + 1}_quality', mapping)
            self.assertEqual(parser.serialize(document, {}), bytes(payload))
            self.assertEqual(parser.maximums(document, {}), {})
            if not editable:
                self.assertFalse(any(field.group == _label for field in mapping.values()))

    def test_higher_originals_can_unstage_without_normalization(self):
        raw = bytearray(fixture())
        opened = parser.decode(bytes(raw))
        cole = parser.field_map(opened)['cole']
        raw[cole.offset:cole.offset + 4] = (0xffffffff).to_bytes(4, 'big')
        document = parser.decode(bytes(raw))
        for key, value in (('cole', 0xffffffff), ('basket_2_quality', 1200)):
            changes = parser.stage(document, {}, key, 7)
            self.assertEqual(parser.stage(document, changes, key, value), {})
            self.assertEqual(parser.serialize(document, {key: value}), document.raw)
        self.assertEqual(parser.maximums(document, {}), {})

    def test_mutable_frozen_and_foreign_documents_cannot_write(self):
        document = parser.decode(fixture())
        variants = [replace(document, **{name: bytearray(getattr(document, name))})
                    for name in ('raw', 'payload')]
        variants.append(replace(document, format=replace(document.format, id='atelier_sophie_dx')))
        for forged in variants:
            for operation in (lambda: parser.fields_for(forged),
                              lambda: parser.stage(forged, {}, 'cole', 7),
                              lambda: parser.serialize(forged, {})):
                with self.assertRaises(SaveError):
                    operation()


@unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'A graphical display is required')
class SophieIndependentGuiTests(unittest.TestCase):
    def test_extensionless_open_undo_review_theme_save_backup_and_restore(self):
        import tkinter as tk
        from tkinter import ttk
        from koei_editor.games.sophie.editor import Editor

        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)

        root = tk.Tk()
        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as folder:
                folder = Path(folder)
                source, destination, restored = (folder / name for name in ('GAMEDATA00', 'GAMEDATA01', 'GAMEDATA02'))
                source.write_bytes(fixture())
                editor = Editor(root)
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)), \
                     patch('koei_editor.shared.verified_gui.messagebox.showerror') as errors:
                    editor.open()
                    errors.assert_not_called()
                self.assertEqual(editor.save_extension, '')
                editor.search.set('Cole')
                self.assertEqual(editor.fields.get_children(), ('cole',))
                editor.fields.selection_set('cole')
                editor.value.set('7')
                editor.apply_selected()
                self.assertEqual(editor.changes, {'cole': 7})
                editor.undo()
                self.assertEqual(editor.changes, {})
                editor.value.set('7')
                editor.apply_selected()
                editor.apply_theme('Dark')
                editor.review()
                review = next(widget for widget in root.winfo_children() if isinstance(widget, tk.Toplevel))
                tree = next(widget for widget in descendants(review) if isinstance(widget, ttk.Treeview))
                self.assertEqual(len(tree.get_children()), 1)
                review.destroy()
                with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename', return_value=str(destination)), \
                     patch('koei_editor.shared.verified_gui.messagebox.showerror') as errors:
                    editor.save_as()
                    errors.assert_not_called()
                self.assertEqual(parser.field_map(parser.read_save(destination))['cole'].value(destination.read_bytes()), 7)
                self.assertEqual(source.read_bytes(), fixture())
                backups = [path for path in (folder / 'WarriorsEditorBackups').iterdir() if path.suffix != '.json']
                self.assertTrue(backups)
                self.assertEqual(backups[0].read_bytes(), fixture())
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(backups[0])), \
                     patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename', return_value=str(restored)), \
                     patch('koei_editor.shared.verified_gui.messagebox.showerror') as errors:
                    editor.restore()
                    errors.assert_not_called()
                self.assertEqual(restored.read_bytes(), fixture())
                self.assertEqual(editor.changes, {})
        finally:
            root.destroy()


if __name__ == '__main__':
    unittest.main()
