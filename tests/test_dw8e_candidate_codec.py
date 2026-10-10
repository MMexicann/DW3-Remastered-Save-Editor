"""Synthetic DW8E arithmetic tests; these do not qualify native PC support."""
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import koei_editor.research.dw8e.dw8e_candidate_codec as candidate


def reference_byte_cipher(payload):
    # Independently expressed arithmetic used only for synthetic fixtures.
    state = 336078849  # 0x14082801
    result = bytearray()
    for value in payload:
        state = (1103515245 * state + 12345) % (2 ** 32)
        result.append(value ^ ((state // 65536) % 256))
    return bytes(result)


def reference_word_cipher(body, seed):
    result = bytearray()
    for offset in range(0, len(body), 4):
        for _ in range(3):
            seed = (1528461393 * seed + 52814) % (2 ** 32)
        value = int.from_bytes(body[offset:offset + 4], 'little') ^ seed
        result.extend(value.to_bytes(4, 'little'))
    return bytes(result)


def reference_envelope(body, header):
    result = bytearray(header)
    checksum = sum(int.from_bytes(body[i:i + 2], 'little')
                   for i in range(0, len(body), 2)) % 65536
    result[0x408:0x40A] = checksum.to_bytes(2, 'little')
    seed = int.from_bytes(result[0x40A:0x40C], 'little')
    return bytes(result) + reference_word_cipher(body, seed)


def synthetic(kind, size=63, seed=0x6D87):
    if kind == 'BattleSave':
        size += 1
    # Include distinctive nonzero unknown header data to expose data loss.
    header = bytearray((i * 17 + 9) % 256 for i in range(1036))
    header[0x40A:0x40C] = seed.to_bytes(2, 'little')
    payload = bytes((i * 37 + 11) % 256 for i in range(size))
    body = (reference_byte_cipher(payload) + bytes([sum(payload) % 256])
            if kind == 'SystemSave' else payload)
    return reference_envelope(body, header), payload


class DW8EmpiresCandidateTests(unittest.TestCase):
    def test_candidate_does_not_claim_native_pc_verification_or_registration(self):
        from koei_editor.game_registry import GAMES
        from koei_editor.shared.verified_editor import FORMATS
        self.assertFalse(candidate.PC_SAMPLE_VERIFIED)
        self.assertFalse(candidate.NATIVE_IDENTITY_VERIFIED)
        self.assertNotIn('dw8e', GAMES)
        self.assertNotIn('dw8e', FORMATS)
        self.assertIn('PS3', candidate.__doc__)
        self.assertIn('remains unverified', candidate.__doc__)

    def test_synthetic_system_and_battle_decoding_and_roundtrip(self):
        for kind in ('SystemSave', 'BattleSave'):
            for seed in (0, 1, 0x6D87, 0xFFFF):
                for size in (3, 63, 1023):
                    with self.subTest(kind=kind, seed=seed, size=size):
                        raw, payload = synthetic(kind, size, seed)
                        document = candidate.decode_candidate(raw, kind=kind)
                        self.assertEqual(document.payload, payload)
                        self.assertEqual(document.raw, raw)
                        self.assertEqual(document.header, raw[:1036])
                        self.assertEqual(document.encode_candidate(), raw)

    def test_same_size_edit_changes_only_requested_plaintext_and_checksums(self):
        for kind in ('SystemSave', 'BattleSave'):
            raw, payload = synthetic(kind)
            document = candidate.decode_candidate(raw, kind=kind)
            changed = bytearray(payload)
            changed[19] ^= 0x40
            output = document.encode_candidate(changed)
            reread = candidate.decode_candidate(output, kind=kind)
            differences = {i for i, (before, after) in enumerate(zip(payload, reread.payload))
                           if before != after}
            self.assertEqual(differences, {19})
            self.assertEqual(reread.payload, changed)
            self.assertEqual(output[:0x408], raw[:0x408])
            self.assertEqual(output[0x40A:0x40C], raw[0x40A:0x40C])
            self.assertEqual(len(output), len(raw))
            self.assertEqual(document.raw, raw)
            self.assertEqual(document.payload, payload)

    def test_all_checksum_sums_wrap(self):
        header = bytes(0x40C)
        payload = bytes([255] * 63)
        body = reference_byte_cipher(payload) + bytes([sum(payload) % 256])
        raw = reference_envelope(body, header)
        document = candidate.decode_candidate(raw, kind='SystemSave')
        self.assertEqual(document.payload, payload)
        self.assertEqual(document.encode_candidate(), raw)
        body = bytes([255] * 64)
        raw = reference_envelope(body, header)
        self.assertEqual(candidate.decode_candidate(raw, kind='BattleSave').payload, body)
        self.assertEqual(int.from_bytes(raw[0x408:0x40A], 'little'), 65504)

    def test_truncated_empty_and_unaligned_envelopes_are_rejected(self):
        raw, _ = synthetic('SystemSave')
        for bad in (b'', raw[:0x408], raw[:0x40C], raw[:0x40F], raw[:-1], raw + b'x'):
            with self.subTest(size=len(bad)), self.assertRaises(ValueError):
                candidate.decode_candidate(bad, kind='SystemSave')

    def test_classification_is_explicit_and_accepts_only_exact_known_strings(self):
        raw, _ = synthetic('SystemSave')
        with self.assertRaises(TypeError):
            candidate.decode_candidate(raw)
        for kind in ('', 'systemsave', 'SystemSave.dat', 'save.dat', b'SystemSave',
                     None, True, 1, [], {}, ['SystemSave']):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                candidate.decode_candidate(raw, kind=kind)

    def test_outer_layer_cannot_identify_system_versus_battle_or_the_game(self):
        raw, payload = synthetic('SystemSave')
        outer_only = candidate.decode_candidate(raw, kind='BattleSave')
        self.assertNotEqual(outer_only.payload, payload)
        self.assertEqual(outer_only.encode_candidate(), raw)
        # Successful arithmetic on an explicitly supplied hypothesis must never
        # imply that the hypothesis or the save's game identity was validated.
        self.assertFalse(candidate.NATIVE_IDENTITY_VERIFIED)

    def test_raw_input_types_do_not_silently_allocate_or_coerce(self):
        for raw in (None, True, 100, 'savedata', [0] * 8, (0,) * 8, object()):
            with self.subTest(type=type(raw)), self.assertRaises(ValueError):
                candidate.decode_candidate(raw, kind='SystemSave')

    def test_bytearray_and_multibyte_memoryview_are_frozen_without_mutation(self):
        raw, payload = synthetic('SystemSave')
        mutable = bytearray(raw)
        for value in (mutable, memoryview(mutable), memoryview(mutable).cast('I')):
            document = candidate.decode_candidate(value, kind='SystemSave')
            self.assertIs(type(document.raw), bytes)
            self.assertEqual(document.payload, payload)
            self.assertEqual(document.encode_candidate(), raw)
        self.assertEqual(mutable, raw)
        document = candidate.decode_candidate(mutable, kind='SystemSave')
        mutable[0] ^= 0x80
        self.assertEqual(document.raw, raw)

    def test_edit_payload_types_and_length_are_validated(self):
        raw, payload = synthetic('SystemSave')
        document = candidate.decode_candidate(raw, kind='SystemSave')
        for edited in (len(payload), True, 'x' * len(payload), list(payload),
                       payload[:-1], payload + b'x'):
            with self.subTest(type=type(edited)), self.assertRaises(ValueError):
                document.encode_candidate(edited)
        self.assertEqual(document.encode_candidate(memoryview(payload)), raw)

    def test_research_size_limit_applies_before_copy_or_cipher(self):
        raw, _ = synthetic('SystemSave')
        for value in (raw, bytearray(raw), memoryview(raw).cast('I')):
            with patch.object(candidate, 'MAX_BYTES', len(raw) - 1), \
                 patch.object(candidate, 'word_cipher', side_effect=AssertionError('must not cipher')), \
                 self.assertRaisesRegex(ValueError, 'research input limit'):
                candidate.decode_candidate(value, kind='SystemSave')

    def test_same_limit_is_enforced_for_forged_raw_snapshot(self):
        raw, _ = synthetic('SystemSave')
        document = candidate.decode_candidate(raw, kind='SystemSave')
        with patch.object(candidate, 'MAX_BYTES', len(raw) - 1), \
             patch.object(candidate, 'word_cipher', side_effect=AssertionError('must not cipher')), \
             self.assertRaisesRegex(ValueError, 'research input limit'):
            document.encode_candidate()

    def test_rejects_outer_checksum_seed_and_ciphertext_corruption(self):
        for kind in ('SystemSave', 'BattleSave'):
            raw, _ = synthetic(kind)
            for pos in (0x408, 0x409, 0x40A, 0x40B, 0x40C, len(raw) - 1):
                bad = bytearray(raw)
                bad[pos] ^= 1
                with self.subTest(kind=kind, pos=pos), self.assertRaisesRegex(ValueError, 'outer checksum'):
                    candidate.decode_candidate(bad, kind=kind)

    def test_rejects_system_checksum_when_outer_checksum_is_valid(self):
        raw, payload = synthetic('SystemSave')
        body = reference_byte_cipher(payload) + bytes([(sum(payload) % 256) ^ 1])
        bad = reference_envelope(body, raw[:0x40C])
        with self.assertRaisesRegex(ValueError, 'byte checksum'):
            candidate.decode_candidate(bad, kind='SystemSave')

    def test_uncovered_header_bytes_are_preserved_without_identity_claims(self):
        raw, payload = synthetic('SystemSave')
        changed = bytearray(raw)
        changed[0x100] ^= 0x80
        document = candidate.decode_candidate(changed, kind='SystemSave')
        self.assertEqual(document.payload, payload)
        self.assertEqual(document.encode_candidate(), changed)
        self.assertFalse(candidate.NATIVE_IDENTITY_VERIFIED)

    def test_snapshot_is_frozen_and_forged_payload_is_rejected(self):
        raw, _ = synthetic('SystemSave')
        document = candidate.decode_candidate(raw, kind='SystemSave')
        with self.assertRaises(FrozenInstanceError):
            document.payload = b'changed'
        payload = bytes([document.payload[0] ^ 1]) + document.payload[1:]
        forged = replace(document, payload=payload)
        with self.assertRaisesRegex(ValueError, 'snapshot was changed'):
            forged.encode_candidate()

    def test_forged_mutable_data_raw_classification_and_object_are_rejected(self):
        raw, _ = synthetic('SystemSave')
        document = candidate.decode_candidate(raw, kind='SystemSave')
        for forged in (replace(document, raw=bytearray(raw)),
                       replace(document, payload=bytearray(document.payload)),
                       replace(document, raw=raw[:-1]),
                       replace(document, kind='SystemSave.dat'),
                       replace(document, kind='BattleSave')):
            with self.subTest(kind=forged.kind), self.assertRaises(ValueError):
                forged.encode_candidate()
        with self.assertRaises(ValueError):
            candidate.validate_candidate_document(object())

    def test_rejects_forged_corrupted_original_even_when_replacement_matches_size(self):
        raw, _ = synthetic('BattleSave')
        document = candidate.decode_candidate(raw, kind='BattleSave')
        bad = bytearray(raw)
        bad[0x40C] ^= 1
        forged = replace(document, raw=bytes(bad))
        with self.assertRaisesRegex(ValueError, 'outer checksum'):
            forged.encode_candidate(bytes(len(document.payload)))

    def test_candidate_operations_do_not_open_or_write_files(self):
        raw, _ = synthetic('SystemSave')
        with patch('builtins.open', side_effect=AssertionError('no file I/O')):
            document = candidate.decode_candidate(raw, kind='SystemSave')
            self.assertEqual(document.encode_candidate(), raw)


if __name__ == '__main__':
    unittest.main()
