"""Independent original Ryza 2 surgical/revision audit on generated buffers."""
from dataclasses import replace
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.ryza import codec, parser
from tests.test_ryza_format import procedural_payload, procedural_raw


class Ryza2IndependentAuditTests(unittest.TestCase):
    def test_inner_item_and_party_revisions_are_qualified(self):
        payload = procedural_payload()
        roots = {node.name: node for node in parser._nodes(payload, 32, len(payload))}
        for parent_name in (b'item', b'party'):
            parent = roots[parent_name]
            version_name = payload.find(b'version\0', parent.body, parent.end)
            self.assertGreaterEqual(version_name, parent.body)
            version_offset = version_name + len(b'version\0')
            mutated = bytearray(payload)
            mutated[version_offset:version_offset + 2] = b'\x7f\x7f'
            with self.subTest(parent=parent_name), self.assertRaises(SaveError):
                parser.decode(procedural_raw(bytes(mutated)), 'atelier_ryza2')

    def test_all_fields_preserve_neighbours_and_unknown_envelope_bytes(self):
        document = parser.decode(procedural_raw(), 'atelier_ryza2')
        fields = parser.fields_for(document)
        changes = {field.id: field.minimum for field in fields}
        encoded = parser.serialize(document, changes)
        reopened = parser.decode(encoded, 'atelier_ryza2')
        allowed = {field.offset + byte for field in fields for byte in range(field.size)}
        self.assertEqual(reopened.payload, parser.changed_payload(document, changes))
        self.assertTrue(all(a == b or offset in allowed
                            for offset, (a, b) in enumerate(zip(document.payload, reopened.payload))))
        self.assertEqual((reopened.header, reopened.seed, reopened.footer, reopened.trailer),
                         (document.header, document.seed, document.footer, document.trailer))
        self.assertEqual(parser.maximums(document, changes), changes)
        self.assertTrue(all(not field.maxable for field in fields))

    def test_malformed_pending_maps_rejected_before_stage_or_max(self):
        document = parser.decode(procedural_raw(), 'atelier_ryza2')
        key = parser.fields_for(document)[0].id
        for changes in ({'unmapped': 1}, {key: True}, {key: 101}, None, []):
            for operation in (lambda: parser.stage(document, changes, key, 7),
                              lambda: parser.maximums(document, changes),
                              lambda: parser.limit_values(document, changes, (key,))):
                with self.subTest(changes=changes), self.assertRaises(SaveError):
                    operation()

    def test_mutable_and_boolean_seed_metadata_never_enter_writers(self):
        header = bytearray(256)
        header[:48] = b'\1' + bytes(39) + struct.pack('<II', 1, 1)
        raw = codec.encode_file(bytes(header), procedural_payload(), 0)
        document = parser.decode(raw, 'atelier_ryza2')
        variants = [replace(document, seed=False), replace(document, seed=0.0)]
        variants.extend(replace(document, **{name: bytearray(getattr(document, name))})
                        for name in ('raw', 'payload', 'header', 'footer', 'trailer'))
        variants.append(replace(document, format=replace(document.format, id='atelier_ryza')))
        for forged in variants:
            for operation in (lambda: parser.fields_for(forged),
                              lambda: parser.serialize(forged, {})):
                with self.assertRaises(SaveError):
                    operation()

    def test_no_quality_and_important_records_never_become_new_items(self):
        document = parser.decode(procedural_raw(), 'atelier_ryza2')
        field = parser.fields_for(document)[0]
        for quality in (0, 0xffff):
            payload = bytearray(document.payload)
            struct.pack_into('<H', payload, field.offset, quality)
            opened = parser.decode(procedural_raw(bytes(payload)), 'atelier_ryza2')
            self.assertNotIn(field.id, parser.field_map(opened))
            with self.assertRaises(SaveError):
                parser.stage(opened, {}, field.id, 1)
            self.assertEqual(parser.serialize(opened, {}), opened.raw)
        for key in ('important_0_quality', 'important_basket_0_quality', 'recipe', 'skill', 'cole'):
            with self.subTest(key=key), self.assertRaises(SaveError):
                parser.stage(document, {}, key, 1)


@unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'A graphical display is required')
class Ryza2IndependentGuiTests(unittest.TestCase):
    def test_open_undo_review_save_backup_restore(self):
        import tkinter as tk
        from koei_editor.games.ryza.editor import Ryza2Editor
        root = tk.Tk()
        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as folder:
                folder = Path(folder)
                source, target, restored = (folder / name for name in ('source.dat', 'edited.dat', 'restored.dat'))
                raw = procedural_raw()
                source.write_bytes(raw)
                editor = Ryza2Editor(root)
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)), \
                     patch('koei_editor.shared.verified_gui.messagebox.showerror') as errors:
                    editor.open()
                    errors.assert_not_called()
                field = parser.fields_for(editor.document)[0]
                editor.fields.selection_set(field.id)
                editor.value.set('7')
                editor.apply_selected()
                self.assertEqual(editor.changes, {field.id: 7})
                editor.undo()
                self.assertEqual(editor.changes, {})
                editor.value.set('7')
                editor.apply_selected()
                editor.review()
                next(widget for widget in root.winfo_children() if isinstance(widget, tk.Toplevel)).destroy()
                editor.apply_theme('Dark')
                with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename', return_value=str(target)), \
                     patch('koei_editor.shared.verified_gui.messagebox.showerror') as errors:
                    editor.save_as()
                    errors.assert_not_called()
                self.assertEqual(parser.field_map(parser.read_save(target, 'atelier_ryza2'))[field.id].value(editor.document.payload), 7)
                self.assertEqual(source.read_bytes(), raw)
                backups = list((folder / 'WarriorsEditorBackups').glob('*.dat'))
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
