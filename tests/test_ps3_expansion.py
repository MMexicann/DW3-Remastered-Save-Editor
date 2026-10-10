"""Procedural and optional genuine decrypted PS3 export validation."""
from dataclasses import replace
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.dw7_ps3 import parser as dw7
from koei_editor.games.sw4_ps3 import parser as sw4


def fixture(backend):
    data = bytearray(backend.SAVE_SIZE)
    data[:4] = backend.REVISION
    if backend is sw4:
        for index in range(55):
            offset = 0xC1A + index * 0x44
            data[offset:offset + 4] = index.to_bytes(4, 'big')
            data[0xC44 + index * 0x44] = 3
        data[0xC45] = 0  # Empty proficiency must stay unexposed.
        data[0xC46] = 255  # Unknown/higher value must stay unexposed.
    for field in backend.FORMAT.fields:
        data[field.offset:field.offset + field.size] = min(field.maximum, 7).to_bytes(field.size, 'big')
    return backend.seal(bytes(data))


class PS3ExpansionTests(unittest.TestCase):
    def test_procedural_roundtrip_manual_edit_and_surgical_preservation(self):
        for backend in (dw7, sw4):
            with self.subTest(game=backend.GAME_ID):
                raw = fixture(backend)
                doc = backend.decode(raw)
                self.assertEqual(backend.serialize(doc, {}), raw)
                changed = backend.stage(doc, {}, 'gold', 12345)
                reopened = backend.decode(backend.serialize(doc, changed))
                self.assertEqual(backend.field_map(reopened)['gold'].value(reopened.payload), 12345)
                self.assertEqual(backend.changed_payload(doc, changed), reopened.payload)
                allowed = set(range(backend.FORMAT.fields[0].offset, backend.FORMAT.fields[0].offset + 4))
                for offset in getattr(backend, 'CHECKSUM_OFFSETS', ()):
                    allowed.update(range(offset, offset + 4))
                touched = {i for i, (a, b) in enumerate(zip(raw, reopened.raw)) if a != b}
                self.assertTrue(touched)
                self.assertLessEqual(touched, allowed)
                self.assertEqual(backend.stage(doc, changed, 'gold', 7), {})
                self.assertEqual(backend.maximums(doc, changed), changed)
                self.assertEqual(len(backend.review(doc, changed)), 1)

    def test_wrong_platform_revision_encryption_truncation_and_mutability_rejected(self):
        for backend in (dw7, sw4):
            raw = fixture(backend)
            for bad in (b'bad', raw[:-1], raw + b'\0', b'\xff' * len(raw), bytearray(raw)):
                with self.subTest(game=backend.GAME_ID), self.assertRaises(SaveError):
                    backend.decode(bad)
            doc = backend.decode(raw)
            for modified in (replace(doc, raw=bytearray(raw)), replace(doc, payload=bytearray(raw)),
                             replace(doc, payload=raw[:-1] + b'\xff')):
                with self.assertRaises(SaveError):
                    backend.fields_for(modified)
            for value in (True, -1, 1000000):
                with self.assertRaises(SaveError):
                    backend.stage(doc, {}, 'gold', value)
            with self.assertRaises(SaveError):
                backend.stage(doc, {}, 'story_complete', 1)

    def test_us_sw4_checksum_corruption_identity_and_jp_layout_rejected(self):
        raw = fixture(sw4)
        for offset in (0x7842, 0xC44, 4, 0xA8, 0xC16, 0x58532):
            bad = bytearray(raw)
            bad[offset] ^= 1
            with self.assertRaises(SaveError):
                sw4.decode(bytes(bad))
        bad = bytearray(raw)
        bad[0xC1A:0xC1E] = b'\0\0\0\x02'
        with self.assertRaises(SaveError):
            sw4.decode(sw4.seal(bytes(bad)))
        bad = bytearray(raw)
        bad[0x58298] = 1
        with self.assertRaises(SaveError):
            sw4.decode(sw4.seal(bytes(bad)))
        fields = sw4.field_map(sw4.decode(raw))
        self.assertNotIn('officer_0_proficiency_0', fields)
        self.assertNotIn('officer_0_proficiency_1', fields)
        self.assertNotIn('officer_0_proficiency_2', fields)

    def test_backup_restore_source_copy_and_changed_source(self):
        for backend in (dw7, sw4):
            with tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / 'copy.bin'
                raw = fixture(backend)
                source.write_bytes(raw)
                doc = backend.read_save(source)
                snapshot = backend.backup(doc)
                destination = Path(folder) / 'edited.bin'
                backend.save_as(doc, {'gold': 12}, destination)
                self.assertEqual(source.read_bytes(), raw)
                self.assertEqual(backend.read_save(destination).payload[backend.FORMAT.fields[0].offset:
                                 backend.FORMAT.fields[0].offset + 4], (12).to_bytes(4, 'big'))
                restored = backend.restore(snapshot, Path(folder) / 'restored.bin')
                self.assertEqual(restored.read_bytes(), raw)
                with self.assertRaises(FileExistsError):
                    backend.save_as(doc, {}, destination)
                source.write_bytes(raw[:-1] + b'\xff')
                with self.assertRaises(SaveError):
                    backend.save_as(doc, {}, Path(folder) / 'changed.bin')

    def test_optional_genuine_dw7_us_eu_and_sw4_us(self):
        cases = [(dw7, 'DW7_PS3_US_COPY'), (dw7, 'DW7_PS3_EU_COPY'), (sw4, 'SW4_PS3_US_COPY')]
        found = 0
        for backend, variable in cases:
            path = os.environ.get(variable)
            if not path:
                continue
            found += 1
            raw = Path(path).read_bytes()
            document = backend.decode(raw)
            self.assertEqual(backend.serialize(document, {}), raw)
            field = backend.field_map(document)['gold']
            value = field.value(raw)
            output = backend.serialize(document, {'gold': max(0, min(value - 1, field.maximum))})
            self.assertEqual(field.value(backend.decode(output).payload), max(0, min(value - 1, field.maximum)))
        if not found:
            self.skipTest('No private genuine decrypted PS3 fixture paths supplied.')

    def test_real_tk_search_manual_apply_review_undo_max_and_save(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        from koei_editor.games.dw7_ps3.editor import Editor as DW7Editor
        from koei_editor.games.sw4_ps3.editor import Editor as SW4Editor
        for backend, editor_type in ((dw7, DW7Editor), (sw4, SW4Editor)):
            with tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / 'copy.bin'
                raw = fixture(backend)
                source.write_bytes(raw)
                editor = editor_type(root)
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                    editor.open()
                editor.search.set('Gold')
                editor.refresh()
                self.assertEqual(editor.fields.get_children(), ('gold',))
                editor.fields.selection_set('gold')
                editor.value.set('1234')
                editor.apply_selected()
                self.assertEqual(editor.changes, {'gold': 1234})
                editor.review()
                editor.undo()
                self.assertEqual(editor.changes, {})
                editor.max_visible()
                self.assertEqual(editor.changes, {})
                editor.stage_values({'gold': 1234})
                editor.save_to(Path(folder) / 'edited.bin')
                self.assertEqual(source.read_bytes(), raw)
                self.assertEqual(backend.field_map(backend.read_save(Path(folder) / 'edited.bin'))['gold'].value(
                                 backend.read_save(Path(folder) / 'edited.bin').payload), 1234)


class PS3ContextTests(unittest.TestCase):
    @staticmethod
    def metadata(directory):
        import struct
        key = b'SAVEDATA_DIRECTORY\0'
        value = directory.encode('ascii') + b'\0'
        return (struct.pack('<5I', 0x46535000, 0x101, 36, 36 + len(key), 1)
                + struct.pack('<HH3I', 0, 0x204, len(value), len(value), 0)
                + key + value)

    def test_selective_sfo_identity_foreign_region_duplicates_and_malformed_bounds(self):
        from koei_editor.shared.ps3_export import savedata_directory
        data = self.metadata('BLUS30690-SAVEDATA')
        self.assertEqual(savedata_directory(data), 'BLUS30690-SAVEDATA')
        for bad in (data[:-1], data + b'\0' * 4096, bytearray(data), b'\0' * 20):
            with self.assertRaises(SaveError):
                savedata_directory(bad)
        for backend, correct, wrong in ((dw7, 'BLUS30690-SAVEDATA', 'BLUS30873-SAVEDATA'),
                                        (sw4, 'NPUB31564-00', 'NPJB00534-00')):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'copy.bin'
                path.write_bytes(fixture(backend))
                companion = path.parent / 'PARAM.SFO'
                companion.write_bytes(self.metadata(correct))
                backend.read_save(path)
                companion.write_bytes(self.metadata(wrong))
                with self.assertRaises(SaveError):
                    backend.read_save(path)

    def test_dw7_unknown_upper_power_and_speed_bytes_are_read_only(self):
        data = bytearray(fixture(dw7))
        data[0x14BD] = 1
        data[0x14BF] = 255
        document = dw7.decode(bytes(data))
        fields = dw7.field_map(document)
        self.assertNotIn('officer_0_power', fields)
        self.assertNotIn('officer_0_speed', fields)
        output = dw7.serialize(document, {'gold': 8})
        self.assertEqual(output[0x14BD:0x14C1], bytes(data)[0x14BD:0x14C1])
        self.assertEqual(dw7.maximums(document, {}), {})
