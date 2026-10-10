"""Independent copied-save race and bounded-restore safety regressions.

Generated fixtures exercise storage contracts; they are not game-load evidence.
Native corpus and GUI evidence remain in the adapters' separate test modules.
"""
import hashlib
import json
from dataclasses import replace
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.nioh3 import inventory, parser as nioh3
from koei_editor.games.ninja_gaiden_ii import parser as ngii
from koei_editor.research.nioh2 import nioh2_parser as nioh2
from koei_editor.shared import copy_storage
from tests.test_nioh3_format import procedural_raw as nioh3_fixture, resign
from tests.test_ninja_gaiden_ii import procedural_story as ngii_fixture
from tests.test_nioh2_format import procedural_raw as nioh2_fixture


class TeamNinjaStorageReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = ((nioh3, '.bin', nioh3_fixture()),
                        (ngii, '.dat', ngii_fixture()))

    def test_source_replaced_during_serialization_never_authorizes_a_new_copy(self):
        for backend, suffix, raw in self.profiles:
            with self.subTest(game=backend.GAME_ID), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                source, destination = folder / ('source' + suffix), folder / ('edited' + suffix)
                source.write_bytes(raw)
                document = backend.read_save(source)
                field = backend.fields_for(document)[0]
                pending = backend.stage(document, {}, field.id, field.minimum)
                altered_source = raw[:-1] + bytes([raw[-1] ^ 1])
                actual_serialize = backend.serialize

                def replace_source(*args):
                    result = actual_serialize(*args)
                    source.write_bytes(altered_source)
                    return result

                with patch.object(backend, 'serialize', side_effect=replace_source), \
                        patch.object(backend, 'backup', wraps=backend.backup) as backup:
                    with self.assertRaises(SaveError):
                        backend.save_as(document, pending, destination)
                backup.assert_not_called()
                self.assertFalse(destination.exists())
                self.assertEqual(source.read_bytes(), altered_source)

    def test_destination_created_during_serialization_is_preserved(self):
        for backend, suffix, raw in self.profiles:
            with self.subTest(game=backend.GAME_ID), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                source, destination = folder / ('source' + suffix), folder / ('edited' + suffix)
                source.write_bytes(raw)
                document = backend.read_save(source)
                actual_serialize = backend.serialize
                concurrent = b'Created by another process'

                def create_destination(*args):
                    result = actual_serialize(*args)
                    destination.write_bytes(concurrent)
                    return result

                with patch.object(backend, 'serialize', side_effect=create_destination):
                    with self.assertRaises(FileExistsError):
                        backend.save_as(document, {}, destination)
                self.assertEqual(destination.read_bytes(), concurrent)
                self.assertEqual(source.read_bytes(), raw)
                self.assertFalse(list(folder.glob('.*.tmp')))

    def test_source_replaced_while_snapshot_backup_is_written_blocks_save(self):
        for backend, suffix, raw in self.profiles:
            with self.subTest(game=backend.GAME_ID), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                source, destination = folder / ('source' + suffix), folder / ('edited' + suffix)
                source.write_bytes(raw)
                document = backend.read_save(source)
                altered_source = raw[:-1] + bytes([raw[-1] ^ 1])
                actual_backup = backend.backup
                snapshots = []

                def replace_source(*args):
                    result = actual_backup(*args)
                    snapshots.append(result)
                    source.write_bytes(altered_source)
                    return result

                with patch.object(backend, 'backup', side_effect=replace_source):
                    with self.assertRaises(SaveError):
                        backend.save_as(document, {}, destination)
                self.assertFalse(destination.exists())
                self.assertEqual(source.read_bytes(), altered_source)
                self.assertEqual(len(snapshots), 1)
                self.assertEqual(snapshots[0].read_bytes(), raw)

    def test_restore_revalidates_native_structure_after_coherent_backup_swap(self):
        for backend, suffix, raw in self.profiles:
            with self.subTest(game=backend.GAME_ID), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                source, destination = folder / ('source' + suffix), folder / ('restored' + suffix)
                source.write_bytes(raw)
                document = backend.read_save(source)
                backup = backend.backup(document)
                damaged = bytearray(raw)
                if backend is nioh3:
                    # Correct native checksum cannot qualify a false pool length.
                    damaged[inventory.POOLS[1].tag_offset + 4] ^= 1
                    damaged = resign(damaged)
                else:
                    # Correct sum cannot qualify a different first owned weapon.
                    damaged[48:52] = b'\x00\x08\x01\x00'
                    damaged[ngii.codec.CHECKSUM_OFFSET:ngii.codec.CHECKSUM_OFFSET + 4] = \
                        ngii.codec.checksum(bytes(damaged)).to_bytes(4, 'big')
                    damaged = bytes(damaged)
                actual_restore = copy_storage.restore_snapshot

                def swap_backup(*args, **kwargs):
                    backup.write_bytes(damaged)
                    manifest_path = backup.with_suffix('.json')
                    manifest = json.loads(manifest_path.read_text())
                    manifest['sha256'] = hashlib.sha256(damaged).hexdigest()
                    manifest_path.write_text(json.dumps(manifest))
                    return actual_restore(*args, **kwargs)

                with patch.object(backend, 'restore_snapshot', side_effect=swap_backup):
                    with self.assertRaises(SaveError):
                        backend.restore(backup, destination)
                self.assertFalse(destination.exists())
                self.assertEqual(source.read_bytes(), raw)

    def test_unhashable_field_keys_fail_with_the_backend_validation_error(self):
        for backend, _suffix, raw in self.profiles:
            document = backend.decode(raw)
            for key in ([], {}, True, None):
                for operation in (lambda: backend.stage(document, {}, key, 1),
                                  lambda: backend.limit_values(document, {}, [key])):
                    with self.subTest(game=backend.GAME_ID, key=key), self.assertRaises(SaveError):
                        operation()

    def test_noniterable_or_string_max_keys_are_validation_errors(self):
        for backend, _suffix, raw in self.profiles:
            document = backend.decode(raw)
            for keys in (None, 1, 'quantity', b'quantity'):
                with self.subTest(game=backend.GAME_ID, keys=keys), self.assertRaises(SaveError):
                    backend.limit_values(document, {}, keys)

    def test_xenia_live_content_and_resolved_aliases_are_copy_protected(self):
        raw = self.profiles[1][2]
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = folder / 'separate-copy.dat'
            source.write_bytes(raw)
            document = ngii.read_save(source)
            snapshot = ngii.backup(document)
            live = folder / 'xenia/content/0000000000000000/544307D5/00000001/story.dat'
            alias = folder / 'aliased-copy.dat'
            actions = (lambda: ngii.read_save(live),
                       lambda: ngii.save_as(document, {}, live),
                       lambda: ngii.backup(replace(document, source=live)),
                       lambda: ngii.restore(snapshot, live),
                       lambda: ngii.restore(live, folder / 'restored.dat'))
            for action in actions:
                with self.assertRaises(SaveError):
                    action()
            actual_resolve = Path.resolve

            def resolved(path, *args, **kwargs):
                return live if path == alias else actual_resolve(path, *args, **kwargs)

            with patch.object(Path, 'resolve', resolved):
                for action in (lambda: ngii.read_save(alias),
                               lambda: ngii.save_as(document, {}, alias),
                               lambda: ngii.restore(snapshot, alias)):
                    with self.assertRaises(SaveError):
                        action()
            self.assertFalse(live.parent.exists())
            self.assertEqual(source.read_bytes(), raw)

    def test_nioh2_unchanged_copy_rejects_source_replacement_during_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            raw = nioh2_fixture()
            source, destination = folder / 'source.bin', folder / 'copy.bin'
            source.write_bytes(raw)
            document = nioh2.read_save(source)
            altered_source = raw[:-1] + bytes([raw[-1] ^ 1])
            actual_backup = nioh2.backup

            def replace_source(*args):
                result = actual_backup(*args)
                source.write_bytes(altered_source)
                return result

            with patch.object(nioh2, 'backup', side_effect=replace_source):
                with self.assertRaises(SaveError):
                    nioh2.save_as(document, {}, destination)
            self.assertFalse(destination.exists())
            self.assertEqual(source.read_bytes(), altered_source)


class Nioh3BalanceReviewTests(unittest.TestCase):
    def test_unsigned_balance_edits_preserve_all_other_native_state_in_both_revisions(self):
        # Offsets independently matched to historical source and native tags.
        profiles = ((0x01040000, 0x3ADE49, 0x3ADE59),
                    (0x01030001, 0x3ADE25, 0x3ADE35))
        for revision, amrita_at, gold_at in profiles:
            raw = bytearray(nioh3_fixture(revision))
            amounts = {'amrita': 0xFEDCBA9876543210, 'gold': 0xFFFFFFFFFFFFFFFF}
            for key, offset in (('amrita', amrita_at), ('gold', gold_at)):
                raw[offset:offset + 8] = amounts[key].to_bytes(8, 'little')
            document = nioh3.decode(resign(raw))
            mapping = nioh3.field_map(document)
            self.assertEqual(nioh3.serialize(document, {}), document.raw)
            for key, offset in (('amrita', amrita_at), ('gold', gold_at)):
                with self.subTest(revision=revision, balance=key):
                    field = mapping[key]
                    self.assertEqual((field.offset, field.size, field.minimum, field.maximum),
                                     (offset, 8, 0, amounts[key]))
                    self.assertFalse(field.maxable)
                    pending = nioh3.stage(document, {}, key, 0)
                    self.assertEqual(nioh3.maximums(document, pending), pending)
                    self.assertEqual(nioh3.limit_values(document, pending, [key]), {})
                    self.assertEqual(nioh3.stage(document, pending, key, amounts[key]), {})
                    result = nioh3.decode(nioh3.serialize(document, pending))
                    self.assertEqual(field.value(result.payload), 0)
                    restored = bytearray(result.payload)
                    restored[offset:offset + 8] = document.payload[offset:offset + 8]
                    checksum = nioh3.codec.CHECKSUM_OFFSET
                    restored[checksum:checksum + 4] = document.payload[checksum:checksum + 4]
                    # Grave/reward/EXP/level and neighboring tag values stay exact.
                    self.assertEqual(bytes(restored), document.payload)
                    for value in (-1, amounts[key] + 1, True, float(amounts[key]), '0'):
                        with self.assertRaises(SaveError):
                            nioh3.stage(document, {}, key, value)

    @unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'),
                         'A Tk display is required for unsigned 64-bit input checks.')
    def test_gui_keeps_exact_unsigned_64_bit_balances_through_undo_and_save(self):
        import tkinter as tk
        from koei_editor.game_registry import get_game

        root = tk.Tk()
        self.addCleanup(root.destroy)
        root.withdraw()
        original = 0xFFFFFFFFFFFFFFFF
        raw = bytearray(nioh3_fixture())
        raw[0x3ADE59:0x3ADE61] = original.to_bytes(8, 'little')
        raw = resign(raw)
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source, destination = folder / 'source.bin', folder / 'edited.bin'
            source.write_bytes(raw)
            editor = get_game('nioh3').create_editor(root, root)
            errors = []
            with patch('koei_editor.shared.verified_gui.messagebox.showerror',
                       side_effect=lambda *args: errors.append(args)), \
                    patch('koei_editor.shared.verified_gui.filedialog.askopenfilename',
                          return_value=str(source)):
                editor.open()
                self.assertEqual(errors, [])
                editor.search.set('gold')
                editor.refresh()
                self.assertEqual(editor.fields.get_children(), ('gold',))
                editor.fields.selection_set('gold')
                editor.value.set(str(original - 1))
                editor.apply_selected()
                self.assertEqual(editor.changes, {'gold': original - 1})
                editor.max_selected()
                self.assertEqual(editor.changes, {'gold': original - 1})
                review = nioh3.review(editor.document, editor.changes)
                self.assertEqual([(field.id, before, after) for field, before, after in review],
                                 [('gold', original, original - 1)])
                editor.undo()
                self.assertEqual(editor.changes, {})
                editor.fields.selection_set('gold')
                editor.value.set(str(original - 1))
                editor.apply_selected()
                self.assertEqual(editor.changes, {'gold': original - 1})
                editor.save_to(destination)
                self.assertEqual(errors, [])
            result = nioh3.read_save(destination)
            self.assertEqual(nioh3.field_map(result)['gold'].value(result.payload), original - 1)
            self.assertEqual(source.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
