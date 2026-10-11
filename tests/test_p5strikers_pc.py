"""Procedural native-size guards plus optional complete private player copies.

No player bytes, stream/account values or names are published. Synthetic
fixtures test safety and byte preservation, not successful game loading.
"""
from dataclasses import replace
from functools import lru_cache
import os
from pathlib import Path
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.p5strikers_pc import codec, parser
from koei_editor.research.p5s import p5s_codec as research


@lru_cache(maxsize=1)
def procedural_payload():
    data = bytearray(codec.SAVE_SIZE)
    data[:4] = codec.PC_VERSION_BYTES
    data[4:8] = (1).to_bytes(4, 'little', signed=True)
    for slot in range(codec.PC_SLOT_COUNT):
        base = codec.PC_HEADER_SIZE + slot * codec.PC_SLOT_SIZE
        data[base:base + 2] = b'\xff\xff'
        data[base + codec.MARKER_RELATIVE:base + codec.MARKER_RELATIVE + 4] = codec.PC_LAYOUT_MARKER.to_bytes(4, 'little')
    base = parser._base(1)
    data[base:base + 2] = b'\x12\x00'
    for offset, text in ((codec.NAME_RELATIVE, b'Example'), (codec.NAME_RELATIVE + codec.NAME_SIZE, b'Player')):
        data[base + offset:base + offset + len(text)] = text
    data[base + 0x8788E:base + 0x87892] = (12345).to_bytes(4, 'little')
    data[base + 0x87892:base + 0x87896] = (99999999).to_bytes(4, 'little')
    data[base + 0x876E2:base + 0x876E6] = (7).to_bytes(4, 'little')
    data[base + 0x869B2] = 4
    data[base + 0x869B8:base + 0x869BA] = b'\x08\x19'  # Unknown adjacent byte; inspection only.
    data[base + 0x869DA] = 143  # Preserve unusual quantity.
    data[base + 0x86B08] = 3
    data[base + 0x2000:base + 0x2010] = b'opaque ownership'
    data[-20:-4] = b'opaque tail data'
    return codec.with_checksum(bytes(data))


@lru_cache(maxsize=1)
def procedural_save():
    return research.transform(procedural_payload()[:-4], 0x123456) + procedural_payload()[-4:]


class NativePCSafetyTests(unittest.TestCase):
    def setUp(self):
        self.doc = parser.decode(procedural_save())

    def test_unchanged_roundtrip_and_known_checksum_layer(self):
        self.assertEqual(parser.serialize(self.doc, {}), procedural_save())
        self.assertEqual(self.doc.payload, procedural_payload())
        self.assertEqual(self.doc.payload[-4], sum(self.doc.payload[:-4]) % 256)
        self.assertNotIn(str(self.doc.seed), repr(self.doc))
        self.assertTrue(parser.FORMAT.sample_verified)
        self.assertFalse(parser.FORMAT.game_load_verified)

    def test_only_occupied_slot_positive_ordinary_stacks(self):
        mapping = parser.field_map(self.doc)
        self.assertEqual(set(mapping), {'slot_1_money', 'slot_1_persona_points', 'slot_1_bond_points',
                                        'slot_1_item_869b2', 'slot_1_item_86b08'})
        for key in ('slot_0_money', 'slot_2_money', 'slot_1_item_869b8', 'slot_1_item_869da', 'slot_1_item_869dc'):
            with self.subTest(key=key), self.assertRaises(SaveError): parser.stage(self.doc, {}, key, 1)

    def test_character_and_persona_inspection_does_not_expose_writers(self):
        characters, personas = parser.progression_records(self.doc)
        self.assertEqual(len(characters), 10)
        self.assertEqual(characters[0][:2], (1, 'Protagonist'))
        self.assertEqual(len(personas), 10)
        for key in ('slot_1_level', 'slot_1_persona_1', 'slot_1_unlock'):
            with self.assertRaises(SaveError): parser.stage(self.doc, {}, key, 1)

    def test_individual_edits_change_exact_target_bytes_and_checksum(self):
        changes = {'slot_1_money': 12346, 'slot_1_item_869b2': 9}
        edited = parser.serialize(self.doc, changes)
        decoded = parser.decode(edited)
        mapping = parser.field_map(self.doc)
        allowed = {codec.SAVE_SIZE - 4}
        for key in changes:
            field = mapping[key]
            allowed.update(range(field.offset, field.offset + field.size))
        differences = {i for i, (a, b) in enumerate(zip(self.doc.payload, decoded.payload)) if a != b}
        self.assertTrue(differences <= allowed)
        self.assertEqual(decoded.seed, self.doc.seed)
        self.assertEqual(decoded.payload[-3:], self.doc.payload[-3:])
        self.assertEqual(mapping['slot_1_item_869b2'].value(decoded.payload), 9)
        self.assertEqual(parser.serialize(self.doc, changes), edited)

    def test_max_preserves_higher_values_and_pending_edits(self):
        changes = {'slot_1_money': 9}
        self.assertEqual(parser.maximums(self.doc, changes), changes)
        self.assertEqual(parser.maximums(self.doc, {}, 'Resources'), {})
        self.assertEqual(parser.limit_values(self.doc, changes, ['slot_1_persona_points']), {})
        self.assertEqual(parser.field_map(self.doc)['slot_1_persona_points'].value(self.doc.payload), 99999999)
        self.assertEqual(parser.stage(self.doc, {}, 'slot_1_persona_points', 99999999), {})
        for bad in (True, -1, 10000000, '5'):
            with self.subTest(bad=bad), self.assertRaises(SaveError): parser.stage(self.doc, {}, 'slot_1_money', bad)
        for bad in (0, 100, False):
            with self.subTest(bad=bad), self.assertRaises(SaveError): parser.serialize(self.doc, {'slot_1_item_869b2': bad})
        with self.assertRaises(SaveError): parser.maximums(self.doc, {'slot_1_money': True})

    def test_snapshot_mutable_values_bool_seed_and_external_payload_rejected(self):
        for forged in (replace(self.doc, raw=bytearray(self.doc.raw)),
                       replace(self.doc, payload=bytearray(self.doc.payload)),
                       replace(self.doc, seed=True), replace(self.doc, seed=self.doc.seed + 1)):
            with self.subTest(kind=type(forged.raw)), self.assertRaises(SaveError): parser.serialize(forged, {})
        payload = bytearray(self.doc.payload); payload[300] ^= 1
        with self.assertRaises(SaveError): parser.fields_for(replace(self.doc, payload=codec.with_checksum(bytes(payload))))

    def test_malformed_raw_size_encryption_checksum_revision_and_layout(self):
        for raw in (self.doc.raw[:-1], self.doc.raw + b'x', self.doc.payload):
            with self.subTest(size=len(raw)), self.assertRaises(SaveError): parser.decode(raw)
        damaged = bytearray(self.doc.raw); damaged[100] ^= 1
        with self.assertRaises(SaveError): parser.decode(damaged)
        damaged = bytearray(self.doc.raw); damaged[-3] = 1
        with self.assertRaises(SaveError): parser.decode(damaged)
        payload = bytearray(self.doc.payload); payload[parser._base(9) + codec.MARKER_RELATIVE] ^= 1
        payload = codec.with_checksum(bytes(payload))
        raw = research.transform(payload[:-4], self.doc.seed) + payload[-4:]
        with self.assertRaises(SaveError): parser.decode(raw)
        with self.assertRaises(SaveError): codec.encode(self.doc.payload, True)

    def test_unknown_names_or_slot_identity_inspection_only(self):
        for offset, value in ((parser._base(1), 255),
                              (parser._base(1) + codec.NAME_RELATIVE, 0),
                              (parser._base(1) + codec.NAME_RELATIVE, 0xC0)):
            payload = bytearray(self.doc.payload); payload[offset] = value
            if offset == parser._base(1): payload[offset + 1] = 255
            raw = codec.encode(codec.with_checksum(bytes(payload)), self.doc.seed)
            self.assertEqual(parser.fields_for(parser.decode(raw)), ())

    def test_safe_copy_save_backup_restore_and_same_read_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'copy.bin'; source.write_bytes(self.doc.raw)
            doc = parser.read_save(source)
            saved = parser.save_as(doc, {'slot_1_money': 9}, Path(folder) / 'edited.bin')
            self.assertEqual(parser.field_map(saved)['slot_1_money'].value(saved.payload), 9)
            self.assertEqual(source.read_bytes(), self.doc.raw)
            backup = parser.backup(doc)
            restored = parser.restore(backup, Path(folder) / 'restored.bin')
            self.assertEqual(restored.read_bytes(), self.doc.raw)
            with self.assertRaises(FileExistsError): parser.save_as(doc, {}, source)
            source.write_bytes(doc.raw[:-1])
            with self.assertRaises(SaveError): parser.save_as(doc, {}, Path(folder) / 'stale.bin')
            # A valid metadata checksum does not excuse a corrupt native body.
            damaged = bytearray(doc.raw); damaged[300] ^= 1
            corrupt = replace(doc, raw=bytes(damaged), source=Path(folder) / 'corrupt.bin')
            corrupt.source.write_bytes(corrupt.raw)
            from koei_editor.shared.copy_storage import snapshot_backup
            bad_backup = snapshot_backup(corrupt.raw, corrupt.source, parser.GAME_ID, Path(folder) / 'backups')
            destination = Path(folder) / 'invalid-restore.bin'
            with self.assertRaises(SaveError): parser.restore(bad_backup, destination)
            self.assertFalse(destination.exists())


@unittest.skipUnless(os.environ.get('P5S_PC_SAVE_COPIES'), 'No private complete PC player saves')
class GenuinePCPlayerTests(unittest.TestCase):
    def test_each_public_player_copy_roundtrips_and_targeted_edits_preserve_context(self):
        for filename in os.environ['P5S_PC_SAVE_COPIES'].split(os.pathsep):
            with self.subTest(fixture='private player copy'):
                raw = Path(filename).read_bytes()
                doc = parser.decode(raw)
                self.assertEqual(parser.serialize(doc, {}), raw)
                fields = parser.fields_for(doc)
                self.assertTrue(fields)
                self.assertTrue(any(field.group == 'Consumables' for field in fields))
                field = next(field for field in fields if field.group == 'Consumables')
                value = 2 if field.value(doc.payload) != 2 else 3
                edited = parser.decode(parser.serialize(doc, {field.id: value}))
                self.assertEqual(edited.seed, doc.seed)
                self.assertEqual(field.value(edited.payload), value)
                allowed = {field.offset, len(raw) - 4}
                self.assertTrue({i for i, (a, b) in enumerate(zip(doc.payload, edited.payload)) if a != b} <= allowed)
                self.assertEqual(parser.maximums(doc, {}), {})
