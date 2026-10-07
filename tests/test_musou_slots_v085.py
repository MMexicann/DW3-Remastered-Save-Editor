"""Regression checks for in-place Musou campaign slot resets."""
from pathlib import Path
import struct
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT
sys.path.insert(0, str(PROJECT))
from models import Change, SaveError, fields
from save_parser import read_save, parse_bytes
from save_writer import serialize
from test_weapon_rolls import edited_fixture_bytes, enum_bytes, tag_bytes
import musou_slots as musou

FIXTURES = [
    WORKSPACE / 'work/original-upload/GameStatusData.sav',
    WORKSPACE / 'work/received-user-save/4c38f5aeb9add15003b03761dee7dec6b8a792b2a705e6d70f0f957f018c7409.sav',
    WORKSPACE / 'work/received-v034/report-1-9d25e968bcca.sav',
    WORKSPACE / 'work/received-v034/report-2-dd54eb37ba5d.sav',
]


def array_records(document):
    return document.properties['EngiSaveDataArray']['value']['records']


@unittest.skipUnless(all(path.exists() for path in FIXTURES), 'All four supplied save copies are required.')
class MusouSlotTests(unittest.TestCase):
    def assert_native_defaults(self, document, index):
        row = fields(array_records(document)[index])
        self.assertEqual(row['CharaID']['value'], musou.EMPTY_OFFICER)
        for name in ('NowStage', 'EventFlag', 'PCColor'):
            self.assertEqual(row[name]['value'], 0, name)
        for name in ('StageSPoint', 'ClearTime', 'GuardNum'):
            self.assertTrue(all(value == 0 for value in row[name]['value']['values']), name)
        self.assertFalse(row['isClearChara']['value'])
        self.assertFalse(row['isNewMusouMode']['value'])
        self.assertEqual(struct.unpack_from('<q', document.plaintext, row['SaveDate']['data_offset'])[0], 0)
        for ko in row['KOData']['value']['records']:
            entry = fields(ko)
            self.assertEqual(entry['KOCnt']['value'], 0)
            self.assertEqual(entry['KOCommanderList']['value']['count'], 0)
            self.assertFalse(entry['isGekiMusou']['value'])

    def test_selected_reset_keeps_slot_identity_and_every_other_campaign(self):
        document = read_save(FIXTURES[0])
        states = musou.slot_state(document)
        self.assertEqual(states['active_count'], 3)
        self.assertTrue(all(row['editable'] for row in states['slots']))
        untouched = [tag_bytes(document, record[0]) for i, record in enumerate(array_records(document)) if i != 1]
        before_other_arrays = {name: tag_bytes(document, prop) for name, prop in document.properties.items()
                               if name != 'EngiSaveDataArray'}
        change = musou.remove_slot_change(1)
        raw, audit = serialize(document, [change])
        saved = parse_bytes(raw)
        self.assertEqual(len(array_records(saved)), len(array_records(document)))
        self.assert_native_defaults(saved, 1)
        self.assertEqual([tag_bytes(saved, record[0]) for i, record in enumerate(array_records(saved)) if i != 1], untouched)
        self.assertEqual({name: tag_bytes(saved, saved.properties[name]) for name in before_other_arrays}, before_other_arrays)
        self.assertEqual(musou.slot_state(saved)['active_count'], 2)
        self.assertTrue(audit['plaintext_changes'])
        self.assertEqual(serialize(saved, [musou.remove_slot_change(1)])[0], saved.encrypted)
        self.assertTrue(musou.original_value(saved, change))

    def test_remove_all_resets_active_slots_in_place_and_leaves_other_regions(self):
        document = read_save(FIXTURES[0])
        changes = musou.remove_all_changes(document)
        self.assertEqual([change.index for change in changes], [0, 1, 2])
        saved = parse_bytes(serialize(document, changes)[0])
        self.assertEqual(musou.slot_state(saved)['active_count'], 0)
        self.assertEqual(len(array_records(saved)), len(array_records(document)))
        for index in range(len(array_records(saved))):
            self.assert_native_defaults(saved, index)
        for name, prop in document.properties.items():
            if name != 'EngiSaveDataArray':
                self.assertEqual(tag_bytes(saved, saved.properties[name]), tag_bytes(document, prop), name)
        self.assertEqual(serialize(saved, musou.remove_all_changes(saved))[0], saved.encrypted)

    def test_supplied_variants_remain_readable_and_slot_identity_survives_reset(self):
        for path in FIXTURES:
            with self.subTest(path=path.name):
                document = read_save(path)
                state = musou.slot_state(document)
                self.assertTrue(state['slots'])
                self.assertEqual(state['active_count'], sum(row['active'] for row in state['slots']))
                target = next((row['index'] for row in state['slots'] if row['active'] and row['editable']), None)
                if target is not None:
                    saved = parse_bytes(serialize(document, [musou.remove_slot_change(target)])[0])
                    self.assertEqual(len(array_records(saved)), len(array_records(document)))
                    self.assert_native_defaults(saved, target)

    def test_unknown_record_field_is_visible_but_refuses_removal(self):
        document = read_save(FIXTURES[0])
        array = document.properties['EngiSaveDataArray']
        # Change a known tag name in one record to an unknown same-length name.
        prop = fields(array_records(document)[0])['PCColor']
        payload = bytearray(document.plaintext[:4 + struct.unpack_from('>I', document.plaintext)[0]])
        start, end = prop['tag_offset'] + 4, prop['tag_offset'] + 4 + len('PCColor')
        payload[start:end] = b'PCColox'
        payload.extend(bytes((-len(payload)) % 16))
        from save_codec import encrypt
        modified = parse_bytes(encrypt(bytes(payload)))
        row = musou.slot_state(modified)['slots'][0]
        self.assertFalse(row['editable'])
        self.assertTrue(row['reason'])
        with self.assertRaises(SaveError):
            serialize(modified, [musou.remove_slot_change(0)])

    def test_invalid_and_duplicate_actions_are_refused(self):
        document = read_save(FIXTURES[0])
        for action in (Change('musou_slot', 0, 'Clear', True),
                       Change('musou_slot', 99, 'Remove', True),
                       Change('musou_slot', 0, 'Remove', False)):
            with self.subTest(action=action), self.assertRaises(SaveError):
                serialize(document, [action])
        with self.assertRaises(SaveError):
            serialize(document, [musou.remove_slot_change(0), musou.remove_slot_change(0)])


if __name__ == '__main__':
    unittest.main(verbosity=2)
