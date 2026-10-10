"""Independent adversarial checks of the native SW4 DX production contract."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import samurai4dx_codec as codec
import samurai4dx_parser as backend
from models import SaveError
from tests.scalar_contract import ScalarContractTests
from tests.test_samurai4dx_format import procedural_raw, seal


class Samurai4DXIndependentContractTests(ScalarContractTests, unittest.TestCase):
    game_id = 'samurai4dx'
    payload_integrity_offsets = frozenset(
        position for offset in codec.CHECKSUM_OFFSETS for position in range(offset, offset + 4))

    def fixture_bytes(self):
        return procedural_raw()

    def test_noop_stage_unstage_review_and_surgical_roundtrip(self):
        self.assertEqual(self.adapter.serialize(self.document, {}), self.raw)
        field, original, value = self.editable_value()
        pending = {}
        edits = self.adapter.stage(self.document, pending, field.id, value)
        self.assertEqual(pending, {})
        self.assertEqual(edits, {field.id: value})
        self.assertEqual(self.adapter.stage(self.document, edits, field.id, original), {})
        self.assertEqual([(f.id, before, after) for f, before, after in self.adapter.review(self.document, edits)],
                         [(field.id, original, value)])
        reopened = self.adapter.decode(self.adapter.serialize(self.document, edits))
        expected = bytearray(self.adapter.changed_payload(self.document, edits))
        for offset, checksum in zip(codec.CHECKSUM_OFFSETS, codec.checksums(expected)):
            struct.pack_into('<I', expected, offset, checksum)
        self.assertEqual(reopened.payload, bytes(expected))
        allowed = set(range(field.offset, field.offset + field.size)) | set(self.payload_integrity_offsets)
        touched = {offset for offset, (before, after) in enumerate(zip(self.document.payload, reopened.payload))
                   if before != after}
        self.assertTrue(touched)
        self.assertLessEqual(touched, allowed)
        self.assertEqual(self.source.read_bytes(), self.raw)

    def test_mutable_memoryview_and_boolean_seed_snapshots_fail_closed(self):
        document = self.document
        zero = backend.decode(seal(document.payload, seed=0))
        forged = (replace(document, raw=bytearray(document.raw)),
                  replace(document, raw=memoryview(document.raw)),
                  replace(document, payload=bytearray(document.payload)),
                  replace(document, payload=memoryview(document.payload)),
                  replace(zero, seed=False))
        for snapshot in forged:
            with self.subTest(raw=type(snapshot.raw), payload=type(snapshot.payload), seed=type(snapshot.seed)):
                with self.assertRaises(SaveError):
                    backend.validate_document(snapshot)
                with self.assertRaises(SaveError):
                    backend.serialize(snapshot, {})

    def test_unlock_requires_usable_owned_weapon_pool(self):
        # Explicitly empty the own pool; helper fixtures may include starters.
        payload = bytearray(self.document.payload)
        payload[backend.OFFICER_BASE + backend.OFFICER_STRIDE + 0x3F] &= ~1
        for slot in range(backend.WEAPON_SLOTS):
            offset = backend.WEAPON_BASE + (backend.WEAPON_SLOTS + slot) * backend.WEAPON_STRIDE
            struct.pack_into('<H', payload, offset, 180)
        document = backend.decode(seal(payload))
        key = 'officer_1_unlocked'
        with self.assertRaises(SaveError):
            backend.stage(document, {}, key, 1)
        with self.assertRaises(SaveError):
            backend.serialize(document, {key: 1})
        maximums = backend.maximums(document, {}, 'Unlocks')
        self.assertNotIn(key, maximums)
        # Officer zero has occupied slots; unlocking does not manufacture items.
        edits = backend.stage(document, {}, 'officer_0_unlocked', 1)
        opened = backend.decode(backend.serialize(document, edits))
        begin = backend.WEAPON_BASE
        end = begin + backend.WEAPON_OWNERS * backend.WEAPON_SLOTS * backend.WEAPON_STRIDE
        self.assertEqual(opened.payload[begin:end], document.payload[begin:end])
        self.assertEqual(opened.payload[backend.OFFICER_BASE + 0x3F], 0xA5)

    def test_rank_max_preserves_below_minimum_existing_rank(self):
        payload = bytearray(self.document.payload)
        payload[backend.WEAPON_BASE + 0x12] = 0
        document = backend.decode(seal(payload))
        key = 'weapon_0_0_skill_0_rank'
        self.assertNotIn(key, backend.maximums(document, {}, 'Weapons'))
        self.assertEqual(backend.serialize(document, {}), document.raw)

    def test_skill_rank_and_activation_order_preserve_marker_and_unrelated_flags(self):
        rank, active = 'weapon_0_0_skill_0_rank', 'weapon_0_0_skill_0_active'
        first = backend.serialize(self.document, {rank: 5, active: 1})
        second = backend.serialize(self.document, {active: 1, rank: 5})
        self.assertEqual(first, second)
        payload = backend.decode(first).payload
        self.assertEqual(payload[backend.WEAPON_BASE + 0x1A], 0xA2)
        lowered = backend.decode(backend.serialize(backend.decode(first), {rank: 2})).payload
        self.assertEqual(lowered[backend.WEAPON_BASE + 0x1A], 0xA2)

    def test_restore_qualifies_exact_written_bytes_after_snapshot_replacement(self):
        snapshot = backend.backup(self.document)
        damaged = bytearray(self.raw)
        damaged[codec.PAYLOAD_OFFSET + 77] ^= 1
        damaged = bytes(damaged)
        real_restore = backend.restore_snapshot

        def replace_before_final_read(path, *args, **kwargs):
            metadata_path = Path(path).with_suffix('.json')
            metadata = json.loads(metadata_path.read_text())
            metadata['sha256'] = hashlib.sha256(damaged).hexdigest()
            Path(path).write_bytes(damaged)
            metadata_path.write_text(json.dumps(metadata))
            return real_restore(path, *args, **kwargs)

        destination = self.folder / 'raced-restored.dat'
        with patch.object(backend, 'restore_snapshot', side_effect=replace_before_final_read):
            with self.assertRaises(SaveError):
                backend.restore(snapshot, destination)
        self.assertFalse(destination.exists())

    def test_live_and_symlinked_save_paths_are_rejected_for_all_copy_operations(self):
        live = self.folder / 'KoeiTecmo' / 'SAMURAI WARRIORS 4 DX' / 'Savedata'
        live.mkdir(parents=True)
        source = live / 'save.dat'
        source.write_bytes(self.raw)
        alias = self.folder / 'alias.dat'
        alias.symlink_to(source)
        for path in (source, alias):
            with self.assertRaises(SaveError):
                backend.read_save(path)
        with self.assertRaises(SaveError):
            backend.save_as(self.document, {}, live / 'edited.dat')
        with self.assertRaises(SaveError):
            backend.backup(replace(self.document, source=alias))
        snapshot = backend.backup(self.document)
        with self.assertRaises(SaveError):
            backend.restore(snapshot, live / 'restored.dat')


if __name__ == '__main__':
    unittest.main()
