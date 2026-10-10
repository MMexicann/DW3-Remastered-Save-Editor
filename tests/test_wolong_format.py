"""Procedural contract tests plus optional privately acquired native PC saves.

WOLONG_SAVE_COPY selects a separate genuine USER copy; no player save is bundled.
Procedural data demonstrates safety behavior, not successful game loading.
"""
from dataclasses import replace
from functools import lru_cache
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.wolong import wolong_json, wolong_parser as parser
from koei_editor.research.katana import katana_codec as codec


def item(**changes):
    record = {'key': 0, 'key_num': 0xffffffff, 'num': 0, 'flag': 0, 'rarity': 0,
              'entry_number': 0, 'item_level': 1, 'weapon_skill_level': 0,
              'equipment_part': 0, 'equipment_slot': -1, 'unknown': '\u2603 keep'}
    record.update(changes)
    return {'ItemObjectData': record}


def seal(payload, encrypted=False):
    payload = bytearray(payload)
    payload[0x3c:0x5c] = codec._checksum(payload[0x100:])
    payload[0x5c:0x7c] = bytes(32)
    payload[0x5c:0x7c] = codec._checksum(payload[:0x100])
    payload = bytes(payload)
    if encrypted:
        return payload[:0x100] + codec._cbc(payload[0x100:], codec._WOLONG_KEY, codec._WOLONG_IV, 'encrypt')
    return payload


@lru_cache(maxsize=1)
def procedural_payload():
    root = {'PlayerData': {'senki': 1234, 'sen': 5678, 'bukun': 90,
                          'senki_storage': 777, 'new_senki_storage': 1234567890123,
                          'level': 50, 'skill_max_level': 500, 'xing': [10, 20, 30, 40, 50],
                          'unknown': {'sen': 555, 'string': 'PlayerData and \\"sen\\": 8'},
                          'fellow_character_info': [{'FellowCharacterInfoData':
                              {'fellow_character_id': 7, 'bond_level': 3, 'bond_point': 9, 'flag': 4}}]},
            'TempRecordData': {}, 'UIData': {}, 'MissionData': {'untouched': [7, False, None]},
            'PossessionItemData': {'possession_items': [item() for _ in range(600)],
                                   'storage_items': [item() for _ in range(2000)]},
            'UnknownRoot': [1.5, '\u00e9', {'sen': 789}]}
    root['PossessionItemData']['possession_items'][4] = item(key=123, key_num=17, num=12, flag=8)
    root['PossessionItemData']['storage_items'][8] = item(key=456, key_num=18, num=123, flag=8)
    root['PossessionItemData']['storage_items'][9] = item(key=789, key_num=19, num=50, flag=10)
    body = json.dumps(root, ensure_ascii=False, separators=(', ', ': ')).encode('utf-8')
    payload = bytearray(parser.SAVE_SIZE)
    payload[:8] = b'WLNUSR\0\0'
    struct.pack_into('<I', payload, 8, 0x23121200)
    struct.pack_into('<II', payload, 0x14, 0x100, len(payload) - 0x100)
    payload[0x10:0x14] = b'KEEP'
    payload[0x100:0x108] = payload[8:16]
    payload[parser.JSON_OFFSET:parser.JSON_OFFSET + len(body)] = body
    return seal(payload)


def root_of(payload):
    return json.loads(payload[parser.JSON_OFFSET:].rstrip(b'\0'))


class JsonSpanTests(unittest.TestCase):
    def test_exact_paths_utf8_escapes_and_integer_tokens(self):
        raw = b'{"Unknown":"\xc3\xa9", "PlayerData":{"sen":12,"senki":3,"bukun":9,"nested":{"sen":77}}}'
        root, spans = wolong_json.parse(raw)
        self.assertEqual(root['Unknown'], '\u00e9')
        self.assertEqual(set(spans), {('PlayerData', key) for key in ('sen', 'senki', 'bukun')})
        for path, (start, end) in spans.items():
            self.assertEqual(int(raw[start:end]), root['PlayerData'][path[1]])

    def test_duplicates_malformed_nonfinite_and_depth_rejected(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":}', b'[1,]', b'{"a":01}', b'{"a":NaN}',
                    b'{"a":1e400}', b'{"a":"\\q"}', b'{}junk', b'[' * 66 + b'0' + b']' * 66):
            with self.subTest(raw=raw[:40]), self.assertRaises(SaveError):
                wolong_json.parse(raw)


class WolongFormatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = procedural_payload()
        cls.document = parser.decode(cls.raw)

    def test_exact_plain_and_encrypted_noop(self):
        self.assertEqual(parser.serialize(self.document, {}), self.raw)
        encrypted = seal(self.raw, True)
        document = parser.decode(encrypted)
        self.assertEqual(document.payload, self.raw)
        self.assertEqual(parser.serialize(document, {}), encrypted)

    def test_balances_and_only_existing_ordinary_stacks(self):
        fields = parser.field_map(self.document)
        self.assertEqual(set(fields), {'senki', 'sen', 'bukun', 'possession_items_4_num', 'storage_items_8_num'})
        self.assertEqual(fields['storage_items_8_num'].maximum, 123)
        self.assertTrue(all(not field.maxable for field in fields.values()))
        with self.assertRaises(TypeError):
            fields['new'] = fields['sen']

    def test_currency_tokens_and_zero_padding_only_change_before_integrity(self):
        changes = {'sen': 1, 'senki': 987654321, 'bukun': 0, 'storage_items_8_num': 2}
        payload = parser.changed_payload(self.document, changes)
        old, new = root_of(self.raw), root_of(payload)
        for key in ('sen', 'senki', 'bukun'):
            old['PlayerData'][key] = changes[key]
        old['PossessionItemData']['storage_items'][8]['ItemObjectData']['num'] = 2
        self.assertEqual(old, new)
        self.assertEqual(payload[:parser.JSON_OFFSET], self.raw[:parser.JSON_OFFSET])
        # Independently replace only the four original tokens in reverse order.
        original_body = self.raw[parser.JSON_OFFSET:].rstrip(b'\0')
        for field in sorted((parser.field_map(self.document)[key] for key in changes), key=lambda f: f.offset, reverse=True):
            start = field.offset - parser.JSON_OFFSET
            original_body = original_body[:start] + str(changes[field.id]).encode() + original_body[start + field.size:]
        self.assertEqual(payload[parser.JSON_OFFSET:].rstrip(b'\0'), original_body)
        encoded = parser.serialize(self.document, changes)
        reopened = parser.decode(encoded)
        self.assertEqual(root_of(reopened.payload), new)
        self.assertEqual(reopened.payload[:0x3c], self.raw[:0x3c])
        self.assertEqual(reopened.payload[0x7c:0x108], self.raw[0x7c:0x108])

    def test_undo_review_manual_limits_and_max_disabled(self):
        changes = parser.stage(self.document, {}, 'sen', 987)
        self.assertEqual([(f.id, a, b) for f, a, b in parser.review(self.document, changes)], [('sen', 5678, 987)])
        self.assertEqual(parser.stage(self.document, changes, 'sen', 5678), {})
        self.assertEqual(parser.maximums(self.document, changes), changes)
        self.assertEqual(parser.limit_values(self.document, changes, list(parser.field_map(self.document))), {})
        for key, value in [('sen', -1), ('sen', 2**31), ('sen', True), ('sen', '1'),
                           ('storage_items_8_num', 124), ('storage_items_8_num', 0),
                           ('level', 50), ('senki_storage', 0), ('storage_items_9_num', 1)]:
            with self.subTest(key=key, value=value), self.assertRaises(SaveError):
                parser.stage(self.document, {}, key, value)
        for changes in ([], None, {'made_up': 1}):
            with self.assertRaises(SaveError):
                parser.serialize(self.document, changes)

    def test_unusual_opened_currency_is_preserved_and_can_be_unstaged(self):
        f = parser.field_map(self.document)['sen']
        payload = self.raw[:f.offset] + b'9999999999' + self.raw[f.offset + f.size:]
        # Adjust existing zero padding to retain the native size.
        payload = payload[:parser.SAVE_SIZE]
        unusual = parser.decode(seal(payload))
        self.assertEqual(parser.serialize(unusual, {}), unusual.raw)
        self.assertEqual(parser.maximums(unusual, {}), {})
        changed = parser.stage(unusual, {}, 'sen', 1)
        self.assertEqual(parser.stage(unusual, changed, 'sen', 9999999999), {})

    def test_corruption_wrong_title_revision_lengths_and_layout_rejected(self):
        for offset in (8, 0x14, 0x18, 0x3c, 0x5c, 0x108, 0x3000):
            raw = bytearray(self.raw)
            raw[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(SaveError):
                parser.decode(raw)
        for raw in (b'', self.raw[:-1], self.raw + b'\0', b'WLNSYS\0\0' + self.raw[8:]):
            with self.assertRaises(SaveError):
                parser.decode(raw)
        # Even correctly checksummed foreign schemas cannot expose fields.
        for body in (b'{"PlayerData":{}}', b'{"PlayerData":{"sen":1,"sen":2}}'):
            payload = self.raw[:parser.JSON_OFFSET] + body + bytes(parser.SAVE_SIZE - parser.JSON_OFFSET - len(body))
            with self.assertRaises(SaveError):
                parser.decode(seal(payload))

    def test_forged_snapshot_is_rejected(self):
        for document in (replace(self.document, payload=self.raw[:-1]),
                         replace(self.document, raw=bytearray(self.raw)),
                         replace(self.document, format=replace(parser.FORMAT, sample_verified=False))):
            with self.assertRaises(SaveError):
                parser.serialize(document, {})

    def test_inspection_keeps_history_and_stored_values_distinct(self):
        rows = parser.inspection_rows(self.document)
        self.assertTrue(any('new_senki_storage' in row['value'] for row in rows))
        self.assertTrue(any(row['group'] == 'Companions' for row in rows))
        self.assertTrue(any('stored item_level' in row['value'] for row in rows))
        self.assertFalse(any('account' in row['label'].lower() for row in rows))

    def test_backup_restore_source_change_and_destinations(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / 'copy.bin'
            source.write_bytes(self.raw)
            document = parser.read_save(source)
            snapshot = parser.backup(document)
            self.assertEqual(snapshot.read_bytes(), self.raw)
            restored = parser.restore(snapshot, folder / 'restored.bin')
            self.assertEqual(restored.read_bytes(), self.raw)
            copied = parser.save_as(document, {'sen': 123}, folder / 'edited.bin')
            self.assertEqual(parser.field_map(copied)['sen'].value(copied.payload), 123)
            self.assertEqual(source.read_bytes(), self.raw)
            with self.assertRaises(FileExistsError):
                parser.save_as(document, {}, source)
            source.write_bytes(self.raw[:-1])
            with self.assertRaises(SaveError):
                parser.save_as(document, {}, folder / 'stale.bin')
            self.assertFalse((folder / 'stale.bin').exists())
            # Matching manifest cannot authorize a native-corrupt backup.
            damaged = bytearray(snapshot.read_bytes())
            damaged[0x200] ^= 1
            snapshot.write_bytes(damaged)
            metadata = json.loads(snapshot.with_suffix('.json').read_text())
            import hashlib
            metadata['sha256'] = hashlib.sha256(damaged).hexdigest()
            snapshot.with_suffix('.json').write_text(json.dumps(metadata))
            with self.assertRaises(SaveError):
                parser.restore(snapshot, folder / 'invalid.bin')
            self.assertFalse((folder / 'invalid.bin').exists())


@unittest.skipUnless(os.environ.get('WOLONG_SAVE_COPY'), 'Private genuine Wo Long PC USER copy unavailable.')
class NativeWolongTests(unittest.TestCase):
    def test_genuine_native_integrity_noop_and_targeted_edits(self):
        raw = Path(os.environ['WOLONG_SAVE_COPY']).read_bytes()
        document = parser.decode(raw)
        self.assertEqual(parser.serialize(document, {}), raw)
        fields = parser.field_map(document)
        self.assertTrue(all(key in fields for key in ('sen', 'senki', 'bukun')))
        changes = {'sen': 12345, 'senki': 98765, 'bukun': 321}
        stack = next(field for field in fields.values() if field.group == 'Stored stacks')
        changes[stack.id] = 1
        output = parser.serialize(document, changes)
        reopened = parser.decode(output)
        for key, value in changes.items():
            self.assertEqual(parser.field_map(reopened)[key].value(reopened.payload)
                             if key in parser.field_map(reopened) else 1, value)
        self.assertEqual(raw[:0x3c], output[:0x3c])
        before, after = root_of(document.payload), root_of(reopened.payload)
        for key in ('sen', 'senki', 'bukun'):
            before['PlayerData'][key] = changes[key]
        slot = stack.slot - 601
        before['PossessionItemData']['storage_items'][slot]['ItemObjectData']['num'] = 1
        self.assertEqual(before, after)
