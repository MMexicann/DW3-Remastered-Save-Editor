"""Constructed contract cases are separate from optional public-native copies."""
from dataclasses import replace
from functools import lru_cache
import json
import os
from pathlib import Path
import random
import struct
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.fatal_frame2_remake import codec, parser
from koei_editor.research.katana import katana_codec


def system_json(points=123456):
    return {'SystemData': {'is_ce_demo_': False}, 'SystemUiData': {'ghost_photo_array_': [None] * 379},
            'SystemPlayerRecordData': {'shop_point_': points,
                'futago_doll_unlock_data_': [None] * 100, 'omamori_unlock_data_': [None] * 210,
                'reiseki_unlock_data_': [None] * 100, 'ghost_list_unlock_data_': [None] * 379},
            'PHOTO_SYSTEM': {'photo_info_array_': [None] * 144},
            'PHOTO_GHOST_LIST': {'photo_info_array_': [None] * 384},
            'Unknown': {'shop_point_': 123, 'text': 'keep \\ and é exactly', 'list': [1, True, None, 1.234e4]}}


def gameplay_json():
    item = {'ItemObjectData': {'key': 0, 'key_num': 0xffffffff, 'num': 0, 'flag': 0,
                              'entry_number': 0, 'equipment_slot': -1, 'amulet_level': 0}}
    return {'PlayerData': {'costume_mio': 0, 'costume_mayu': 0, 'current_film_slot': 0,
        'unlock_amulet_slot_num': 1, 'amulet_slot': [-1] * 4, 'equipment_mayu': [-1] * 26,
        'camera_enhance_data': dict.fromkeys(('flag_L_', 'flag_R_', 'flag_release_L_', 'flag_release_R_'), 0)},
        'PossessionItemData': {'possession_items': [item] * 650, 'storage_items': [item] * 550},
        'PHOTO_SLOT': {'photo_info_array_': []}, 'MissionData': {}, 'WorldData': {},
        'PlayRecordData': {}, 'TempRecordData': {}, 'UIData': {}}


def make_raw(value, system=True, *, json_bytes=None, tail=b'\x91\x82\x73\x64PHOTO'):
    size = codec.SYSTEM_SIZE if system else codec.GAMEPLAY_SIZE
    header = bytearray(256)
    header[:8] = b'WLNSYS\0\0' if system else b'WLNUSR\0\0'
    struct.pack_into('<I', header, 8, codec.REVISION)
    struct.pack_into('<II', header, 0x14, 256, size - 256)
    header[0xc0:0xd0] = b'unknown framing!'
    encoded = json_bytes or json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    body = bytearray(size - 256)
    body[:8] = header[8:16]
    body[16:16 + len(encoded)] = encoded
    body[-len(tail):] = tail
    return codec.encode(bytes(header), bytes(body))


@lru_cache(maxsize=2)
def procedural_raw(system=True):
    return make_raw(system_json() if system else gameplay_json(), system)


class NativeFormatTests(unittest.TestCase):
    def test_bulk_checksum_matches_original_primitives(self):
        rng = random.Random(2381)
        for length in (0, 1, 7, 8, 9, 255, 10003):
            raw = bytes(rng.randrange(256) for _ in range(length))
            self.assertEqual(codec.checksum(raw), katana_codec._checksum(raw))

    def test_noop_surgical_reduce_and_reopen(self):
        raw = procedural_raw()
        document = parser.decode(raw)
        field, = parser.fields_for(document)
        self.assertEqual(field.maximum, 123456)
        changes = parser.stage(document, {}, field.id, 7)
        self.assertEqual(parser.serialize(document, {}), raw)
        self.assertEqual(parser.stage(document, changes, field.id, 123456), {})
        self.assertEqual(parser.review(document, changes), [(field, 123456, 7)])
        self.assertEqual(parser.maximums(document, changes), changes)
        encoded = parser.serialize(document, changes)
        reopened = parser.decode(encoded)
        self.assertEqual(reopened.payload, parser.changed_payload(document, changes))
        self.assertEqual(field.value(reopened.payload), 7)
        expected = document.payload[:field.offset] + b'     7' + document.payload[field.offset + field.size:]
        self.assertEqual(reopened.payload, expected)
        self.assertEqual(document.payload[-9:], b'\x91\x82\x73\x64PHOTO')
        allowed = set(range(0x50, 0x90))
        self.assertTrue(all(a == b for i, (a, b) in enumerate(zip(document.header, reopened.header)) if i not in allowed))
        self.assertEqual(document.raw, raw)
        self.assertEqual(parser.fields_for(reopened)[0].value(reopened.payload), 7)

    def test_gameplay_is_inspection_only(self):
        document = parser.decode(procedural_raw(False))
        self.assertEqual(parser.fields_for(document), ())
        self.assertEqual(parser.serialize(document, {}), document.raw)
        for key in ('photo_points', 'senki', 'inventory_0_quantity', 'camera_enhance_data'):
            with self.assertRaises(SaveError):
                parser.stage(document, {}, key, 999)
        self.assertEqual(parser.item_records(document), ())
        self.assertTrue(parser.inspection_rows(document))

    def test_increases_unlocks_malformed_and_tampered_snapshots(self):
        document = parser.decode(procedural_raw())
        for key, value in (('photo_points', 123457), ('photo_points', -1),
                           ('photo_points', True), ('ghost_unlock', 1), ('photo_points', '7')):
            with self.subTest(key=key, value=value), self.assertRaises(SaveError):
                parser.stage(document, {}, key, value)
        for bad in (replace(document, header=bytes(256)),
                    replace(document, payload=document.payload[:-1] + b'!'),
                    replace(document, format=replace(document.format, id='wolong'))):
            with self.assertRaises(SaveError):
                parser.serialize(bad, {})
        raw = document.raw
        for position in (8, 0x14, 0x50, 0x70, 0x200, len(raw) - 1):
            corrupted = bytearray(raw); corrupted[position] ^= 1
            with self.subTest(position=position), self.assertRaises(SaveError):
                parser.decode(bytes(corrupted))
        for bad in (raw[:-1], b'not a save', document.header + document.payload, bytearray(raw), None):
            with self.assertRaises(SaveError):
                parser.decode(bad)

    def test_title_schema_and_duplicate_members_rejected(self):
        value = system_json()
        del value['SystemPlayerRecordData']['omamori_unlock_data_']
        with self.assertRaises(SaveError):
            parser.decode(make_raw(value))
        duplicate = json.dumps(system_json(), separators=(',', ':')).replace('"shop_point_":123456', '"shop_point_":123456,"shop_point_":7').encode()
        with self.assertRaises(SaveError):
            parser.decode(make_raw(system_json(), json_bytes=duplicate))
        value = system_json();value['SystemData']['is_ce_demo_'] = True
        with self.assertRaises(SaveError):
            parser.decode(make_raw(value))

    def test_unusual_balance_unchanged_and_no_fields(self):
        raw = make_raw(system_json(0xffffffff))
        document = parser.decode(raw)
        self.assertEqual(parser.fields_for(document), ())
        self.assertEqual(parser.serialize(document, {}), raw)

    def test_save_backup_restore_and_source_protection(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root / 'source.bin';source.write_bytes(procedural_raw())
            document = parser.read_save(source)
            snapshot = parser.backup(document)
            changes = parser.stage(document, {}, 'photo_points', 7)
            written = parser.save_as(document, changes, root / 'edited.bin')
            self.assertEqual(parser.fields_for(written)[0].value(written.payload), 7)
            self.assertEqual(source.read_bytes(), document.raw)
            self.assertEqual(snapshot.read_bytes(), document.raw)
            restored = parser.restore(snapshot, root / 'restored.bin')
            self.assertEqual(restored.read_bytes(), document.raw)
            with self.assertRaises(FileExistsError):parser.save_as(document, {}, written.source)
            source.write_bytes(document.raw[:-1] + b'!')
            with self.assertRaises(SaveError):parser.save_as(document, {}, root / 'changed.bin')
            self.assertFalse((root / 'changed.bin').exists())
            damaged = snapshot; damaged.write_bytes(snapshot.read_bytes()[:-1])
            with self.assertRaises(SaveError):parser.restore(damaged, root / 'damaged-restored.bin')
            self.assertFalse((root / 'damaged-restored.bin').exists())

    def test_optional_native_system_and_gameplay(self):
        variables = ('FF2_REMAKE_SYSTEM_COPY', 'FF2_REMAKE_GAMEPLAY_COPY')
        if not any(os.environ.get(key) for key in variables):
            self.skipTest('Native FF2 remake copies are not bundled; both optional paths unset.')
        for variable in variables:
            if not os.environ.get(variable):continue
            with self.subTest(variable=variable):
                document = parser.read_save(Path(os.environ[variable]))
                self.assertEqual(parser.serialize(document, {}), document.raw)
                if document.header[:8] == b'WLNSYS\0\0':
                    fields = parser.fields_for(document)
                    if fields and fields[0].maximum > 0:
                        changes = parser.stage(document, {}, fields[0].id, 0)
                        reopened = parser.decode(parser.serialize(document, changes))
                        self.assertEqual(reopened.payload, parser.changed_payload(document, changes))
                else:
                    self.assertEqual(parser.fields_for(document), ())
                    self.assertIsInstance(parser.item_records(document), tuple)


from tests.scalar_contract import ScalarContractTests


class RegisteredContractTests(ScalarContractTests, unittest.TestCase):
    game_id = parser.GAME_ID

    def fixture_bytes(self):
        return procedural_raw()


if __name__ == '__main__':unittest.main()
