"""Procedural envelope checks and optional private genuine PS3 exports."""
from dataclasses import replace
import os
from pathlib import Path
import unittest

from koei_editor.research.dw8e_ps3 import codec
from koei_editor.shared.koei_codec import byte_cipher


def fixture(kind):
    payload = bytearray(codec.SIZES[kind] - (kind == 'system'))
    payload[:4] = codec.REVISION
    if kind == 'empire':
        for index in range(40):
            offset = 0x5BF4 + index * 0xE4
            payload[offset - 6:offset - 4] = index.to_bytes(2, 'little')
            for delta in (0, 4, 8):
                payload[offset + delta:offset + delta + 4] = (10 + index + delta).to_bytes(4, 'little')
    payload = bytes(payload)
    return (byte_cipher(payload, codec.SYSTEM_SEED) + bytes([sum(payload) & 255])
            if kind == 'system' else payload)


class DW8EmpiresPS3CodecTests(unittest.TestCase):
    def test_explicit_profiles_roundtrip_surgical_research_edit_and_readonly_rows(self):
        for kind in ('system', 'empire'):
            raw = fixture(kind)
            document = codec.decode(raw, kind=kind)
            self.assertEqual(codec.encode(document), raw)
            changed = bytearray(document.payload)
            changed[0x5BF4] ^= 1
            output = codec.encode(document, bytes(changed))
            self.assertEqual(codec.decode(output, kind=kind).payload, bytes(changed))
            rows = codec.resource_candidates(document)
            self.assertEqual(len(rows), 40 if kind == 'empire' else 0)
            if rows:
                self.assertEqual(rows[4].ordinal, 4)
                self.assertEqual(rows[4].candidate_materials, 14)
                self.assertEqual(rows[4].second_value, 18)
                self.assertFalse(any(row.editable for row in rows))
        for unsafe in ('stage', 'maximums', 'save_as', 'read_save', 'restore'):
            self.assertFalse(hasattr(codec, unsafe))

    def test_malformed_profile_revision_checksum_mutability_and_pc_sizes_reject(self):
        for kind in ('system', 'empire'):
            raw = fixture(kind)
            for bad in (bytearray(raw), raw[:-1], raw + b'\0', b'\0' * len(raw),
                        b'\0' * (244952 if kind == 'system' else 1083236)):
                with self.subTest(kind=kind, size=len(bad)), self.assertRaises(ValueError):
                    codec.decode(bad, kind=kind)
            document = codec.decode(raw, kind=kind)
            for bad in (replace(document, payload=bytearray(document.payload)),
                        replace(document, raw=bytearray(raw)), replace(document, kind=True)):
                with self.assertRaises(ValueError):
                    codec.encode(bad)
            with self.assertRaises(ValueError):
                codec.encode(document, bytearray(document.payload))
        raw = bytearray(fixture('system'))
        raw[-1] ^= 1
        with self.assertRaises(ValueError):
            codec.decode(bytes(raw), kind='system')
        for kind in (None, True, 'auto', 'SystemSave'):
            with self.assertRaises(ValueError):
                codec.decode(b'', kind=kind)

    def test_optional_genuine_us_system_and_empire_exports(self):
        found = 0
        for kind, variable in (('system', 'DW8E_PS3_SYSTEM_COPY'), ('empire', 'DW8E_PS3_EMPIRE_COPY')):
            path = os.environ.get(variable)
            if not path:
                continue
            found += 1
            raw = Path(path).read_bytes()
            document = codec.decode(raw, kind=kind)
            self.assertEqual(codec.encode(document), raw)
            changed = bytearray(document.payload)
            changed[-16] ^= 1
            self.assertEqual(codec.decode(codec.encode(document, bytes(changed)), kind=kind).payload,
                             bytes(changed))
        if not found:
            self.skipTest('No private genuine PS3 DW8 Empires fixtures supplied.')
