"""Procedural SW2 PC contract checks; copied-file checks are explicitly optional."""
import os
from collections.abc import Mapping
from pathlib import Path
import struct
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.sw2 import sw2_parser as backend
from tests.scalar_contract import ScalarContractTests


def checksum(payload):
    struct.pack_into('<I', payload, backend.CHECKSUM_OFFSET,
                     sum(payload[:backend.CHECKSUM_OFFSET]) & 0xFFFFFFFF)
    return bytes(payload)


def procedural_raw():
    raw = bytearray((i * 37 + 11) & 255 for i in range(backend.SAVE_SIZE))
    struct.pack_into('<H', raw, 4, 2)
    raw[0x214C:0x2150] = bytes.fromhex('ffffff03')
    struct.pack_into('<I', raw, 0x2150, 12345)
    for officer in range(26):
        base = backend.OFFICER_BASE + officer * backend.OFFICER_STRIDE
        for stat in range(8):
            struct.pack_into('<I', raw, base + stat * 4, 100 + officer + stat)
        struct.pack_into('<I', raw, base + 0x20, 1000 + officer)
        raw[base + 0x24] = 12
        for weapon in range(8):
            offset = base + 0x28 + weapon * 19
            raw[offset] = 0x7F
        weapon = base + 0x28
        raw[weapon] = officer * 4 + 1
        raw[weapon + 1] = 4
        raw[weapon + 2:weapon + 10] = bytes(range(8))
        raw[weapon + 10:weapon + 18] = bytes(range(1, 9))
        raw[weapon + 18] = 8
        raw[base + 0xC0] = 0
        raw[base + 0xC1:base + 0xE9] = bytes([0x82] * 40)
    return checksum(raw)


class SW2ContractTests(ScalarContractTests, unittest.TestCase):
    game_id = 'sw2'
    payload_integrity_offsets = frozenset(range(backend.CHECKSUM_OFFSET, backend.CHECKSUM_OFFSET + 4))

    def fixture_bytes(self):
        return procedural_raw()


class SW2FormatTests(unittest.TestCase):
    def setUp(self):
        self.raw = procedural_raw()
        self.document = backend.decode(self.raw)

    def test_native_integrity_revision_and_lengths_rejected(self):
        for raw in (self.raw[:-1], self.raw + b'\x00', b'STFS' + self.raw[4:]):
            with self.subTest(length=len(raw)), self.assertRaises(SaveError):
                backend.decode(raw)
        for offset in (0, 12, 0x214C, backend.CHECKSUM_OFFSET):
            raw = bytearray(self.raw)
            raw[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(SaveError):
                backend.decode(raw)
        raw = bytearray(self.raw)
        struct.pack_into('<H', raw, 4, 3)
        with self.assertRaises(SaveError):
            backend.decode(checksum(raw))
        with self.assertRaises(SaveError):
            backend.decode(self.raw, 'sw2hd_ps3')

    def test_skill_rank_preserves_flag_and_does_not_acquire_or_unlock_rare(self):
        key = 'officer_0_skill_0'
        field = backend.field_map(self.document)[key]
        edited = backend.serialize(self.document, backend.stage(self.document, {}, key, 3))
        self.assertEqual(edited[field.offset], 0x83)
        self.assertEqual(edited[field.offset + 9], self.raw[field.offset + 9])
        with self.assertRaises(SaveError):
            backend.stage(self.document, {}, key, 0)
        with self.assertRaises(SaveError):
            backend.stage(self.document, {}, 'officer_0_skill_9', 4)
        raw = bytearray(self.raw)
        raw[field.offset] = 0x80
        document = backend.decode(checksum(raw))
        self.assertNotIn(key, backend.field_map(document))

    def test_original_unusual_values_and_unknown_trailer_are_preserved(self):
        raw = bytearray(self.raw)
        raw[backend.OFFICER_BASE + 0xC1] = 0xFF
        raw[-1] = 0xB7  # Trailer lies outside the native checksum coverage.
        document = backend.decode(checksum(raw))
        changes = backend.stage(document, {}, 'officer_0_skill_0', 2)
        self.assertEqual(backend.stage(document, changes, 'officer_0_skill_0', 127), {})
        changed = backend.serialize(document, changes)
        self.assertEqual(changed[backend.OFFICER_BASE + 0xC1], 0x82)
        self.assertEqual(changed[-1], 0xB7)
        self.assertEqual(backend.serialize(document, {}), document.raw)

    def test_storage_bounds_are_not_used_as_natural_maxima(self):
        self.assertTrue(backend.fields_for(self.document))
        self.assertTrue(all(not field.maxable for field in backend.fields_for(self.document)))
        changes = backend.stage(self.document, {}, 'money', 45678)
        self.assertEqual(backend.maximums(self.document, changes), changes)
        self.assertEqual(backend.limit_values(self.document, changes, ['money']), {})

    def test_malformed_mapping_key_rejects_without_mutating_snapshot(self):
        class MalformedPending(Mapping):
            def __iter__(self):
                return iter(['money'])

            def __len__(self):
                return 1

            def __getitem__(self, key):
                return 999

            def items(self):
                # A custom Mapping can expose keys a dict cannot represent.
                return iter([('money', 999), ([], 1)])

        pending = MalformedPending()
        for operation in (backend.changed_payload, backend.serialize, backend.review):
            with self.subTest(operation=operation.__name__), self.assertRaises(SaveError):
                operation(self.document, pending)
        self.assertEqual(self.document.raw, self.raw)
        self.assertEqual(self.document.payload, self.raw)

    def test_ownership_weapon_identity_and_occupied_slots_qualify_original_records(self):
        raw = bytearray(self.raw)
        raw[0x214C] &= ~1
        document = backend.decode(checksum(raw))
        self.assertFalse(any(field.id.startswith('officer_0_') for field in backend.fields_for(document)))
        for relative, value in ((0, 127), (0, 4), (18, 9), (2, 255)):
            raw = bytearray(self.raw)
            raw[backend.OFFICER_BASE + 0x28 + relative] = value
            document = backend.decode(checksum(raw))
            self.assertNotIn('officer_0_weapon_0_bonus_0', backend.field_map(document))
        with self.assertRaises(SaveError):
            backend.stage(self.document, {}, 'officer_0_weapon_0_bonus_8', 1)

    def test_surgical_edits_keep_level_exp_story_ownership_equipment_and_weapon_types(self):
        keys = {'money': 999, 'officer_0_stat_0': 320,
                'officer_0_skill_0': 3, 'officer_0_weapon_0_bonus_0': 12}
        changed = backend.serialize(self.document, keys)
        mapped = backend.field_map(self.document)
        allowed = set(range(backend.CHECKSUM_OFFSET, backend.CHECKSUM_OFFSET + 4))
        for key in keys:
            allowed.update(range(mapped[key].offset, mapped[key].offset + mapped[key].size))
        self.assertLessEqual({i for i, (a, b) in enumerate(zip(self.raw, changed)) if a != b}, allowed)
        self.assertEqual(backend.decode(changed).payload, changed)
        self.assertEqual(backend.inspection_rows(self.document)[0]['group'], 'Officers')

    def test_registered_copied_save_self_test_declares_native_checksum(self):
        from koei_editor.shared.verified_self_test import run
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = folder / 'source-copy.dat'
            source.write_bytes(self.raw)
            report = run('sw2', source, folder / 'report')
            self.assertTrue(report['success'])
            self.assertEqual(report['integrity_kind'], 'checksum')
            self.assertTrue(report['native_integrity_verified'])
            self.assertEqual(report['fields_changed'], 0)
            self.assertFalse(report['in_game_load_tested'])
            self.assertEqual(source.read_bytes(), self.raw)


class GenuineSW2CopyTests(unittest.TestCase):
    def test_optional_genuine_native_copy_roundtrip_and_surgical_money_edit(self):
        path = os.environ.get('SW2_PC_SAVE_COPY')
        if not path:
            self.skipTest('SW2_PC_SAVE_COPY genuine native Windows PC copy not supplied.')
        document = backend.read_save(Path(path))
        self.assertEqual(backend.serialize(document, {}), document.raw)
        field = backend.field_map(document)['money']
        old = field.value(document.payload)
        changes = backend.stage(document, {}, 'money', old - 1 if old else 1)
        edited = backend.serialize(document, changes)
        self.assertEqual(field.value(backend.decode(edited).payload), changes['money'])
        allowed = set(range(field.offset, field.offset + field.size)) | set(
            range(backend.CHECKSUM_OFFSET, backend.CHECKSUM_OFFSET + 4))
        self.assertLessEqual({i for i, (a, b) in enumerate(zip(document.raw, edited)) if a != b}, allowed)
        self.assertEqual(Path(path).read_bytes(), document.raw)
