"""Native-static envelope regressions; procedural inputs are not genuine saves."""
from dataclasses import replace
import unittest

from koei_editor.games.dw3.models import SaveError
import koei_editor.research.orochiz.orochiz_candidate_codec as codec


def procedural_raw():
    raw = bytearray((index * 13 + 7) & 255 for index in range(codec.SAVE_SIZE))
    raw[4:6] = (2).to_bytes(2, 'little')
    raw[codec.CHECKSUM_OFFSET:codec.CHECKSUM_OFFSET + 20] = (
        sum(raw[:codec.CHECKSUM_OFFSET]).to_bytes(4, 'little') + bytes(16))
    return bytes(raw)


class OrochiZCandidateTests(unittest.TestCase):
    def test_unchanged_roundtrip_and_identity_is_unverified(self):
        raw = procedural_raw()
        candidate = codec.inspect(raw)
        self.assertFalse(candidate.native_identity_verified)
        self.assertEqual(codec.unchanged(candidate), raw)

    def test_checksum_and_integrity_padding_reject_corruption(self):
        for offset in (0, 5000, codec.CHECKSUM_OFFSET - 1,
                       codec.CHECKSUM_OFFSET, codec.CHECKSUM_OFFSET + 4,
                       codec.CHECKSUM_OFFSET + 19):
            raw = bytearray(procedural_raw())
            raw[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(SaveError):
                codec.inspect(raw)

    def test_native_checksum_excludes_last_sixteen_bytes(self):
        raw = bytearray(procedural_raw())
        raw[-16:] = b'opaque trailer!!'
        candidate = codec.inspect(raw)
        self.assertEqual(codec.unchanged(candidate), raw)

    def test_revision_lengths_and_modified_metadata_rejected(self):
        raw = procedural_raw()
        for value in (raw[:-1], raw + b'0', b'', b'\0' * len(raw)):
            with self.assertRaises(SaveError):
                codec.inspect(value)
        wrong = bytearray(raw)
        wrong[4:6] = b'\x01\0'
        with self.assertRaises(SaveError):
            codec.inspect(wrong)
        candidate = codec.inspect(raw)
        with self.assertRaises(SaveError):
            codec.unchanged(replace(candidate, native_identity_verified=True))
