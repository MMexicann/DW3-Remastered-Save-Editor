"""Independent adversarial review: immutable snapshots and restore qualification."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from models import SaveError
import wo3u_parser as parser
import copy_storage
from tests.test_wo3u_format import procedural_raw


class WO3ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = procedural_raw()
        cls.document = parser.decode(cls.raw)

    def test_forged_mutable_snapshot_and_boolean_seed_are_rejected(self):
        doc = self.document
        forged = (replace(doc, raw=bytearray(doc.raw)),
                  replace(doc, payload=bytearray(doc.payload)),
                  replace(doc, seed=False))
        for snapshot in forged:
            with self.subTest(raw_type=type(snapshot.raw), payload_type=type(snapshot.payload),
                              seed_type=type(snapshot.seed)), self.assertRaises(SaveError):
                parser.serialize(snapshot, {})

    def test_unrecognized_weapon_slot_layout_is_read_only(self):
        raw = bytearray(self.raw)
        raw[parser.WEAPON_BASE + 2] = 255
        doc = parser.decode(raw)
        self.assertFalse(any(key.startswith('weapon_0_') for key in parser.field_map(doc)))
        changed = parser.serialize(doc, parser.maximums(doc, {}, 'Weapons'))
        self.assertEqual(changed[parser.WEAPON_BASE:parser.WEAPON_BASE + parser.WEAPON_STRIDE],
                         bytes(raw[parser.WEAPON_BASE:parser.WEAPON_BASE + parser.WEAPON_STRIDE]))

    def test_restore_validates_the_same_bytes_that_are_written(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            source = folder / 'source.bin'
            source.write_bytes(self.raw)
            backup = parser.backup(parser.read_save(source))
            destination = folder / 'restored.bin'
            genuine_restore = copy_storage.restore_snapshot

            def change_backup_then_restore(*args, **kwargs):
                # Simulate another process replacing the backup and manifest
                # after any earlier parser read but before the restore read.
                bad = b'MZ\0\0' + self.raw[4:]
                backup.write_bytes(bad)
                manifest_path = backup.with_suffix('.json')
                metadata = json.loads(manifest_path.read_text())
                metadata['sha256'] = hashlib.sha256(bad).hexdigest()
                manifest_path.write_text(json.dumps(metadata))
                return genuine_restore(*args, **kwargs)

            with patch.object(parser, 'restore_snapshot', side_effect=change_backup_then_restore):
                with self.assertRaises(SaveError):
                    parser.restore(backup, destination)
            self.assertFalse(destination.exists())

    def test_slot_reduction_checks_unknown_and_zero_rank_attributes(self):
        for identity, rank in ((222, 1), (5, 0)):
            raw = bytearray(self.raw)
            raw[parser.WEAPON_BASE + 5] = identity
            raw[parser.WEAPON_BASE + 13] = rank
            doc = parser.decode(raw)
            with self.subTest(identity=identity, rank=rank), self.assertRaises(SaveError):
                parser.stage(doc, {}, 'weapon_0_slots', 1)

    def test_zero_rank_stays_zero_after_weapon_max_and_new_slot_count(self):
        raw = bytearray(self.raw)
        raw[parser.WEAPON_BASE + 12] = 0
        doc = parser.decode(raw)
        changes = parser.maximums(doc, {}, 'Weapons')
        changes = parser.stage(doc, changes, 'weapon_0_slots', 8)
        self.assertEqual(parser.serialize(doc, changes)[parser.WEAPON_BASE + 12], 0)

    def test_resource_bulk_limit_requests_remain_excluded(self):
        keys = ['growth_points', 'gems', 'orb_0', 'material_0_0']
        self.assertEqual(parser.limit_values(self.document, {}, keys), {})

    def test_speed_max_respects_natural_cap_and_preserves_existing_cheat_value(self):
        raw = bytearray(self.raw)
        first = parser.OFFICER_BASE + 8
        second = first + parser.OFFICER_STRIDE
        raw[first:first + 2] = (100).to_bytes(2, 'little')
        raw[second:second + 2] = (200).to_bytes(2, 'little')
        doc = parser.decode(raw)
        changes = parser.maximums(doc, {}, 'Officers')
        self.assertEqual(changes['officer_0_speed'], 180)
        self.assertNotIn('officer_1_speed', changes)
        changed = parser.serialize(doc, changes)
        self.assertEqual(int.from_bytes(changed[first:first + 2], 'little'), 180)
        self.assertEqual(int.from_bytes(changed[second:second + 2], 'little'), 200)
        with self.assertRaises(SaveError):
            parser.stage(doc, {}, 'officer_0_speed', 181)


if __name__ == '__main__':
    unittest.main()
