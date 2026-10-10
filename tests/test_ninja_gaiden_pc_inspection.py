"""Unregistered research tests; procedural evidence is distinct from native copies."""
from dataclasses import replace
import os
from pathlib import Path
import struct
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.research.ninja_gaiden_2_black import inspection as black
from koei_editor.research.ninja_gaiden_sigma2_pc import inspection as sigma2


def native_story():
    data = bytearray((i * 37 + 11) & 255 for i in range(sigma2.NATIVE_SIZE))
    struct.pack_into('<II', data, 0, sigma2.NATIVE_SIZE, 6)
    struct.pack_into('<I', data, 0xC, sigma2.metadata_crc(data[0x10:0x1C]))
    return bytes(data)


def procedural_sigma2():
    header = bytearray(sigma2.PREAMBLE_SIZE)
    for offset, text in ((0, 'Saved Game / CHAPTER 1 CHECK POINT'), (0x100, 'CHAPTER 1-1'),
                         (0x200, 'PATH OF THE WARRIOR')):
        value = text.encode('utf-16le')
        header[offset:offset + len(value)] = value
    return bytes(header) + native_story()


def string(text):
    value = text.encode('utf-8') + b'\0'
    return struct.pack('<i', len(value)) + value


def property_tag(name, text=None, data=None):
    if data is not None:
        typ = string('ArrayProperty') + struct.pack('<I', 1) + string('ByteProperty') + bytes(4)
        value = struct.pack('<I', len(data)) + data
    else:
        typ = string('StrProperty') + bytes(4)
        value = string(text)
    return string(name) + typ + struct.pack('<I', len(value)) + b'\0' + value


def procedural_black(kind='story'):
    data = (b'GVAS' + struct.pack('<IIIHHHI', 3, 522, 1012, 5, 4, 2, 0) + string('UE5')
            + struct.pack('<II', 3, 79) + bytes((i * 13 + 3) & 255 for i in range(79 * 20))
            + string(black.SAVE_CLASS) + b'\0')
    if kind == 'story':
        data += property_tag('Title', 'Saved Game / CHAPTER 1 CHECKPOINT')
        data += property_tag('Subtitle', 'CHAPTER 1-1') + property_tag('Detail', 'ESSENCE 150')
        data += property_tag('ByteData', data=native_story())
    else:
        data += property_tag('Title', 'System Preferences')
        data += property_tag('ByteData', data=bytes(black.SYSTEM_SIZE))
    return data + string('None') + bytes(4)


class Sigma2InspectionTests(unittest.TestCase):
    def test_independent_crc_known_answer_and_partial_integrity_boundary(self):
        self.assertEqual(sigma2.metadata_crc(b'123456789'), 0xFC891918)
        raw = procedural_sigma2()
        document = sigma2.inspect(raw)
        self.assertTrue(document.metadata_crc_verified)
        self.assertFalse(document.integrity_verified)
        self.assertFalse(document.writable)
        self.assertFalse(document.qualified_game_profile)
        self.assertEqual(sigma2.encode(document), raw)
        modified = bytearray(raw)
        modified[0x14A0] ^= 1
        # The unresolved payload checksum must never be mistaken for a passing
        # integrity check merely because the separate metadata CRC is valid.
        self.assertFalse(sigma2.inspect(bytes(modified)).integrity_verified)
        with self.assertRaisesRegex(SaveError, 'inspection-only'):
            sigma2.encode(document, bytes(modified))

    def test_truncation_foreign_revision_metadata_corruption_and_snapshot_forgery(self):
        raw = procedural_sigma2()
        for malformed in (raw[:-1], raw + b'\0', bytes(sigma2.SIZE), raw[:0xA04] + b'\x07' + raw[0xA05:]):
            with self.subTest(length=len(malformed)), self.assertRaises(SaveError):
                sigma2.inspect(malformed)
        damaged = bytearray(raw)
        damaged[0xA14] ^= 1
        with self.assertRaisesRegex(SaveError, 'metadata CRC'):
            sigma2.inspect(bytes(damaged))
        with self.assertRaises(SaveError):
            sigma2.encode(replace(sigma2.inspect(raw), integrity_verified=True))

    def test_profile_facts_preserve_unsigned_health_and_signed_essence(self):
        raw = bytearray(procedural_sigma2())
        struct.pack_into('<i', raw, 0x14A0, 0x7FFFFFFF)
        struct.pack_into('<HH', raw, 0x1454, 65535, 65534)
        document = sigma2.inspect(bytes(raw))
        self.assertEqual(document.profiles[0].essence, 0x7FFFFFFF)
        self.assertEqual(document.profiles[0].current_health, 65535)
        self.assertEqual(sigma2.encode(document), bytes(raw))

    def test_equal_boolean_integer_and_mutable_metadata_are_not_valid_snapshots(self):
        document = sigma2.inspect(procedural_sigma2())
        with self.assertRaises(SaveError):
            sigma2.encode(document, bytearray(document.raw))
        for forged in (replace(document, metadata_crc_verified=1), replace(document, writable=0),
                       replace(document, raw=bytearray(document.raw)),
                       replace(document, profiles=list(document.profiles)),
                       replace(document, profiles=(replace(document.profiles[0], enabled_marker=True),)
                               + document.profiles[1:])):
            with self.assertRaises(SaveError):
                sigma2.encode(forged)


class BlackInspectionTests(unittest.TestCase):
    def test_bounded_native_story_and_system_are_distinct_no_edit_roundtrips(self):
        for kind in ('story', 'system'):
            raw = procedural_black(kind)
            document = black.inspect(raw)
            self.assertEqual(document.kind, kind)
            self.assertFalse(document.integrity_verified)
            self.assertFalse(document.writable)
            self.assertEqual(black.encode(document), raw)
            self.assertEqual(document.metadata_crc_verified, kind == 'story')
            self.assertEqual(raw[document.byte_data_offset:document.byte_data_offset + len(document.byte_data)],
                             document.byte_data)

    def test_reject_foreign_class_revision_property_type_count_and_trailer(self):
        raw = procedural_black()
        invalid = [raw[:-1], raw + b'\0', raw.replace(b'NINJAGAIDEN2BLACK', b'NINJAGAIDEN2WHITX'),
                   raw.replace(b'ByteProperty', b'Int_Property'), raw.replace(b'Subtitle', b'Unknown_'),
                   raw[:8] + struct.pack('<I', 523) + raw[12:], raw[:4] + struct.pack('<I', 4) + raw[8:]]
        document = black.inspect(raw)
        changed = bytearray(raw)
        struct.pack_into('<I', changed, document.byte_data_offset - 4, 0xFFFFFFFF)
        invalid.append(bytes(changed))
        for malformed in invalid:
            with self.subTest(length=len(malformed)), self.assertRaises(SaveError):
                black.inspect(malformed)

    def test_embedded_metadata_crc_and_unresolved_payload_are_separate(self):
        raw = procedural_black()
        document = black.inspect(raw)
        damaged = bytearray(raw)
        damaged[document.byte_data_offset + 0x14] ^= 1
        with self.assertRaisesRegex(SaveError, 'metadata CRC'):
            black.inspect(bytes(damaged))
        damaged = bytearray(raw)
        damaged[document.byte_data_offset + 0xAA0] ^= 1
        self.assertFalse(black.inspect(bytes(damaged)).integrity_verified)
        with self.assertRaisesRegex(SaveError, 'inspection-only'):
            black.encode(document, bytes(damaged))
        with self.assertRaises(SaveError):
            black.encode(replace(document, writable=True))

    def test_huge_or_nonterminated_fstrings_are_rejected(self):
        raw = procedural_black()
        malformed = bytearray(raw)
        struct.pack_into('<i', malformed, 26, 0x7FFFFFFF)
        with self.assertRaises(SaveError):
            black.inspect(bytes(malformed))
        malformed = raw.replace(b'UE5\0', b'UE5X')
        with self.assertRaises(SaveError):
            black.inspect(malformed)

    def test_equal_boolean_integer_and_mutable_metadata_are_not_valid_snapshots(self):
        document = black.inspect(procedural_black())
        with self.assertRaises(SaveError):
            black.encode(document, bytearray(document.raw))
        for forged in (replace(document, metadata_crc_verified=1), replace(document, writable=0),
                       replace(document, raw=bytearray(document.raw)),
                       replace(document, byte_data=bytearray(document.byte_data)),
                       replace(document, properties=list(document.properties))):
            with self.assertRaises(SaveError):
                black.encode(forged)


class NativeInspectionTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('SIGMA2_PC_NATIVE_DIR'), 'Separate native Sigma 2 PC copies unavailable.')
    def test_native_sigma2_story_corpus(self):
        files = tuple(Path(os.environ['SIGMA2_PC_NATIVE_DIR']).rglob('STORY*.DAT'))
        self.assertTrue(files)
        for path in files:
            raw = path.read_bytes()
            document = sigma2.inspect(raw)
            self.assertTrue(document.metadata_crc_verified)
            self.assertFalse(document.integrity_verified)
            self.assertEqual(sigma2.encode(document), raw)

    @unittest.skipUnless(os.environ.get('NG2_BLACK_STEAM_NATIVE_DIR'), 'Separate native Black Steam copies unavailable.')
    def test_native_black_story_system_corpus(self):
        files = tuple(Path(os.environ['NG2_BLACK_STEAM_NATIVE_DIR']).rglob('*.sav'))
        self.assertTrue(files)
        kinds = set()
        for path in files:
            raw = path.read_bytes()
            document = black.inspect(raw)
            kinds.add(document.kind)
            self.assertFalse(document.integrity_verified)
            self.assertEqual(black.encode(document), raw)
        self.assertEqual(kinds, {'story', 'system'})
