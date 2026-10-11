"""Registered copied-save integrity reports, with distinct private native checks.

Generated fixtures test workflow/report contracts, not actual game loading.
Optional native files stay outside source and are never embedded in this suite.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from koei_editor.game_registry import get_game
from koei_editor.shared.verified_self_test import run
from tests.test_nioh3_format import procedural_raw
from tests.test_ninja_gaiden_ii import procedural_story


class CopiedSaveIntegrityAssertions:
    def assert_copied_self_test(self, game_id, raw):
        game = get_game(game_id)
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = folder / ('source-copy' + game.extension)
            source.write_bytes(raw)
            output = folder / 'selftest'
            report = run(game_id, source, output)
            self.assertTrue(report['success'])
            self.assertEqual(report['game_id'], game_id)
            self.assertEqual(report['integrity_kind'], 'checksum')
            for flag in ('checksum_verified', 'native_integrity_verified',
                         'format_sample_verified', 'input_preserved',
                         'unchanged_roundtrip', 'backup_restored'):
                self.assertIs(report[flag], True, flag)
            self.assertIs(report['in_game_load_tested'], False)
            self.assertGreater(report['fields_checked'], 0)
            # Both adapters deliberately exclude every field from bulk Max.
            # Their self-test must preserve full native bytes, including context.
            self.assertEqual(report['fields_changed'], 0)
            digest = hashlib.sha256(raw).hexdigest()
            self.assertEqual(report['input_sha256'], digest)
            self.assertEqual(report['edited_sha256'], digest)
            self.assertEqual(source.read_bytes(), raw)
            for name in ('input-copy', 'edited', 'restored'):
                self.assertEqual((output / (name + game.extension)).read_bytes(), raw)
            self.assertEqual(json.loads((output / 'self-test-report.json').read_text()), report)


class GeneratedIntegrityReportTests(CopiedSaveIntegrityAssertions, unittest.TestCase):
    def test_registered_nioh3_self_test_reports_its_native_checksum(self):
        self.assert_copied_self_test('nioh3', procedural_raw())

    def test_registered_ngii_self_test_reports_its_native_checksum(self):
        self.assert_copied_self_test('ninjagaiden2_x360', procedural_story())


class PrivateNativeIntegrityReportTests(CopiedSaveIntegrityAssertions, unittest.TestCase):
    @unittest.skipUnless(os.environ.get('NIOH3_NATIVE_DIR') and os.environ.get('NIOH3_ENCRYPTED_COPY'),
                         'Private native Nioh3 revisions and encrypted USER are not configured.')
    def test_native_nioh3_both_revisions_and_encrypted_context_are_preserved(self):
        from koei_editor.games.nioh3 import codec
        paths = []
        for path in Path(os.environ['NIOH3_NATIVE_DIR']).rglob('*'):
            if (path.is_file() and path.suffix.lower() == '.bin'
                    and path.stat().st_size == codec.USER_SIZE):
                with path.open('rb') as stream:
                    if stream.read(8) == b'RNNUSR\0\0':
                        paths.append(path)
        self.assertTrue(paths)
        revisions = set()
        paths.append(Path(os.environ['NIOH3_ENCRYPTED_COPY']))
        encrypted = 0
        for index, path in enumerate(paths):
            with self.subTest(fixture=index):
                raw = path.read_bytes()
                native = codec.decode(raw)
                revisions.add(native.revision)
                encrypted += native.encrypted
                self.assert_copied_self_test('nioh3', raw)
                self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(revisions, codec.SUPPORTED_REVISIONS)
        self.assertGreater(encrypted, 0)

    @unittest.skipUnless(os.environ.get('NGII_NATIVE_DIR'), 'Private native NGII stories are not configured.')
    def test_native_ngii_story_self_tests_preserve_full_raw_copies(self):
        from koei_editor.games.ninja_gaiden_ii import codec
        paths = tuple(path for path in Path(os.environ['NGII_NATIVE_DIR']).rglob('ng2stryd*.dat')
                      if path.is_file() and path.stat().st_size == codec.SAVE_SIZE)
        self.assertTrue(paths)
        for index, path in enumerate(paths):
            with self.subTest(fixture=index):
                raw = path.read_bytes()
                self.assert_copied_self_test('ninjagaiden2_x360', raw)
                self.assertEqual(path.read_bytes(), raw)
