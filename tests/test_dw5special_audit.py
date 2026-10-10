"""Independent record-boundary and native-copy workflow checks.

Procedural inputs exercise invalid states; an optional premodified public native
file exercises the real Tk workflow. Neither establishes an edited game load.
"""
from dataclasses import replace
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.dw5special import dw5special_codec as codec
from koei_editor.games.dw5special import dw5special_parser as backend
from koei_editor.games.dw5special.dw5special_editor import Editor
from tests.test_dw5special_format import procedural_envelope, procedural_raw


class IndependentSpecialSafety(unittest.TestCase):
    def test_unoccupied_officers_cannot_edit_qualified_looking_weapons(self):
        for flag in (0, 2, 255):
            data = bytearray(procedural_raw())
            data[backend.OFFICER_BASE] = flag
            document = backend.decode(procedural_envelope(data))
            self.assertFalse(any(field.id.startswith('officer_0_')
                                 for field in backend.fields_for(document)))
            with self.assertRaises(SaveError):
                backend.stage(document, {}, 'officer_0_weapon_0_weight', 0)
            self.assertEqual(backend.serialize(document, backend.maximums(document, {})), document.raw)

    def test_unknown_attribute_states_preserved_during_neighbor_rank_edit(self):
        data = bytearray(procedural_raw())
        start = backend.OFFICER_BASE + backend.WEAPON_RELATIVE
        data[start + 6:start + 8] = bytes((255, 231))
        data[start + 10:start + 12] = bytes((39, 17))
        document = backend.decode(procedural_envelope(data))
        mapping = backend.field_map(document)
        self.assertIn('officer_0_weapon_0_attribute_0', mapping)
        self.assertNotIn('officer_0_weapon_0_attribute_1', mapping)
        self.assertNotIn('officer_0_weapon_0_attribute_3', mapping)
        expected = bytearray(document.raw)
        expected[start + 5] = 19
        actual = backend.serialize(document, {'officer_0_weapon_0_attribute_0': 19})
        self.assertEqual(actual, procedural_envelope(expected))
        self.assertEqual(actual[start + 6:start + 8], bytes((255, 231)))
        self.assertEqual(actual[start + 10:start + 12], bytes((39, 17)))

    def test_checksum_boundary_does_not_rewrite_opaque_trailer(self):
        data = bytearray(procedural_raw())
        tail = bytes(range(28))
        data[codec.CHECKSUM_OFFSET + 4:] = tail
        document = backend.decode(procedural_envelope(data))
        edited = backend.serialize(document, {'item_0_rank': 19})
        self.assertEqual(edited[codec.CHECKSUM_OFFSET + 4:], tail)
        self.assertEqual(int.from_bytes(edited[codec.CHECKSUM_OFFSET:codec.CHECKSUM_OFFSET + 4], 'little'),
                         sum(edited[:codec.CHECKSUM_OFFSET]))
        corrupted = bytearray(edited)
        corrupted[codec.CHECKSUM_OFFSET - 1] ^= 1
        with self.assertRaises(SaveError):
            backend.decode(corrupted)

    def test_custom_equality_cannot_spoof_immutable_profile(self):
        class PretendFormat:
            def __eq__(self, other):
                return True
        document = backend.decode(procedural_raw())
        forged = replace(document, format=PretendFormat())
        for operation in (backend.fields_for,
                          lambda doc: backend.stage(doc, {}, 'item_0_rank', 1),
                          lambda doc: backend.serialize(doc, {}),
                          lambda doc: backend.maximums(doc, {})):
            with self.assertRaises(SaveError):
                operation(forged)

    def test_malformed_requested_field_ids_raise_save_error_without_staging(self):
        document = backend.decode(procedural_raw())
        pending = {'item_0_rank': 19}
        for key in ([], {}, None, True, 1):
            with self.subTest(key=key), self.assertRaises(SaveError):
                backend.stage(document, pending, key, 0)
            with self.subTest(max_key=key), self.assertRaises(SaveError):
                backend.limit_values(document, pending, [key])
        self.assertEqual(pending, {'item_0_rank': 19})
        self.assertEqual(document.raw, procedural_raw())


class SpecialGuiWorkflow:
    fixture = staticmethod(procedural_raw)

    def test_named_weight_choice_review_undo_inspection_copy_restore(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'special-copy.dat'
            raw = self.fixture()
            source.write_bytes(raw)
            editor = Editor(root)
            errors = []
            with patch('koei_editor.shared.verified_gui.messagebox.showerror', side_effect=lambda *args: errors.append(args)), \
                    patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                editor.open()
                self.assertFalse(errors)
                field = next(field for field in backend.fields_for(editor.document) if field.id.endswith('_weight'))
                target = (field.value(editor.document.payload) + 1) % 3
                editor.search.set(field.label)
                editor.refresh()
                self.assertIn(field.id, editor.fields.get_children())
                editor.fields.selection_set(field.id)
                editor.selected()
                editor.value.set(str(target))
                editor.apply_selected()
                self.assertEqual(editor.changes, {field.id: target})
                editor.max_visible()
                self.assertEqual(editor.changes, {field.id: target})
                editor.review()
                self.assertTrue(any(isinstance(child, tk.Toplevel) for child in root.winfo_children()))
                editor.undo()
                self.assertEqual(editor.changes, {})
                editor.fields.selection_set(field.id)
                editor.value.set(str(target))
                editor.apply_selected()
                editor.show_inspector()
                self.assertEqual([table.title for table in editor.presentation.inspection_tables(editor.document)],
                                 ['Officers', 'Weapons', 'Items', 'Bodyguards', 'Shura resources'])
                destination = source.with_name('edited.dat')
                editor.save_to(destination)
                self.assertFalse(errors)
                self.assertEqual(source.read_bytes(), raw)
                self.assertTrue(editor.backup.exists())
                restored = backend.restore(editor.backup, source.with_name('restored.dat'))
                self.assertEqual(restored.read_bytes(), raw)
                self.assertEqual(field.value(backend.read_save(destination).payload), target)


class ProceduralSpecialGui(SpecialGuiWorkflow, unittest.TestCase):
    pass


@unittest.skipUnless(os.environ.get('DW5_SPECIAL_COPY'), 'No private native Windows Special save')
class NativeSpecialGui(SpecialGuiWorkflow, unittest.TestCase):
    fixture = staticmethod(lambda: Path(os.environ['DW5_SPECIAL_COPY']).read_bytes())
