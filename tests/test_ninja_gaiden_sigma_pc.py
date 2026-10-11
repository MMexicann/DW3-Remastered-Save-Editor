"""Bounded Sigma1 PC research shape tests; no gameplay support is inferred."""
from dataclasses import replace
import os
from pathlib import Path
import struct
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.research.ninja_gaiden_sigma_pc import inspection as backend


def procedural_sigma():
    """Distinct generated diagnostic bytes, not a genuine gameplay save."""
    raw = bytearray((index * 73 + 17) & 255 for index in range(backend.SIZE))
    raw[:0x200] = bytes(0x200)
    title = 'Game Save'.encode('utf-16le')
    description = '1 / 2 / 0 / 4294967295 / 23 / 9 / 0'.encode('utf-16le')
    raw[:len(title)] = title
    raw[0x100:0x100 + len(description)] = description
    return bytes(raw)


class SigmaPCInspectionTests(unittest.TestCase):
    def test_exact_unmodified_envelope_with_explicit_unqualified_integrity(self):
        raw = procedural_sigma()
        result = backend.inspect(raw)
        self.assertEqual(result.native, raw[backend.PREAMBLE_SIZE:])
        self.assertEqual(result.native_prefix_words, struct.unpack_from('<8I', raw, backend.PREAMBLE_SIZE))
        self.assertEqual(result.description_values, (1, 2, 0, 4294967295, 23, 9, 0))
        self.assertIsNone(result.revision)
        self.assertFalse(result.qualified_game_profile)
        self.assertFalse(result.integrity_verified)
        self.assertFalse(result.writable)
        self.assertEqual(backend.encode(result), raw)

    def test_malformed_sizes_descriptions_and_other_editions_are_rejected(self):
        raw = procedural_sigma()
        variants = [raw[:-1], raw + b'\0', bytes(backend.SIZE), bytes(35968),
                    b'GVAS' + raw[4:], None, bytearray(raw)]
        for region in ((0, 'System Save'), (0x100, '1 / 2'), (0x100, '-1 / 2 / 0 / 1 / 2 / 3 / 4')):
            broken = bytearray(raw)
            at, text = region
            broken[at:at + 0x100] = bytes(0x100)
            encoded = text.encode('utf-16le')
            broken[at:at + len(encoded)] = encoded
            variants.append(bytes(broken))
        broken = bytearray(raw)
        broken[0x100:0x200] = b'A\0' * 128  # no terminator
        variants.append(bytes(broken))
        broken = bytearray(raw)
        broken[0x100:0x104] = b'\x00\xD8\0\0'  # unmatched UTF-16 surrogate
        variants.append(bytes(broken))
        for malformed in variants:
            with self.subTest(length=len(malformed) if malformed is not None else None), self.assertRaises(SaveError):
                backend.inspect(malformed)

    def test_body_corruption_does_not_become_integrity_validation_or_edit_permission(self):
        raw = procedural_sigma()
        document = backend.inspect(raw)
        altered = bytearray(raw)
        altered[0x11000] ^= 1
        altered = bytes(altered)
        self.assertFalse(backend.inspect(altered).integrity_verified)
        with self.assertRaisesRegex(SaveError, 'inspection-only'):
            backend.encode(document, altered)
        with self.assertRaises(SaveError):
            backend.encode(replace(document, integrity_verified=True))
        with self.assertRaises(SaveError):
            backend.encode(replace(document, native=altered[backend.PREAMBLE_SIZE:]))
        with self.assertRaises(SaveError):
            backend.encode(document, bytearray(raw))

    def test_equal_mutable_or_coerced_snapshot_fields_are_rejected(self):
        document = backend.inspect(procedural_sigma())
        forged = [
            replace(document, raw=bytearray(document.raw)),
            replace(document, native=bytearray(document.native)),
            replace(document, native=memoryview(document.native)),
            replace(document, description_values=list(document.description_values)),
            replace(document, native_prefix_words=list(document.native_prefix_words)),
            replace(document, description_values=(True,) + document.description_values[1:]),
            replace(document, description_values=tuple(float(value) for value in document.description_values)),
            replace(document, native_prefix_words=tuple(float(value) for value in document.native_prefix_words)),
            replace(document, revision=0),
            replace(document, revision=False),
        ]
        for flag in ('integrity_verified', 'writable', 'qualified_game_profile'):
            for value in (0, 0.0):
                forged.append(replace(document, **{flag: value}))
        for index, snapshot in enumerate(forged):
            with self.subTest(index=index), self.assertRaises(SaveError):
                backend.encode(snapshot)
        self.assertEqual(backend.encode(document), document.raw)

    @unittest.skipUnless(os.environ.get('SIGMA_PC_NATIVE_DIR'), 'private genuine Sigma PC copies not selected')
    def test_genuine_original_pc_gameplay_roundtrip_distinct_from_native_integrity(self):
        paths = list(Path(os.environ['SIGMA_PC_NATIVE_DIR']).rglob('*SAVEDATA.DAT'))
        self.assertTrue(paths)
        for path in paths:
            raw = path.read_bytes()
            document = backend.inspect(raw)
            self.assertEqual(backend.encode(document), raw)
            self.assertFalse(document.integrity_verified)
            self.assertFalse(document.writable)
            with self.assertRaises(SaveError):
                backend.encode(document, raw[:-1] + bytes([raw[-1] ^ 1]))
            self.assertEqual(path.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
