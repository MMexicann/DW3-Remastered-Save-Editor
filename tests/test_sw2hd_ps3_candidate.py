"""Synthetic diagnostic tests; not genuine-file or gameplay qualification."""
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.research.sw2hd_ps3 import inspection


class SW2HDSourceCandidateTests(unittest.TestCase):
    def test_checksum_fact_big_endian_money_and_no_edit_support(self):
        raw = bytearray(inspection.MIN_CANDIDATE_SIZE + 20)
        raw[inspection.MONEY_OFFSET:inspection.MONEY_OFFSET + 4] = (123456).to_bytes(4, 'big')
        start, end = inspection.CHECKSUM_RANGE
        checksum = sum(raw[start:end])
        for offset in inspection.CHECKSUM_OFFSETS:
            raw[offset:offset + 4] = checksum.to_bytes(4, 'big')
        before = bytes(raw)
        result = inspection.inspect(before)
        self.assertEqual(result.candidate_money, 123456)
        self.assertEqual(result.expected_byte_sum, checksum)
        self.assertTrue(result.checksums_match)
        self.assertFalse(result.editable)
        self.assertFalse(result.qualified_game_profile)
        self.assertEqual(bytes(raw), before)
        raw[8] ^= 1
        self.assertFalse(inspection.inspect(bytes(raw)).checksums_match)
        for operation in ('stage', 'serialize', 'save_as', 'maximums'):
            self.assertFalse(hasattr(inspection, operation))

    def test_bounded_frozen_input_rejection(self):
        for raw in (b'', b'\0' * (inspection.MIN_CANDIDATE_SIZE - 1),
                    b'\0' * (inspection.MAX_CANDIDATE_SIZE + 1),
                    bytearray(inspection.MIN_CANDIDATE_SIZE)):
            with self.assertRaises(SaveError):
                inspection.inspect(raw)
