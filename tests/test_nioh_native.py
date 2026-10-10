"""Nioh PC inspection qualification; procedural fixtures are not player saves."""
from dataclasses import replace
from functools import lru_cache
import os
from pathlib import Path
import struct
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.research.nioh import nioh_native as inspector


@lru_cache(maxsize=1)
def procedural_user():
    raw = bytearray((index * 29 + 7) & 255 for index in range(inspector.USER_SIZE))
    raw[:8] = b'NIOHUSR\0'
    struct.pack_into('<I', raw, 8, inspector.REVISION)
    struct.pack_into('<II', raw, 0x14, inspector.HEADER_SIZE, inspector.USER_BODY_SIZE)
    struct.pack_into('<I', raw, inspector.HEADER_SIZE + 8, inspector.REVISION)
    for offset in inspector.INTEGRITY_FLAG_OFFSETS:
        raw[offset] = 1
    return bytes(raw)


class NiohNativeInspectionTests(unittest.TestCase):
    def test_noop_snapshot_preserves_every_byte_and_exposes_no_gameplay_fields(self):
        document = inspector.decode(procedural_user())
        self.assertEqual(inspector.serialize(document, {}), procedural_user())
        self.assertEqual(inspector.fields_for(document), ())
        self.assertFalse(document.writable)
        self.assertFalse(document.integrity_verified)
        self.assertEqual(len(inspector.inspection_rows(document)), 11)
        self.assertFalse(any('account' in row['label'].lower()
                             for row in inspector.inspection_rows(document)))

    def test_decoder_freezes_mutable_input(self):
        raw = bytearray(procedural_user())
        document = inspector.decode(raw)
        raw[inspector.INTEGRITY_FLAG_OFFSETS[0]] = 0
        self.assertIs(type(document.raw), bytes)
        self.assertEqual(inspector.serialize(document, {}), procedural_user())

    def test_wrong_game_system_title_revision_length_and_flags_rejected(self):
        for invalid in (b'', procedural_user()[:-1], procedural_user() + b'\0'):
            with self.assertRaises(SaveError):
                inspector.decode(invalid)
        for offset, replacement in (
                (0, b'NIOHSYS\0'), (8, struct.pack('<I', 0x21030200)),
                (0x14, struct.pack('<I', 0x158)),
                (0x18, struct.pack('<I', inspector.USER_BODY_SIZE - 1)),
                (0x150, struct.pack('<I', 0x21030200)),
                (inspector.INTEGRITY_FLAG_OFFSETS[0], b'\x02')):
            data = bytearray(procedural_user())
            data[offset:offset + len(replacement)] = replacement
            with self.subTest(offset=offset), self.assertRaises(SaveError):
                inspector.decode(data)
        for game in ('nioh2', 'nioh3', 'nioh_ps4', 'guess'):
            with self.assertRaises(SaveError):
                inspector.decode(procedural_user(), game)

    def test_every_gameplay_write_and_bypass_rejected(self):
        document = inspector.decode(procedural_user())
        for changes in ({'gold': 1}, {'level': 750}, {'disable_integrity': 1}, [], None):
            with self.subTest(changes=changes), self.assertRaisesRegex(SaveError, 'not mapped'):
                inspector.serialize(document, changes)
        data = bytearray(procedural_user())
        for offset in inspector.INTEGRITY_FLAG_OFFSETS:
            data[offset] = 0
        zero_flags = inspector.decode(data)
        self.assertFalse(zero_flags.writable)
        self.assertEqual(inspector.serialize(zero_flags, {}), bytes(data))
        with self.assertRaises(SaveError):
            inspector.serialize(zero_flags, {'gold': 1})

    def test_unknown_body_damage_is_never_claimed_checksum_valid(self):
        data = bytearray(procedural_user())
        data[0x148] ^= 1
        document = inspector.decode(data)
        self.assertFalse(document.integrity_verified)
        self.assertFalse(document.writable)
        self.assertEqual(inspector.serialize(document, {}), bytes(data))

    def test_forged_mutable_or_inconsistent_document_rejected(self):
        document = inspector.decode(procedural_user())
        for forged in (replace(document, raw=bytearray(document.raw)),
                       replace(document, payload=bytearray(document.payload)),
                       replace(document, encrypted=0),
                       replace(document, encrypted=True),
                       replace(document, payload=document.payload[:-1])):
            with self.subTest(encrypted=forged.encrypted), self.assertRaises(SaveError):
                inspector.serialize(forged, {})

    def test_copy_paths_reject_live_resolved_aliases_and_wrong_suffix(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'copy.bin'
            source.write_bytes(procedural_user())
            self.assertEqual(inspector.read_save(source).raw, procedural_user())
            wrong = root / 'copy.dat'
            wrong.write_bytes(procedural_user())
            with self.assertRaises(SaveError):
                inspector.read_save(wrong)
            live = root / 'KoeiTecmo' / 'NIOH' / 'Savedata'
            live.mkdir(parents=True)
            native = live / 'SAVEDATA.BIN'
            native.write_bytes(procedural_user())
            with self.assertRaisesRegex(SaveError, 'separate copy'):
                inspector.read_save(native)
            alias = root / 'alias.bin'
            try:
                alias.symlink_to(native)
            except (OSError, NotImplementedError):
                return
            with self.assertRaises(SaveError):
                inspector.read_save(alias)
        with self.assertRaises(SaveError):
            inspector._copy_path(r'C:\Users\Player\Documents\KoeiTecmo\NIOH\Savedata\SAVEDATA.BIN')


@unittest.skipUnless(os.environ.get('NIOH_SAVE_COPY'), 'No explicit native Nioh PC USER copy')
class ExplicitNativeNiohInspectionTests(unittest.TestCase):
    def test_genuine_copy_retains_flags_and_has_exact_unchanged_cipher_roundtrip(self):
        from koei_editor.research.katana import katana_codec
        document = inspector.read_save(os.environ['NIOH_SAVE_COPY'])
        self.assertEqual(inspector.serialize(document, {}), document.raw)
        encoded = katana_codec._nioh_encrypt(document.payload, katana_codec.PROFILES['nioh'])
        reopened = inspector.decode(encoded)
        self.assertEqual(reopened.payload, document.payload)
        if document.encrypted:
            self.assertEqual(encoded, document.raw)
        self.assertEqual([document.payload[o] for o in inspector.INTEGRITY_FLAG_OFFSETS],
                         [reopened.payload[o] for o in inspector.INTEGRITY_FLAG_OFFSETS])
        self.assertFalse(reopened.writable)


if __name__ == '__main__':
    unittest.main()
