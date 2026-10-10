"""Procedural US SYSTEM profile checks and optional genuine qualification."""
from dataclasses import replace
import os
import struct
from pathlib import Path
import tempfile
import unittest

from koei_editor.games.dw7e_ps3 import parser
from koei_editor.games.dw3.models import SaveError


def fixture():
    data = bytearray(parser.SAVE_SIZE)
    data[:4] = parser.REVISION
    data[0xA54:0xA58] = (123).to_bytes(4, 'big')
    return bytes(data)


class DW7EmpiresPS3Tests(unittest.TestCase):
    def test_roundtrip_surgical_manual_bonus_no_max_and_immutable_snapshot(self):
        raw = fixture()
        document = parser.decode(raw)
        self.assertEqual(parser.serialize(document, {}), raw)
        changes = parser.stage(document, {}, 'bonus_points', 456)
        output = parser.serialize(document, changes)
        self.assertEqual(parser.field_map(parser.decode(output))['bonus_points'].value(output), 456)
        self.assertEqual(output[:0xA54], raw[:0xA54])
        self.assertEqual(output[0xA58:], raw[0xA58:])
        self.assertEqual(parser.maximums(document, changes), changes)
        self.assertEqual(parser.stage(document, changes, 'bonus_points', 123), {})
        self.assertEqual(len(parser.review(document, changes)), 1)
        with self.assertRaises(SaveError):
            parser.fields_for(replace(document, payload=bytearray(raw)))
        for bad in (True, -1, 100000):
            with self.assertRaises(SaveError):
                parser.stage(document, {}, 'bonus_points', bad)

    def test_reject_other_games_campaign_wrong_size_and_invalid_changes(self):
        for bad in (fixture()[:-1], fixture() + b'\0', b'\xff' * parser.SAVE_SIZE, bytearray(fixture())):
            with self.assertRaises(SaveError):
                parser.decode(bad)
        document = parser.decode(fixture())
        for changes in ({'campaign_gold': 999}, {'bonus_points': -1}, {'story_complete': 1}):
            with self.assertRaises(SaveError):
                parser.maximums(document, changes)

    def test_copy_backups_restore_and_changed_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'copy.bin'
            source.write_bytes(fixture())
            document = parser.read_save(source)
            backup = parser.backup(document)
            parser.save_as(document, {'bonus_points': 456}, Path(directory) / 'edited.bin')
            self.assertEqual(source.read_bytes(), fixture())
            self.assertEqual(parser.restore(backup, Path(directory) / 'restored.bin').read_bytes(), fixture())
            source.write_bytes(fixture()[:-1] + b'\xff')
            with self.assertRaises(SaveError):
                parser.save_as(document, {}, Path(directory) / 'changed.bin')

    def test_optional_genuine_us_system_export(self):
        path = os.environ.get('DW7E_PS3_SYSTEM_COPY')
        if not path:
            self.skipTest('No private genuine US PS3 SYSTEM fixture supplied.')
        document = parser.read_save(path)
        self.assertEqual(parser.serialize(document, {}), document.raw)
        value = parser.field_map(document)['bonus_points'].value(document.payload)
        changed = parser.serialize(document, {'bonus_points': max(0, min(value - 1, 99999))})
        self.assertEqual(parser.field_map(parser.decode(changed))['bonus_points'].value(changed), max(0, min(value - 1, 99999)))

    def test_system_companion_required_when_present_and_campaign_rejected(self):
        def metadata(directory):
            key = b'SAVEDATA_DIRECTORY\0'
            value = directory.encode('ascii') + b'\0'
            return (struct.pack('<5I', 0x46535000, 0x101, 36, 36 + len(key), 1)
                    + struct.pack('<HH3I', 0, 0x204, len(value), len(value), 0)
                    + key + value)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'copy.bin'
            source.write_bytes(fixture())
            companion = source.with_name('PARAM.SFO')
            companion.write_bytes(metadata('NPUB30846-SYSTEM'))
            document = parser.read_save(source)
            snapshot = parser.backup(document)
            for foreign in ('NPUB30846-PLAY-00', 'NPUB30846-SYSTEM-extra', 'NPEB01263-SYSTEM'):
                companion.write_bytes(metadata(foreign))
                with self.subTest(directory=foreign):
                    with self.assertRaises(SaveError):
                        parser.read_save(source)
                    with self.assertRaises(SaveError):
                        parser.save_as(document, {}, Path(folder) / 'edited.bin')
                    with self.assertRaises(SaveError):
                        parser.restore(snapshot, Path(folder) / 'restored.bin')
                    self.assertFalse((Path(folder) / 'edited.bin').exists())
                    self.assertFalse((Path(folder) / 'restored.bin').exists())

    def test_real_tk_bonus_control_review_undo_max_and_save(self):
        import tkinter as tk
        from unittest.mock import patch
        from koei_editor.games.dw7e_ps3.editor import Editor
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'copy.bin'
            source.write_bytes(fixture())
            editor = Editor(root)
            with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                editor.open()
            editor.search.set('Bonus')
            editor.refresh()
            self.assertEqual(editor.fields.get_children(), ('bonus_points',))
            editor.fields.selection_set('bonus_points')
            editor.value.set('789')
            editor.apply_selected()
            self.assertEqual(editor.changes, {'bonus_points': 789})
            editor.review()
            editor.undo()
            self.assertEqual(editor.changes, {})
            editor.max_visible()
            self.assertEqual(editor.changes, {})
            editor.stage_values({'bonus_points': 789})
            destination = Path(directory) / 'edited.bin'
            editor.save_to(destination)
            self.assertEqual(parser.field_map(parser.read_save(destination))['bonus_points'].value(
                             parser.read_save(destination).payload), 789)
            self.assertEqual(source.read_bytes(), fixture())
            self.assertTrue(editor.backup.exists())
