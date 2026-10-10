"""Procedural envelope checks; no published player data or game-load claims."""
from dataclasses import replace
import os
from pathlib import Path
import struct
import unittest

from koei_editor.games.dw3.save_codec import CNG_AES
import koei_editor.research.stars.stars_candidate_codec as codec


def procedural_raw():
    """Independent fixture generator from the documented static arithmetic."""
    parts = []
    with CNG_AES('CBC') as aes:
        for index in (9, *range(9)):
            size = 0x79B66 if index == 9 else 0x78E41
            payload = (bytes(range(256)) * ((size + 255) // 256))[:size]
            padding = bytes([0xA0 + index]) * ((-size) % 16)
            value = (index + 1) * 0.5 / 10.0
            for _ in range(10):
                value = (1.0 - value) * (value * 3.66)
            state = struct.unpack('<I', struct.pack('<d', value)[:4])[0]
            key = bytearray()
            for _ in range(16):
                state = (state * 214013 + 2531011) & 0xFFFFFFFF
                key.append(state >> 24)
            seed = 0x76543210 + index
            state = seed
            iv = bytearray()
            for _ in range(16):
                state = (state * 22695477 + 1) & 0xFFFFFFFF
                iv.append((state >> 16) & 255)
            parts.append(aes.transform(payload + padding + b'FingerPrint01234',
                                       bytes(key), direction='encrypt', iv=bytes(iv))
                         + struct.pack('<I', seed))
    return b''.join(parts)


class StarsCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.raw = procedural_raw()
        except RuntimeError as error:
            raise unittest.SkipTest(str(error))
        cls.document = codec.inspect_candidate(cls.raw)

    def test_ten_blocks_and_nonzero_padding_preserved(self):
        doc = self.document
        self.assertEqual(len(doc.raw), 0x4B9D08)
        self.assertEqual([block.index for block in doc.blocks], [9, *range(9)])
        self.assertEqual(len(doc.blocks[0].payload), 0x79B66)
        for slot in doc.blocks[1:]:
            self.assertEqual(len(slot.payload), 0x78E41)
            self.assertEqual(slot.padding, bytes([0xA0 + slot.index]) * 15)
        self.assertEqual(codec.reencode_unchanged(doc), self.raw)
        for flag in ('native_fixture_verified', 'revision_verified', 'integrity_verified', 'writable'):
            self.assertFalse(getattr(doc, flag))

    def test_payload_padding_seed_and_order_mutations_rejected(self):
        block = self.document.blocks[0]
        mutations = (replace(block, payload=b'X' + block.payload[1:]),
                     replace(block, padding=b'X' + block.padding[1:]),
                     replace(block, iv_seed=block.iv_seed ^ 1))
        for changed in mutations:
            with self.subTest(changed=changed.index), self.assertRaises(ValueError):
                codec.reencode_unchanged(replace(self.document,
                                                blocks=(changed, *self.document.blocks[1:])))
        with self.assertRaises(ValueError):
            codec.reencode_unchanged(replace(self.document,
                                            blocks=tuple(reversed(self.document.blocks))))

    def test_forged_mutable_snapshots_rejected(self):
        doc = self.document
        for forged in (replace(doc, raw=bytearray(doc.raw)),
                       replace(doc, blocks=list(doc.blocks)),
                       replace(doc, blocks=(replace(doc.blocks[0],
                                                   payload=bytearray(doc.blocks[0].payload)),
                                            *doc.blocks[1:]))):
            with self.assertRaises(ValueError):
                codec.reencode_unchanged(forged)

    def test_bad_size_foreign_and_trailer_rejected(self):
        for value in (self.raw[:-1], self.raw + b'X', bytes(len(self.raw))):
            with self.assertRaises(ValueError):
                codec.inspect_candidate(value)
        for offset in (codec.SYSTEM_BLOCK_SIZE - 5, len(self.raw) - 5):
            damaged = bytearray(self.raw)
            damaged[offset] ^= 0x80
            with self.assertRaises(ValueError):
                codec.inspect_candidate(damaged)

    def test_sentinel_is_explicitly_not_full_payload_integrity(self):
        # CBC corruption far from the trailer leaves the sentinel intact.
        damaged = bytearray(self.raw)
        damaged[20] ^= 0x80
        candidate = codec.inspect_candidate(damaged)
        self.assertNotEqual(candidate.blocks[0].payload, self.document.blocks[0].payload)
        self.assertFalse(candidate.integrity_verified)
        self.assertFalse(candidate.writable)

    def test_parameter_validation(self):
        for value in (True, -1, 10, '0', None):
            with self.assertRaises(ValueError):
                codec.key_for_block(value)
        for value in (False, -1, 1 << 32, '0'):
            with self.assertRaises(ValueError):
                codec.iv_from_seed(value)
        with self.assertRaises(TypeError):
            codec.inspect_candidate('not a byte buffer')
        with self.assertRaises(TypeError):
            codec.reencode_unchanged(self.raw)

    def test_distinct_slot_keys_do_not_qualify_global_revision(self):
        self.assertEqual(codec.key_for_block(0).hex(), '830284a809ce8f8865cc668dd3cf29bd')
        self.assertEqual(codec.key_for_block(8).hex(), 'f3a06c0e5210e4f2c546bb96b6d11542')
        self.assertEqual(codec.key_for_block(9).hex(), '685e72a485f9b2fe4dbe386a94b2a921')
        self.assertNotEqual(codec.key_for_block(4), codec.key_for_block(9))
        self.assertEqual(len(set(codec.key_for_block(i) for i in range(10))), 10)


class OptionalNativeStarsTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('STARS_SAVE_COPY'), 'No genuine All-Stars PC save copy supplied')
    def test_copied_native_unchanged_roundtrip(self):
        # Keep source names, account data and save contents out of public output.
        raw = Path(os.environ['STARS_SAVE_COPY']).read_bytes()
        candidate = codec.inspect_candidate(raw)
        self.assertEqual(codec.reencode_unchanged(candidate), raw)
        self.assertFalse(candidate.writable)


if __name__ == '__main__':
    unittest.main()
