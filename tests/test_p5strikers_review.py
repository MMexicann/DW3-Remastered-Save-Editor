"""Independent PC native framing and surgical-write review.

Procedural tests do not claim game loading. Optional full native player copies
remain private and are supplied only through P5S_PC_SAVE_COPIES.
"""
from dataclasses import replace
from functools import lru_cache
import os
from pathlib import Path
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.p5strikers_pc import codec, parser
from tests.test_p5strikers_pc import procedural_save


@lru_cache(maxsize=1)
def procedural_document():
    return parser.decode(procedural_save())


class IndependentFramingReview(unittest.TestCase):
    def test_stream_matches_independent_full_32bit_lcg(self):
        document = procedural_document()
        # Retain all 32 bits here rather than sharing the implementation's
        # 24-bit reduction. The emitted bits must still match.
        state = document.seed | (0xA7 << 24)
        clear = document.payload[:4096]
        encrypted = bytearray()
        for value in clear:
            state = (1103515245 * state + 12345) % (1 << 32)
            encrypted.append(value ^ ((state // 65536) % 256))
        self.assertEqual(bytes(encrypted), document.raw[:4096])

    def test_mutable_input_not_changed_even_on_integrity_rejection(self):
        document = procedural_document()
        mutable = bytearray(document.raw)
        original = bytes(mutable)
        self.assertEqual(codec.decode(mutable).payload, document.payload)
        self.assertEqual(mutable, original)
        mutable[0x6000] ^= 1
        damaged = bytes(mutable)
        with self.assertRaises(SaveError):
            codec.decode(mutable)
        self.assertEqual(mutable, damaged)
        self.assertEqual(codec.decode(original).payload, document.payload)

    def test_reserved_empty_and_unknown_name_slots_expose_no_writes(self):
        document = procedural_document()
        base = parser._base(1)
        name = base + codec.NAME_RELATIVE
        cases = ('empty_header', 'unterminated_first', 'unterminated_last',
                 'empty_last', 'control_name', 'del_control', 'c1_control', 'invalid_utf8')
        for case in cases:
            with self.subTest(case=case):
                data = bytearray(document.payload)
                if case == 'empty_header':
                    data[base:base + 2] = b'\xff\xff'
                elif case == 'unterminated_first':
                    data[name:name + codec.NAME_SIZE] = b'A' * codec.NAME_SIZE
                elif case == 'unterminated_last':
                    data[name + codec.NAME_SIZE:name + 2 * codec.NAME_SIZE] = b'A' * codec.NAME_SIZE
                elif case == 'empty_last':
                    data[name + codec.NAME_SIZE] = 0
                elif case == 'control_name':
                    data[name] = 0x1F
                elif case == 'del_control':
                    data[name] = 0x7F
                elif case == 'c1_control':
                    data[name:name + 2] = b'\xc2\x85'
                else:
                    data[name:name + 3] = b'\xf0\x80\0'
                mutated = parser.decode(codec.encode(codec.with_checksum(bytes(data)), document.seed))
                self.assertEqual(parser.fields_for(mutated), ())
                self.assertEqual(parser.serialize(mutated, {}), mutated.raw)
                with self.assertRaises(SaveError):
                    parser.serialize(mutated, {'slot_1_money': 1})
        # Block 0 remains reserved even if it looks exactly like an active slot.
        data = bytearray(document.payload)
        data[parser._base(0):parser._base(0) + codec.PC_SLOT_SIZE] = data[base:base + codec.PC_SLOT_SIZE]
        mutated = parser.decode(codec.encode(codec.with_checksum(bytes(data)), document.seed))
        self.assertFalse(any(field.slot == 0 for field in parser.fields_for(mutated)))
        with self.assertRaises(SaveError):
            parser.stage(mutated, {}, 'slot_0_money', 1)

    def test_pending_mapping_and_stage_reject_malformed_existing_edits(self):
        document = procedural_document()
        for changes in (None, [], True, [('slot_1_money', 1)]):
            with self.subTest(kind=type(changes).__name__):
                with self.assertRaises(SaveError):
                    parser.serialize(document, changes)
                with self.assertRaises(SaveError):
                    parser.stage(document, changes, 'slot_1_money', 1)
        for changes in ({'unknown': 1}, {'slot_1_money': True}, {'slot_1_item_869b2': 0}):
            with self.subTest(keys=tuple(changes)), self.assertRaises(SaveError):
                parser.stage(document, changes, 'slot_1_bond_points', 9)

    def test_snapshot_requires_canonical_profile_object(self):
        document = procedural_document()
        class UnqualifiedFormat:
            def __eq__(self, other):
                return True
        for format_object in (UnqualifiedFormat(), replace(parser.FORMAT)):
            with self.subTest(kind=type(format_object).__name__), self.assertRaises(SaveError):
                parser.fields_for(replace(document, format=format_object))

    def test_valid_checksum_does_not_excuse_unknown_layout_or_selected_slot(self):
        document = procedural_document()
        for selected in (-2, 10, 0x7FFFFFFF):
            data = bytearray(document.payload)
            data[4:8] = selected.to_bytes(4, 'little', signed=True)
            with self.subTest(selected=selected), self.assertRaises(SaveError):
                codec.encode(codec.with_checksum(bytes(data)), document.seed)
        data = bytearray(document.payload)
        data[parser._base(8) + codec.MARKER_RELATIVE] ^= 1
        with self.assertRaises(SaveError):
            codec.encode(codec.with_checksum(bytes(data)), document.seed)


@unittest.skipUnless(os.environ.get('P5S_PC_SAVE_COPIES'), 'No private complete PC player saves')
class IndependentGenuineReview(unittest.TestCase):
    def test_both_native_copies_checksum_rejection_and_surgical_multi_slot_edits(self):
        filenames = os.environ['P5S_PC_SAVE_COPIES'].split(os.pathsep)
        self.assertGreaterEqual(len(filenames), 2)
        for index, filename in enumerate(filenames):
            with self.subTest(fixture=index):
                raw = Path(filename).read_bytes()
                document = parser.decode(raw)
                self.assertEqual(parser.serialize(document, {}), raw)
                self.assertEqual(document.payload[-4], sum(document.payload[:-4]) % 256)
                self.assertNotEqual(document.payload[-4], sum(raw[:-4]) % 256)
                changes, allowed = {}, {len(raw) - 4}
                for field in parser.fields_for(document):
                    old = field.value(document.payload)
                    value = field.minimum if old != field.minimum else field.minimum + 1
                    changes[field.id] = value
                    allowed.update(range(field.offset, field.offset + field.size))
                self.assertTrue(changes)
                saved_raw = parser.serialize(document, changes)
                saved = parser.decode(saved_raw)
                self.assertEqual(saved.seed, document.seed)
                differences = {position for position, (before, after) in enumerate(
                    zip(document.payload, saved.payload)) if before != after}
                self.assertTrue(differences <= allowed)
                self.assertTrue(differences)
                self.assertEqual(saved.payload[-3:], document.payload[-3:])
                self.assertEqual(parser.maximums(document, changes), changes)
                for field in parser.fields_for(document):
                    self.assertEqual(field.value(saved.payload), changes[field.id])
                damaged = bytearray(raw)
                damaged[0x10000] ^= 1
                original_damaged = bytes(damaged)
                with self.assertRaises(SaveError):
                    parser.decode(damaged)
                self.assertEqual(damaged, original_damaged)
                damaged = bytearray(raw)
                damaged[-4] ^= 1
                with self.assertRaises(SaveError):
                    parser.decode(damaged)
