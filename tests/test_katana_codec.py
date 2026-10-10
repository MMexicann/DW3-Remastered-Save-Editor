"""PC codec vectors and optional local source golden files; no saves bundled.

KATANA_GOLDEN_DIR selects the upstream QualityControl.xUnit/Resources directory.
KATANA_<GAME>_SAVE_COPY selects a copied native PC save for a read-only roundtrip.
Golden files demonstrate upstream differential agreement, not game loading.
"""
import json
import os
from pathlib import Path
import struct
import unittest

import koei_editor.research.katana.katana_codec as codec


_AES_SBOX = bytes.fromhex(
    '637c777bf26b6fc53001672bfed7ab76ca82c97dfa5947f0add4a2af9ca472c0'
    'b7fd9326363ff7cc34a5e5f171d8311504c723c31896059a071280e2eb27b275'
    '09832c1a1b6e5aa0523bd6b329e32f8453d100ed20fcb15b6acbbe394a4c58cf'
    'd0efaafb434d338545f9027f503c9fa851a3408f929d38f5bcb6da2110fff3d2'
    'cd0c13ec5f974417c4a77e3d645d197360814fdc222a908846eeb814de5e0bdb'
    'e0323a0a4906245cc2d3ac629195e479e7c8376d8dd54ea96c56f4ea657aae08'
    'ba78252e1ca6b4c6e8dd741f4bbd8b8a703eb5664803f60e613557b986c11d9e'
    'e1f8981169d98e949b1e87e9ce5528df8ca1890dbfe6426841992d0fb054bb16')


def procedural_payload(game_id):
    """Deliberately generated format data, never a playable/native fixture."""
    profile = codec.PROFILES[game_id]
    result = bytearray((index * 17 + 29) & 255
                       for index in range(profile.header_size + 256))
    result[:8] = profile.magic[0]
    struct.pack_into('<I', result, 8, profile.revision)
    result[12:16] = bytes(4)
    struct.pack_into('<II', result, profile.length_offset, profile.header_size, 256)
    if profile.cipher == 'custom_ctr':
        struct.pack_into('<I', result, profile.header_size + 8, profile.revision)
    elif profile.cipher == 'sop_cbc':
        result[profile.header_size + 8:profile.header_size + 16] = result[8:16]
    else:
        result[0x100:0x108] = result[8:16]
        encoded = b'{"PlayerData":{"money":123},"Unknown":{"array":[7,9],"text":"keep"}}'
        result[0x108:] = encoded + bytes(len(result) - 0x108 - len(encoded))
        result[0x3c:0x5c] = codec._checksum(result[0x100:])
        result[0x5c:0x7c] = bytes(32)
        result[0x5c:0x7c] = codec._checksum(result[:0x100])
    return bytes(result)


def encrypted_payload(payload, game_id):
    profile = codec.PROFILES[game_id]
    if profile.cipher == 'custom_ctr':
        return codec._nioh_encrypt(payload, profile)
    if profile.cipher == 'sop_cbc':
        return codec._cbc(payload, codec._SOP_KEY, codec._SOP_IV, 'encrypt')
    return payload[:0x100] + codec._cbc(payload[0x100:], codec._WOLONG_KEY,
                                      codec._WOLONG_IV, 'encrypt')


class CryptographicVectors(unittest.TestCase):
    def test_fips_197_aes128_known_answer(self):
        key = bytes.fromhex('000102030405060708090a0b0c0d0e0f')
        block = bytes.fromhex('00112233445566778899aabbccddeeff')
        expected = bytes.fromhex('69c4e0d86a7b0430d8cdb78070b4c55a')
        self.assertEqual(codec._encrypt_block(block, codec._expand_key(key, _AES_SBOX),
                                             _AES_SBOX), expected)

    def test_independent_custom_sbox_known_answers(self):
        # Independently compiled pawREP MIT Nioh tool's AES implementation,
        # supplying its expected reversed-word key input. No fixture/account
        # bytes are used. Only the generated known-answer values are retained.
        vectors = (
            (bytes(16), bytes(16), 'd1ab3839994caa3d6b0cd38e518f1582'),
            (bytes(range(16)), bytes(range(16, 32)), 'fe24df281c5bbf7d59e78a3c37c34309'),
            (bytes(range(16)), bytes.fromhex('00112233445566778899aabbccddeeff'),
             'fb3fcfa02ce44bfc2dcf6cec54a6cb24'))
        for key, block, expected in vectors:
            with self.subTest(block=block.hex()):
                self.assertEqual(codec._encrypt_block(block, codec._expand_key(key)),
                                 bytes.fromhex(expected))

    def test_ctr_partial_block_and_counter_wrap(self):
        key = bytes(range(16))
        state = bytes(12) + bytes.fromhex('ffffffff')
        data = bytes(range(35))
        result = codec._ctr(data, key, state)
        expected = b''.join(codec._encrypt_block(bytes(12) + struct.pack('>I', count),
                                                 codec._expand_key(key))
                            for count in (0xffffffff, 0, 1))[:len(data)]
        self.assertEqual(result, bytes(a ^ b for a, b in zip(data, expected)))
        self.assertEqual(codec._ctr(result, key, state), data)

    def test_checksum_independent_literal_algorithm_known_answers(self):
        # Independent C translation of the literal upstream ushort accumulator,
        # contrasted with this module's deferred seven-lane accumulation.
        vectors = (
            (b'', 'f25c83f640f05638ddc7939b58f21628e6d3047852bf804f48de58ca8f22c8f1'),
            (bytes(range(256)), 'ce759611ef09789fa6ceeeffb365086f20dd5085178008cea39f1b7d65b19f97'),
            (bytes(range(256)) * 16, 'f22f95843f2ee56dbde1d975d4d476d93156e7178651c30412ea013d625d766b'))
        for data, expected in vectors:
            with self.subTest(length=len(data)):
                self.assertEqual(codec._checksum(data), bytes.fromhex(expected))


class EnvelopeTests(unittest.TestCase):
    def test_all_profiles_plain_and_encrypted_exact_noop(self):
        for game_id in codec.PROFILES:
            payload = procedural_payload(game_id)
            for raw in (payload, encrypted_payload(payload, game_id)):
                with self.subTest(game=game_id, encrypted=raw != payload):
                    document = codec.decode(raw, game_id)
                    self.assertEqual(document.payload, payload)
                    self.assertEqual(codec.encode(payload, raw, game_id), raw)
                    self.assertEqual(document.encrypted, raw != payload)
                    self.assertEqual(document.integrity_verified, game_id == 'wolong')
                    self.assertEqual(document.writable, game_id == 'wolong')
                    with self.assertRaises((AttributeError, TypeError)):
                        document.payload = b''

    def test_unknown_profile_and_foreign_same_magic_rejected(self):
        with self.assertRaises(ValueError):
            codec.decode(b'anything', 'guess')
        for first, second in (('nioh', 'nioh2'), ('nioh2', 'nioh'),
                              ('nioh3', 'sopffo'), ('sopffo', 'nioh3')):
            payload = procedural_payload(first)
            for raw in (payload, encrypted_payload(payload, first)):
                with self.subTest(first=first, second=second, encrypted=raw != payload):
                    with self.assertRaises(ValueError):
                        codec.decode(raw, second)

    def test_structural_corruption_truncation_and_size_bounds(self):
        for game_id, profile in codec.PROFILES.items():
            payload = procedural_payload(game_id)
            for invalid in (b'', payload[:16], payload[:-1], payload + b'\0'):
                with self.subTest(game=game_id, size=len(invalid)):
                    with self.assertRaises(ValueError):
                        codec.decode(invalid, game_id)
            for offset in (0, 8, profile.length_offset, profile.length_offset + 4):
                damaged = bytearray(payload)
                damaged[offset] ^= 1
                with self.subTest(game=game_id, offset=offset):
                    with self.assertRaises(ValueError):
                        codec.decode(damaged, game_id)
        with self.assertRaises(ValueError):
            codec.decode(bytes(codec.MAX_SIZE + 1), 'nioh2')

    def test_unmapped_integrity_rejects_edits_without_changing_flags(self):
        for game_id in ('nioh', 'nioh2', 'nioh3', 'sopffo'):
            payload = procedural_payload(game_id)
            raw = encrypted_payload(payload, game_id)
            changed = bytearray(payload)
            changed[-1] ^= 1
            with self.subTest(game=game_id):
                with self.assertRaisesRegex(ValueError, 'inspection-only'):
                    codec.encode(changed, raw, game_id)
                # Body checksums are unknown; expose this limitation honestly.
                inspected = codec.decode(changed, game_id)
                self.assertFalse(inspected.integrity_verified)
                self.assertEqual(codec.decode(raw, game_id).payload, payload)

    def test_wolong_surgical_edit_updates_only_checksum_ranges(self):
        payload = procedural_payload('wolong')
        offset = payload.index(b'123')
        changed = payload[:offset] + b'456' + payload[offset + 3:]
        for raw in (payload, encrypted_payload(payload, 'wolong')):
            with self.subTest(encrypted=raw != payload):
                encoded = codec.encode(changed, raw, 'wolong')
                decoded = codec.decode(encoded, 'wolong')
                self.assertEqual(decoded.payload[0x100:], changed[0x100:])
                self.assertEqual(decoded.encrypted, raw != payload)
                differences = {index for index, (a, b) in
                               enumerate(zip(payload, decoded.payload)) if a != b}
                allowed = set(range(0x3c, 0x7c)) | set(range(offset, offset + 3))
                self.assertTrue(differences <= allowed)
                self.assertTrue(set(range(offset, offset + 3)) <= differences)
                self.assertEqual(codec.decode(raw, 'wolong').payload, payload)

    def test_wolong_checksum_corruption_rejected_without_repair(self):
        payload = procedural_payload('wolong')
        for offset in (0x10, 0x3c, 0x5c, 0x80, payload.index(b'123'), len(payload) - 1):
            damaged = bytearray(payload)
            damaged[offset] ^= 1
            with self.subTest(offset=offset):
                with self.assertRaises(ValueError):
                    codec.decode(damaged, 'wolong')
                with self.assertRaises(ValueError):
                    codec.encode(payload, damaged, 'wolong')
        raw = bytearray(encrypted_payload(payload, 'wolong'))
        raw[0x150] ^= 1
        with self.assertRaises(ValueError):
            codec.decode(raw, 'wolong')

    def test_wolong_header_account_size_and_json_edits_rejected(self):
        payload = procedural_payload('wolong')
        cases = [payload + bytes(16)]
        header_change = bytearray(payload)
        header_change[0x10] ^= 1
        cases.append(header_change)
        invalid_json = bytearray(payload)
        invalid_json[0x108] = ord('[')
        cases.append(invalid_json)
        for changed in cases:
            with self.assertRaises(ValueError):
                codec.encode(changed, payload, 'wolong')


class OptionalSourceGoldenFiles(unittest.TestCase):
    def _golden(self, game_id):
        location = os.environ.get('KATANA_GOLDEN_DIR')
        if not location:
            self.skipTest('KATANA_GOLDEN_DIR is unset; no upstream save fixtures are bundled.')
        stem = 'wolong-dummy' if game_id == 'wolong' else game_id
        base = Path(location)
        return ((base / (stem + '-encrypted.bin')).read_bytes(),
                (base / (stem + '-decrypted.bin')).read_bytes())

    def _valid_golden(self, game_id):
        raw, expected = self._golden(game_id)
        document = codec.decode(raw, game_id)
        self.assertEqual(document.payload, expected)
        self.assertEqual(codec.encode(document.payload, raw, game_id), raw)
        self.assertEqual(codec.decode(expected, game_id).payload, expected)
        profile = codec.PROFILES[game_id]
        if profile.cipher == 'custom_ctr':
            self.assertEqual(codec._nioh_encrypt(expected, profile), raw)
        else:
            self.assertEqual(codec._cbc(expected, codec._SOP_KEY, codec._SOP_IV,
                                        'encrypt'), raw)

    def test_nioh_full_source_pair(self):
        self._valid_golden('nioh')

    def test_nioh2_full_source_pair(self):
        self._valid_golden('nioh2')

    def test_nioh3_full_source_pair(self):
        self._valid_golden('nioh3')

    def test_sopffo_full_source_pair(self):
        self._valid_golden('sopffo')

    def test_wolong_dummy_cipher_pair_is_not_valid_save_evidence(self):
        raw, expected = self._golden('wolong')
        decrypted = raw[:0x100] + codec._cbc(raw[0x100:], codec._WOLONG_KEY,
                                             codec._WOLONG_IV, 'decrypt')
        self.assertEqual(decrypted, expected)
        self.assertEqual(expected[:0x100] + codec._cbc(expected[0x100:], codec._WOLONG_KEY,
                                                      codec._WOLONG_IV, 'encrypt'), raw)
        # Upstream calls this fixture dummy: its JSON is incomplete and both
        # checksums are stale. Accepting it would silently bless corrupt input.
        with self.assertRaises(ValueError):
            codec.decode(raw, 'wolong')
        with self.assertRaises(ValueError):
            codec.decode(expected, 'wolong')
        with self.assertRaises(ValueError):
            codec._wolong_checksums(expected)


class OptionalCopiedNativeFiles(unittest.TestCase):
    def _copied(self, game_id):
        variable = 'KATANA_' + game_id.upper() + '_SAVE_COPY'
        location = os.environ.get(variable)
        if not location:
            self.skipTest(variable + ' is unset.')
        path = Path(location)
        raw = path.read_bytes()
        document = codec.decode(raw, game_id)
        self.assertEqual(codec.encode(document.payload, raw, game_id), raw)
        self.assertEqual(path.read_bytes(), raw)

    def test_nioh_copied_native_save(self):
        self._copied('nioh')

    def test_nioh2_copied_native_save(self):
        self._copied('nioh2')

    def test_nioh3_copied_native_save(self):
        self._copied('nioh3')

    def test_sopffo_copied_native_save(self):
        self._copied('sopffo')

    def test_wolong_copied_native_save(self):
        self._copied('wolong')


if __name__ == '__main__':
    unittest.main()
