"""DW8 Empires codec qualification; no gameplay or in-game load claims."""
from dataclasses import replace
import os
from pathlib import Path
import struct
import unittest

import koei_editor.research.dw8e.dw8e_codec as codec
import koei_editor.research.dw8e.dw8e_candidate_codec as candidate
from koei_editor.shared.koei_codec import byte_cipher, word_cipher, word_sum


def generated(kind):
    size = codec.SIZES[kind]
    count = size - candidate.BODY_OFFSET - (kind == 'SystemSave')
    payload = codec.MAGIC + bytes((i * 67 + 3) & 255 for i in range(count - 4))
    body = (byte_cipher(payload, candidate.SYSTEM_BYTE_SEED)
            + bytes([sum(payload) & 255])) if kind == 'SystemSave' else payload
    header = bytearray((i * 31 + 11) & 255 for i in range(candidate.BODY_OFFSET))
    struct.pack_into('<HH', header, candidate.CHECKSUM_OFFSET, word_sum(body), 0x2F03)
    return bytes(header) + word_cipher(body, 0x2F03)


class DW8ENativeCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = {kind: generated(kind) for kind in codec.SIZES}

    def test_explicit_profile_exact_revision_and_noop_roundtrips(self):
        for kind, raw in self.fixtures.items():
            with self.subTest(kind=kind):
                document = codec.decode(raw, kind=kind)
                self.assertEqual(document.payload[:4], codec.MAGIC)
                self.assertEqual(codec.encode(document), raw)
                self.assertEqual(codec.encode(document, document.payload), raw)
                self.assertEqual(document.seed, 0x2F03)
                with self.assertRaises(ValueError):
                    codec.decode(raw, kind='BattleSave' if kind == 'SystemSave' else 'SystemSave')

    def test_raw_edit_is_surgical_and_preserves_unprotected_envelope(self):
        # This proves serialization only; offset 29 has no gameplay claim.
        for kind, raw in self.fixtures.items():
            document = codec.decode(raw, kind=kind)
            edited = bytearray(document.payload)
            edited[29] ^= 1
            changed = codec.encode(document, edited)
            self.assertEqual(codec.decode(changed, kind=kind).payload, bytes(edited))
            self.assertEqual(changed[:candidate.CHECKSUM_OFFSET], raw[:candidate.CHECKSUM_OFFSET])
            self.assertEqual(changed[candidate.SEED_OFFSET:candidate.BODY_OFFSET], raw[candidate.SEED_OFFSET:candidate.BODY_OFFSET])
            altered = bytearray(raw)
            altered[12] ^= 1  # Native checksum does not cover envelope metadata.
            self.assertEqual(codec.encode(codec.decode(altered, kind=kind)), altered)

    def test_checksum_size_kind_revision_and_type_rejection(self):
        raw = self.fixtures['SystemSave']
        for offset in (candidate.CHECKSUM_OFFSET, candidate.SEED_OFFSET, candidate.BODY_OFFSET, len(raw) - 1):
            altered = bytearray(raw)
            altered[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                codec.decode(altered, kind='SystemSave')
        for data in (raw[:-1], raw + b'x', 244952, True, list(raw[:5])):
            with self.assertRaises(ValueError):
                codec.decode(data, kind='SystemSave')
        for kind in ('systemsave', '', None, True):
            with self.assertRaises(ValueError):
                codec.decode(raw, kind=kind)
        document = codec.decode(raw, kind='SystemSave')
        wrong_revision = b'\0\0\0\0' + document.payload[4:]
        foreign_raw = candidate.decode_candidate(raw, kind='SystemSave').encode_candidate(wrong_revision)
        with self.assertRaisesRegex(ValueError, 'title/revision'):
            codec.decode(foreign_raw, kind='SystemSave')
        with self.assertRaises(ValueError):
            codec.encode(document, wrong_revision)

    def test_frozen_document_and_edited_payload_size_limits(self):
        raw = self.fixtures['SystemSave']
        mutable = bytearray(raw)
        document = codec.decode(memoryview(mutable), kind='SystemSave')
        mutable[0] ^= 1
        self.assertEqual(document.raw, raw)
        for forged in (replace(document, raw=bytearray(raw)),
                       replace(document, payload=bytearray(document.payload)),
                       replace(document, kind='BattleSave'),
                       replace(document, payload=document.payload[:-1] + bytes([document.payload[-1] ^ 1]))):
            with self.assertRaises(ValueError):
                codec.encode(forged)
        for payload in (1, True, document.payload[:-1], document.payload + b'x'):
            with self.assertRaises(ValueError):
                codec.encode(document, payload)

    @unittest.skipUnless(os.environ.get('DW8E_SAVE_FOLDER'), 'Private genuine PC save copies not configured.')
    def test_five_genuine_pc_profiles_roundtrip_and_raw_only_edit(self):
        root = Path(os.environ['DW8E_SAVE_FOLDER'])
        for name in ('SystemSave.dat', 'EmpireSave00.dat', 'EmpireSave01.dat', 'EmpireSave02.dat', 'QuickSave.dat'):
            kind = 'SystemSave' if name == 'SystemSave.dat' else 'BattleSave'
            source = root / name
            raw = source.read_bytes()
            document = codec.decode(raw, kind=kind)
            self.assertEqual(codec.encode(document), raw)
            edited = bytearray(document.payload)
            edited[29] ^= 1
            result = codec.encode(document, edited)
            self.assertEqual(codec.decode(result, kind=kind).payload, bytes(edited))
            self.assertEqual(source.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
