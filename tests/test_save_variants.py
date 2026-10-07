"""Variable bodyguard-team and conservative saved-roll compatibility regressions.

No player save is shipped with these tests. Integration tests use the original
explicit workspace fixture, or an optional copied save selected through
DW3_TEST_REPORTED_SAVE. All writes go to newly created test directories.
"""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import os
import shutil
import struct
import sys
import unittest
import uuid
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / 'tests'))
from models import Change, SaveError, fields
from save_parser import read_save, parse_bytes
from save_writer import serialize
from save_codec import encrypt
import bodyguard_editor as guard
import bodyguard_growth as growth
from test_bodyguards import edited_fixture_bytes, enum_bytes, record_bytes, tag_bytes

ORIGINAL = WORKSPACE / 'work' / 'original-upload' / 'GameStatusData.sav'
REPORTED = Path(os.environ['DW3_TEST_REPORTED_SAVE']) if os.environ.get('DW3_TEST_REPORTED_SAVE') else None
RUNS = PROJECT / 'tests' / '.variant-test-runs'
BG_ARRAYS = ('GuardDataArray', 'GuardWeaponDataArray', 'GuardEquipItemDataArray')


def saved_name(record, index):
    names = fields(record).get('UnitNameLang', {}).get('value', {}).get('values', [])
    return next((name for name in names if isinstance(name, str) and name.strip()), f'Team {index + 1}')


def two_team_copy(document):
    """Keep two whole tagged records without manufacturing a team or its name."""
    prop = document.properties['GuardDataArray']
    payload = struct.pack('<i', 2) + b''.join(record_bytes(document, 'GuardDataArray', i) for i in range(2))
    return parse_bytes(edited_fixture_bytes(document, [(prop, payload)]))


class PublicTeamBoundsTests(unittest.TestCase):
    def setUp(self):
        def prop(name, value):
            return {'name': name, 'value': value}
        team = [prop('SPoint', 0), prop('BGLevels', {'values': [0] * 6}),
                prop('MemberItem', 'EGuardEquipItemID::NUM'),
                prop('MemberWeapon', {'values': [-1] * 10})]
        arrays = {'GuardDataArray': [team, team], 'GuardEquipItemDataArray': [], 'GuardWeaponDataArray': []}
        self.document = SimpleNamespace(records=lambda name: arrays[name])

    def test_second_saved_team_is_accessible_without_four_records(self):
        self.assertEqual(guard.team_state(self.document, 1)['SPoint'], 0)

    def test_absent_negative_and_boolean_team_indexes_fail_explicitly(self):
        for index in (2, 3, -1, True, False):
            with self.subTest(index=index), self.assertRaises(SaveError):
                guard.team_state(self.document, index)

    def test_absent_team_requests_are_rejected_by_all_state_readers(self):
        changes = [Change('bodyguard', 2, 'SPoint', 99999)]
        for reader in (guard.item_state, guard.weapon_state):
            with self.subTest(reader=reader.__name__), self.assertRaises(SaveError):
                reader(self.document, changes)
        with self.assertRaises(SaveError):
            guard.team_state(self.document, 0, changes)

    def test_authored_weapon_roll_validation_remains_strict(self):
        # This is a compatibility read case, not permission to author the roll.
        with self.assertRaises(SaveError):
            guard.validate_skills(185, [{'id': 2, 'value': 1}])
        with self.assertRaises(SaveError):
            guard.validate_skills(175, [{'id': 0, 'value': 29}])


class TwoTeamChecks:
    def assert_teams_unchanged(self, edited):
        self.assertEqual(tag_bytes(edited, edited.properties['GuardDataArray']),
                         tag_bytes(self.document, self.document.properties['GuardDataArray']))

    def test_unchanged_encrypted_roundtrip_is_exact(self):
        self.assertEqual(len(self.document.records('GuardDataArray')), 2)
        raw, audit = serialize(self.document)
        self.assertEqual(raw, self.document.encrypted)
        self.assertEqual(audit['plaintext_changes'], [])
        self.assertEqual(audit['changed_aes_blocks'], [])

    def test_one_officer_edit_preserves_every_bodyguard_region(self):
        original = fields(self.document.records('PCSaveDataArray')[0])['SPoint']['value']
        value = original - 1 if original else 1
        raw, audit = serialize(self.document, [Change('officer', 0, 'SPoint', value)])
        edited = parse_bytes(raw)
        self.assertEqual(fields(edited.records('PCSaveDataArray')[0])['SPoint']['value'], value)
        for name in BG_ARRAYS:
            self.assertEqual(tag_bytes(edited, edited.properties[name]), tag_bytes(self.document, self.document.properties[name]), name)
        self.assertTrue(audit['plaintext_changes'])
        self.assertFalse(audit['resized'])

    def test_both_saved_teams_accept_max_growth_without_adding_records(self):
        changes = [Change('bodyguard', i, field, value) for i in range(2)
                   for field, value in [('SPoint', 99999), ('BGLevels', growth.safe_preset())]]
        raw, _ = serialize(self.document, changes)
        edited = parse_bytes(raw)
        self.assertEqual(len(edited.records('GuardDataArray')), 2)
        self.assertEqual(edited.properties['GuardDataArray']['value']['count'], 2)
        for i, original in enumerate(self.document.records('GuardDataArray')):
            before, after = fields(original), fields(edited.records('GuardDataArray')[i])
            self.assertEqual(guard.team_state(edited, i)['SPoint'], 99999)
            self.assertEqual(guard.team_state(edited, i)['BGLevels'], growth.safe_preset())
            for name in before:
                if name not in ('SPoint', 'BGLevels'):
                    self.assertEqual(tag_bytes(edited, after[name]), tag_bytes(self.document, before[name]), (i, name))
        self.assertEqual([saved_name(r, i) for i, r in enumerate(edited.records('GuardDataArray'))],
                         [saved_name(r, i) for i, r in enumerate(self.document.records('GuardDataArray'))])

    def test_guard_item_only_edits_preserve_team_records(self):
        changes = [Change('guard_item', i, 'Owned', True) for i in guard.GUARD_ITEMS]
        changes += [Change('guard_item', i, 'Value', row['max_value'])
                    for i, row in guard.GUARD_ITEMS.items() if row['kind'] == 'normal']
        edited = parse_bytes(serialize(self.document, changes)[0])
        self.assert_teams_unchanged(edited)
        self.assertTrue(all(row['owned'] for row in guard.item_state(edited).values()))

    def test_guard_weapon_only_edits_preserve_team_records(self):
        changes = [Change('guard_weapon', i, field, True) for i in guard.GUARD_WEAPONS
                   for field in ('Owned', 'MaxBonuses')]
        edited = parse_bytes(serialize(self.document, changes)[0])
        self.assert_teams_unchanged(edited)
        self.assertEqual({row['weapon_id'] for row in guard.weapon_state(edited) if row['weapon_id'] is not None}, set(guard.GUARD_WEAPONS))

    def test_absent_team_cannot_be_edited_through_any_api(self):
        for field, value in [('SPoint', 99999), ('BGLevels', growth.safe_preset()),
                             ('MemberItem', None), ('MemberWeapon', [-1] * 10)]:
            changes = [Change('bodyguard', 2, field, value)]
            for operation in (serialize, guard.item_state, guard.weapon_state):
                with self.subTest(field=field, operation=operation.__name__), self.assertRaises(SaveError):
                    operation(self.document, changes)

    def test_mismatched_negative_and_truncated_guard_arrays_are_rejected(self):
        prop = self.document.properties['GuardDataArray']
        payload = self.document.plaintext[prop['data_offset']:prop['data_offset'] + prop['data_size']]
        probes = [struct.pack('<i', 3) + payload[4:], struct.pack('<i', 1) + payload[4:],
                  struct.pack('<i', -1) + payload[4:], payload[:-1]]
        for i, malformed in enumerate(probes):
            with self.subTest(case=i), self.assertRaises(SaveError):
                parse_bytes(edited_fixture_bytes(self.document, [(prop, malformed)]))

    def test_wrong_guard_struct_type_is_rejected_even_with_valid_record_bytes(self):
        prop = self.document.properties['GuardDataArray']
        data = bytearray(self.document.plaintext)
        start, end = prop['tag_offset'], prop['data_offset']
        tag = bytes(data[start:end])
        self.assertIn(b'GuardSaveData', tag)
        data[start:end] = tag.replace(b'GuardSaveData', b'OtherSaveData')
        with self.assertRaises(SaveError):
            parse_bytes(encrypt(bytes(data)))

    def test_invalid_growth_and_unowned_equipment_still_fail(self):
        for change in [Change('bodyguard', 0, 'BGLevels', [11, 11, 11, 3, 3, 3]),
                       Change('bodyguard', 0, 'SPoint', 100000),
                       Change('bodyguard', 0, 'MemberWeapon', [999] + [-1] * 9)]:
            with self.subTest(field=change.field), self.assertRaises(SaveError):
                serialize(self.document, [change])


@unittest.skipUnless(ORIGINAL.exists(), 'The explicitly supplied original fixture is required.')
class OriginalVariantIntegrationTests(TwoTeamChecks, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_hash = hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
        cls.original = read_save(ORIGINAL)
        cls.document = two_team_copy(cls.original)

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == cls.fixture_hash

    def test_original_four_team_layout_remains_supported(self):
        self.assertEqual(len(self.original.records('GuardDataArray')), 4)
        self.assertEqual(serialize(self.original)[0], self.original.encrypted)

    def test_known_positive_nonprofile_weapon_roll_is_preserved_until_explicit_max(self):
        record = fields(self.document.records('GuardWeaponDataArray')[1])
        skill = fields(record['Skill']['value']['records'][0])
        self.assertNotIn(29, guard.GUARD_WEAPONS[175]['allowed_values_by_guard_item_id']['0'])
        document = parse_bytes(edited_fixture_bytes(self.document, [
            (skill['GuardEquipItemID'], enum_bytes(guard.GUARD_ITEMS[0]['enum'])),
            (skill['Value'], struct.pack('<i', 29))]))
        self.assertTrue(guard.weapon_state(document)[1]['editable'])
        self.assertFalse(guard.weapon_state(document)[1]['reason'])
        self.assertEqual(serialize(document)[0], document.encrypted)
        changes = [Change('guard_weapon', i, 'MaxBonuses', True)
                   for i in {r['weapon_id'] for r in guard.weapon_state(document) if r['weapon_id'] is not None}]
        edited = parse_bytes(serialize(document, changes)[0])
        before = guard.weapon_state(document)[1]
        after = guard.weapon_state(edited)[1]
        for saved in before['skills']:
            updated = next(row for row in after['skills'] if row['id'] == saved['id'])
            self.assertGreaterEqual(updated['value'], saved['value'])
        self.assertEqual(after['skills'][0], {'id': 0, 'value': 30})
        unchanged = parse_bytes(serialize(document, [Change('guard_weapon_slot', 1, 'Skills', before['skills'])])[0])
        self.assertEqual(unchanged.encrypted, document.encrypted)
        bad = [dict(row) for row in before['skills']]
        bad[0]['value'] = 31
        with self.assertRaises(SaveError):
            serialize(document, [Change('guard_weapon_slot', 1, 'Skills', bad)])

    def test_unrecognized_saved_bonuses_are_view_only_but_new_authored_bonuses_fail(self):
        record = fields(self.document.records('GuardWeaponDataArray')[1])
        def malformed(skills):
            replacements = []
            for i, saved in enumerate(record['Skill']['value']['records']):
                slot = fields(saved)
                item, value = skills[i] if i < len(skills) else (None, 0)
                replacements += [(slot['GuardEquipItemID'], enum_bytes('EGuardEquipItemID::NUM' if item is None else guard.GUARD_ITEMS[item]['enum'])),
                                 (slot['Value'], struct.pack('<i', value))]
            return edited_fixture_bytes(self.document, replacements)
        for skills in ([(0, 30), (0, 25)], [(0, 1), (1, 1), (2, 1), (3, 1)],
                       [(0, 0)], [(0, -1)], [(9, 1)]):
            with self.subTest(skills=skills):
                document = parse_bytes(malformed(skills))
                self.assertFalse(guard.weapon_state(document)[1]['editable'])
                self.assertEqual(serialize(document)[0], document.encrypted)
                with self.assertRaises(SaveError):
                    serialize(document, [Change('guard_weapon_slot', 1, 'Skills', guard.max_skills(175))])

    def test_gui_switches_from_four_to_two_saved_teams(self):
        import tkinter as tk
        import gui
        RUNS.mkdir(parents=True, exist_ok=True)
        folder = RUNS / uuid.uuid4().hex
        folder.mkdir()
        root = None
        try:
            paths = [folder / 'four-teams.sav', folder / 'two-teams.sav']
            for path, document in zip(paths, (self.original, self.document)):
                path.write_bytes(document.encrypted)
            root = tk.Tk()
            root.withdraw()
            editor = gui.Editor(root)
            errors = []
            with patch.object(gui.filedialog, 'askopenfilename', side_effect=[str(p) for p in paths]), \
                 patch.object(gui.messagebox, 'askyesno', return_value=True), \
                 patch.object(gui.messagebox, 'showerror', side_effect=lambda *a, **kw: errors.append(a)):
                editor.open()
                self.assertEqual(len(editor.bodyguards.get_children()), 4)
                editor.bodyguards.selection_set('3')
                editor.select_bodyguard()
                self.assertEqual(editor.current_bodyguard, 3)
                editor.open()
                self.assertFalse(errors)
                self.assertEqual(len(editor.bodyguards.get_children()), 2)
                self.assertIn(editor.current_bodyguard, (0, 1))
                self.assertEqual([editor.bodyguards.item(str(i), 'text') for i in range(2)],
                                 [saved_name(r, i) for i, r in enumerate(self.document.records('GuardDataArray'))])
                editor.max_bodyguards()
                self.assertFalse(errors)
                self.assertEqual({c.index for c in editor.changes.values() if c.category == 'bodyguard'}, {0, 1})
                self.assertEqual([path.read_bytes() for path in paths], [self.original.encrypted, self.document.encrypted])
        finally:
            if root is not None:
                root.destroy()
            assert folder.resolve().is_relative_to(RUNS.resolve())
            shutil.rmtree(folder)


@unittest.skipUnless(REPORTED is not None and REPORTED.exists(), 'Set DW3_TEST_REPORTED_SAVE to an explicitly supplied save copy.')
class ReportedSaveIntegrationTests(TwoTeamChecks, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_hash = hashlib.sha256(REPORTED.read_bytes()).hexdigest()
        cls.document = read_save(REPORTED)

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(REPORTED.read_bytes()).hexdigest() == cls.fixture_hash

    def test_reported_nonprofile_copy_is_preserved_by_bulk_max_and_refuses_direct_edits(self):
        state = guard.weapon_state(self.document)[23]
        self.assertIsNotNone(state['weapon_id'])
        self.assertFalse(state['editable'])
        self.assertTrue(state['reason'])
        changes = [Change('guard_weapon', i, field, True) for i in guard.GUARD_WEAPONS
                   for field in ('Owned', 'MaxBonuses')]
        edited = parse_bytes(serialize(self.document, changes)[0])
        self.assertEqual(record_bytes(edited, 'GuardWeaponDataArray', 23), record_bytes(self.document, 'GuardWeaponDataArray', 23))
        self.assertEqual(guard.weapon_state(edited)[23]['skills'], state['skills'])
        with self.assertRaises(SaveError):
            serialize(self.document, [Change('guard_weapon_slot', 23, 'Skills', guard.max_skills(state['weapon_id']))])


if __name__ == '__main__':
    unittest.main()
