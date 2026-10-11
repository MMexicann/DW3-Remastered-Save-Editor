"""Independent stored-field/equipment expansion regressions; no saves are bundled."""
import importlib
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.sw4ii import sw4ii_parser as ii
from koei_editor.games.sw2 import sw2_parser as sw2
from koei_editor.games.dw5special import dw5special_parser as five
from koei_editor.games.dw6 import dw6_parser as six
from koei_editor.games.dw4hyper import dw4hyper_parser as hyper
from koei_editor.games.dw4xl import dw4xl_parser as xl
from tests.test_sw4ii_format import procedural_raw as ii_raw, seal as ii_seal
from tests.test_sw2_pc_format import procedural_raw as sw2_raw, checksum as sw2_seal
from tests.test_dw5special_format import procedural_raw as five_raw, procedural_envelope
from tests.test_dw6_format import procedural_raw as six_raw
from tests.test_dw4hyper_format import procedural_raw as hyper_raw, repair_checksum
from tests.test_dw4xl_format import procedural_inner, procedural_psu, repair_inner


def examples():
    payload = bytearray(ii.decode(ii_raw()).payload)
    payload[0x1052 + 0x3D] = 0
    payload[0xCA42 + 16:0xCA42 + 32] = payload[0xCA42:0xCA42 + 16]
    payload[0xCA42 + 16] = 3
    original_sw2 = bytearray(sw2_raw())
    original_sw2[0xC + 0x28 + 19:0xC + 0x28 + 38] = original_sw2[0xC + 0x28:0xC + 0x28 + 19]
    h = bytearray(hyper_raw())
    h[0x7F6:0x7F6 + 13] = bytes([3]) * 13
    x = bytearray(procedural_inner())
    x[0x7F6:0x7F6 + 13] = bytes([3]) * 13
    x[0x7F6 + 29] = 0
    return ((ii, ii_seal(payload), 'officer_0_equipped_mount', 1),
            (sw2, sw2_seal(original_sw2), 'officer_0_equipped_weapon', 1),
            (five, five_raw(), 'officer_0_attack', 123),
            (six, six_raw(), 'officer_0_weapon_0_damage_bonus', 12),
            (hyper, repair_checksum(h), 'officer_0_general_item_2', 0),
            (xl, procedural_psu(repair_inner(x)), 'officer_0_general_item_2', 0))


def integrity_positions(backend):
    if backend is ii:
        return {i for base in (4, 0xA8, 0x104E, 0x5D86E) for i in range(base, base + 4)}
    if backend is sw2:
        return set(range(0x22E94, 0x22E98))
    if backend is five:
        return set(range(0xB390, 0xB394))
    if backend is hyper:
        return set(range(0x10FA8, 0x10FAC))
    return {0, 1} if backend is xl else set()


class DepthTests(unittest.TestCase):
    def surgical(self, backend, document, key, value):
        field = backend.field_map(document)[key]
        original = field.value(document.payload)
        changes = backend.stage(document, {}, key, value)
        output = backend.serialize(document, changes)
        edited = backend.decode(output)
        self.assertEqual(field.value(edited.payload), value)
        allowed = set(range(field.offset, field.offset + field.size)) | integrity_positions(backend)
        self.assertLessEqual({i for i, (a, b) in enumerate(zip(document.payload, edited.payload)) if a != b}, allowed)
        self.assertEqual(backend.stage(document, changes, key, original), {})
        self.assertEqual([(f.id, before, after) for f, before, after in backend.review(document, changes)],
                         [] if value == original else [(key, original, value)])
        self.assertFalse(field.maxable)
        self.assertEqual(backend.maximums(document, changes, field.group), changes)
        if backend is ii:
            self.assertEqual(output[:0x20C], document.raw[:0x20C])
            self.assertEqual(edited.seed, document.seed)
        if backend is xl:
            start = document.payload_offset
            self.assertEqual(output[:start], document.raw[:start])
            self.assertEqual(output[start + 34064:], document.raw[start + 34064:])
        return changes

    def test_new_fields_unchanged_surgical_review_unstage_bounds(self):
        for backend, raw, key, value in examples():
            with self.subTest(game=backend.GAME_ID):
                document = backend.decode(raw)
                self.assertEqual(backend.serialize(document, {}), raw)
                self.surgical(backend, document, key, value)
                field = backend.field_map(document)[key]
                for bad in (-1, field.maximum + 1, True, '1', 1.5):
                    with self.assertRaises(SaveError):
                        backend.stage(document, {}, key, bad)

    def test_known_occupied_mounts_only_and_unusual_reference_undo(self):
        _, raw, key, _ = examples()[0]
        document = ii.decode(raw)
        self.assertEqual(tuple(value for value, _ in ii.field_options(document, key)), (0, 1))
        for value in (2, 19):
            with self.assertRaises(SaveError):
                ii.stage(document, {}, key, value)
        payload = bytearray(document.payload)
        payload[0x1052 + 0x3D] = 255
        payload[0xCA42 + 16] = 25
        document = ii.decode(ii_seal(payload))
        self.assertEqual(ii.field_options(document, key)[0][0], 0)
        self.assertEqual(ii.stage(document, ii.stage(document, {}, key, 0), key, 255), {})
        with self.assertRaises(SaveError):
            ii.stage(document, {}, key, 1)
        payload[0xCA42] = 26
        document = ii.decode(ii_seal(payload))
        self.assertNotIn(key, ii.field_map(document))

    def test_weapon_selection_owned_officer_own_pool_only(self):
        _, raw, key, _ = examples()[1]
        document = sw2.decode(raw)
        self.assertEqual(tuple(value for value, _ in sw2.field_options(document, key)), (0, 1))
        for relative, value in ((0, 127), (0, 4), (18, 0), (18, 9)):
            modified = bytearray(raw)
            modified[0xC + 0x28 + 19 + relative] = value
            doc = sw2.decode(sw2_seal(modified))
            with self.assertRaises(SaveError):
                sw2.stage(doc, {}, key, 1)
        modified = bytearray(raw)
        modified[0x214C] &= ~1
        self.assertNotIn(key, sw2.field_map(sw2.decode(sw2_seal(modified))))
        modified = bytearray(raw)
        modified[0xC + 0xC0] = 254
        doc = sw2.decode(sw2_seal(modified))
        self.assertEqual(sw2.stage(doc, sw2.stage(doc, {}, key, 1), key, 254), {})

    def test_stored_stats_and_bonus_keep_growth_and_identity_separate(self):
        for backend, raw, key, _ in examples()[2:4]:
            document = backend.decode(raw)
            field = backend.field_map(document)[key]
            self.surgical(backend, document, key, field.maximum)
            self.assertEqual(backend.limit_values(document, {}, [key]), {})
        raw = bytearray(five_raw())
        raw[0xEC] = 0
        doc = five.decode(procedural_envelope(raw))
        self.assertNotIn('officer_0_attack', five.field_map(doc))
        self.assertNotIn('officer_0_defense', five.field_map(doc))
        raw = bytearray(six_raw())
        struct.pack_into('<I', raw, 2904 + 8, 174)
        self.assertNotIn('officer_0_weapon_0_damage_bonus', six.field_map(six.decode(raw)))

    def test_pending_batches_reject_before_max_or_unstage_without_partial_mutation(self):
        for backend, raw, key, value in examples():
            document = backend.decode(raw)
            for invalid in ({'unknown': 1}, {key: True}, {key: -1}):
                before = dict(invalid)
                with self.subTest(game=backend.GAME_ID, pending=invalid):
                    with self.assertRaises(SaveError):
                        backend.stage(document, invalid, key, backend.field_map(document)[key].value(document.payload))
                    with self.assertRaises(SaveError):
                        backend.maximums(document, invalid)
                    self.assertEqual(invalid, before)
                    self.assertEqual(document.raw, raw)
        for backend, raw, key, value in examples()[4:]:
            doc = backend.decode(raw)
            duplicate = 11 if backend is hyper else 4
            pending = {key: duplicate}
            with self.assertRaises(SaveError):
                backend.stage(doc, pending, key, backend.field_map(doc)[key].value(doc.payload))
            self.assertEqual(pending, {key: duplicate})

    def test_general_slots_do_not_expand_capacity_or_grant_ownership(self):
        for backend, raw, key, value in examples()[4:]:
            with self.subTest(game=backend.GAME_ID):
                document = backend.decode(raw)
                sentinel = 32 if backend is hyper else 41
                fields = backend.field_map(document)
                self.assertNotIn('officer_0_general_item_7', fields)
                options = backend.field_options(document, key)
                self.assertIn((0, 'Peacock Urn'), options)
                for bad in (13, 19, 24, 11 if backend is hyper else 4):
                    with self.assertRaises(SaveError):
                        backend.stage(document, {}, key, bad)
                self.surgical(backend, document, key, sentinel)
                # A pending grant cannot qualify a previously unowned replacement.
                with self.assertRaises(SaveError):
                    backend.serialize(document, {'item_24': 1, key: 24})
                changes = backend.stage(document, {}, key, value)
                with self.assertRaises(SaveError):
                    backend.stage(document, changes, 'officer_0_weapon_experience', 1)
                with self.assertRaises(SaveError):
                    backend.serialize(document, {key: value, 'item_0': 0})

    def test_copied_save_backup_restore_and_unchanged_source_for_every_new_group(self):
        for backend, raw, key, value in examples():
            with self.subTest(game=backend.GAME_ID), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                extension = '.psu' if backend is xl else '.dat'
                source = folder / ('source' + extension)
                source.write_bytes(raw)
                document = backend.read_save(source)
                changes = backend.stage(document, {}, key, value)
                target = folder / ('edited' + extension)
                reopened = backend.save_as(document, changes, target)
                self.assertEqual(backend.field_map(reopened)[key].value(reopened.payload), value)
                self.assertEqual(source.read_bytes(), raw)
                backups = list(folder.glob('*Backups/*' + extension))
                self.assertEqual(len(backups), 1)
                restored = backend.restore(backups[0], folder / ('restored' + extension))
                self.assertEqual(restored.read_bytes(), raw)
                damaged = bytearray(raw)
                damage_offset = document.payload_offset + 100 if backend is xl else 0x210 + 100 if backend is ii else 100
                damaged[damage_offset] ^= 1
                if backend is six:
                    struct.pack_into('<I', damaged, 2904 + 136, 99)
                with self.assertRaises(SaveError):
                    backend.decode(damaged)

    def test_native_new_field_matrix_separately_qualified(self):
        inputs = ((ii, 'SW4II_SAVE_COPY', 'Mount equipment'),
                  (sw2, 'SW2_PC_SAVE_COPY', 'Equipment'),
                  (five, 'DW5_SPECIAL_COPY', 'Officer base stats'),
                  (six, 'DW6_SAVE', 'Weapon bonuses'),
                  (hyper, 'DW4HYPER_SAVE_COPY', 'General equipment'),
                  (xl, 'DW4XL_PSU_COPY', 'General equipment'))
        supplied = 0
        for backend, variable, group in inputs:
            if not os.environ.get(variable):
                continue
            supplied += 1
            source = Path(os.environ[variable])
            raw = source.read_bytes()
            document = backend.read_save(source)
            self.assertEqual(backend.serialize(document, {}), raw)
            fields = [field for field in backend.fields_for(document) if field.group == group]
            self.assertTrue(fields, backend.GAME_ID)
            for field in fields:
                options = backend.field_options(document, field.id)
                original = field.value(document.payload)
                value = next((v for v, _ in options if v != original), original) if options else (0 if original else 1)
                self.surgical(backend, document, field.id, value)
            self.assertEqual(source.read_bytes(), raw)
        if not supplied:
            self.skipTest('No private native inputs were supplied')

    def test_tk_new_groups_apply_review_undo_save_and_backup(self):
        import tkinter as tk
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.addCleanup(root.destroy)
        root.withdraw()
        modules = ('sw4ii.sw4ii_editor', 'sw2.sw2_editor', 'dw5special.dw5special_editor',
                   'dw6.dw6_editor', 'dw4hyper.dw4hyper_editor', 'dw4xl.dw4xl_editor')
        for module, (backend, raw, key, value) in zip(modules, examples()):
            with self.subTest(game=backend.GAME_ID), tempfile.TemporaryDirectory() as temporary:
                host = tk.Toplevel(root)
                host.withdraw()
                try:
                    extension = '.psu' if backend is xl else '.dat'
                    source = Path(temporary) / ('copy' + extension)
                    source.write_bytes(raw)
                    editor = importlib.import_module('koei_editor.games.' + module).Editor(host)
                    with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                        editor.open()
                    self.assertIsNotNone(editor.document)
                    editor.group.set(backend.field_map(editor.document)[key].group)
                    editor.search.set(key)
                    editor.refresh()
                    editor.fields.selection_set(key)
                    editor.value.set(str(value))
                    editor.apply_selected()
                    self.assertEqual(editor.changes, {key: value})
                    editor.review()
                    editor.undo()
                    self.assertEqual(editor.changes, {})
                    editor.fields.selection_set(key)
                    editor.value.set(str(value))
                    editor.apply_selected()
                    editor.save_to(Path(temporary) / ('edited' + extension))
                    restored = backend.restore(editor.backup, Path(temporary) / ('restored' + extension))
                    self.assertEqual(restored.read_bytes(), raw)
                    self.assertEqual(source.read_bytes(), raw)
                finally:
                    host.destroy()
