import unittest

from koei_editor.games.dw3.models import SaveError
import koei_editor.games.origins.origins_weapons as weapons


def inventory(revision):
    base = weapons.BASES[revision]
    payload = bytearray(b'\xa7' * (base + weapons.SERIALIZED_COUNT * weapons.RECORD_SIZE))
    for index in range(weapons.SERIALIZED_COUNT):
        offset = base + index * weapons.RECORD_SIZE
        payload[offset:offset + 2] = b'\xff\xff'
    return payload


def record(payload, revision, index, weapon_id, upgrade):
    offset = weapons.BASES[revision] + index * weapons.RECORD_SIZE
    payload[offset:offset + 2] = weapon_id.to_bytes(2, 'little')
    payload[offset + 2] = upgrade
    return offset


class WeaponInventoryTests(unittest.TestCase):
    def test_revision_offsets_and_record_preservation(self):
        for revision in (16, 17, 29):
            with self.subTest(revision=revision):
                payload = inventory(revision)
                offset = record(payload, revision, 43, 175, 17)
                original = bytes(payload)
                spec, = weapons.weapon_specs(original, revision)
                self.assertEqual(spec['offset'], offset + 2)
                self.assertEqual(spec['size'], 1)
                self.assertEqual(spec['maximum'], 99)
                weapons.validate_weapon_changes(original, revision, {spec['id']: 99})
                output = bytearray(original)
                output[spec['offset']] = 99
                self.assertEqual([i for i, pair in enumerate(zip(original, output))
                                  if pair[0] != pair[1]], [offset + 2])
                self.assertEqual(weapons.weapon_records(original, revision)[0].traits,
                                 (0xa7a7,) * 6)

    def test_qualification_preserves_unknown_empty_and_reserved_records(self):
        payload = inventory(29)
        record(payload, 29, 0, 0, 0)
        record(payload, 29, 1, 299, 1)
        record(payload, 29, 2, 300, 99)
        record(payload, 29, 3, 1, 100)
        record(payload, 29, 4, 7, 99)  # Valid special weapon, material flag clear.
        record(payload, 29, 5, 100, 17)  # Unused catalogue ID.
        record(payload, 29, 849, 2, 99)
        record(payload, 29, 850, 2, 99)
        record(payload, 29, 999, 2, 99)
        self.assertEqual([spec['slot'] for spec in weapons.weapon_specs(payload, 29)],
                         [1, 850])
        self.assertEqual([rec.index for rec in weapons.weapon_records(payload, 29)],
                         [0, 1, 3, 4, 5, 849])
        weapons.validate_weapon_changes(payload, 29, {'weapon_0000_upgrade': 99})
        for key in ('weapon_0001_upgrade', 'weapon_0002_upgrade',
                    'weapon_0003_upgrade', 'weapon_0004_upgrade', 'weapon_0005_upgrade',
                    'weapon_0850_upgrade', 'weapon_0999_upgrade'):
            with self.assertRaises(SaveError):
                weapons.validate_weapon_changes(payload, 29, {key: 99})

    def test_catalogue_qualification_includes_zero_and_excludes_special_ids(self):
        self.assertEqual(len(weapons.KNOWN_WEAPON_IDS), 244)
        self.assertEqual(len(weapons.REFORGABLE_WEAPON_IDS), 195)
        self.assertTrue(weapons.REFORGABLE_WEAPON_IDS <= weapons.KNOWN_WEAPON_IDS)
        for revision in (16, 17, 29):
            payload = inventory(revision)
            for index, weapon_id in enumerate((0, 7, 97, 100, 230, 237, 285, 291, 299)):
                record(payload, revision, index, weapon_id, 0)
            self.assertEqual([spec['slot'] for spec in weapons.weapon_specs(payload, revision)],
                             [1, 5, 7])

    def test_limits_are_gameplay_limits(self):
        payload = inventory(16)
        record(payload, 16, 0, 1, 1)
        key = 'weapon_0000_upgrade'
        for value in (0, 98, 99):
            weapons.validate_weapon_changes(payload, 16, {key: value})
        for value in (-1, 100, 255, True, 1.0, '99'):
            with self.assertRaises(SaveError):
                weapons.validate_weapon_changes(payload, 16, {key: value})

    def test_invalid_revision_and_truncated_inventory_rejected(self):
        with self.assertRaises(SaveError):
            weapons.weapon_specs(inventory(29), 28)
        with self.assertRaises(SaveError):
            weapons.weapon_specs(inventory(29)[:-1], 29)


if __name__ == '__main__':
    unittest.main()
