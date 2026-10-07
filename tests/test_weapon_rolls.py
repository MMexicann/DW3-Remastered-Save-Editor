"""Private-copy integration checks for proven officer weapon bonus edits.

The original upload is read only; outputs and deliberately malformed fixtures
are created solely inside inherited-permission workspace test directories.
"""
from pathlib import Path
import hashlib
import shutil
import struct
import sys
import unittest
import uuid

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT
sys.path.insert(0, str(PROJECT))
from models import Change, SaveError, fields
from save_parser import read_save, parse_bytes
from save_writer import serialize, write_save, restore_backup, UNIQUE_WEAPONS
from save_codec import encrypt
import officer_weapon_editor as weapon

FIXTURE = WORKSPACE / 'work' / 'original-upload' / 'GameStatusData.sav'
RUNS = PROJECT / 'tests' / '.weapon-roll-test-runs'
NORMAL_IDS = set(range(13)) | {25, 26, 27}


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
    payload = bytearray(document.plaintext[:4 + struct.unpack_from('>I', document.plaintext)[0]])
    patches = [(prop['data_offset'], prop['data_size'], data) for prop, data in replacements]
    deltas = {}
    for offset, size, data in patches:
        delta = len(data) - size
        if delta:
            for prop in all_properties(document):
                if prop['data_offset'] <= offset and offset + size <= prop['data_offset'] + prop['data_size']:
                    deltas[prop['size_offset']] = deltas.get(prop['size_offset'], 0) + delta
    for offset, delta in deltas.items():
        patches.append((offset, 4, struct.pack('<i', struct.unpack_from('<i', payload, offset)[0] + delta)))
    for offset, size, data in sorted(patches, reverse=True):
        payload[offset:offset + size] = data
    struct.pack_into('>I', payload, 0, len(payload) - 4)
    payload.extend(bytes((-len(payload)) % 16))
    return encrypt(bytes(payload))


def enum_bytes(name):
    data = name.encode('utf8') + b'\0'
    return struct.pack('<i', len(data)) + data


def tag_bytes(document, prop):
    return document.plaintext[prop['tag_offset']:prop['data_offset'] + prop['data_size']]


def record_bytes(document, array, index):
    records = document.records(array)
    start = records[index][0]['tag_offset']
    end = records[index + 1][0]['tag_offset'] if index + 1 < len(records) else document.properties[array]['data_offset'] + document.properties[array]['data_size']
    return document.plaintext[start:end]


def clone_skills(state):
    return [dict(row) for row in state['skills']]


@unittest.skipUnless(FIXTURE.exists(), 'The explicitly supplied private fixture is required.')
class OfficerWeaponIntegrationTests(unittest.TestCase):
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

    def edit(self, data_id, skills, document=None, other=()):
        source = document or self.document
        raw, audit = serialize(source, list(other) + [Change('weapon_roll', data_id, 'Skills', skills)])
        return parse_bytes(raw), audit

    def assert_unrelated_preserved(self, document, allowed):
        for name, prop in self.document.properties.items():
            if name not in allowed:
                self.assertEqual(tag_bytes(document, document.properties[name]), tag_bytes(self.document, prop), name)

    def test_unchanged_roundtrip_is_byte_identical(self):
        raw, audit = serialize(self.document, [])
        self.assertEqual(raw, self.document.encrypted)
        self.assertEqual(audit['plaintext_changes'], [])

    def test_fixture_fused_weapon_has_six_normal_and_rare_at_six(self):
        row = weapon.state(self.document, 36)
        self.assertTrue(row['owned'])
        self.assertTrue(row['editable'], row['reason'])
        self.assertEqual(row['weapon_id'], 48)
        self.assertEqual(row['array'], 'WeaponDataArray')
        self.assertEqual(row['index'], 36)
        self.assertEqual(row['attr'], 3)
        self.assertEqual(row['blue_limit'], 6)
        self.assertEqual(row['skills'], [{'id': 2, 'value': 10}, {'id': 0, 'value': 5}, {'id': 12, 'value': 5},
                                        {'id': 5, 'value': 14}, {'id': 4, 'value': 5}, {'id': 11, 'value': 5},
                                        {'id': 14, 'value': 0}, {'id': None, 'value': 0}, {'id': None, 'value': 0}])

    def test_single_roll_scalar_only_expected_tag_and_aes_block(self):
        state = weapon.state(self.document, 36)
        skills = clone_skills(state); skills[0]['value'] = 1
        original = fields(fields(self.document.records('WeaponDataArray')[36])['Skill']['value']['records'][0])['Value']
        document, audit = self.edit(36, skills)
        changed = [index for index, (a, b) in enumerate(zip(document.plaintext, self.document.plaintext)) if a != b]
        self.assertEqual(changed, [original['data_offset']])
        self.assertEqual(audit['changed_aes_blocks'], [original['data_offset'] // 16])
        self.assertFalse(audit['resized'])
        self.assertEqual(weapon.state(document, 36)['skills'], skills)
        self.assert_unrelated_preserved(document, {'WeaponDataArray'})
        for index in range(500):
            if index != 36:
                self.assertEqual(record_bytes(document, 'WeaponDataArray', index), record_bytes(self.document, 'WeaponDataArray', index))

    def test_bonus_edit_preserves_identity_time_attr_equipment_and_cache(self):
        skills = weapon.max_existing_skills(self.document, 36)
        document, _ = self.edit(36, skills)
        old = fields(self.document.records('WeaponDataArray')[36]); new = fields(document.records('WeaponDataArray')[36])
        for name in ('WeaponID', 'ID', 'DataID', 'Attr', 'GetTime'):
            self.assertEqual(tag_bytes(document, new[name]), tag_bytes(self.document, old[name]), name)
        self.assert_unrelated_preserved(document, {'WeaponDataArray'})
        self.assertEqual(weapon.state(document, 36)['skills'][6], {'id': 14, 'value': 0})

    def test_max_existing_keeps_every_bonus_identity_and_position(self):
        state = weapon.state(self.document, 36)
        skills = weapon.max_existing_skills(self.document, 36)
        self.assertEqual([row['id'] for row in skills], [row['id'] for row in state['skills']])
        for old, new in zip(state['skills'], skills):
            if old['id'] in NORMAL_IDS:
                self.assertEqual(new['value'], max(weapon.allowed_values(state, old['id'])))
            else:
                self.assertEqual(new, old)
        document, _ = self.edit(36, skills)
        raw, audit = serialize(document, [Change('weapon_roll', 36, 'Skills', skills)])
        self.assertEqual(raw, document.encrypted)
        self.assertEqual(audit['plaintext_changes'], [])

    def test_max_empty_starter_does_not_add_new_bonuses(self):
        state = weapon.state(self.document, 0)
        self.assertEqual(weapon.max_existing_skills(self.document, 0), state['skills'])
        document, audit = self.edit(0, state['skills'])
        self.assertEqual(document.encrypted, self.document.encrypted)
        self.assertEqual(audit['plaintext_changes'], [])

    def test_add_six_normal_bonuses_to_starter_and_remove_to_zero(self):
        info = weapon.state(self.document, 0)
        self.assertEqual(info['blue_minimum'], 0)
        skills = [{'id': item, 'value': max(weapon.allowed_values(info, item))} for item in range(6)]
        skills += [{'id': None, 'value': 0} for _ in range(3)]
        document, audit = self.edit(0, skills)
        self.assertTrue(audit['resized'])
        self.assertEqual(weapon.state(document, 0)['skills'], skills)
        self.assertEqual(weapon.state(document, 0)['attr'], info['attr'])
        self.assert_unrelated_preserved(document, {'WeaponDataArray'})
        empty = [{'id': None, 'value': 0} for _ in range(9)]
        restored, _ = self.edit(0, empty, document)
        self.assertEqual(restored.encrypted, self.document.encrypted)

    def test_replace_normal_identity_handles_nested_sizes_keeps_rare(self):
        info = weapon.state(self.document, 36)
        skills = clone_skills(info)
        skills[0] = {'id': 25, 'value': max(weapon.allowed_values(info, 25))}
        document, audit = self.edit(36, skills)
        self.assertTrue(audit['resized'])
        self.assertEqual(weapon.state(document, 36)['skills'], skills)
        self.assertEqual(weapon.state(document, 36)['skills'][6], info['skills'][6])
        self.assert_unrelated_preserved(document, {'WeaponDataArray'})
        unchanged, _ = serialize(document, [Change('weapon_roll', 36, 'Skills', skills)])
        self.assertEqual(unchanged, document.encrypted)

    def test_regular_drop_one_bonus_floor_and_rank_six_ceiling(self):
        info = weapon.state(self.document, 36)
        self.assertEqual(info['blue_minimum'], 1)
        skills = clone_skills(info)
        for index in range(6): skills[index] = {'id': None, 'value': 0}
        with self.assertRaises(SaveError): self.edit(36, skills)
        skills[0] = {'id': 3, 'value': 1}
        document, _ = self.edit(36, skills)
        self.assertEqual(sum(row['id'] in NORMAL_IDS for row in weapon.state(document, 36)['skills']), 1)
        self.assertEqual(weapon.state(document, 36)['skills'][6], {'id': 14, 'value': 0})
        overfull = clone_skills(info); overfull[7] = {'id': 3, 'value': 1}
        with self.assertRaises(SaveError): self.edit(36, overfull)

    def test_unique_stock_normal_count_is_minimum_and_can_fill_rank_limit(self):
        acquire = Change('unique_weapon', 89, 'Owned', True)
        data_id = UNIQUE_WEAPONS[89]['data_id']
        info = weapon.state(self.document, data_id, [acquire])
        skills = clone_skills(info)
        present = {row['id'] for row in skills if row['id'] is not None}
        count = sum(row['id'] in NORMAL_IDS for row in skills)
        self.assertEqual(info['blue_minimum'], count)
        removed = clone_skills(info)
        removed[next(index for index, row in enumerate(removed) if row['id'] in NORMAL_IDS)] = {'id': None, 'value': 0}
        with self.assertRaises(SaveError): self.edit(data_id, removed, other=[acquire])
        available = iter(sorted(NORMAL_IDS - present))
        for index, row in enumerate(skills):
            if row['id'] is None and count < info['blue_limit']:
                item = next(available)
                skills[index] = {'id': item, 'value': max(weapon.allowed_values(info, item))}
                count += 1
        document, _ = self.edit(data_id, skills, other=[acquire])
        self.assertEqual(sum(row['id'] in NORMAL_IDS for row in weapon.state(document, data_id)['skills']), info['blue_limit'])

    def test_states_returns_all_owned_references_without_blank_slots(self):
        states = list(weapon.states(self.document))
        self.assertEqual(len(states), 43)
        self.assertEqual(len({row['data_id'] for row in states}), 43)
        self.assertTrue(all(row['owned'] for row in states))
        self.assertEqual({row['data_id'] for row in states if row['array'] == 'WeaponDataArray'}, set(range(42)))
        self.assertEqual({row['data_id'] for row in states if row['array'] == 'UniqueWeaponDataArray'}, {10004})

    def test_rare_replacement_canonicalizes_and_invalid_rare_changes_refused(self):
        original = clone_skills(weapon.state(self.document, 36))
        probes = []
        removed = [dict(row) for row in original]; removed[6] = {'id': None, 'value': 0}; probes.append(removed)
        moved = [dict(row) for row in original]; moved[6], moved[8] = moved[8], moved[6]
        document,_=self.edit(36,moved)
        self.assertEqual(weapon.state(document,36)['skills'],moved)
        changed = [dict(row) for row in original]; changed[6]['id'] = 13
        document,_=self.edit(36,changed)
        result=weapon.state(document,36)['skills']
        self.assertEqual(result[:6],original[:6])
        self.assertEqual(result[6:8],[{'id':None,'value':0}]*2)
        self.assertEqual(result[8],{'id':13,'value':0})
        valued = [dict(row) for row in original]; valued[6]['value'] = 1; probes.append(valued)
        extra = [dict(row) for row in original]; extra[8] = {'id': 13, 'value': 0}; probes.append(extra)
        for skills in probes:
            with self.subTest(skills=skills), self.assertRaises(SaveError):
                self.edit(36, skills)

    def test_invalid_value_type_and_range_refused(self):
        state = weapon.state(self.document, 36)
        maximum = max(weapon.allowed_values(state, 2))
        for value in (-1, 0, maximum + 1, True, 1.0, '1'):
            skills = clone_skills(state); skills[0]['value'] = value
            with self.subTest(value=value), self.assertRaises(SaveError):
                self.edit(36, skills)

    def test_invalid_skill_array_schema_and_identity_refused(self):
        original = clone_skills(weapon.state(self.document, 36))
        bad_id = [dict(row) for row in original]; bad_id[0]['id'] = 100
        bool_id = [dict(row) for row in original]; bool_id[0]['id'] = True
        extra_field = [dict(row) for row in original]; extra_field[0]['ignored'] = 1
        missing = [dict(row) for row in original]; del missing[0]['value']
        duplicate = [dict(row) for row in original]; duplicate[1]['id'] = 2
        empty_value = [dict(row) for row in original]; empty_value[8]['value'] = 1
        for skills in (None, [], original[:8], original + [original[8]], bad_id, bool_id, extra_field, missing, duplicate, empty_value):
            with self.subTest(skills=skills), self.assertRaises(SaveError):
                self.edit(36, skills)

    def test_unowned_and_unsupported_data_ids_refused(self):
        empty = [{'id': None, 'value': 0} for _ in range(9)]
        for data_id in (42, 499, 10000, -1, 500, 9999, 10084, True, '36'):
            with self.subTest(data_id=data_id), self.assertRaises(SaveError):
                self.edit(data_id, empty)

    def test_unique_unlock_then_roll_same_batch_uses_final_stock(self):
        weapon_id = 89
        data_id = UNIQUE_WEAPONS[weapon_id]['data_id']
        acquire = Change('unique_weapon', weapon_id, 'Owned', True)
        state = weapon.state(self.document, data_id, [acquire])
        self.assertTrue(state['owned'])
        skills = weapon.max_existing_skills(self.document, data_id, [acquire])
        document, _ = self.edit(data_id, skills, other=[acquire])
        self.assertEqual(weapon.state(document, data_id)['skills'], skills)
        self.assertEqual(weapon.state(document, data_id)['weapon_id'], weapon_id)
        self.assertEqual(fields(document.records('UniqueWeaponDataArray')[0])['DataID']['value'], data_id)
        self.assertEqual(fields(document.records('CollectedWeaponDataArray')[weapon_id])['WeaponID']['value'], 'EWeaponID::WeaponID_089')

    def test_unique_tiers_use_seven_and_eight_blue_slots(self):
        for weapon_id, limit in [(89, 7), (132, 8)]:
            acquire = Change('unique_weapon', weapon_id, 'Owned', True)
            state = weapon.state(self.document, UNIQUE_WEAPONS[weapon_id]['data_id'], [acquire])
            self.assertEqual(state['blue_limit'], limit)
            self.assertLessEqual(sum(row['id'] in NORMAL_IDS for row in state['skills']), limit)

    def test_unique_stock_attack_43_exception_stays_weapon_specific(self):
        weapon_id = 116
        acquire = Change('unique_weapon', weapon_id, 'Owned', True)
        data_id = UNIQUE_WEAPONS[weapon_id]['data_id']
        state = weapon.state(self.document, data_id, [acquire])
        self.assertIn(43, weapon.allowed_values(state, 4))
        self.assertNotIn(31, weapon.allowed_values(state, 4))
        ordinary = weapon.state(self.document, 36)
        self.assertNotIn(43, weapon.allowed_values(ordinary, 4))
        skills = clone_skills(state)
        attack_slot = next(index for index, row in enumerate(skills) if row['id'] == 4)
        skills[attack_slot]['value'] = 43
        document, _ = self.edit(data_id, skills, other=[acquire])
        self.assertEqual(weapon.state(document, data_id)['skills'][attack_slot]['value'], 43)

    def test_duplicate_roll_request_refused_before_source_mutation(self):
        change = Change('weapon_roll', 36, 'Skills', weapon.max_existing_skills(self.document, 36))
        with self.assertRaises(SaveError):
            serialize(self.document, [change, change])
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(), self.fixture_hash)

    def test_failed_edit_leaves_copy_destination_and_audit_untouched(self):
        source = self.folder / 'source-copy.sav'; source.write_bytes(self.document.encrypted)
        destination = self.folder / 'existing-copy.sav'; destination.write_bytes(self.document.encrypted)
        document = read_save(source)
        skills = clone_skills(weapon.state(document, 36)); skills[6]['value'] = 1
        with self.assertRaises(SaveError):
            write_save(document, destination, [Change('weapon_roll', 36, 'Skills', skills)], overwrite=True)
        self.assertEqual(source.read_bytes(), self.document.encrypted)
        self.assertEqual(destination.read_bytes(), self.document.encrypted)
        self.assertFalse(list(self.folder.glob('*.changes.json')))

    def test_valid_replace_creates_original_backup_and_restore(self):
        source = self.folder / 'source-copy.sav'; source.write_bytes(self.document.encrypted)
        document = read_save(source)
        skills = weapon.max_existing_skills(document, 36)
        saved, _ = write_save(document, source, [Change('weapon_roll', 36, 'Skills', skills)], overwrite=True)
        self.assertEqual(weapon.state(read_save(saved), 36)['skills'], skills)
        backups = list((self.folder / 'DW3EditorBackups').glob('*.sav'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), self.document.encrypted)
        restored = restore_backup(backups[0], self.folder / 'restored-copy.sav')
        self.assertEqual(restored.read_bytes(), self.document.encrypted)

    def test_malformed_nested_slot_count_enum_and_scalar_shape_rejected(self):
        record = fields(self.document.records('WeaponDataArray')[36])
        skill = record['Skill']; first = fields(skill['value']['records'][0])
        raw_skill = bytearray(self.document.plaintext[skill['data_offset']:skill['data_offset'] + skill['data_size']])
        struct.pack_into('<i', raw_skill, 0, 8)
        probes = [[(skill, bytes(raw_skill))],
                  [(first['EquipItemID'], enum_bytes('OtherItemID::BAD'))],
                  [(first['Value'], struct.pack('<q', 10))]]
        for changes in probes:
            with self.subTest(changes=changes), self.assertRaises(SaveError):
                parse_bytes(edited_fixture_bytes(self.document, changes))
        unknown=parse_bytes(edited_fixture_bytes(self.document,[(first['EquipItemID'],enum_bytes('EEquipItemID::BAD'))]))
        self.assertFalse(weapon.state(unknown,36)['editable'])
        self.assertEqual(serialize(unknown)[0],unknown.encrypted)


if __name__ == '__main__':
    unittest.main(verbosity=2)
