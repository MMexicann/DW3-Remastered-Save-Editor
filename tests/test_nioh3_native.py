"""Procedural/native-fixture qualification; no unsupported Nioh 3 gameplay writes."""
from dataclasses import replace
import hashlib
import os
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from models import SaveError
import nioh3_native as native


def procedural_raw():
    payload = bytearray(native.USER_SIZE)
    payload[:8] = b'RNNUSR\0\0'
    struct.pack_into('<I', payload, 8, 0x01040000)
    struct.pack_into('<II', payload, 0x18, native.HEADER_SIZE, native.USER_SIZE-native.HEADER_SIZE)
    struct.pack_into('<I', payload, 0x15c, 0x01040000)
    return payload


class Nioh3NativeTests(unittest.TestCase):
    def test_independent_signed_qword_boundary_vectors(self):
        payload = procedural_raw()
        for value, expected in ((0, 0), (1, 1), (-2, 0xfffffffe), (-(1 << 63), 0x80000000)):
            struct.pack_into('<q', payload, native.BODY_START, value)
            self.assertEqual(native.body_checksum(payload), expected)
        # An even number of all-zero blocks cancels the XOR of a constant seed.
        struct.pack_into('<q', payload, native.BODY_START, 0)
        struct.pack_into('<I', payload, native.CHECKSUM_SEED_OFFSET, 0x12345678)
        self.assertEqual(native.body_checksum(payload), 0)

    def test_exact_noop_and_all_gameplay_writes_rejected(self):
        raw = bytes(procedural_raw())
        document = native.decode_plaintext(raw)
        self.assertTrue(document.integrity_verified)
        self.assertFalse(document.writable)
        self.assertEqual(hashlib.sha256(native.serialize(document, {})).digest(),
                         hashlib.sha256(raw).digest())
        with self.assertRaises(SaveError):
            native.serialize(document, {'gold':999})
        with self.assertRaises(SaveError):
            native.serialize(replace(document, payload=raw[:-1]+b'\1'), {})
        with self.assertRaises(SaveError):
            native.serialize(replace(document, payload=bytearray(raw)), {})
        with self.assertRaises(SaveError):
            native.serialize(replace(document, encrypted=0), {})

    def test_foreign_system_revision_lengths_and_corrupt_body_rejected(self):
        raw = procedural_raw()
        for offset, value in ((0, b'RNNSYS\0\0'), (8, struct.pack('<I', 0x01050000)),
                              (0x15c, struct.pack('<I', 0x01030001)),
                              (0x18, struct.pack('<I', 0x148)),
                              (native.BODY_START, b'\1'), (native.CHECKSUM_OFFSET, b'\1')):
            changed = bytearray(raw)
            changed[offset:offset+len(value)] = value
            with self.subTest(offset=hex(offset)), self.assertRaises(SaveError):
                native.decode_plaintext(changed)
        for value in (b'', raw[:-1], raw+b'\0', 'not binary', None):
            with self.assertRaises(SaveError):
                native.decode_plaintext(value)
        with patch.object(native.katana_codec, '_nioh_decrypt') as body_decoder:
            with self.assertRaises(SaveError):
                native.decode(bytes(native.USER_SIZE))
            body_decoder.assert_not_called()

    @unittest.skipUnless(os.environ.get('NIOH3_NATIVE_DIR'), 'Private native Nioh 3 user copies not configured.')
    def test_genuine_native_user_copies_checksum_roundtrip_and_corruption(self):
        folder = Path(os.environ['NIOH3_NATIVE_DIR'])
        copies = []
        for path in folder.rglob('*'):
            if path.is_file() and path.suffix.lower() == '.bin' and path.stat().st_size == native.USER_SIZE:
                with path.open('rb') as stream:
                    if stream.read(8) == b'RNNUSR\0\0':
                        copies.append(path)
        self.assertTrue(copies)
        for path in copies:
            raw = path.read_bytes()
            document = native.decode_plaintext(raw)
            self.assertEqual(hashlib.sha256(native.serialize(document, {})).digest(),
                         hashlib.sha256(raw).digest())
            corrupted = bytearray(raw)
            corrupted[native.BODY_START] ^= 1
            with self.assertRaises(SaveError):
                native.decode_plaintext(corrupted)
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), hashlib.sha256(raw).digest())

    @unittest.skipUnless(os.environ.get('NIOH3_ENCRYPTED_COPY') and os.environ.get('NIOH3_DECRYPTED_COPY'),
                         'Private native Nioh 3 encrypted/decrypted pair not configured.')
    def test_genuine_encrypted_pair_preserves_wrapped_keys_tail_and_body(self):
        raw = Path(os.environ['NIOH3_ENCRYPTED_COPY']).read_bytes()
        expected = Path(os.environ['NIOH3_DECRYPTED_COPY']).read_bytes()
        document = native.decode(raw)
        self.assertTrue(document.encrypted)
        self.assertTrue(document.integrity_verified)
        self.assertFalse(document.writable)
        self.assertEqual(hashlib.sha256(document.payload[:0x49]).digest(),
                         hashlib.sha256(expected[:0x49]).digest())
        self.assertEqual(hashlib.sha256(document.payload[0x89:]).digest(),
                         hashlib.sha256(expected[0x89:]).digest())
        self.assertEqual(expected[0x49:0x89], bytes(64))
        self.assertEqual(document.payload[-8:], raw[-8:])
        self.assertEqual(hashlib.sha256(native.serialize(document, {})).digest(),
                         hashlib.sha256(raw).digest())


if __name__=='__main__':
    unittest.main()
