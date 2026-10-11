"""Read-only envelope regressions; procedural inputs are not genuine saves."""
from dataclasses import FrozenInstanceError, replace
from functools import lru_cache
import os
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.research.berserk_aot import envelope


# Deliberately independent from production profile constants/arithmetic.
SAMPLES = (('berserk', 1268512, 3), ('aot1', 769568, 3), ('aot2_pk', 3687964, 1))


def reference_cipher(payload, seed, advances):
    output = bytearray()
    for (word,) in struct.iter_unpack('<I', payload):
        for _ in range(advances):
            seed = (1528461393 * seed + 52814) % 4294967296
        output.extend((word ^ seed).to_bytes(4, 'little'))
    return bytes(output)


def reference_envelope(payload, seed, advances):
    checksum = sum(word[0] for word in struct.iter_unpack('<H', payload)) % 65536
    return struct.pack('<HH', checksum, seed) + reference_cipher(payload, seed, advances)


@lru_cache(maxsize=3)
def procedural(profile):
    _, size, advances = next(item for item in SAMPLES if item[0] == profile)
    # No fabricated title/revision header. Distinctive unknown data must survive.
    body_size = size - 4
    payload = (bytes(range(256)) * ((body_size + 255) // 256))[:body_size]
    return reference_envelope(payload, 0x1234, advances), payload


class EnvelopeTests(unittest.TestCase):
    def test_documented_family_arithmetic_vectors(self):
        # Independent arithmetic vectors, not player-save bytes.
        for advances, expected in ((1, 'c2f1d45eb4ee97dcf6e98c54a003ff99'),
                                   (3, 'fee1845c2cee06cdbaf3dde590340fdc')):
            with self.subTest(advances=advances):
                actual = envelope._cipher(bytes(range(16)), 0x1234, advances)
                self.assertEqual(actual.hex(), expected)
                self.assertEqual(envelope._cipher(actual, 0x1234, advances), bytes(range(16)))

    def test_explicit_sample_profiles_preserve_every_byte_and_seed(self):
        for profile, size, advances in SAMPLES:
            with self.subTest(profile=profile):
                raw, payload = procedural(profile)
                doc = envelope.inspect(raw, profile=profile)
                self.assertEqual(len(raw), size)
                self.assertEqual(doc.payload, payload)
                self.assertEqual(doc.seed, 0x1234)
                self.assertEqual(envelope.PROFILES[profile].advances, advances)
                self.assertEqual(envelope.reencode_unchanged(doc), raw)
                for flag in ('native_identity_verified', 'revision_verified',
                             'all_integrity_verified', 'writable'):
                    self.assertFalse(getattr(doc, flag))

    def test_outer_checksum_header_seed_body_and_tail_corruption_rejected(self):
        for profile, _, _ in SAMPLES:
            raw, _ = procedural(profile)
            for offset in (0, 1, 2, 3, 4, len(raw) // 2, len(raw) - 1):
                with self.subTest(profile=profile, offset=offset):
                    damaged = bytearray(raw)
                    damaged[offset] ^= 1
                    with self.assertRaisesRegex(SaveError, 'outer u16 checksum'):
                        envelope.inspect(damaged, profile=profile)

    def test_wrong_cipher_family_fails_without_probing_other_profiles(self):
        for profile, _, advances in SAMPLES:
            _, payload = procedural(profile)
            incorrect = reference_envelope(payload, 0x1234, 1 if advances == 3 else 3)
            with self.subTest(profile=profile), self.assertRaises(SaveError):
                envelope.inspect(incorrect, profile=profile)

    def test_additive_collision_does_not_claim_all_integrity_or_identity(self):
        raw, payload = procedural('aot1')
        changed = bytearray(payload)
        first, second = struct.unpack_from('<HH', changed)
        struct.pack_into('<HH', changed, 0, first + 1, second - 1)
        collision = raw[:4] + reference_cipher(changed, 0x1234, 3)
        doc = envelope.inspect(collision, profile='aot1')
        self.assertNotEqual(doc.payload, payload)
        self.assertEqual(doc.checksum, struct.unpack_from('<H', raw)[0])
        self.assertFalse(doc.all_integrity_verified)
        self.assertFalse(doc.native_identity_verified)
        self.assertFalse(doc.writable)

    def test_size_and_foreign_input_rejected_before_copy_or_cipher(self):
        raw, _ = procedural('aot1')
        bad_values = (b'', raw[:4], raw[:-1], raw + b'x', procedural('berserk')[0],
                      True, len(raw), None, 'save', list(range(4)))
        with patch.object(envelope, '_cipher', side_effect=AssertionError('must not cipher')):
            for value in bad_values:
                with self.subTest(type=type(value)), self.assertRaises(SaveError):
                    envelope.inspect(value, profile='aot1')

    def test_profile_selection_is_required_and_does_not_coerce(self):
        raw, _ = procedural('aot1')
        with self.assertRaises(TypeError):
            envelope.inspect(raw)
        for profile in (None, True, 1, [], {}, 'AOT1', 'aot2', 'atwin0000.dat', ''):
            with self.subTest(profile=profile), self.assertRaises(SaveError):
                envelope.inspect(raw, profile=profile)
        with self.assertRaises(TypeError):
            envelope.PROFILES['aot1'] = envelope.PROFILES['berserk']

    def test_byte_buffers_are_frozen_and_invalid_views_rejected(self):
        raw, _ = procedural('aot1')
        mutable = bytearray(raw)
        for value in (mutable, memoryview(mutable)):
            doc = envelope.inspect(value, profile='aot1')
            self.assertIs(type(doc.raw), bytes)
            self.assertEqual(doc.raw, raw)
        mutable[4] ^= 1
        self.assertEqual(doc.raw, raw)
        for view in (memoryview(raw).cast('I'), memoryview(raw)[::2],
                     memoryview(raw).cast('B', shape=(2, len(raw) // 2))):
            with self.assertRaises(SaveError):
                envelope.inspect(view, profile='aot1')

    def test_buffer_subclasses_cannot_override_size_or_copy_guards(self):
        raw, _ = procedural('aot1')

        class OversizedCopy(bytes):
            def __len__(self):
                return len(raw)

            def __bytes__(self):
                raise AssertionError('must not copy an untrusted subclass')

        class MutableCopy(bytearray):
            def __len__(self):
                return len(raw)

            def __bytes__(self):
                raise AssertionError('must not copy an untrusted subclass')

        with patch.object(envelope, '_cipher', side_effect=AssertionError('must not cipher')):
            for value in (OversizedCopy(b'foreign'), MutableCopy(b'foreign')):
                with self.subTest(type=type(value)), self.assertRaises(SaveError):
                    envelope.inspect(value, profile='aot1')

    def test_immutable_snapshot_and_forged_fields_fail_unchanged_reencoding(self):
        raw, _ = procedural('aot1')
        doc = envelope.inspect(raw, profile='aot1')
        with self.assertRaises(FrozenInstanceError):
            doc.seed = 1
        forged = (replace(doc, raw=bytearray(raw)), replace(doc, payload=bytearray(doc.payload)),
                  replace(doc, payload=b'x' + doc.payload[1:]),
                  replace(doc, seed=doc.seed ^ 1), replace(doc, checksum=doc.checksum ^ 1),
                  replace(doc, seed=True), replace(doc, profile_id='aot2_pk'),
                  replace(doc, raw=raw[:-1]), object(), raw)
        for value in forged:
            with self.subTest(type=type(value)), self.assertRaises(SaveError):
                envelope.reencode_unchanged(value)
        with self.assertRaises(TypeError):
            envelope.reencode_unchanged(doc, doc.payload)

    def test_forged_qualification_flags_require_literal_false(self):
        raw, _ = procedural('aot1')
        doc = envelope.inspect(raw, profile='aot1')
        for name in ('native_identity_verified', 'revision_verified',
                     'all_integrity_verified', 'writable'):
            for value in (True, 0, 0.0, None):
                forged = replace(doc)
                object.__setattr__(forged, name, value)
                with self.subTest(flag=name, value=value), self.assertRaises(SaveError):
                    envelope.reencode_unchanged(forged)

    def test_no_file_io_save_operations_registration_or_player_bytes_in_repr(self):
        from koei_editor.game_registry import GAMES
        raw, _ = procedural('aot1')
        with patch('builtins.open', side_effect=AssertionError('no file I/O')):
            doc = envelope.inspect(raw, profile='aot1')
            self.assertEqual(envelope.reencode_unchanged(doc), raw)
        self.assertNotIn('payload=', repr(doc))
        self.assertNotIn('raw=', repr(doc))
        for name in ('stage', 'save_as', 'restore', 'backup', 'fields_for', 'serialize'):
            self.assertFalse(hasattr(envelope, name))
        for name in ('berserk', 'aot1', 'aot2', 'aot2_pk'):
            self.assertNotIn(name, GAMES)


class OptionalNativeEnvelopeTests(unittest.TestCase):
    def check_copy(self, variable, profile):
        path = os.environ.get(variable)
        if not path:
            self.skipTest(f'No genuine copied native input supplied through {variable}')
        size = envelope.PROFILES[profile].observed_size
        # Bounded read; do not print owner paths, hashes or player contents.
        with Path(path).open('rb') as source:
            raw = source.read(size + 1)
        document = envelope.inspect(raw, profile=profile)
        self.assertEqual(envelope.reencode_unchanged(document), raw)
        for offset in (4, len(raw) - 1):
            damaged = bytearray(raw)
            damaged[offset] ^= 1
            with self.assertRaises(SaveError):
                envelope.inspect(damaged, profile=profile)
        self.assertFalse(document.writable)
        self.assertFalse(document.all_integrity_verified)

    def test_berserk_native_unchanged_outer_envelope(self):
        self.check_copy('BERSERK_SAVE_COPY', 'berserk')

    def test_aot1_native_unchanged_outer_envelope(self):
        self.check_copy('AOT1_SAVE_COPY', 'aot1')

    def test_aot2_pk_native_unchanged_outer_envelope(self):
        self.check_copy('AOT2_PK_SAVE_COPY', 'aot2_pk')


if __name__ == '__main__':
    unittest.main()
