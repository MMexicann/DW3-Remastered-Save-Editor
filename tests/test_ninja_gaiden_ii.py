"""Procedural contract/regression checks; native corpus is opt-in and private."""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.ninja_gaiden_ii import codec, parser as backend
from koei_editor.shared.adapter_contract import BoundScalarAdapter
from tests.scalar_contract import ScalarContractTests


def procedural_story():
    """Generated distinctive bytes, not a player save or game-load evidence."""
    raw = bytearray((index * 37 + 19) & 255 for index in range(codec.SAVE_SIZE))
    raw[:32] = codec.PROFILE_HEADER
    raw[48:560] = bytes(512)
    raw[48:52] = bytes.fromhex('00010102')
    for slot, (identity, quantity, variant) in enumerate(((8, 5, 0), (35, 12, 0),
                                                       (148, 30, 0), (75, 255, 0),
                                                       (999, 19, 7)), 1):
        struct.pack_into('>HBB', raw, 48 + 4 * slot, identity, quantity, variant)
    struct.pack_into('>I', raw, backend.ESSENCE_OFFSET, 0xF1234567)
    return codec.rebuild(raw)


class NGIIFormatTests(unittest.TestCase):
    def setUp(self):
        self.raw = procedural_story()
        self.document = backend.decode(self.raw)

    def test_checksum_modulo_and_noop_roundtrip(self):
        independent = 0
        for at in range(0, codec.CHECKSUM_OFFSET, 4):
            independent = (independent + int.from_bytes(self.raw[at:at + 4], 'big')) & 0xFFFFFFFF
        self.assertEqual(codec.checksum(self.raw), independent)
        self.assertEqual(int.from_bytes(self.raw[codec.CHECKSUM_OFFSET:codec.CHECKSUM_OFFSET + 4], 'big'), independent)
        self.assertEqual(backend.serialize(self.document, {}), self.raw)
        self.assertEqual(codec.decode(bytearray(self.raw)), self.raw)
        self.assertEqual(codec.decode(memoryview(self.raw)), self.raw)

    def test_header_revision_record_and_edition_rejection(self):
        for at in (0, 4, 8, 12, 16, 20, 24, 28, 48, 50, 51):
            broken = bytearray(self.raw)
            broken[at] ^= 0x80
            # A matching generic checksum must not replace native identity.
            struct.pack_into('>I', broken, codec.CHECKSUM_OFFSET, codec.checksum(bytes(broken)))
            with self.subTest(at=at), self.assertRaises(SaveError):
                backend.decode(broken)
        for raw in (self.raw[:-1], self.raw + b'\0', b'CON ' + self.raw,
                    b'ng2stryd' + bytes(35832), bytes(codec.SAVE_SIZE), None, 31744):
            with self.subTest(size=len(raw) if isinstance(raw, bytes) else None), self.assertRaises(SaveError):
                backend.decode(raw)
        with self.assertRaises(SaveError):
            backend.decode(self.raw, 'ninjagaiden_sigma2_pc')

    def test_body_and_stored_checksum_corruption_are_rejected(self):
        for at in (32, 40, 52, 559, 560, codec.CHECKSUM_OFFSET - 1, codec.CHECKSUM_OFFSET):
            broken = bytearray(self.raw)
            broken[at] ^= 1
            with self.subTest(at=at), self.assertRaises(SaveError):
                backend.decode(broken)

    def test_surgical_edits_preserve_native_seeds_unknowns_score_and_tail(self):
        changes = backend.stage(self.document, {}, 'yellow_essence', 12345)
        for field in backend.fields_for(self.document):
            if field.group == 'Existing stacks':
                changes = backend.stage(self.document, changes, field.id, 1)
        result = backend.serialize(self.document, changes)
        allowed = set(range(codec.CHECKSUM_OFFSET, codec.CHECKSUM_OFFSET + 4))
        for field in backend.fields_for(self.document):
            if field.id in changes:
                allowed.update(range(field.offset, field.offset + field.size))
        touched = {at for at, pair in enumerate(zip(self.raw, result)) if pair[0] != pair[1]}
        self.assertLessEqual(touched, allowed)
        self.assertEqual(result[:32], self.raw[:32])
        self.assertEqual(result[32:36], self.raw[32:36])
        self.assertEqual(result[560:564], self.raw[560:564])
        self.assertEqual(result[572:576], self.raw[572:576])
        self.assertEqual(result[588:592], self.raw[588:592])
        self.assertEqual(result[codec.CHECKSUM_OFFSET + 4:], self.raw[codec.CHECKSUM_OFFSET + 4:])
        self.assertEqual(backend.decode(result).payload, result)
        self.assertEqual(self.document.raw, self.raw)

    def test_item_eligibility_is_existing_unique_ordinary_quantity_only(self):
        raw = bytearray(self.raw)
        struct.pack_into('>HBB', raw, 48 + 6 * 4, 8, 2, 0)  # duplicate
        struct.pack_into('>HBB', raw, 48 + 7 * 4, 9, 5, 3)  # unknown variant
        struct.pack_into('>HBB', raw, 48 + 8 * 4, 10, 1, 0)  # one remaining
        struct.pack_into('>HBB', raw, 48 + 9 * 4, 11, 0, 0)  # empty/ownership ambiguity
        document = backend.decode(codec.rebuild(raw))
        keys = backend.field_map(document)
        for slot in (0, 1, 5, 6, 7, 8, 9, 10):
            self.assertNotIn(f'item_{slot}_quantity', keys)
        self.assertIn('item_2_quantity', keys)
        self.assertIn('item_3_quantity', keys)
        self.assertIn('item_4_quantity', keys)
        for value in (0, 13, True, 1.5, '2'):
            with self.subTest(value=value), self.assertRaises(SaveError):
                backend.stage(document, {}, 'item_2_quantity', value)

    def test_unusual_opened_values_unstage_and_bulk_max_is_disabled(self):
        fields = backend.fields_for(self.document)
        self.assertTrue(all(not field.maxable for field in fields))
        original = backend.field_map(self.document)['yellow_essence'].value(self.raw)
        changes = backend.stage(self.document, {}, 'yellow_essence', 1)
        self.assertEqual(backend.stage(self.document, changes, 'yellow_essence', original), {})
        self.assertEqual(backend.limit_values(self.document, changes, [field.id for field in fields]), {})
        self.assertEqual(backend.maximums(self.document, changes), changes)
        self.assertEqual(changes, {'yellow_essence': 1})
        stack = backend.field_map(self.document)['item_4_quantity']
        self.assertEqual(stack.maximum, 255)
        reduced = backend.stage(self.document, {}, stack.id, 1)
        self.assertEqual(backend.stage(self.document, reduced, stack.id, 255), {})

    def test_every_operation_rejects_foreign_forged_snapshot_and_malformed_changes(self):
        forged = replace(self.document, payload=self.raw[:-1] + bytes([self.raw[-1] ^ 1]))
        foreign = replace(self.document, format=replace(self.document.format, id='sigma2'))
        for document in (forged, foreign):
            for action in (lambda d: backend.fields_for(d), lambda d: backend.stage(d, {}, 'yellow_essence', 1),
                           lambda d: backend.maximums(d, {}), lambda d: backend.review(d, {}),
                           lambda d: backend.serialize(d, {})):
                with self.subTest(document=document.format.id), self.assertRaises(SaveError):
                    action(document)
        for changes in ([], None, {'unknown': 1}, {'yellow_essence': True},
                        {'item_1_quantity': 6}, {'item_1_quantity': 0}):
            for action in (lambda c: backend.stage(self.document, c, 'yellow_essence', 1),
                           lambda c: backend.maximums(self.document, c),
                           lambda c: backend.limit_values(self.document, c, []),
                           lambda c: backend.review(self.document, c),
                           lambda c: backend.serialize(self.document, c)):
                with self.subTest(changes=changes), self.assertRaises(SaveError):
                    action(changes)

    def test_restore_validates_bounded_bytes_even_with_matching_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = folder / 'copy.dat'
            source.write_bytes(self.raw)
            document = backend.read_save(source)
            snapshot = backend.backup(document)
            broken = bytearray(self.raw)
            broken[40] ^= 1
            snapshot.write_bytes(broken)
            manifest_path = snapshot.with_suffix('.json')
            manifest = json.loads(manifest_path.read_text())
            manifest['sha256'] = hashlib.sha256(broken).hexdigest()
            manifest_path.write_text(json.dumps(manifest))
            destination = folder / 'restore.dat'
            with self.assertRaises(SaveError):
                backend.restore(snapshot, destination)
            self.assertFalse(destination.exists())
            self.assertEqual(source.read_bytes(), self.raw)


class NGIIContractTests(ScalarContractTests, unittest.TestCase):
    game_id = backend.GAME_ID
    payload_integrity_offsets = frozenset(range(codec.CHECKSUM_OFFSET, codec.CHECKSUM_OFFSET + 4))

    def fixture_bytes(self):
        return procedural_story()


class NGIINativeTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('NGII_NATIVE_DIR'), 'private genuine NGII corpus not selected')
    def test_independent_genuine_stories_roundtrip_surgical_edits_and_foreign_con(self):
        folder = Path(os.environ['NGII_NATIVE_DIR'])
        stories = [path for path in folder.rglob('ng2stryd*.dat')
                   if path.is_file() and path.stat().st_size == codec.SAVE_SIZE]
        self.assertTrue(stories)
        for path in stories:
            document = backend.read_save(path)
            self.assertEqual(backend.serialize(document, {}), document.raw)
            changes = backend.stage(document, {}, 'yellow_essence', 12345)
            for field in backend.fields_for(document):
                if field.group == 'Existing stacks':
                    changes = backend.stage(document, changes, field.id, 1)
            result = backend.decode(backend.serialize(document, changes))
            self.assertEqual(backend.field_map(result)['yellow_essence'].value(result.payload), 12345)
            self.assertEqual(path.read_bytes(), document.raw)
        for path in folder.rglob('ng2stryd*.dat'):
            if path.is_file() and path.stat().st_size != codec.SAVE_SIZE:
                with self.assertRaises(SaveError):
                    backend.read_save(path)


if __name__ == '__main__':
    unittest.main()
