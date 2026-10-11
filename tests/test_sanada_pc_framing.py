"""Framing evidence only: these tests do not qualify gameplay editing."""
from dataclasses import replace
import os
from pathlib import Path
import struct
import unittest

from koei_editor.research.sw_sanada import codec
from koei_editor.shared.koei_codec import word_cipher, word_sum


def procedural_raw(kind="system", seed=0xCDEF):
    # Distinct opaque bytes exercise preservation; this is not a playable save.
    payload = bytearray(bytes(range(256)) * ((codec.FILE_SIZES[kind] - 4) // 256))
    struct.pack_into("<II", payload, 0, *codec.OBSERVED_PREFIX)
    return struct.pack("<HH", word_sum(payload), seed) + word_cipher(payload, seed)


class SanadaFramingTests(unittest.TestCase):
    def test_unchanged_seed_and_unknown_bytes(self):
        raw = procedural_raw()
        document = codec.inspect(raw, kind="system")
        self.assertEqual(document.seed, 0xCDEF)
        self.assertEqual(codec.unchanged_roundtrip(document), raw)
        self.assertEqual(document.payload[8:264], (bytes(range(256)) * 2)[8:264])

    def test_mutable_input_copied_and_invalid_types_rejected(self):
        raw = bytearray(procedural_raw())
        document = codec.inspect(raw, kind="system")
        original = bytes(raw)
        raw[20] ^= 1
        self.assertEqual(document.raw, original)
        self.assertEqual(codec.unchanged_roundtrip(document), original)
        for kind in ([], {}, None, 1):
            with self.subTest(kind=kind), self.assertRaises(codec.FramingError):
                codec.inspect(original, kind=kind)
        for raw in (None, "copy.dat", 123):
            with self.subTest(raw=raw), self.assertRaises(codec.FramingError):
                codec.inspect(raw, kind="system")

    def test_corruption_truncation_and_class_rejected(self):
        raw = procedural_raw()
        for changed in (raw[:-1], raw + b"\0", raw[:8] + bytes([raw[8] ^ 1]) + raw[9:]):
            with self.subTest(size=len(changed)), self.assertRaises(codec.FramingError):
                codec.inspect(changed, kind="system")
        for kind in ("gameplay", "auto", "samurai4dx"):
            with self.subTest(kind=kind), self.assertRaises(codec.FramingError):
                codec.inspect(raw, kind=kind)

    def test_checksum_valid_foreign_prefix_rejected(self):
        document = codec.inspect(procedural_raw(), kind="system")
        payload = bytes(8) + document.payload[8:]
        raw = struct.pack("<HH", word_sum(payload), document.seed) + word_cipher(payload, document.seed)
        with self.assertRaises(codec.FramingError):
            codec.inspect(raw, kind="system")

    def test_research_payload_cannot_be_written(self):
        document = codec.inspect(procedural_raw(), kind="system")
        changed = replace(document, payload=document.payload[:100] + b"\0" + document.payload[101:])
        with self.assertRaises(codec.FramingError):
            codec.unchanged_roundtrip(changed)
        with self.assertRaises(codec.FramingError):
            codec.unchanged_roundtrip(replace(document, seed=0))


class GenuineSanadaFramingTests(unittest.TestCase):
    def test_publicly_shared_complete_native_copies(self):
        location = os.environ.get("SANADA_PC_SAVE_COPIES")
        if not location:
            self.skipTest("No private copied Sanada PC SAVEDATA folder selected.")
        folder = Path(location)
        names = (("SAVEDATA0000.dat", "gameplay"), ("SAVEDATA0001.dat", "gameplay"),
                 ("SYSDATA.dat", "system"))
        for name, kind in names:
            with self.subTest(kind=kind, slot=name):
                raw = (folder / name).read_bytes()
                document = codec.inspect(raw, kind=kind)
                self.assertEqual(codec.unchanged_roundtrip(document), raw)
                self.assertEqual(struct.unpack_from("<I", document.payload, 0x100)[0],
                                 0x846 if kind == "gameplay" else 0x10)


if __name__ == "__main__":
    unittest.main()
