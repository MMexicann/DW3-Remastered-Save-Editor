"""PC horse positions are qualified independently from the console adapter."""
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.dw8e import dw8e_parser as backend
from koei_editor.games.dw8e import dw8e_codec as codec
from tests.test_dw8e_horses import procedural_raw, procedural_envelope


class PCHorseDepthTests(unittest.TestCase):
    def test_same_member_original_choices_unknown_rows_and_no_max(self):
        doc = backend.decode(procedural_raw())
        self.assertEqual(len(backend.fields_for(doc)), 14)
        self.assertEqual(set(dict(backend.field_options(doc, 'horse_0_head'))), {1, 3})
        for value in (0, 2, 4, 5, True, '3'):
            with self.subTest(value=value), self.assertRaises(SaveError):
                backend.stage(doc, {}, 'horse_0_head', value)
        changes = backend.stage(doc, {}, 'horse_0_head', 3)
        self.assertEqual(backend.stage(doc, changes, 'horse_0_head', 1), {})
        self.assertEqual(backend.maximums(doc, changes), changes)
        self.assertEqual(backend.limit_values(doc, changes, changes), {})
        for relative, value in ((0x11, 250), (0x0F, 19), (0x1E, 62)):
            payload = bytearray(doc.payload)
            payload[backend.HORSE_BASE + relative] = value
            unusual = backend.decode(procedural_envelope(bytes(payload)))
            self.assertNotIn('horse_0_head', backend.field_map(unusual))
            self.assertEqual(backend.serialize(unusual, {}), unusual.raw)
            result = backend.decode(backend.serialize(unusual, {'horse_149_body': 4}))
            self.assertEqual(result.payload[backend.HORSE_BASE + relative], value)

    @unittest.skipUnless(os.environ.get('DW8E_SYSTEM_COPY'), 'Private native PC SYSTEM not supplied')
    def test_native_pc_own_ordinals_positions_and_surgical_reconstruction(self):
        source = Path(os.environ['DW8E_SYSTEM_COPY'])
        raw = source.read_bytes()
        doc = backend.decode(raw)
        self.assertEqual(backend.serialize(doc, {}), raw)
        self.assertEqual(len(backend.horses(doc)), 150)
        self.assertEqual(len(backend.fields_for(doc)), 14)
        expected = {'head': {0, 4}, 'neck': {0, 4}, 'torso': {0},
                    'legs': {0}, 'tail': {0, 4}, 'muscle': {2}}
        edits = 0
        for field in backend.fields_for(doc):
            member = field.id.rsplit('_', 1)[-1]
            options = dict(backend.field_options(doc, field.id))
            if member != 'body':
                self.assertEqual(set(options), expected[member])
            for value in options:
                if value == field.value(doc.payload):
                    continue
                result = backend.decode(backend.serialize(doc, {field.id: value}))
                self.assertEqual(field.value(result.payload), value)
                self.assertEqual(result.payload[:field.offset], doc.payload[:field.offset])
                self.assertEqual(result.payload[field.offset + 1:], doc.payload[field.offset + 1:])
                self.assertEqual(result.seed, doc.seed)
                self.assertEqual(result.raw[:codec.CHECKSUM_OFFSET], raw[:codec.CHECKSUM_OFFSET])
                self.assertEqual(result.raw[codec.SEED_OFFSET:codec.BODY_OFFSET], raw[codec.SEED_OFFSET:codec.BODY_OFFSET])
                edits += 1
        self.assertEqual(edits, 14)  # Four body alternatives each; one for each head/neck/tail.
        self.assertEqual(source.read_bytes(), raw)

    @unittest.skipUnless(os.environ.get('DW8E_SYSTEM_COPY'), 'Private native PC SYSTEM not supplied')
    def test_actual_native_tk_head_choice_review_undo_backup_save_restore(self):
        from koei_editor.games.dw8e.dw8e_editor import Editor
        private_source = Path(os.environ['DW8E_SYSTEM_COPY'])
        raw = private_source.read_bytes()
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        source = Path(temporary.name) / 'native-copy.dat'
        source.write_bytes(raw)
        editor = Editor(root)
        errors = []
        with patch('koei_editor.shared.verified_gui.messagebox.showerror',
                   side_effect=lambda *args: errors.append(args)), \
             patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
            editor.open()
            editor.fields.selection_set('horse_0_head')
            editor.selected()
            self.assertEqual(set(editor._choice_values.values()), {0, 4})
            editor.choice_value.set(next(label for label, value in editor._choice_values.items() if value == 4))
            editor.selected_choice()
            editor.apply_selected()
            self.assertEqual(editor.changes, {'horse_0_head': 4})
            editor.review()
            editor.undo()
            self.assertEqual(editor.changes, {})
            editor.stage_values({'horse_0_head': 4})
            editor.save_to(source.with_name('edited.dat'))
            self.assertEqual(errors, [])
            self.assertEqual(backend.field_map(editor.document)['horse_0_head'].value(editor.document.payload), 4)
            self.assertEqual(backend.restore(editor.backup, source.with_name('restored.dat')).read_bytes(), raw)
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(private_source.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
