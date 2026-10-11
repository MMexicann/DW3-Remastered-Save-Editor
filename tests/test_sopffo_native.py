"""Procedural framing tests and optional independent SOP PC corpus checks.

No procedural input is described as a genuine save or gameplay-valid fixture.
Native gameplay integrity remains unqualified and no gameplay writer is tested.
"""
from dataclasses import replace
import hashlib
import os
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.research.sopffo import sopffo_native as native


def procedural_payload(file_kind='user', revision=native.LAUNCH_REVISION):
    size = native.PROFILE_SIZES[(file_kind, revision)]
    payload = bytearray(size)
    payload[:8] = native.MAGIC[file_kind]
    struct.pack_into('<I', payload, 8, revision)
    struct.pack_into('<II', payload, 0x14, native.HEADER_SIZE, size - native.HEADER_SIZE)
    payload[0x108:0x110] = payload[8:16]
    # Distinctive opaque header/body/tail bytes expose accidental normalization.
    payload[0x20:0x24] = b'\x91\x82\x73\x64'
    payload[0x88:0x90] = b'unknown!'
    payload[0x900:0x90c] = b'opaque-body!'
    payload[-16:] = bytes(range(16))
    return bytes(payload)


def encrypted(payload):
    # Production callers supply immutable bytes; ctypes-backed Windows CNG
    # requires the same contract for mutated procedural fixture buffers.
    return native.katana_codec._cbc(bytes(payload), native.katana_codec._SOP_KEY,
                                   native.katana_codec._SOP_IV, 'encrypt')


class SopffoNativeTests(unittest.TestCase):
    def test_all_observed_profiles_have_exact_noop_and_reject_every_write(self):
        for file_kind, revision in native.PROFILE_SIZES:
            raw = procedural_payload(file_kind, revision)
            for value in (raw, encrypted(raw)):
                with self.subTest(file_kind=file_kind, revision=revision, encrypted=value != raw):
                    document = native.decode(value, file_kind)
                    self.assertEqual(document.payload, raw)
                    self.assertFalse(document.writable)
                    self.assertFalse(document.integrity_verified)
                    self.assertEqual(native.serialize(document, {}), value)
                    self.assertEqual(encrypted(document.payload), encrypted(raw))
                    for changes in ({'anima_shards': 1}, {'job_exp': 1}, {'owner': 1}, {'flags': 0}):
                        with self.assertRaises(SaveError):
                            native.serialize(document, changes)

    def test_snapshot_mutation_forgery_and_restoration_rejected(self):
        raw = procedural_payload('system')
        original = native.decode(raw, 'system')
        mutations = (
            replace(original, payload=raw[:-1] + b'!'),
            replace(original, payload=bytearray(raw)),
            replace(original, raw=bytearray(raw)),
            replace(original, raw=encrypted(raw)),
            replace(original, revision=native.LATER_REVISION),
            replace(original, file_kind='user'),
            replace(original, encrypted=0),
            replace(original, encrypted=True),
        )
        for document in mutations:
            with self.subTest(type=type(document.payload), revision=document.revision, encrypted=document.encrypted):
                with self.assertRaises(SaveError):
                    native.serialize(document, {})
                with self.assertRaises(SaveError):
                    native.inspection_rows(document)
        with self.assertRaises(SaveError):
            native.serialize(object(), {})
        # Undo/restoration is an exact original snapshot, never a repaired body.
        self.assertEqual(native.serialize(original, {}), raw)

    def test_foreign_kind_revision_context_lengths_and_size_rejected(self):
        raw = procedural_payload('system')
        mutations = (
            (0, b'NIOHSYS\0'), (0, native.MAGIC['user']),
            (8, struct.pack('<I', 0x23040100)),
            (0x14, struct.pack('<I', 0x158)),
            (0x18, struct.pack('<I', len(raw))),
            (0x108, struct.pack('<I', native.LATER_REVISION)),
            (0x10c, b'\1'),
        )
        for offset, value in mutations:
            changed = bytearray(raw)
            changed[offset:offset + len(value)] = value
            for representation in (bytes(changed), encrypted(changed)):
                with self.subTest(offset=hex(offset), encrypted=representation[:8] != native.MAGIC['system']):
                    with self.assertRaises(SaveError):
                        native.decode(representation, 'system')
        for value in (raw[:-1], raw + bytes(16), b'', 'not binary', None):
            with self.assertRaises(SaveError):
                native.decode(value, 'system')
        for kind in ('nioh3', None, 0, [], 'USER'):
            with self.assertRaises(SaveError):
                native.decode(raw, kind)
        # SYSTEM and USER are always selected separately.
        with self.assertRaises(SaveError):
            native.decode(raw)
        with self.assertRaises(SaveError):
            native.decode(procedural_payload(), 'system')

    def test_foreign_encrypted_header_is_rejected_before_body_decryption(self):
        raw = bytes(native.USER_SIZE)
        original_cbc = native.katana_codec._cbc
        with patch.object(native.katana_codec, '_cbc', wraps=original_cbc) as cbc:
            with self.assertRaises(SaveError):
                native.decode(raw)
            self.assertEqual(cbc.call_count, 1)
            self.assertEqual(len(cbc.call_args.args[0]), native.HEADER_SIZE)
        with patch.object(native.katana_codec, '_cbc') as cbc:
            with self.assertRaises(SaveError):
                native.decode(raw[:-1])
            cbc.assert_not_called()

    def test_unqualified_body_integrity_is_reported_honestly(self):
        raw = bytearray(procedural_payload('system'))
        raw[0x901] ^= 1
        # Framing cannot detect this damage; it must never grant write access.
        document = native.decode(raw, 'system')
        raw[0x902] ^= 1
        self.assertNotEqual(document.payload, raw)
        self.assertFalse(document.integrity_verified)
        self.assertFalse(document.writable)
        rows = dict(native.inspection_rows(document))
        self.assertIn('corruption may be undetected', rows['Native gameplay integrity'])
        self.assertEqual(rows['Gameplay writes'], 'Disabled')
        # Public summaries omit arbitrary opaque header/tail and owner values.
        self.assertNotIn('unknown!', repr(rows))
        self.assertNotIn('owner', repr(rows).lower())

    def test_unreviewed_user_revision_is_not_promoted_from_a_matching_size(self):
        raw = bytearray(procedural_payload())
        struct.pack_into('<I', raw, 8, 0x23040100)
        raw[0x108:0x110] = raw[8:16]
        with self.assertRaises(SaveError):
            native.decode(raw)


class OptionalSopffoNativeFiles(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('SOPFFO_NATIVE_DIR'), 'Independent SOP PC corpus not configured.')
    def test_genuine_epic_pair_cipher_framing_noop_and_source_preservation(self):
        directory = Path(os.environ['SOPFFO_NATIVE_DIR'])
        files = [path for path in directory.rglob('SAVEDATA.BIN') if path.is_file()]
        self.assertEqual(sorted(path.stat().st_size for path in files),
                         [native.SYSTEM_SIZE, native.USER_SIZE])
        observed_kinds = set()
        for path in files:
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).digest()
            kind = 'user' if len(raw) == native.USER_SIZE else 'system'
            document = native.decode(raw, kind)
            self.assertTrue(document.encrypted)
            self.assertEqual(document.revision, native.LAUNCH_REVISION)
            self.assertFalse(document.integrity_verified)
            self.assertEqual(encrypted(document.payload), raw)
            self.assertEqual(native.serialize(document, {}), raw)
            self.assertEqual(native.decode(document.payload, kind).payload, document.payload)
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), digest)
            observed_kinds.add(kind)
        self.assertEqual(observed_kinds, {'user', 'system'})

    @unittest.skipUnless(os.environ.get('SOPFFO_STEAM_NATIVE_DIR'), 'Independent SOP Steam corpus not configured.')
    def test_genuine_steam_two_users_and_system_are_qualified_separately(self):
        directory = Path(os.environ['SOPFFO_STEAM_NATIVE_DIR'])
        files = [path for path in directory.rglob('SAVEDATA.BIN') if path.is_file()]
        self.assertEqual(sorted(path.stat().st_size for path in files),
                         [native.SYSTEM_SIZE, native.USER_SIZE, native.USER_SIZE])
        observed_kinds = []
        for path in files:
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).digest()
            kind = 'user' if len(raw) == native.USER_SIZE else 'system'
            document = native.decode(raw, kind)
            self.assertTrue(document.encrypted)
            self.assertEqual(document.revision, native.LATER_REVISION)
            self.assertFalse(document.integrity_verified)
            self.assertEqual(encrypted(document.payload), raw)
            self.assertEqual(native.serialize(document, {}), raw)
            self.assertEqual(native.decode(document.payload, kind).payload, document.payload)
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), digest)
            observed_kinds.append(kind)
        self.assertEqual(sorted(observed_kinds), ['system', 'user', 'user'])

    @unittest.skipUnless(os.environ.get('KATANA_GOLDEN_DIR'), 'Upstream SOP source pair not configured.')
    def test_newer_system_source_pair_is_separate_from_genuine_user_evidence(self):
        directory = Path(os.environ['KATANA_GOLDEN_DIR'])
        raw = (directory / 'sopffo-encrypted.bin').read_bytes()
        expected = (directory / 'sopffo-decrypted.bin').read_bytes()
        document = native.decode(raw, 'system')
        self.assertEqual(document.payload, expected)
        self.assertEqual(document.revision, native.LATER_REVISION)
        self.assertEqual(native.serialize(document, {}), raw)
        self.assertFalse(document.integrity_verified)
        self.assertIn('Steam', dict(native.inspection_rows(document))['Evidence'])
        with self.assertRaises(SaveError):
            native.decode(raw, 'user')


if __name__ == '__main__':
    unittest.main()
