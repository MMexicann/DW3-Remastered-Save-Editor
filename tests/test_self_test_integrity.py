"""Copied-save reports distinguish checksums from plaintext/external signing."""
from pathlib import Path
import tempfile
import unittest

from koei_editor.shared.verified_self_test import run
from tests.test_dw9emp_format import procedural_raw
from tests.test_ps3_expansion import fixture, dw7, sw4
from tests.test_orochiz_format import procedural_raw as orochiz_raw
from tests.test_stars_format import procedural_raw as stars_raw


class SelfTestIntegrityTests(unittest.TestCase):
    def test_structural_roundtrip_does_not_claim_checksum_or_console_signing(self):
        cases = (('dw9emp', procedural_raw(), 'none'),
                 ('dw7_ps3', fixture(dw7), 'external'),
                 ('sw4_ps3', fixture(sw4), 'checksum'),
                 ('orochiz', orochiz_raw(), 'checksum'),
                 ('stars', stars_raw(), 'none'))
        for game_id, raw, integrity_kind in cases:
            with self.subTest(game=game_id), tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / ('copy.dat' if game_id == 'orochiz' else 'copy.bin')
                source.write_bytes(raw)
                report = run(game_id, source, Path(folder) / 'report')
                self.assertTrue(report['success'])
                self.assertTrue(report['unchanged_roundtrip'])
                self.assertTrue(report['input_preserved'])
                self.assertEqual(source.read_bytes(), raw)
                self.assertEqual(report['integrity_kind'], integrity_kind)
                self.assertEqual(report['checksum_verified'], integrity_kind == 'checksum')
                self.assertEqual(report['native_integrity_verified'], integrity_kind == 'checksum')
                self.assertFalse(report['in_game_load_tested'])


if __name__ == '__main__':
    unittest.main()
