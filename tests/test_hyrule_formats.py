"""Procedural preservation/dependency tests; optional upstream reference exports.

Upstream bundled files are source examples, not independent player-save or
edited game-load validation. They are never committed to this repository.
"""
from dataclasses import replace
import os
from pathlib import Path
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.hyrule_warriors import parser as hw
from koei_editor.games.age_of_calamity import parser as aoc


def procedural_hw():
    raw = bytearray((17 * i + 23) & 255 for i in range(hw.SAVE_SIZE))
    raw[:4] = hw.LAYOUT_MARKER
    raw[hw.WEAPON_OFFSET:hw.WEAPON_OFFSET + hw.WEAPON_COUNT * hw.WEAPON_STRIDE] = bytes(hw.WEAPON_COUNT * hw.WEAPON_STRIDE)
    raw[0x13D2C:0x13D2C + len(hw.MATERIALS) * 2] = bytes(len(hw.MATERIALS) * 2)
    for _, offset, items in hw.MAPS:
        for index, _ in items:
            raw[offset + index] = 0
    raw[0x13D2C:0x13D2E] = (10).to_bytes(2, 'big')
    raw[0x13D2E:0x13D30] = (1200).to_bytes(2, 'big')
    raw[0x141E8] = 2
    raw[0x19240] = 1
    raw[hw.RUPEES_OFFSET:hw.RUPEES_OFFSET + 4] = (500).to_bytes(4, 'big')
    offset = hw.WEAPON_OFFSET
    raw[offset] = 3
    raw[offset + 4:offset + 8] = (0).to_bytes(4, 'big')
    raw[offset + 8:offset + 10] = (80).to_bytes(2, 'big')
    raw[offset + 10:offset + 12] = (2).to_bytes(2, 'big')
    raw[offset + 12:offset + 44] = b'\xff' * 32
    raw[offset + 12:offset + 16] = (32).to_bytes(4, 'big')
    raw[offset + 44:offset + 48] = (1000).to_bytes(4, 'big')
    raw[offset + 16:offset + 20] = (41).to_bytes(4, 'big')
    raw[offset + 48:offset + 52] = (25000).to_bytes(4, 'big')
    raw[offset + hw.WEAPON_STRIDE] = 11  # Master Sword state, never writable.
    unknown = offset + 2 * hw.WEAPON_STRIDE
    raw[unknown] = 3
    raw[unknown + 4:unknown + 8] = (0xF00D).to_bytes(4, 'big')
    return bytes(raw)


def procedural_aoc():
    raw = bytearray((19 * i + 27) & 255 for i in range(aoc.SAVE_SIZE))
    raw[:4] = aoc.LAYOUT_MARKER
    raw[0x2C2DD:0x2C2DD + 176] = bytes(176)
    raw[aoc.WEAPON_OFFSET:aoc.WEAPON_OFFSET + 21 * 71 * 81] = bytes(21 * 71 * 81)
    offset = aoc.WEAPON_OFFSET
    raw[offset:offset + 2] = (1).to_bytes(2, 'little')
    raw[offset + 0x4C] = 0
    raw[aoc.TOTAL_RUPEES_OFFSET:aoc.TOTAL_RUPEES_OFFSET + 4] = (500_000).to_bytes(4, 'little')
    raw[aoc.RUPEES_OFFSET:aoc.RUPEES_OFFSET + 4] = (500).to_bytes(4, 'little')
    for identity, quantity, discovered in ((0, 10, 1), (1, 1200, 1), (151, 1250, 1),
                                            (149, 5, 1), (166, 2, 2), (170, 2000, 1),
                                            (7, 0, 1), (175, 100, 1)):
        offset = 0x2C14E + identity * 2
        raw[offset:offset + 2] = quantity.to_bytes(2, 'little')
        raw[0x2C2DD + identity] = discovered
    return bytes(raw)


class BackendChecks:
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / ('copy' + self.backend.EXTENSION)
        self.raw = self.fixture()
        self.path.write_bytes(self.raw)
        self.document = self.backend.read_save(self.path)

    def test_immutable_roundtrip_and_cross_platform_rejection(self):
        backend, document = self.backend, self.document
        self.assertEqual(backend.serialize(document, {}), self.raw)
        self.assertTrue(document.format.sample_verified)
        with self.assertRaises(SaveError):
            backend.decode(self.raw, 'other_platform')
        for mutated in (replace(document, payload=bytearray(document.payload)),
                        replace(document, payload=document.payload[:-1] + bytes([document.payload[-1] ^ 1]))):
            with self.assertRaises(SaveError):
                backend.serialize(mutated, {})

    def test_reject_truncated_oversized_wrong_marker_and_invalid_changes(self):
        backend = self.backend
        for raw in (self.raw[:-1], self.raw + b'\0', b'\0' * len(self.raw), self.raw[4:] + self.raw[:4]):
            with self.subTest(size=len(raw)), self.assertRaises(SaveError):
                backend.decode(raw)
        for key, value in (('unmapped', 1), ('rupees', True), ('rupees', -1), ('rupees', 10_000_000)):
            with self.assertRaises(SaveError):
                backend.stage(self.document, {}, key, value)

    def test_endian_surgical_edit_review_and_unstage(self):
        backend, document = self.backend, self.document
        pending = {}
        changes = backend.stage(document, pending, 'rupees', 123456)
        self.assertEqual(pending, {})
        self.assertEqual(backend.stage(document, changes, 'rupees', 500), {})
        self.assertEqual(backend.review(document, changes)[0][1:], (500, 123456))
        raw = backend.serialize(document, changes)
        offset = backend.RUPEES_OFFSET
        self.assertEqual(raw[:offset], self.raw[:offset])
        self.assertEqual(raw[offset + 4:], self.raw[offset + 4:])
        self.assertEqual(raw[offset:offset + 4], (123456).to_bytes(4, backend.BYTEORDER))

    def test_max_preserves_above_cap_and_original_unstage(self):
        backend, document = self.backend, self.document
        field = backend.field_map(document)['material_1']
        self.assertEqual(field.value(document.payload), 1200)
        changes = backend.maximums(document, {})
        self.assertNotIn('material_1', changes)
        pending = backend.stage(document, {}, 'material_1', 1)
        self.assertEqual(backend.stage(document, pending, 'material_1', 1200), {})
        self.assertEqual(self.path.read_bytes(), self.raw)

    def test_backup_save_restore_and_source_change_protection(self):
        backend, document = self.backend, self.document
        destination = self.path.with_name('edited' + backend.EXTENSION)
        changes = backend.stage(document, {}, 'rupees', 321)
        edited = backend.save_as(document, changes, destination)
        self.assertEqual(backend.field_map(edited)['rupees'].value(edited.payload), 321)
        self.assertEqual(self.path.read_bytes(), self.raw)
        snapshots = tuple((self.path.parent / 'WarriorsEditorBackups').glob('*'))
        backup = next(path for path in snapshots if path.suffix != '.json')
        restored = backend.restore(backup, self.path.with_name('restored' + backend.EXTENSION))
        self.assertEqual(restored.read_bytes(), self.raw)
        with self.assertRaises(FileExistsError):
            backend.save_as(document, {}, destination)
        self.path.write_bytes(self.raw[:-1] + bytes([self.raw[-1] ^ 1]))
        with self.assertRaises(SaveError):
            backend.save_as(document, {}, self.path.with_name('stale' + backend.EXTENSION))

    def test_optional_upstream_reference_roundtrip_and_edit(self):
        path = os.environ.get(self.reference_env)
        if not path:
            self.skipTest('No private upstream reference export supplied; independent/game-load claims excluded.')
        document = self.backend.read_save(path)
        self.assertEqual(self.backend.serialize(document, {}), document.raw)
        field = self.backend.field_map(document)['rupees']
        value = (field.value(document.payload) + 1) % field.maximum
        changes = self.backend.stage(document, {}, field.id, value)
        raw = self.backend.serialize(document, changes)
        self.assertEqual(self.backend.field_map(self.backend.decode(raw))[field.id].value(raw), value)
        self.assertTrue(document.format.sample_verified)


    def test_optional_genuine_export_all_qualified_fields_are_surgical(self):
        path = os.environ.get(self.genuine_env)
        if not path:
            self.skipTest('No private genuine exported save copy supplied.')
        document = self.backend.read_save(path)
        original = Path(path).read_bytes()
        self.assertEqual(self.backend.serialize(document, {}), original)
        changes = {}
        fields = self.backend.fields_for(document)
        for field in fields:
            old = field.value(document.payload)
            for value in (field.minimum, min(field.maximum, old + 1)):
                if old != value:
                    changes = self.backend.stage(document, changes, field.id, value)
                    break
        result = self.backend.serialize(document, changes)
        allowed = {i for field in fields if field.id in changes
                   for i in range(field.offset, field.offset + field.size)}
        self.assertLessEqual({i for i, (a, b) in enumerate(zip(original, result)) if a != b}, allowed)
        self.assertEqual(Path(path).read_bytes(), original)
        self.assertEqual(self.backend.decode(result).payload, result)


class HyruleTests(BackendChecks, unittest.TestCase):
    backend = hw
    fixture = staticmethod(procedural_hw)
    reference_env = 'HYRULE_SOURCE_REFERENCE'
    genuine_env = 'HYRULE_SAVE_COPY'

    def test_existing_material_map_and_weapon_qualification(self):
        fields = hw.field_map(self.document)
        self.assertIn('material_0', fields)
        self.assertNotIn('material_2', fields)
        self.assertIn('map_1_0', fields)
        self.assertNotIn('map_2_0', fields)
        self.assertIn('weapon_1_stars', fields)
        self.assertNotIn('weapon_2_stars', fields)
        self.assertNotIn('weapon_3_stars', fields)
        self.assertNotIn('weapon_1_skill_1_kos', fields)
        self.assertIn('weapon_1_skill_0_kos', fields)
        for identity in (61, 109, 110, 152):
            changed = bytearray(self.raw)
            changed[hw.WEAPON_OFFSET + 4:hw.WEAPON_OFFSET + 8] = identity.to_bytes(4, 'big')
            self.assertNotIn('weapon_1_stars', hw.field_map(hw.decode(bytes(changed))))

    def test_stars_and_ordinary_seal_surgical_and_prerequisites_preserved(self):
        changes = hw.stage(self.document, {}, 'weapon_1_stars', 5)
        changes = hw.stage(self.document, changes, 'weapon_1_skill_0_kos', 0)
        raw = hw.serialize(self.document, changes)
        allowed = set(range(hw.WEAPON_OFFSET + 10, hw.WEAPON_OFFSET + 12))
        allowed.update(range(hw.WEAPON_OFFSET + 44, hw.WEAPON_OFFSET + 48))
        self.assertLessEqual({i for i, (a, b) in enumerate(zip(self.raw, raw)) if a != b}, allowed)
        for key, value in (('weapon_1_skill_0_kos', 1001), ('weapon_1_skill_1_kos', 0),
                           ('weapon_1_stars', 6)):
            with self.assertRaises(SaveError):
                hw.stage(self.document, {}, key, value)
        self.assertNotIn('weapon_1_skill_0_kos', hw.maximums(self.document, {}))
        self.assertFalse(hw.field_map(self.document)['weapon_1_skill_0_kos'].maxable)


class CalamityTests(BackendChecks, unittest.TestCase):
    backend = aoc
    fixture = staticmethod(procedural_aoc)
    reference_env = 'CALAMITY_SOURCE_REFERENCE'
    genuine_env = 'CALAMITY_SAVE_COPY'

    def test_discovered_exhausted_dlc_and_special_qualification(self):
        fields = aoc.field_map(self.document)
        self.assertIn('material_7', fields)  # Exhausted but previously discovered.
        self.assertNotIn('material_2', fields)
        self.assertNotIn('material_166', fields)  # Unknown discovery flag2.
        self.assertNotIn('material_149', fields)  # Terrako story collectible.
        self.assertEqual(fields['material_151'].maximum, 9999)
        self.assertEqual(fields['material_170'].maximum, 9999)
        self.assertEqual(fields['material_175'].maximum, 9999)
        self.assertIn('weapon_0_1_protected', fields)
        self.assertEqual(fields['material_0'].maximum, 999)

    def test_inventory_refill_preserves_discovery_and_collectibles(self):
        changes = aoc.maximums(self.document, {})
        raw = aoc.serialize(self.document, changes)
        allowed = set()
        for key in changes:
            field = aoc.field_map(self.document)[key]
            allowed.update(range(field.offset, field.offset + field.size))
        self.assertLessEqual({i for i, (a, b) in enumerate(zip(self.raw, raw)) if a != b}, allowed)
        self.assertEqual(raw[0x2C2DD:0x2C2DD + 175], self.raw[0x2C2DD:0x2C2DD + 175])
        self.assertEqual(raw[0x2C14E + 149 * 2:0x2C14E + 150 * 2],
                         self.raw[0x2C14E + 149 * 2:0x2C14E + 150 * 2])

    def test_weapon_protection_identity_and_lifetime_dependencies(self):
        fields = aoc.field_map(self.document)
        self.assertEqual(fields['rupees'].maximum, 500_000)
        with self.assertRaises(SaveError):
            aoc.stage(self.document, {}, 'rupees', 500_001)
        changes = aoc.stage(self.document, {}, 'weapon_0_1_protected', 1)
        raw = aoc.serialize(self.document, changes)
        self.assertEqual({i for i, (a, b) in enumerate(zip(self.raw, raw)) if a != b},
                         {aoc.WEAPON_OFFSET + 0x4C})
        self.assertNotIn('weapon_0_1_protected', aoc.maximums(self.document, {}))
        for delta, value in ((0x4C, 2), (0x27, 1)):
            modified = bytearray(self.raw)
            modified[aoc.WEAPON_OFFSET + delta] = value
            self.assertNotIn('weapon_0_1_protected', aoc.field_map(aoc.decode(bytes(modified))))
        modified = bytearray(self.raw)
        modified[aoc.WEAPON_OFFSET:aoc.WEAPON_OFFSET + 2] = (171).to_bytes(2, 'little')
        self.assertNotIn('weapon_0_1_protected', aoc.field_map(aoc.decode(bytes(modified))))


# Exercise the registered platform binding as well as the standalone parsers.
from tests.scalar_contract import ScalarContractTests


class HyruleRegisteredTests(ScalarContractTests, unittest.TestCase):
    game_id = 'hyrule_warriors'

    def fixture_bytes(self):
        return procedural_hw()


class CalamityRegisteredTests(ScalarContractTests, unittest.TestCase):
    game_id = 'age_of_calamity'

    def fixture_bytes(self):
        return procedural_aoc()
