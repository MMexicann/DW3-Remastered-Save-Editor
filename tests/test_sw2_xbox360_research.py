"""Procedural diagnostics and optional genuine extracted-file observations."""
import os
from pathlib import Path
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.research.sw2_xbox360 import inspection


def procedural_candidate():
    raw = bytearray((index * 29 + 17) & 255 for index in range(inspection.OBSERVED_EXPORT_SIZE))
    first = sum(raw[slice(*inspection.FIRST_RANGE)]) & 0xFFFFFFFF
    second = sum(raw[slice(*inspection.SECOND_CANDIDATE_RANGE)]) & 0xFFFFFFFF
    for offset, value in zip(inspection.CHECKSUM_OFFSETS, (first, second, (first + second) & 0xFFFFFFFF)):
        raw[offset:offset + 4] = value.to_bytes(4, 'big')
    raw[inspection.TRAILER_OFFSET:inspection.TRAILER_OFFSET + 4] = b'\x00\x01\x02\x03'
    return bytes(raw)


class SW2XboxResearchTests(unittest.TestCase):
    def test_diagnostic_only_and_immutable(self):
        raw = procedural_candidate()
        original = bytes(raw)
        result = inspection.inspect(raw)
        self.assertEqual(result.section_matches, (True, True))
        self.assertTrue(result.total_matches)
        self.assertTrue(result.observed_trailer_present)
        self.assertFalse(result.qualified_game_profile)
        self.assertFalse(result.complete_integrity_qualified)
        self.assertFalse(result.editable)
        self.assertEqual(raw, original)
        for operation in ('read_save', 'fields_for', 'stage', 'serialize', 'save_as', 'restore'):
            self.assertFalse(hasattr(inspection, operation), operation)

    def test_corruption_and_explicitly_unchecked_regions(self):
        original = procedural_candidate()
        for offset, expected in ((inspection.FIRST_RANGE[0], (False, True)),
                                 (inspection.SECOND_CANDIDATE_RANGE[0], (True, False))):
            damaged = bytearray(original)
            damaged[offset] ^= 1
            result = inspection.inspect(bytes(damaged))
            self.assertEqual(result.section_matches, expected)
            self.assertFalse(result.total_matches)
        damaged = bytearray(original)
        damaged[inspection.CHECKSUM_OFFSETS[2]] ^= 1
        result = inspection.inspect(bytes(damaged))
        self.assertEqual(result.section_matches, (True, True))
        self.assertFalse(result.total_matches)
        # An unchanged candidate match must not pretend to cover native header,
        # padding or all remaining integrity dependencies.
        for offset in (0, inspection.TRAILER_OFFSET + 1, len(original) - 1):
            changed = bytearray(original)
            changed[offset] ^= 1
            result = inspection.inspect(bytes(changed))
            self.assertEqual(result.section_matches, (True, True))
            self.assertTrue(result.total_matches)
            self.assertFalse(result.complete_integrity_qualified)

    def test_bounded_input(self):
        raw = procedural_candidate()
        for bad in (None, bytearray(raw), raw[:-1], raw + b'\x00', b'CON ' + raw):
            with self.assertRaises(SaveError):
                inspection.inspect(bad)

    def test_optional_genuine_observations(self):
        value = os.environ.get('SW2_XBOX360_EXPORT_COPY')
        if not value:
            self.skipTest('SW2_XBOX360_EXPORT_COPY is not set; no genuine file supplied.')
        path = Path(value)
        raw = path.read_bytes()
        result = inspection.inspect(raw)
        self.assertEqual(result.section_matches, (True, True))
        self.assertTrue(result.total_matches)
        self.assertTrue(result.observed_trailer_present)
        self.assertFalse(result.complete_integrity_qualified)
        self.assertFalse(result.editable)
        self.assertEqual(path.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
