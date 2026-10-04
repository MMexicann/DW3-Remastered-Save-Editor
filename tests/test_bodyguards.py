"""Private-fixture integration checks for verified bodyguard editing.

The fixture is an explicitly supplied workspace copy. Tests never read or write
the game's live save folder, and ordinary UUID directories inherit workspace
permissions (rather than Python 3.14 tempfile's restrictive Windows ACL).
"""
from pathlib import Path
import hashlib
import json
import shutil
import struct
import sys
import unittest
import uuid

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parent.parent
sys.path.insert(0, str(PROJECT))
from models import Change, SaveError, fields
from save_parser import read_save, parse_bytes
from save_writer import serialize, write_save, restore_backup
from save_codec import encrypt
import bodyguard_editor as bg
import bodyguard_growth as growth

FIXTURE = WORKSPACE / 'work' / 'original-upload' / 'GameStatusData.sav'
RUNS = PROJECT / 'tests' / '.bodyguard-test-runs'


def all_properties(document):
    def walk(properties):
        for prop in properties:
            yield prop
            value = prop['value']
            if isinstance(value, list) and value and isinstance(value[0], dict):
                yield from walk(value)
            elif isinstance(value, dict) and 'records' in value:
                for record in value['records']:
                    yield from walk(record)
    return list(walk(document.parsed['properties']))


def edited_fixture_bytes(document, replacements):
    """Synthesize malformed/edge fixtures directly, using parsed boundaries."""
    payload = bytearray(document.plaintext[:4 + struct.unpack_from('>I', document.plaintext)[0]])
    replacements = [(p['data_offset'], p['data_size'], data) for p, data in replacements]
    deltas = {}
    for offset, size, data in replacements:
        delta = len(data) - size
        if delta:
            for prop in all_properties(document):
                if prop['data_offset'] <= offset and offset + size <= prop['data_offset'] + prop['data_size']:
                    deltas[prop['size_offset']] = deltas.get(prop['size_offset'], 0) + delta
    for offset, delta in deltas.items():
        replacements.append((offset, 4, struct.pack('<i', struct.unpack_from('<i', payload, offset)[0] + delta)))
    for offset, size, data in sorted(replacements, reverse=True):
        payload[offset:offset + size] = data
    struct.pack_into('>I', payload, 0, len(payload) - 4)
    payload.extend(bytes((-len(payload)) % 16))
    return encrypt(bytes(payload))


def enum_bytes(name):
    encoded = name.encode('utf8') + b'\0'
    return struct.pack('<i', len(encoded)) + encoded


def tag_bytes(document, prop):
    return document.plaintext[prop['tag_offset']:prop['data_offset'] + prop['data_size']]


def record_bytes(document, array, index):
    records = document.records(array)
    start = records[index][0]['tag_offset']
    end = records[index + 1][0]['tag_offset'] if index + 1 < len(records) else document.properties[array]['data_offset'] + document.properties[array]['data_size']
    return document.plaintext[start:end]


@unittest.skipUnless(FIXTURE.exists(), 'The private uploaded fixture is required for integration tests.')
class BodyguardIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read_save(FIXTURE)
        cls.fixture_hash = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        RUNS.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == cls.fixture_hash

    def setUp(self):
        self.folder = RUNS / ('test-' + uuid.uuid4().hex)
        self.folder.mkdir()

    def tearDown(self):
        assert self.folder.resolve().is_relative_to(RUNS.resolve())
        shutil.rmtree(self.folder)

    def edited(self, changes, document=None):
        source = document or self.document
        raw, audit = serialize(source, changes)
        return parse_bytes(raw), audit

    def assert_other_regions_preserved(self, document, allowed):
        for name, original in self.document.properties.items():
            if name not in allowed:
                self.assertEqual(tag_bytes(document, document.properties[name]), tag_bytes(self.document, original), name)

    def test_fixture_inventory_and_confirmed_item_limits(self):
        self.assertEqual(len(bg.GUARD_ITEMS), 10)
        self.assertEqual([bg.GUARD_ITEMS[i]['max_value'] for i in range(10)], [40, 40, 25, 25, 15, 15, 15, 15, 15, 0])
        state = bg.item_state(self.document)
        self.assertEqual([i for i, row in state.items() if row['owned']], [1, 2, 3, 4, 5, 6])
        self.assertEqual([state[i]['value'] for i in range(1, 7)], [4, 8, 17, 2, 9, 3])

    def test_all_nine_max_rolls_and_one_rare_flag_roundtrip(self):
        changes = [Change('guard_item', i, 'Owned', True) for i in range(10)]
        changes += [Change('guard_item', i, 'Value', bg.GUARD_ITEMS[i]['max_value']) for i in range(9)]
        document, audit = self.edited(changes)
        for i in range(10):
            row = fields(document.records('GuardEquipItemDataArray')[i])
            self.assertEqual(row['GuardEquipItemID']['value'], bg.GUARD_ITEMS[i]['enum'])
            self.assertEqual(row['EquipItemID']['value'], 'EEquipItemID::NUM')
            self.assertEqual(row['Value']['value'], bg.GUARD_ITEMS[i]['max_value'])
        self.assertTrue(audit['resized'])
        self.assert_other_regions_preserved(document, {'GuardEquipItemDataArray'})
        raw, again = serialize(document, changes)
        self.assertEqual(raw, document.encrypted)
        self.assertEqual(again['plaintext_changes'], [])

    def test_item_unlock_defaults_minimum_and_value_implies_owned(self):
        document, _ = self.edited([Change('guard_item', 0, 'Owned', True), Change('guard_item', 7, 'Value', 13)])
        state = bg.item_state(document)
        self.assertEqual(state[0], {'owned': True, 'value': 1})
        self.assertEqual(state[7], {'owned': True, 'value': 13})

    def test_unowned_unequipped_item_removal_resets_id_and_value(self):
        document, _ = self.edited([Change('guard_item', 1, 'Owned', False)])
        self.assertEqual(bg.item_state(document)[1], {'owned': False, 'value': 0})
        self.assert_other_regions_preserved(document, {'GuardEquipItemDataArray'})

    def test_equipped_item_removal_requires_final_unequip(self):
        with self.assertRaises(SaveError):
            serialize(self.document, [Change('guard_item', 2, 'Owned', False)])
        document, _ = self.edited([Change('guard_item', 2, 'Owned', False), Change('bodyguard', 1, 'MemberItem', None)])
        self.assertFalse(bg.item_state(document)[2]['owned'])
        self.assertIsNone(bg.team_state(document, 1)['MemberItem'])
        self.assertEqual(bg.team_state(document, 1)['BGLevels'], [6, 6, 7, 3, 3, 2])

    def test_unowned_equipment_ref_refused_but_same_batch_unlock_works(self):
        with self.assertRaises(SaveError):
            serialize(self.document, [Change('bodyguard', 0, 'MemberItem', 9)])
        document, _ = self.edited([Change('bodyguard', 0, 'MemberItem', 9), Change('guard_item', 9, 'Owned', True)])
        self.assertEqual(bg.team_state(document, 0)['MemberItem'], 9)
        self.assertEqual(bg.item_state(document)[9], {'owned': True, 'value': 0})

    def test_cached_officer_guard_musou_reference_protects_removal(self):
        prop = fields(self.document.records('PCSaveDataArray')[0])['BGMusouEquipItem']
        document = parse_bytes(edited_fixture_bytes(self.document, [(prop, enum_bytes(bg.GUARD_ITEMS[1]['enum']))]))
        with self.assertRaises(SaveError):
            serialize(document, [Change('guard_item', 1, 'Owned', False)])
        result, _ = self.edited([Change('guard_item', 1, 'Value', 40)], document)
        self.assertEqual(fields(result.records('PCSaveDataArray')[0])['BGMusouEquipItem']['value'], bg.GUARD_ITEMS[1]['enum'])

    def test_reserved_officer_cached_reference_is_preserved_and_protects_removal(self):
        prop = fields(self.document.records('PCSaveDataArray')[42])['BGMusouEquipItem']
        document = parse_bytes(edited_fixture_bytes(self.document, [(prop, enum_bytes(bg.GUARD_ITEMS[1]['enum']))]))
        with self.assertRaises(SaveError):
            serialize(document, [Change('guard_item', 1, 'Owned', False)])

    def test_invalid_guard_item_requests_refused(self):
        invalid = [Change('guard_item', 10, 'Owned', True), Change('guard_item', -1, 'Owned', True),
                   Change('guard_item', True, 'Owned', True), Change('guard_item', 0, 'Owned', 1),
                   Change('guard_item', 0, 'Value', 41), Change('guard_item', 0, 'Value', 0),
                   Change('guard_item', 1, 'Value', True), Change('guard_item', 9, 'Value', 1)]
        for change in invalid:
            with self.subTest(change=change), self.assertRaises(SaveError):
                serialize(self.document, [change])

    def test_growth_presets_spend_exact_native_budget(self):
        for merit in (0, 999, 1000, 24999, 25000, 50000, 89999, 90000, 99998, 99999):
            for mode in growth.PRESET_NAMES:
                with self.subTest(merit=merit, mode=mode):
                    levels = growth.safe_preset(merit, mode)
                    self.assertEqual(growth.spent(levels), growth.budget(merit))
                    self.assertEqual(tuple(levels), growth.validate_growth(merit, levels))
        self.assertEqual(growth.safe_preset(99999), [8, 7, 7, 3, 3, 3])

    def test_growth_merit_raises_automatic_count_ai_preserves_allocations(self):
        document, _ = self.edited([Change('bodyguard', 1, 'SPoint', 99999)])
        self.assertEqual(bg.team_state(document, 1)['BGLevels'], [6, 6, 7, 3, 3, 3])
        self.assert_other_regions_preserved(document, {'GuardDataArray'})

    def test_lowered_merit_validates_final_allocation_combination(self):
        with self.assertRaises(SaveError):
            serialize(self.document, [Change('bodyguard', 1, 'SPoint', 49999)])
        levels = growth.safe_preset(49999)
        document, _ = self.edited([Change('bodyguard', 1, 'SPoint', 49999), Change('bodyguard', 1, 'BGLevels', levels)])
        self.assertEqual(bg.team_state(document, 1)['SPoint'], 49999)
        self.assertEqual(bg.team_state(document, 1)['BGLevels'], levels)
        for i in (0, 4, 6):
            self.assertEqual(fields(document.records('PCSaveDataArray')[i])['MemCnt']['value'], 5)
        self.assertEqual(fields(document.records('PCSaveDataArray')[1])['MemCnt']['value'], 3)

    def test_max_growth_refuses_all_six_caps_and_bad_types(self):
        invalid = [Change('bodyguard', 1, 'BGLevels', [11, 11, 11, 3, 3, 3]),
                   Change('bodyguard', 0, 'BGLevels', [1, 0, 0, 0, 0, 0]),
                   Change('bodyguard', 1, 'BGLevels', [0, 0, 0, 0, 0]),
                   Change('bodyguard', 1, 'BGLevels', [True, 0, 0, 0, 0, 0]),
                   Change('bodyguard', 1, 'SPoint', 100000), Change('bodyguard', 1, 'SPoint', -1),
                   Change('bodyguard', 1, 'SPoint', True)]
        for change in invalid:
            with self.subTest(change=change), self.assertRaises(SaveError):
                serialize(self.document, [change])

    def test_growth_count_cache_tracks_team_and_preserves_custom_count(self):
        first = fields(self.document.records('PCSaveDataArray')[0])
        custom = parse_bytes(edited_fixture_bytes(self.document, [(first['MemCnt'], struct.pack('<i', 3))]))
        document, _ = self.edited([Change('bodyguard', 1, 'SPoint', 49999), Change('bodyguard', 1, 'BGLevels', growth.safe_preset(49999))], custom)
        self.assertEqual(fields(document.records('PCSaveDataArray')[0])['MemCnt']['value'], 3)
        self.assertEqual(fields(document.records('PCSaveDataArray')[4])['MemCnt']['value'], 5)
        self.assertEqual(fields(document.records('PCSaveDataArray')[6])['MemCnt']['value'], 5)

    def test_acquire_all_fifteen_without_replacing_owned_copies(self):
        before = bg.weapon_state(self.document)
        changes = [Change('guard_weapon', i, 'Owned', True) for i in bg.GUARD_WEAPONS]
        document, _ = self.edited(changes)
        after = bg.weapon_state(document)
        self.assertEqual({row['weapon_id'] for row in after if row['weapon_id'] is not None}, set(range(173, 188)))
        for row in before:
            if row['weapon_id'] is not None:
                self.assertEqual(record_bytes(document, 'GuardWeaponDataArray', row['slot']), record_bytes(self.document, 'GuardWeaponDataArray', row['slot']))
        for row in after:
            if before[row['slot']]['weapon_id'] is None and row['weapon_id'] is not None:
                f = fields(document.records('GuardWeaponDataArray')[row['slot']])
                self.assertEqual(f['ID']['value'], f['WeaponID']['value'])
                self.assertEqual(f['DataID']['value'], row['slot'])
                self.assertEqual(f['Attr']['value'], 0)
                self.assertEqual(f['GetTime']['value'], fields(self.document.records('GuardWeaponDataArray')[row['slot']])['GetTime']['value'])
                self.assertEqual(row['skills'], bg.max_skills(row['weapon_id']))
        self.assert_other_regions_preserved(document, {'GuardWeaponDataArray', 'CollectedWeaponDataArray'})
        raw, audit = serialize(document, changes)
        self.assertEqual(raw, document.encrypted)
        self.assertEqual(audit['plaintext_changes'], [])

    def test_collection_filled_once_and_owned_cache_preserved(self):
        document, _ = self.edited([Change('guard_weapon', i, 'Owned', True) for i in bg.GUARD_WEAPONS])
        for weapon_id, item in bg.GUARD_WEAPONS.items():
            old = fields(self.document.records('CollectedWeaponDataArray')[weapon_id])
            new = fields(document.records('CollectedWeaponDataArray')[weapon_id])
            if old['WeaponID']['value'] != 'EWeaponID::NUM':
                self.assertEqual(record_bytes(document, 'CollectedWeaponDataArray', weapon_id), record_bytes(self.document, 'CollectedWeaponDataArray', weapon_id))
            else:
                self.assertEqual(new['WeaponID']['value'], item['enum'])
                self.assertEqual(new['ID']['value'], item['enum'])
                self.assertEqual(new['DataID']['value'], weapon_id)
        maximized, _ = self.edited([Change('guard_weapon', 174, 'MaxBonuses', True)], document)
        self.assertEqual(tag_bytes(maximized, maximized.properties['CollectedWeaponDataArray']), tag_bytes(document, document.properties['CollectedWeaponDataArray']))

    def test_bonus_max_updates_all_copies_keeps_identity_timestamp_and_cache(self):
        document, _ = self.edited([Change('guard_weapon', 174, 'MaxBonuses', True)])
        for row in bg.weapon_state(document):
            if row['weapon_id'] == 174:
                self.assertEqual(row['skills'], bg.max_skills(174))
                new = fields(document.records('GuardWeaponDataArray')[row['slot']])
                old = fields(self.document.records('GuardWeaponDataArray')[row['slot']])
                for name in ('ID', 'WeaponID', 'Attr', 'DataID', 'GetTime'):
                    self.assertEqual(tag_bytes(document, new[name]), tag_bytes(self.document, old[name]))
        self.assert_other_regions_preserved(document, {'GuardWeaponDataArray'})

    def test_family_tier_discrete_bonus_limits_and_three_slot_max(self):
        for weapon_id in bg.GUARD_WEAPONS:
            self.assertEqual(bg.validate_skills(weapon_id, bg.max_skills(weapon_id)), bg.max_skills(weapon_id))
        cases = [(174, [{'id': 4, 'value': 10}]), (184, [{'id': 2, 'value': 20}]),
                 (184, [{'id': 7, 'value': 10}]), (174, [{'id': 9, 'value': 0}]),
                 (173, [{'id': 0, 'value': 30}]), (174, [{'id': 0, 'value': 29}]),
                 (174, [{'id': 0, 'value': 30}, {'id': 0, 'value': 25}]),
                 (174, [{'id': i, 'value': 1} for i in (0, 1, 2, 3)]),
                 (174, [{'id': True, 'value': 1}]), (174, [{'id': 0, 'value': True}])]
        for weapon_id, skills in cases:
            with self.subTest(weapon=weapon_id, skills=skills), self.assertRaises(SaveError):
                bg.validate_skills(weapon_id, skills)
        document, _ = self.edited([Change('guard_weapon_slot', 1, 'Skills', [{'id': 0, 'value': 25}, {'id': 2, 'value': 15}])])
        self.assertEqual(bg.weapon_state(document)[1]['skills'], [{'id': 0, 'value': 25}, {'id': 2, 'value': 15}])
        self.assertEqual(record_bytes(document, 'GuardWeaponDataArray', 2), record_bytes(self.document, 'GuardWeaponDataArray', 2))

    def test_equip_uses_inventory_slots_and_preserves_reserved_refs(self):
        document, _ = self.edited([Change('guard_weapon', i, 'Owned', True) for i in bg.GUARD_WEAPONS])
        refs = bg.best_weapon_refs(document)
        self.assertEqual(len(refs), 5)
        pool = bg.weapon_state(document)
        for family, slot in enumerate(refs):
            self.assertLess(slot, 100)
            self.assertEqual(bg.GUARD_WEAPONS[pool[slot]['weapon_id']]['family_index'], family)
            self.assertEqual(bg.GUARD_WEAPONS[pool[slot]['weapon_id']]['tier'], 3)
        equipped, _ = self.edited([Change('bodyguard', 0, 'MemberWeapon', refs + [-1] * 5)], document)
        self.assertEqual(bg.team_state(equipped, 0)['MemberWeapon'], refs + [-1] * 5)
        for bad in ([175, 178, 181, 184, 187] + [-1] * 5, [9, 3, 6, 9, 12] + [-1] * 5, refs + [0] + [-1] * 4):
            with self.subTest(refs=bad), self.assertRaises(SaveError):
                serialize(document, [Change('bodyguard', 0, 'MemberWeapon', bad)])

    def test_full_inventory_refuses_missing_acquisition_without_overwrite(self):
        replacements = []
        for index, row in enumerate(self.document.records('GuardWeaponDataArray')):
            f = fields(row)
            if f['WeaponID']['value'] == 'EWeaponID::NUM':
                replacements += [(f['ID'], enum_bytes(bg.GUARD_WEAPONS[173]['enum'])), (f['WeaponID'], enum_bytes(bg.GUARD_WEAPONS[173]['enum'])), (f['DataID'], struct.pack('<i', index))]
        full = parse_bytes(edited_fixture_bytes(self.document, replacements))
        self.assertTrue(all(row['weapon_id'] is not None for row in bg.weapon_state(full)))
        with self.assertRaises(SaveError):
            serialize(full, [Change('guard_weapon', 178, 'Owned', True)])

    def test_combined_bodyguard_grind_preserves_every_unrelated_region(self):
        changes = [Change('guard_item', i, 'Owned', True) for i in range(10)]
        changes += [Change('guard_item', i, 'Value', bg.GUARD_ITEMS[i]['max_value']) for i in range(9)]
        changes += [Change('guard_weapon', i, field, True) for i in bg.GUARD_WEAPONS for field in ('Owned', 'MaxBonuses')]
        refs = bg.best_weapon_refs(self.document, changes)
        for i in range(4):
            changes += [Change('bodyguard', i, 'SPoint', 99999), Change('bodyguard', i, 'BGLevels', growth.safe_preset()),
                        Change('bodyguard', i, 'MemberWeapon', refs + [-1] * 5)]
        document, audit = self.edited(changes)
        self.assertTrue(audit['plaintext_changes'])
        self.assert_other_regions_preserved(document, {'PCSaveDataArray', 'GuardDataArray', 'GuardEquipItemDataArray', 'GuardWeaponDataArray', 'CollectedWeaponDataArray'})
        for index, old_record in enumerate(self.document.records('PCSaveDataArray')):
            old, new = fields(old_record), fields(document.records('PCSaveDataArray')[index])
            for name in old:
                if index < 42 and name == 'MemCnt':
                    continue
                self.assertEqual(tag_bytes(document, new[name]), tag_bytes(self.document, old[name]), (index, name))
        for i in range(4):
            self.assertEqual(bg.team_state(document, i)['BGLevels'], growth.safe_preset())
        self.assertEqual({x['weapon_id'] for x in bg.weapon_state(document) if x['weapon_id'] is not None}, set(bg.GUARD_WEAPONS))

    def test_copy_save_as_backup_restore_and_source_unchanged(self):
        source = self.folder / 'original-copy.sav'
        source.write_bytes(self.document.encrypted)
        document = read_save(source)
        dest, audit = write_save(document, self.folder / 'edited.sav', [Change('guard_item', 9, 'Owned', True)])
        self.assertEqual(source.read_bytes(), self.document.encrypted)
        self.assertTrue(bg.item_state(read_save(dest))[9]['owned'])
        self.assertTrue(list(self.folder.glob('edited.sav.*.changes.json')))
        write_save(document, source, [Change('guard_item', 9, 'Owned', True)], overwrite=True)
        backup = next((self.folder / 'DW3EditorBackups').glob('*.sav'))
        self.assertEqual(backup.read_bytes(), self.document.encrypted)
        restored = restore_backup(backup, self.folder / 'restored-copy.sav')
        self.assertEqual(restored.read_bytes(), self.document.encrypted)

    def test_noncanonical_item_owned_values_rejected(self):
        empty = fields(self.document.records('GuardEquipItemDataArray')[0])
        normal = fields(self.document.records('GuardEquipItemDataArray')[2])
        rare = fields(self.document.records('GuardEquipItemDataArray')[9])
        probes = [[(empty['Value'], struct.pack('<i', 1))],
                  [(normal['Value'], struct.pack('<i', 0))],
                  [(rare['GuardEquipItemID'], enum_bytes(bg.GUARD_ITEMS[9]['enum'])), (rare['Value'], struct.pack('<i', 1))]]
        for changes in probes:
            with self.subTest(changes=changes), self.assertRaises(SaveError):
                parse_bytes(edited_fixture_bytes(self.document, changes))

    def test_wrong_guard_array_counts_and_property_types_rejected(self):
        for name in ('GuardEquipItemDataArray', 'GuardWeaponDataArray'):
            prop = self.document.properties[name]
            data = bytearray(self.document.plaintext[prop['data_offset']:prop['data_offset'] + prop['data_size']])
            struct.pack_into('<i', data, 0, prop['value']['count'] - 1)
            with self.subTest(array=name), self.assertRaises(SaveError):
                parse_bytes(edited_fixture_bytes(self.document, [(prop, bytes(data))]))
        for array, field in [('GuardDataArray', 'SPoint'), ('GuardWeaponDataArray', 'DataID'), ('GuardEquipItemDataArray', 'Value')]:
            prop = fields(self.document.records(array)[0])[field]
            original = bytearray(self.document.plaintext)
            start, end = prop['tag_offset'], prop['data_offset']
            value = bytes(original[start:end])
            self.assertIn(b'IntProperty', value)
            original[start:end] = value.replace(b'IntProperty', b'StrProperty')
            with self.subTest(array=array, field=field), self.assertRaises(SaveError):
                parse_bytes(encrypt(bytes(original)))

    def test_malformed_guard_item_identity_and_roll_rejected(self):
        row = fields(self.document.records('GuardEquipItemDataArray')[2])
        probes = [(row['GuardEquipItemID'], enum_bytes(bg.GUARD_ITEMS[3]['enum'])),
                  (row['EquipItemID'], enum_bytes('EEquipItemID::EQUIP_ITEM_SEIRYUTAN')),
                  (row['GuardEquipItemID'], enum_bytes('EGuardEquipItemID::BAD')),
                  (row['Value'], struct.pack('<i', 26))]
        for prop, value in probes:
            with self.subTest(field=prop['name'], value=value), self.assertRaises(SaveError):
                parse_bytes(edited_fixture_bytes(self.document, [(prop, value)]))

    def test_malformed_guard_weapon_identity_dataid_and_ref_rejected(self):
        row = fields(self.document.records('GuardWeaponDataArray')[1])
        team = fields(self.document.records('GuardDataArray')[0])
        probes = [(row['ID'], enum_bytes(bg.GUARD_WEAPONS[175]['enum'])),
                  (row['WeaponID'], enum_bytes('EWeaponID::WeaponID_172')),
                  (row['DataID'], struct.pack('<i', 99)),
                  (team['MemberWeapon'], struct.pack('<i', 10) + struct.pack('<10i', 99, 3, 6, 9, 12, -1, -1, -1, -1, -1))]
        for prop, value in probes:
            with self.subTest(field=prop['name'], value=value), self.assertRaises(SaveError):
                parse_bytes(edited_fixture_bytes(self.document, [(prop, value)]))

    def test_saved_guard_bonus_structure_is_separate_from_authored_drop_rules(self):
        records = self.document.records('GuardWeaponDataArray')

        def skills_replacements(slot, skills):
            replacements = []
            for index, record in enumerate(fields(records[slot])['Skill']['value']['records']):
                row = fields(record)
                skill = skills[index] if index < len(skills) else None
                replacements.extend([(row['GuardEquipItemID'], enum_bytes(bg.GUARD_ITEMS[skill['id']]['enum'] if skill else 'EGuardEquipItemID::NUM')),
                                     (row['Value'], struct.pack('<i', skill['value'] if skill else 0))])
            return replacements

        unsupported = [(0, [{'id': 0, 'value': 30}]),
                       (1, [{'id': 0, 'value': 29}]),
                       (1, [{'id': 4, 'value': 10}]),
                       (12, [{'id': 2, 'value': 5}]),
                       (1, [])]
        for slot, skills in unsupported:
            with self.subTest(slot=slot, skills=skills):
                raw = edited_fixture_bytes(self.document, skills_replacements(slot, skills))
                doc = parse_bytes(raw)
                state = bg.weapon_state(doc)[slot]
                self.assertFalse(state['editable'])
                self.assertEqual(state['skills'], skills)
                self.assertEqual(serialize(doc)[0], raw)
                with self.assertRaises(SaveError):
                    serialize(doc, [Change('guard_weapon_slot', slot, 'Skills', bg.max_skills(state['weapon_id']))])
        probes = [(1, [{'id': 0, 'value': 30}, {'id': 0, 'value': 25}]),
                  (1, [{'id': 0, 'value': 0}]),
                  (1, [{'id': 0, 'value': -1}]),
                  (1, [{'id': 9, 'value': 0}]),  # rare inventory item is not a weapon bonus
                  (1, [{'id': index, 'value': 1} for index in (0, 1, 2, 3)])]
        for slot, skills in probes:
            with self.subTest(slot=slot, skills=skills), self.assertRaises(SaveError):
                parse_bytes(edited_fixture_bytes(self.document, skills_replacements(slot, skills)))

    def test_malformed_growth_shape_budget_and_equipped_item_rejected(self):
        row = fields(self.document.records('GuardDataArray')[1])
        probes = [(row['SPoint'], struct.pack('<i', 100000)),
                  (row['BGLevels'], struct.pack('<i', 5) + struct.pack('<5i', 6, 6, 7, 3, 3)),
                  (row['BGLevels'], struct.pack('<i', 6) + struct.pack('<6i', 11, 11, 11, 3, 3, 3)),
                  (row['MemberItem'], enum_bytes(bg.GUARD_ITEMS[9]['enum']))]
        for prop, value in probes:
            with self.subTest(field=prop['name'], value=value), self.assertRaises(SaveError):
                parse_bytes(edited_fixture_bytes(self.document, [(prop, value)]))

    def test_one_roll_edit_changes_only_known_scalar_and_encryption_block(self):
        original = fields(self.document.records('GuardEquipItemDataArray')[3])['Value']
        document, audit = self.edited([Change('guard_item', 3, 'Value', 18)])
        changed = [i for i, (a, b) in enumerate(zip(document.plaintext, self.document.plaintext)) if a != b]
        self.assertEqual(changed, [original['data_offset']])
        self.assertEqual(audit['changed_aes_blocks'], [original['data_offset'] // 16])
        self.assertFalse(audit['resized'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
