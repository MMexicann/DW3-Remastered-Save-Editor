"""Opaque console export context must remain the opened context until writing."""
from dataclasses import replace
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.dw8e_ps3 import parser as dw8e
from koei_editor.games.wo3u_ps3 import parser as wo3u
from tests import test_dw8e_ps3_horses as horse_tests
from tests import test_wo3u_ps3 as orochi_tests


class ConsoleContextRegressions(unittest.TestCase):
    profiles = ((dw8e, horse_tests.procedural_raw, {'horse_0_body': 3}),
                (wo3u, orochi_tests.fixture, {'gems': 321}))

    def copy(self, folder, backend, fixture):
        source = folder / 'APP.BIN'
        source.write_bytes(fixture())
        metadata = orochi_tests.metadata(backend.TITLE_IDS[0])
        source.with_name('PARAM.SFO').write_bytes(metadata)
        return source, metadata, backend.read_save(source)

    def test_same_title_source_and_destination_changes_reject_before_output(self):
        for backend, fixture, changes in self.profiles:
            with self.subTest(game=backend.GAME_ID), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                source, metadata, document = self.copy(folder, backend, fixture)
                companion = source.with_name('PARAM.SFO')
                companion.write_bytes(metadata + b'opaque-context-change')
                with self.assertRaises(SaveError):
                    backend.save_as(document, changes, folder / 'changed-source.bin')
                with self.assertRaises(SaveError):
                    backend.prepare_copy_context(document, folder / 'self-test')
                self.assertFalse((folder / 'changed-source.bin').exists())
                self.assertFalse((folder / 'self-test' / 'PARAM.SFO').exists())
                companion.write_bytes(metadata)
                other = folder / 'different-context'
                other.mkdir()
                (other / 'PARAM.SFO').write_bytes(metadata + b'different-opaque-context')
                with self.assertRaises(SaveError):
                    backend.save_as(document, changes, other / 'changed-destination.bin')
                self.assertFalse((other / 'changed-destination.bin').exists())
                self.assertEqual(source.read_bytes(), document.raw)

    def test_late_source_or_destination_context_change_during_backup_rejects_save(self):
        for backend, fixture, changes in self.profiles:
            for changed_context in ('source', 'destination'):
                with self.subTest(game=backend.GAME_ID, context=changed_context), tempfile.TemporaryDirectory() as directory:
                    folder = Path(directory)
                    source, metadata, document = self.copy(folder, backend, fixture)
                    other = folder / 'output'
                    other.mkdir()
                    output_context = other / 'PARAM.SFO'
                    output_context.write_bytes(metadata)
                    destination = other / 'edited.bin'
                    original_backup = backend.backup
                    def backup_then_replace(snapshot):
                        result = original_backup(snapshot)
                        companion = source.with_name('PARAM.SFO') if changed_context == 'source' else output_context
                        companion.write_bytes(metadata + b'late-opaque-change')
                        return result
                    with patch.object(backend, 'backup', side_effect=backup_then_replace), self.assertRaises(SaveError):
                        backend.save_as(document, changes, destination)
                    self.assertFalse(destination.exists())
                    self.assertEqual(source.read_bytes(), document.raw)

    def test_late_source_gameplay_change_during_backup_rejects_save(self):
        for backend, fixture, changes in self.profiles:
            with self.subTest(game=backend.GAME_ID), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                source, _, document = self.copy(folder, backend, fixture)
                original_backup = backend.backup
                def backup_then_replace(snapshot):
                    result = original_backup(snapshot)
                    source.write_bytes(snapshot.raw[:-1])
                    return result
                destination = folder / 'edited.bin'
                with patch.object(backend, 'backup', side_effect=backup_then_replace), self.assertRaises(SaveError):
                    backend.save_as(document, changes, destination)
                self.assertFalse(destination.exists())

    def test_restore_rechecks_context_after_qualifying_exact_backup_bytes(self):
        for backend, fixture, _ in self.profiles:
            for changed_title in (False, True):
                with self.subTest(game=backend.GAME_ID, foreign=changed_title), tempfile.TemporaryDirectory() as directory:
                    folder = Path(directory)
                    source, metadata, document = self.copy(folder, backend, fixture)
                    snapshot = backend.backup(document)
                    original_decode = backend.decode
                    def decode_then_replace(*args, **kwargs):
                        result = original_decode(*args, **kwargs)
                        source.with_name('PARAM.SFO').write_bytes(
                            orochi_tests.metadata('UNQUALIFIED-TITLE') if changed_title else metadata + b'late-restore-context')
                        return result
                    destination = folder / 'restored.bin'
                    with patch.object(backend, 'decode', side_effect=decode_then_replace), self.assertRaises(SaveError):
                        backend.restore(snapshot, destination)
                    self.assertFalse(destination.exists())
                    self.assertEqual(source.read_bytes(), document.raw)

    def test_read_and_selftest_copy_recheck_context_after_first_read(self):
        for backend, fixture, _ in self.profiles:
            with self.subTest(game=backend.GAME_ID), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                source, metadata, document = self.copy(folder, backend, fixture)
                original_decode = backend.decode
                def decode_then_replace(*args, **kwargs):
                    result = original_decode(*args, **kwargs)
                    source.with_name('PARAM.SFO').write_bytes(metadata + b'changed-during-open')
                    return result
                with patch.object(backend, 'decode', side_effect=decode_then_replace), self.assertRaises(SaveError):
                    backend.read_save(source)
                source.with_name('PARAM.SFO').write_bytes(metadata)
                original_context_raw = backend._context_raw
                def read_then_replace(path):
                    result = original_context_raw(path)
                    source.with_name('PARAM.SFO').write_bytes(metadata + b'changed-before-copy')
                    return result
                destination = folder / 'self-test'
                with patch.object(backend, '_context_raw', side_effect=read_then_replace), self.assertRaises(SaveError):
                    backend.prepare_copy_context(document, destination)
                self.assertFalse((destination / 'PARAM.SFO').exists())

    def test_unchanged_context_copy_save_and_fresh_document_digest(self):
        for backend, fixture, changes in self.profiles:
            with self.subTest(game=backend.GAME_ID), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                source, metadata, document = self.copy(folder, backend, fixture)
                expected_digest = hashlib.sha256(metadata).hexdigest()
                self.assertEqual(document.context_digest, expected_digest)
                for invalid in (None, True, metadata, 1):
                    with self.assertRaises(SaveError):
                        backend.fields_for(replace(document, context_digest=invalid))
                copied = folder / 'context-copy'
                backend.prepare_copy_context(document, copied)
                self.assertEqual((copied / 'PARAM.SFO').read_bytes(), metadata)
                saved = backend.save_as(document, changes, copied / 'edited.bin')
                self.assertEqual(saved.context_digest, expected_digest)
                second = backend.save_as(saved, {}, copied / 'second.bin')
                self.assertEqual(second.raw, saved.raw)
                self.assertEqual(second.context_digest, expected_digest)
                self.assertEqual(source.read_bytes(), document.raw)


if __name__ == '__main__':
    unittest.main()
