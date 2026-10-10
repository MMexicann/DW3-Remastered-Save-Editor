"""Published PC bytes and explicitly synthetic full-layout research checks.

No test fixture here is a complete genuine native PC save. Procedural files
exercise structural guards and cannot prove checksum or in-game validity.
"""

from dataclasses import FrozenInstanceError
from functools import lru_cache
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import koei_editor.research.p5s.p5s_codec as codec


def independent_transform(data, state):
    """Full32-bit expression, independent of the implementation's low24 loop."""
    output = []
    for byte in data:
        state = (1103515245 * state + 12345) % (2 ** 32)
        output.append(byte ^ ((state // 65536) % 256))
    return bytes(output)


@lru_cache(maxsize=1)
def synthetic_clear_candidate():
    """Generated structural fixture only; intentionally arbitrary trailer."""
    raw = bytearray(codec.PC_SIZE)
    raw[:4] = bytes.fromhex("00200120")
    raw[4:8] = (6).to_bytes(4, "little", signed=True)
    offset = codec.PC_LAYOUT_MARKER_OFFSET
    raw[offset:offset + 4] = (0x0036EE7F).to_bytes(4, "little")
    raw[-4:] = bytes.fromhex("deadbeef")
    return bytes(raw)


class PublishedP5SCipherTests(unittest.TestCase):
    def test_exact_published_32_byte_known_answer_and_source(self):
        self.assertEqual(codec.PUBLISHED_CIPHERTEXT.hex(),
                         "e1b9d643f8cd458e0c4ff9fd6f85e4c4085774954d009ddba1d2ac96d40bcbe9")
        self.assertEqual(codec.PUBLISHED_PLAINTEXT.hex(),
                         "00200120060000000001000000000000000000002fd9000000000000ffff0010")
        self.assertEqual(codec.VECTOR_SOURCE_URL,
                         "https://github.com/zarroboogs/p5spc.saveutil/blob/"
                         "2462a2043aba3bc551d2eb6b732a81d2374aa826/img/crypt.png")
        states = codec.recover_stream_states(codec.PUBLISHED_CIPHERTEXT,
                                             codec.PUBLISHED_PLAINTEXT[:4])
        self.assertEqual(len(states), 1)
        state = codec.recover_unique_stream_state(codec.PUBLISHED_CIPHERTEXT,
                                                  codec.PUBLISHED_PLAINTEXT[:4])
        self.assertEqual(states, (state,))
        self.assertEqual(codec.transform(codec.PUBLISHED_CIPHERTEXT, state),
                         codec.PUBLISHED_PLAINTEXT)
        self.assertEqual(codec.transform(codec.PUBLISHED_PLAINTEXT, state),
                         codec.PUBLISHED_CIPHERTEXT)
        self.assertEqual(codec.recover_stream_states(codec.PUBLISHED_CIPHERTEXT,
                                                     codec.PUBLISHED_PLAINTEXT), states)

    def test_arbitrary_seeds_match_full32_expression(self):
        data = bytes(range(256)) * 3
        for state in (0, 1, 0xFFFFFF, 0xFFFFFFFF, 0x12345678, 0xA5B6C7D8):
            with self.subTest(state=state):
                encrypted = codec.transform(data, state)
                self.assertEqual(encrypted, independent_transform(data, state))
                self.assertEqual(codec.transform(encrypted, state), data)

    def test_upper_eight_state_bits_do_not_change_output(self):
        data = bytes(range(256))
        for low24 in (0, 1, 0xFFFFFF, 0x123456):
            expected = codec.transform(data, low24)
            for high8 in (1, 17, 128, 255):
                self.assertEqual(codec.transform(data, low24 | (high8 << 24)), expected)

    def test_recovery_returns_class_without_high_bits(self):
        data = b"Independent known plaintext for a stream probe."
        for state in (0, 1, 0xFFFFFFFF, 0xC5123456):
            encrypted = independent_transform(data, state)
            self.assertEqual(codec.recover_unique_stream_state(encrypted, data),
                             state & 0xFFFFFF)

    def test_known_prefix_conflict_rejects_instead_of_guessing(self):
        incorrect = bytearray(codec.PUBLISHED_PLAINTEXT)
        incorrect[-1] ^= 1
        self.assertEqual(codec.recover_stream_states(codec.PUBLISHED_CIPHERTEXT, incorrect), ())
        with self.assertRaises(ValueError):
            codec.recover_unique_stream_state(codec.PUBLISHED_CIPHERTEXT, incorrect)

    def test_unique_recovery_rejects_ambiguous_result(self):
        with patch.object(codec, "recover_stream_states", return_value=(1, 2)):
            with self.assertRaises(ValueError):
                codec.recover_unique_stream_state(b"four", b"four")

    def test_byteslike_inputs_are_preserved_and_return_bytes(self):
        source = bytearray(range(128))
        before = bytes(source)
        for data in (before, source, memoryview(source)):
            result = codec.transform(data, 12)
            self.assertIsInstance(result, bytes)
            self.assertEqual(result, independent_transform(before, 12))
            self.assertEqual(source, before)
        self.assertEqual(codec.transform(b"", 0), b"")

    def test_transform_rejects_invalid_input_types_and_state_bounds(self):
        for data in (None, "bytes", [1, 2], 12, True):
            with self.subTest(data_type=type(data)):
                with self.assertRaises(TypeError):
                    codec.transform(data, 0)
        for state in (None, True, False, "1", 1.0):
            with self.assertRaises(TypeError):
                codec.transform(b"x", state)
        for state in (-1, 1 << 32):
            with self.assertRaises(ValueError):
                codec.transform(b"x", state)
        with self.assertRaises(ValueError):
            codec.transform(memoryview(b"abcd").cast("B", (2, 2)), 0)
        with self.assertRaises(ValueError):
            codec.transform(memoryview(b"abcd").cast("H"), 0)

    def test_recovery_rejects_malformed_lengths_and_types(self):
        for plain in (b"", b"a", b"abc", b"a" * 257):
            with self.assertRaises(ValueError):
                codec.recover_stream_states(b"x" * 300, plain)
        with self.assertRaises(ValueError):
            codec.recover_stream_states(b"abc", b"abcd")
        for cipher, plain in (("abcd", b"abcd"), (b"abcd", "abcd")):
            with self.assertRaises(TypeError):
                codec.recover_stream_states(cipher, plain)

    def test_research_length_limit_applies_before_work(self):
        with patch.object(codec, "MAX_DATA_SIZE", 3):
            for data in (b"abcd", bytearray(b"abcd"), memoryview(b"abcd")):
                with self.assertRaises(ValueError):
                    codec.transform(data, 0)
            with self.assertRaises(ValueError):
                codec.recover_stream_states(b"abcd", b"abcd")


class P5SCandidateInspectionTests(unittest.TestCase):
    def test_synthetic_layout_is_structural_evidence_only(self):
        report = codec.inspect_pc_plaintext_candidate(synthetic_clear_candidate())
        self.assertEqual(report.byte_length, 0x55DEA0)
        self.assertEqual(report.version, 0x20012000)
        self.assertEqual(report.selected_slot, 6)
        self.assertEqual(len(report.slots), 10)
        self.assertEqual(report.slots[0].start, 0x1C)
        self.assertEqual(report.slots[-1].end, 0x558E38)
        self.assertEqual(report.layout_marker_offset, 0x8978A)
        self.assertEqual(report.layout_marker_value, 0x0036EE7F)
        for index, slot in enumerate(report.slots):
            self.assertEqual(slot.index, index)
            self.assertEqual(slot.end - slot.start, 0x88E36)
            self.assertEqual(slot.first_name[0] - slot.start, 0x87842)
            self.assertEqual(slot.first_name[1] - slot.first_name[0], 33)
            self.assertEqual(slot.last_name[1] - slot.last_name[0], 33)
            self.assertEqual(slot.last_name[0], slot.first_name[1])
            self.assertLessEqual(slot.last_name[1], slot.end)
        self.assertEqual(report.opaque_tail, (0x558E38, 0x55DE9C))
        self.assertEqual(report.trailer, (0x55DE9C, 0x55DEA0))
        self.assertFalse(report.checksum_model_verified)
        self.assertFalse(report.integrity_verified)
        self.assertFalse(report.in_game_load_tested)
        with self.assertRaises(FrozenInstanceError):
            report.integrity_verified = True

    def test_synthetic_encrypted_inspection_preserves_inputs(self):
        clear = synthetic_clear_candidate()
        state = 0xAD123456
        encrypted = independent_transform(clear[:-4], state) + clear[-4:]
        mutable = bytearray(encrypted)
        expected = codec.inspect_pc_plaintext_candidate(clear)
        self.assertEqual(codec.inspect_pc_ciphertext_candidate(mutable, state), expected)
        self.assertEqual(codec.inspect_pc_ciphertext_candidate(mutable), expected)
        self.assertEqual(mutable, encrypted)
        self.assertEqual(mutable[-4:], bytes.fromhex("deadbeef"))

    def test_candidate_requires_exact_pc_size_not_console_size(self):
        for size in (0, 32, 0x55DEA0 - 1, 0x55DEA0 + 1, 0x600000, 0x55DB2C, 0x55DCBC):
            with self.subTest(size=size):
                for inspect in (codec.inspect_pc_plaintext_candidate,
                                codec.inspect_pc_ciphertext_candidate):
                    with self.assertRaises(ValueError):
                        inspect(bytes(size))

    def test_candidate_rejects_wrong_version_slot_and_marker(self):
        cases = ((0, b"NOPE"), (4, (-2).to_bytes(4, "little", signed=True)),
                 (4, (10).to_bytes(4, "little", signed=True)),
                 (codec.PC_LAYOUT_MARKER_OFFSET, b"\0\0\0\0"))
        for offset, value in cases:
            raw = bytearray(synthetic_clear_candidate())
            raw[offset:offset + len(value)] = value
            with self.subTest(offset=offset, value=value):
                with self.assertRaises(ValueError):
                    codec.inspect_pc_plaintext_candidate(raw)

    def test_selected_slot_supports_published_signed_bounds(self):
        for selected in (-1, 0, 9):
            raw = bytearray(synthetic_clear_candidate())
            raw[4:8] = selected.to_bytes(4, "little", signed=True)
            self.assertEqual(codec.inspect_pc_plaintext_candidate(raw).selected_slot, selected)

    def test_trailer_contents_do_not_become_false_checksum_validation(self):
        raw = bytearray(synthetic_clear_candidate())
        for trailer in (b"\0" * 4, b"\xff" * 4, b"test"):
            raw[-4:] = trailer
            report = codec.inspect_pc_plaintext_candidate(raw)
            self.assertFalse(report.integrity_verified)
            self.assertFalse(report.checksum_model_verified)

    def test_ciphertext_inspection_rejects_bad_state_and_plaintext_input(self):
        raw = synthetic_clear_candidate()
        for state in (True, "1", -1, 1 << 32):
            with self.assertRaises((TypeError, ValueError)):
                codec.inspect_pc_ciphertext_candidate(raw, state)
        with self.assertRaises(ValueError):
            codec.inspect_pc_ciphertext_candidate(raw, 0)


if __name__ == "__main__":
    unittest.main()
