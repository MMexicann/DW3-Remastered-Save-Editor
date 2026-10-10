"""Envelope tests; procedural data does not qualify gameplay or game loading."""
from functools import lru_cache
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import origins_codec as codec


@lru_cache(maxsize=2)
def procedural_raw(kind):
    # Independently expressed arithmetic, with recognizable unknown bytes.
    size = codec.FILE_SIZES[kind] - 4
    plain = (bytes(range(256)) * ((size + 255) // 256))[:size]
    seed = 0xa761
    checksum = sum(int.from_bytes(plain[i:i+2], "little")
                   for i in range(0, size, 2)) % 65536
    encrypted = bytearray(size)
    state = seed
    for index in range(0, size, 4):
        state = (1528461393 * state + 52814) % (2 ** 32)
        value = int.from_bytes(plain[index:index+4], "little") ^ state
        encrypted[index:index+4] = value.to_bytes(4, "little")
    return struct.pack("<HH", checksum, seed) + encrypted, plain


class NativeEnvelopeTests(unittest.TestCase):
    def test_independent_reference_and_noop_roundtrip(self):
        for kind in ("slot", "user"):
            with self.subTest(kind=kind):
                raw, plain = procedural_raw(kind)
                original = bytes(raw)
                envelope = codec.decode(raw, kind)
                self.assertEqual(envelope.payload, plain)
                self.assertEqual(envelope.kind, kind)
                self.assertEqual(codec.encode(plain, envelope.seed, kind), raw)
                self.assertEqual(raw, original)

    def test_surgical_edit_preserves_unknown_data_and_seed(self):
        raw, plain = procedural_raw("slot")
        original = codec.decode(raw)
        changed = bytearray(plain)
        changed[0x10a1] ^= 1
        encoded = codec.encode(changed, original.seed, original.kind)
        reopened = codec.decode(encoded)
        self.assertEqual(reopened.payload, changed)
        self.assertEqual(reopened.seed, original.seed)
        differences = [i for i, (a, b) in enumerate(zip(raw, encoded)) if a != b]
        self.assertEqual(differences, [1, 0x10a1 + 4])
        self.assertEqual(raw, procedural_raw("slot")[0])

    def test_corruption_rejected_without_repair(self):
        raw, _ = procedural_raw("user")
        for offset in (0, 4, 0x500, len(raw) - 1):
            with self.subTest(offset=offset):
                corrupt = bytearray(raw)
                corrupt[offset] ^= 1
                with self.assertRaises(codec.SaveFormatError):
                    codec.decode(corrupt)

    def test_truncation_and_wrong_kind_rejected(self):
        raw, plain = procedural_raw("user")
        for invalid in (raw[:4], raw[:-1], raw + b"\0", b"GVAS" + raw):
            with self.assertRaises(codec.SaveFormatError):
                codec.decode(invalid)
        with self.assertRaises(codec.SaveFormatError):
            codec.decode(raw, "slot")
        with self.assertRaises(codec.SaveFormatError):
            codec.decode(raw, "guess")
        with self.assertRaises(codec.SaveFormatError):
            codec.encode(plain, 1, "slot")

    def test_unverified_parameters_rejected(self):
        _, plain = procedural_raw("user")
        for seed in (-1, 65536, True, 1.5):
            with self.subTest(seed=seed), self.assertRaises(codec.SaveFormatError):
                codec.encode(plain, seed, "user")
        with self.assertRaises(codec.SaveFormatError):
            codec.encode(plain, 2, "user", steps=2)
        with self.assertRaises(codec.SaveFormatError):
            codec.word_cipher(b"abc", 2)

    def test_related_game_three_step_stream_rejected(self):
        raw, plain = procedural_raw("user")
        from koei_codec import word_cipher
        foreign = raw[:4] + word_cipher(plain, int.from_bytes(raw[2:4], "little"))
        with self.assertRaises(codec.SaveFormatError):
            codec.decode(foreign)

    def test_copied_native_envelope_roundtrip(self):
        value = os.environ.get("ORIGINS_SAVE_COPY")
        if not value:
            self.skipTest("Set ORIGINS_SAVE_COPY to a privately reviewed copied native save.")
        raw = Path(value).read_bytes()
        original = codec.decode(raw)
        self.assertEqual(codec.encode(original.payload, original.seed, original.kind), raw)
        self.assertEqual(Path(value).read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
