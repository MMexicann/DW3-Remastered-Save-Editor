"""SW4-II procedural robustness and optional genuine private-copy qualification."""
from dataclasses import replace
import os
from pathlib import Path
import random
import struct
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.koei_codec import word_cipher, word_sum
from koei_editor.games.sw4ii import sw4ii_codec as codec, sw4ii_parser as parser
from tests.scalar_contract import ScalarContractTests


def seal(payload, seed=46381, header=None):
    payload = bytearray(payload)
    for offset, checksum in zip(codec.CHECKSUM_OFFSETS, codec.checksums(payload)):
        struct.pack_into('<I', payload, offset, checksum)
    return ((header if header is not None else bytes(codec.PAYLOAD_OFFSET - 4))
            + struct.pack('<HH', word_sum(payload), seed) + word_cipher(payload, seed))


def procedural_raw():
    rng = random.Random(542)
    payload = bytearray(rng.randbytes(codec.PAYLOAD_SIZE))
    struct.pack_into('<I', payload, 0, codec.REVISION)
    for index in range(76):
        base = parser.OFFICER_BASE + index * parser.OFFICER_STRIDE
        struct.pack_into('<I', payload, base, index)
        struct.pack_into('<I', payload, base + 12, 12)
        for _, _, relative in parser.STATS:
            struct.pack_into('<H', payload, base + relative, 237 + index)
    struct.pack_into('<I', payload, parser.GOLD_OFFSET, 15238)
    struct.pack_into('<5H', payload, parser.TOME_BASE, 23, 45, 12, 90, 4)
    for index in range(60 * parser.WEAPON_SLOTS):
        base = parser.WEAPON_BASE + index * parser.WEAPON_STRIDE
        struct.pack_into('<H', payload, base, 351)
        payload[base + 0xC:base + 0x14] = bytes([255]) * 8
    for owner in range(parser.OFFICER_COUNT):
        base = parser.WEAPON_BASE + owner * parser.WEAPON_SLOTS * parser.WEAPON_STRIDE
        struct.pack_into('<H', payload, base, 2 + owner * 2)
        payload[base + 0xC:base + 0x14] = bytes(range(8))
        payload[base + 0x14:base + 0x1C] = bytes([33]) * 8
        payload[parser.OFFICER_BASE + owner * parser.OFFICER_STRIDE + 0x3B] = 0
    for index in range(parser.MOUNT_COUNT):
        payload[parser.MOUNT_BASE + index * parser.MOUNT_STRIDE] = 26
    # A second already-owned primary weapon provides a genuine equipment choice
    # in generated GUI/contract tests; it does not claim in-game acquisition.
    struct.pack_into('<H', payload, parser.WEAPON_BASE + parser.WEAPON_STRIDE, 2)
    payload[parser.WEAPON_BASE + parser.WEAPON_STRIDE + 0xC] = 10
    payload[parser.WEAPON_BASE + parser.WEAPON_STRIDE + 0x14] = 21
    base = parser.MOUNT_BASE
    payload[base] = 0
    payload[base + 3:base + 5] = bytes((12, 25))
    payload[base + 0xA:base + 0xD] = bytes((20, 23, 27))
    return seal(payload, header=rng.randbytes(codec.PAYLOAD_OFFSET - 4))


def edit_values(document):
    result = {}
    for field in parser.fields_for(document):
        if field.group == 'Equipment':
            options = parser.field_options(document, field)
            result[field.id] = next((value for value, _ in options if value != field.value(document.payload)), options[0][0])
        else:
            result[field.id] = max(field.minimum, (field.value(document.payload) + 1) % (field.maximum + 1))
    return result


class SW4IITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = procedural_raw()
        cls.document = parser.decode(cls.raw)

    def test_roundtrip_all_fields_surgical_and_original_seed_header(self):
        document = self.document
        self.assertEqual(parser.serialize(document, {}), self.raw)
        changes = edit_values(document)
        self.assertTrue({'Resources', 'Officers', 'Weapons', 'Equipment', 'Mounts'}
                        <= {field.group for field in parser.fields_for(document)})
        encoded = parser.serialize(document, changes)
        reopened = parser.decode(encoded)
        self.assertEqual(reopened.payload, parser.changed_payload(document, changes))
        allowed = {offset for field in parser.fields_for(document)
                   for offset in range(field.offset, field.offset + field.size)}
        allowed.update(offset for start in codec.CHECKSUM_OFFSETS
                       for offset in range(start, start + 4))
        changed = {offset for offset, (a, b) in enumerate(zip(document.payload, reopened.payload)) if a != b}
        self.assertTrue(changed <= allowed)
        self.assertEqual(encoded[:codec.PAYLOAD_OFFSET - 4], self.raw[:codec.PAYLOAD_OFFSET - 4])
        self.assertEqual(reopened.seed, document.seed)
        # Custom officers, skill-tree bits, progression and all unowned data survive.
        start = parser.OFFICER_BASE + parser.OFFICER_COUNT * parser.OFFICER_STRIDE
        self.assertEqual(document.payload[start:start + 20 * parser.OFFICER_STRIDE],
                         reopened.payload[start:start + 20 * parser.OFFICER_STRIDE])

    def test_malformed_foreign_wrong_cipher_and_native_integrity(self):
        for bad in (self.raw[:-1], self.raw + b'\0', bytes(codec.SAVE_SIZE)):
            with self.assertRaises(SaveError):
                parser.decode(bad)
        damaged = bytearray(self.raw); damaged[codec.PAYLOAD_OFFSET + 1000] ^= 1
        with self.assertRaises(SaveError):
            parser.decode(damaged)
        # Correct envelope integrity cannot conceal a damaged gameplay checksum.
        payload = bytearray(self.document.payload); payload[0xCC40] ^= 1
        raw = self.raw[:codec.PAYLOAD_OFFSET - 4] + struct.pack('<HH', word_sum(payload), self.document.seed) + word_cipher(payload, self.document.seed)
        with self.assertRaises(SaveError):
            parser.decode(raw)
        for revision in (0x39EA, 0x2118, 0):
            payload = bytearray(self.document.payload); struct.pack_into('<I', payload, 0, revision)
            with self.assertRaises(SaveError):
                parser.decode(seal(payload))
        # Independent single-byte corruptions in every native checksum section,
        # including populated opaque/interim data, cannot be concealed by an
        # updated outer word sum. Native section integrity remains mandatory.
        for start, _ in codec.SECTIONS:
            payload = bytearray(self.document.payload); payload[start] ^= 1
            raw = self.raw[:codec.PAYLOAD_OFFSET - 4] + struct.pack('<HH', word_sum(payload), self.document.seed) + word_cipher(payload, self.document.seed)
            with self.assertRaises(SaveError):
                parser.decode(raw)
        for index in (0, 55, 56, 75):
            payload = bytearray(self.document.payload)
            struct.pack_into('<I', payload, parser.OFFICER_BASE + index * parser.OFFICER_STRIDE, 200)
            with self.assertRaises(SaveError):
                parser.decode(seal(payload))

    def test_stats_eligibility_invalid_edits_manual_only_and_unstage(self):
        payload = bytearray(self.document.payload)
        base = parser.OFFICER_BASE
        struct.pack_into('<I', payload, base + 12, 0)
        document = parser.decode(seal(payload))
        self.assertNotIn('officer_0_attack', parser.field_map(document))
        self.assertNotIn('officer_56_attack', parser.field_map(document))
        for changes in ({'gold': True}, {'gold': -1}, {'gold': 0x100000000},
                        {'tome_0': 65536}, {'unknown': 2}, {'officer_0_health': 3}):
            with self.assertRaises(SaveError):
                parser.serialize(document, changes)
            with self.assertRaises(SaveError):
                parser.maximums(document, changes)
        changes = parser.stage(document, {}, 'gold', 1111)
        self.assertEqual(parser.stage(document, changes, 'gold', parser.field_map(document)['gold'].value(document.payload)), {})
        self.assertEqual(parser.maximums(document, changes), changes)
        self.assertEqual(parser.limit_values(document, changes, ['gold']), {})
        self.assertTrue(all(not field.maxable for field in parser.fields_for(document)))
        # Snapshot tampering and mutable source bytes never become editable.
        with self.assertRaises(SaveError):
            parser.fields_for(replace(document, payload=bytes(codec.PAYLOAD_SIZE)))
        with self.assertRaises(SaveError):
            parser.fields_for(replace(document, raw=bytearray(document.raw)))

    def test_safe_save_backup_restore_and_changed_source(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder); source = folder / 'copy.dat'; source.write_bytes(self.raw)
            document = parser.read_save(source); destination = folder / 'edited.dat'
            reopened = parser.save_as(document, {'gold': 14321, 'officer_2_attack': 345}, destination)
            self.assertEqual(source.read_bytes(), self.raw)
            self.assertEqual(parser.field_map(reopened)['gold'].value(reopened.payload), 14321)
            backup = parser.backup(document)
            restored = folder / 'restored.dat'; parser.restore(backup, restored)
            self.assertEqual(restored.read_bytes(), self.raw)
            with self.assertRaises(FileExistsError):
                parser.save_as(document, {}, destination)
            source.write_bytes(self.raw[:-1])
            with self.assertRaises(SaveError):
                parser.save_as(document, {}, folder / 'changed.dat')

    def test_existing_weapon_owner_attribute_and_equipment_guards(self):
        payload = bytearray(self.document.payload)
        # A physically occupied foreign-family identity is not an owned target.
        struct.pack_into('<H', payload, parser.WEAPON_BASE + parser.WEAPON_STRIDE, 4)
        payload[parser.WEAPON_BASE + 0xC] = 250  # Unknown attached identity.
        payload[parser.OFFICER_BASE + 0x3B] = 19  # Unusual original empty reference.
        payload[parser.MOUNT_BASE] = 13  # Unknown native mount type.
        document = parser.decode(seal(payload))
        mapped = parser.field_map(document)
        self.assertNotIn('weapon_0_1_attribute_0', mapped)
        self.assertNotIn('weapon_0_0_attribute_0', mapped)
        self.assertNotIn('mount_0_speed', mapped)
        self.assertEqual(parser.field_options(document, 'officer_0_equipped_weapon'),
                         ((0, 'Existing own-pool slot 0'),))
        for target in (1, 15, 19 + 1):
            with self.assertRaises(SaveError):
                parser.stage(document, {}, 'officer_0_equipped_weapon', target)
        changes = parser.stage(document, {}, 'officer_0_equipped_weapon', 0)
        self.assertEqual(parser.stage(document, changes, 'officer_0_equipped_weapon', 19), {})
        self.assertEqual(parser.serialize(document, {}), document.raw)
        reopened = parser.decode(parser.serialize(document, changes))
        self.assertEqual(reopened.payload[parser.OFFICER_BASE + 0x3B], 0)
        self.assertEqual(reopened.payload[parser.WEAPON_BASE:parser.WEAPON_BASE + 2 * parser.WEAPON_STRIDE],
                         document.payload[parser.WEAPON_BASE:parser.WEAPON_BASE + 2 * parser.WEAPON_STRIDE])

    def test_genuine_private_copies(self):
        paths = [os.environ[name] for name in ('SW4II_SAVE_COPY', 'SW4II_SECOND_SAVE_COPY') if os.environ.get(name)]
        if not paths:
            self.skipTest('No separate genuine native SW4-II copy supplied.')
        for path in paths:
            with self.subTest(copy=Path(path).name):
                document = parser.read_save(path)
                self.assertEqual(parser.serialize(document, {}), document.raw)
                # Excludes fixture/player values from reports; all eligible resources/stats are edited surgically.
                changes = edit_values(document)
                reopened = parser.decode(parser.serialize(document, changes))
                self.assertEqual(reopened.payload, parser.changed_payload(document, changes))
                allowed = {offset for field in parser.fields_for(document)
                           for offset in range(field.offset, field.offset + field.size)}
                allowed.update(offset for start in codec.CHECKSUM_OFFSETS for offset in range(start, start + 4))
                changed = {offset for offset, (a, b) in enumerate(zip(document.payload, reopened.payload)) if a != b}
                self.assertTrue(changed <= allowed)


class SW4IIContractTests(ScalarContractTests, unittest.TestCase):
    game_id = 'sw4ii'
    payload_integrity_offsets = frozenset(offset for start in codec.CHECKSUM_OFFSETS
                                          for offset in range(start, start + 4))

    def fixture_bytes(self):
        return procedural_raw()


if __name__ == '__main__':
    unittest.main()
