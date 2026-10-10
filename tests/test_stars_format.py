"""Independent procedural PC profiles and optional private genuine validation."""
from dataclasses import replace
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.dw3.save_codec import CNG_AES
from koei_editor.games.stars import stars_codec as codec, stars_parser as backend
from koei_editor.shared.adapter_contract import BoundScalarAdapter


@lru_cache(maxsize=4)
def procedural_raw(revision=0x170302F4, selection=3):
    """Generate cipher independently, with distinctive unknown bytes/padding."""
    parts = []
    with CNG_AES('CBC') as aes:
        for index in (9, *range(9)):
            size = 0x79B66 if index == 9 else 0x78E41
            payload = bytearray((bytes(range(256)) * ((size + 255) // 256))[:size])
            if index == 9:
                struct.pack_into('<3I', payload, 0, revision, selection, 2)
                struct.pack_into('<I', payload, 0x1CE, 213456)
            else:
                struct.pack_into('<I', payload, 0x2F6A, 12_000_000 if index == 1 else 500 + index)
                struct.pack_into('<h', payload, 0xA3C, index)
                payload[0x2F10:0x2F6A] = bytes(90)
                if index == 0:
                    struct.pack_into('<3H', payload, 0x2F10, 12, 0, 15000)
                if index == 3:
                    struct.pack_into('<H', payload, 0x2F10 + 44 * 2, 9999)
                if index == 8:
                    struct.pack_into('<H', payload, 0x2F10 + 7 * 2, 13)
            value = (index + 1) * 0.5 / 10
            for _ in range(10):
                value = (1 - value) * (value * 3.66)
            state = struct.unpack('<I', struct.pack('<d', value)[:4])[0]
            key = bytearray()
            for _ in range(16):
                state = (state * 214013 + 2531011) & 0xFFFFFFFF
                key.append(state >> 24)
            seed, state = 0xA9876540 + index, 0xA9876540 + index
            iv = bytearray()
            for _ in range(16):
                state = (state * 22695477 + 1) & 0xFFFFFFFF
                iv.append((state >> 16) & 255)
            padding = bytes([0xA0 + index]) * ((-size) % 16)
            parts.append(aes.transform(bytes(payload) + padding + b'FingerPrint01234',
                                       bytes(key), direction='encrypt', iv=bytes(iv))
                         + struct.pack('<I', seed))
    return b''.join(parts)


class StarsFormatTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / 'all-stars-copy.bin'
        self.raw = procedural_raw()
        self.source.write_bytes(self.raw)
        self.document = backend.read_save(self.source)

    def test_exact_profile_noop_and_adapter_identity(self):
        self.assertEqual(backend.serialize(self.document, {}), self.raw)
        self.assertEqual(backend.decode(memoryview(self.raw)).payload, self.document.payload)
        self.assertEqual(len(backend.fields_for(self.document)), 12)
        self.assertFalse(backend.FORMAT.game_load_verified)
        self.assertEqual(backend.INTEGRITY_KIND, 'none')
        adapter = BoundScalarAdapter('stars', '.bin', backend)
        self.assertEqual(adapter.decode(self.raw).format.id, 'stars')
        with self.assertRaises(SaveError):
            adapter.decode(self.raw, 'wo4')

    def test_foreign_truncated_revision_selection_and_corrupted_trailers(self):
        invalid = (None, '', b'', bytes(len(self.raw)), self.raw[:-1], self.raw + b'X',
                   procedural_raw(0x170302F3), procedural_raw(selection=9),
                   memoryview(self.raw * 2).cast('B', shape=(len(self.raw), 2)))
        for raw in invalid:
            with self.subTest(kind=type(raw).__name__), self.assertRaises(SaveError):
                backend.decode(raw)
        for index in (0, 1, 9):
            offset = 0x79B84 - 5 if index == 0 else 0x79B84 + index * 0x78E64 - 5
            raw = bytearray(self.raw)
            raw[offset] ^= 0x80
            with self.assertRaises(SaveError):
                backend.decode(raw)

    def test_targeted_gold_preserves_all_other_plaintext_and_encrypted_blocks(self):
        key = 'slot_3_gold'
        changes = backend.stage(self.document, {}, key, 321)
        self.assertEqual(backend.review(self.document, changes),
                         [(backend.FIELDS[3], 503, 321)])
        updated = backend.serialize(self.document, changes)
        decoded = backend.decode(updated)
        field = backend.FIELDS[3]
        self.assertEqual(decoded.payload[:field.offset], self.document.payload[:field.offset])
        self.assertEqual(decoded.payload[field.offset + 4:], self.document.payload[field.offset + 4:])
        self.assertEqual(field.value(decoded.payload), 321)
        offset = 0x79B84 + 3 * 0x78E64
        self.assertEqual(updated[:offset], self.raw[:offset])
        self.assertEqual(updated[offset + 0x78E64:], self.raw[offset + 0x78E64:])
        before_blocks, after_blocks = codec.decode(self.raw)[1], codec.decode(updated)[1]
        self.assertEqual([(b.iv_seed, b.padding) for b in before_blocks],
                         [(b.iv_seed, b.padding) for b in after_blocks])
        self.assertEqual(updated[offset + 0x78E64 - 4:offset + 0x78E64],
                         self.raw[offset + 0x78E64 - 4:offset + 0x78E64])

    def test_limits_preserve_cheated_balances_and_lifetime_reward_story_bytes(self):
        changes = backend.maximums(self.document, {})
        self.assertNotIn('slot_1_gold', changes)
        self.assertEqual(len(changes), 8)
        self.assertEqual(backend.maximums(self.document, {}, 'System history'), {})
        edited = backend.decode(backend.serialize(self.document, changes))
        self.assertEqual(edited.payload[:0x79B66], self.document.payload[:0x79B66])
        self.assertEqual(backend.FIELDS[1].value(edited.payload), 12_000_000)
        pending = backend.stage(self.document, {}, 'slot_1_gold', 100)
        self.assertEqual(backend.stage(self.document, pending, 'slot_1_gold', 12_000_000), {})
        for index in range(9):
            start = 0x79B66 + index * 0x78E41
            relative = 0x2F6A
            self.assertEqual(edited.payload[start:start + relative],
                             self.document.payload[start:start + relative])
            self.assertEqual(edited.payload[start + relative + 4:start + 0x78E41],
                             self.document.payload[start + relative + 4:start + 0x78E41])

    def test_invalid_edits_pending_changes_and_forged_snapshots(self):
        for value in (-1, 10_000_000, True, '900', 1.0):
            with self.subTest(value=value), self.assertRaises(SaveError):
                backend.stage(self.document, {}, 'slot_0_gold', value)
        for key in ('lifetime_gold', 'hero_0_exp', 'cards', 'story_complete', 'slot_9_gold'):
            for action in (backend.serialize, backend.maximums):
                with self.subTest(key=key), self.assertRaises(SaveError):
                    action(self.document, {key: 1})
        forged = (replace(self.document, raw=bytearray(self.raw)),
                  replace(self.document, payload=bytearray(self.document.payload)),
                  replace(self.document, format=replace(backend.FORMAT, id='wo4')),
                  replace(self.document, payload=b'X' + self.document.payload[1:]))
        for document in forged:
            with self.assertRaises(SaveError):
                backend.serialize(document, {})
        with self.assertRaises(TypeError):
            backend.field_map(self.document)['fake'] = backend.FIELDS[0]

    def test_empty_and_unknown_campaigns_cannot_be_created_by_resource_edits(self):
        payload = bytearray(self.document.payload)
        for index, hero in ((2, -1), (4, 100)):
            struct.pack_into('<h', payload, 0x79B66 + index * 0x78E41 + 0xA3C, hero)
        document = backend.decode(codec.encode(self.raw, bytes(payload)))
        mapping = backend.field_map(document)
        self.assertNotIn('slot_2_gold', mapping)
        self.assertNotIn('slot_4_gold', mapping)
        changes = backend.maximums(document, {})
        for index in (2, 4):
            with self.assertRaises(SaveError):
                backend.stage(document, {}, f'slot_{index}_gold', 9_999_999)
            self.assertNotIn(f'slot_{index}_gold', changes)
        edited = backend.decode(backend.serialize(document, changes))
        for index in (2, 4):
            start = 0x79B66 + index * 0x78E41
            self.assertEqual(edited.payload[start:start + 0x78E41],
                             document.payload[start:start + 0x78E41])

    def test_existing_material_quantities_are_surgical_without_granting_rewards(self):
        mapping = backend.field_map(self.document)
        self.assertIn('slot_0_material_0', mapping)
        self.assertNotIn('slot_0_material_1', mapping)
        self.assertNotIn('slot_0_material_2', mapping)
        self.assertEqual(backend.maximums(self.document, {}, 'Materials'), {})
        self.assertEqual(backend.limit_values(self.document, {}, ['slot_0_material_0']), {})
        key = 'slot_0_material_0'
        changes = backend.stage(self.document, {}, key, 9876)
        field = mapping[key]
        self.assertEqual(field.offset, 0x79B66 + 0x2F10)
        edited = backend.decode(backend.serialize(self.document, changes))
        self.assertEqual(edited.payload[:field.offset], self.document.payload[:field.offset])
        self.assertEqual(edited.payload[field.offset + 2:], self.document.payload[field.offset + 2:])
        self.assertEqual(field.value(edited.payload), 9876)
        self.assertEqual(backend.stage(self.document, changes, key, 12), {})
        for value in (0, 10000, -1, True):
            with self.assertRaises(SaveError):
                backend.stage(self.document, {}, key, value)
        for key in ('slot_0_material_1', 'slot_0_material_2', 'slot_0_material_45'):
            with self.assertRaises(SaveError):
                backend.stage(self.document, {}, key, 1)

    def test_backup_restore_snapshot_revalidation_and_source_copy_only(self):
        snapshot = backend.backup(self.document)
        self.assertEqual(snapshot.read_bytes(), self.raw)
        destination = self.folder / 'edited.bin'
        edited = backend.save_as(self.document, {'slot_0_gold': 123}, destination)
        self.assertEqual(self.source.read_bytes(), self.raw)
        self.assertEqual(backend.FIELDS[0].value(edited.payload), 123)
        with self.assertRaises(FileExistsError):
            backend.save_as(self.document, {}, destination)
        restored = self.folder / 'restored.bin'
        self.assertEqual(backend.restore(snapshot, restored).read_bytes(), self.raw)
        damaged = procedural_raw(0x170302F3)
        snapshot.write_bytes(damaged)
        metadata_path = snapshot.with_suffix('.json')
        metadata = json.loads(metadata_path.read_text())
        metadata['sha256'] = hashlib.sha256(damaged).hexdigest()
        metadata_path.write_text(json.dumps(metadata))
        rejected = self.folder / 'rejected.bin'
        with self.assertRaises(SaveError):
            backend.restore(snapshot, rejected)
        self.assertFalse(rejected.exists())
        self.source.write_bytes(self.raw[:-1] + b'\0')
        with self.assertRaises(SaveError):
            backend.save_as(self.document, {}, self.folder / 'changed.bin')

    def test_live_game_path_and_resolved_alias_rejected(self):
        live = self.folder / 'Documents' / 'KoeiTecmo' / 'WARRIORS ALL-STARS' / 'Savedata'
        live.mkdir(parents=True)
        source = live / 'SAVEDATA.BIN'
        source.write_bytes(self.raw)
        with self.assertRaises(SaveError):
            backend.read_save(source)
        with self.assertRaises(SaveError):
            backend.save_as(self.document, {}, live / 'edited.bin')
        alias = self.folder / 'alias'
        try:
            alias.symlink_to(live, target_is_directory=True)
        except OSError:
            return
        with self.assertRaises(SaveError):
            backend.read_save(alias / 'SAVEDATA.BIN')

    def test_history_inspection_keeps_available_and_earned_distinct(self):
        rows = backend.inspection_rows(self.document)
        self.assertEqual(len(rows), 15)
        self.assertTrue(any(row['label'] == 'Lifetime earned gold' and '213,456' in row['value']
                            for row in rows))
        self.assertTrue(any('current campaign slot 4' in row['value'] for row in rows))
        self.assertEqual(backend.record_label(4), 'Campaign slot 4')

    @unittest.skipUnless(os.environ.get('STARS_SAVE_COPY'), 'Set STARS_SAVE_COPY to a private genuine native copy.')
    def test_private_genuine_roundtrip_and_available_gold_edit(self):
        raw = Path(os.environ['STARS_SAVE_COPY']).read_bytes()
        document = backend.decode(raw)
        self.assertEqual(backend.serialize(document, {}), raw)
        self.assertEqual(struct.unpack_from('<I', document.payload)[0], 0x170302F4)
        self.assertEqual(backend.FIELDS[8].value(document.payload), 9_999_999)
        updated = backend.decode(backend.serialize(document, {'slot_8_gold': 123456}))
        offset = backend.FIELDS[8].offset
        self.assertEqual(updated.payload[:offset], document.payload[:offset])
        self.assertEqual(updated.payload[offset + 4:], document.payload[offset + 4:])
        self.assertEqual(backend.FIELDS[8].value(updated.payload), 123456)
        self.assertEqual(codec.decode(updated.raw)[1][9].iv_seed, codec.decode(raw)[1][9].iv_seed)
        material = backend.field_map(document)['slot_8_material_0']
        self.assertGreater(material.value(document.payload), 0)
        materials = backend.decode(backend.serialize(document, {material.id: 123}))
        self.assertEqual(materials.payload[:material.offset], document.payload[:material.offset])
        self.assertEqual(materials.payload[material.offset + 2:], document.payload[material.offset + 2:])
        self.assertEqual(material.value(materials.payload), 123)
        # Genuine parse/reconstruction evidence; this test never runs the game.
