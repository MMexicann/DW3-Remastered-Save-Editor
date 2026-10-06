"""Officer weapon element and rare-skill regressions; private fixtures optional.

Public cases use invented model values and shipped rules. Integration cases
read only the explicitly supplied workspace fixture and edit in-memory copies.
No game installation or player save is included in the published tests.
"""
from pathlib import Path
import hashlib
import shutil
import struct
import sys
import unittest
import uuid
from contextlib import ExitStack
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / 'tests'))
from models import Change, SaveError, fields
from save_parser import read_save, parse_bytes
from save_writer import serialize, UNIQUE_WEAPONS
import officer_weapon_editor as weapon
from test_weapon_rolls import edited_fixture_bytes, enum_bytes, record_bytes, tag_bytes, clone_skills

FIXTURE = PROJECT.parent.parent / 'work' / 'original-upload' / 'GameStatusData.sav'
GUI_RUNS = PROJECT.parent.parent / 'work' / 'weapon-attribute-gui-tests'


def blank_skills():
    return [{'id': None, 'value': 0} for _ in range(9)]


class PublicAttributeRules(unittest.TestCase):
    def info(self, elements=0):
        return {'owned': True, 'array': 'WeaponDataArray', 'weapon_id': 6,
                'blue_limit': 6, 'blue_minimum': 0, 'red_limit': 1,
                'red_minimum': 0, 'skills': blank_skills(), 'attr': elements,
                'elements': elements, 'element_editable': True, 'element_reason': ''}

    def test_element_mapping_uses_exact_native_bits(self):
        self.assertEqual(weapon.ELEMENT_MASK, 0x3c)
        self.assertEqual(weapon.ELEMENTS, {'None': 0, 'Fire': 4, 'Lightning': 8, 'Steel': 16, 'Wind': 32})

    def test_authored_elements_use_one_native_element(self):
        for value in (0, 4, 8, 16, 32):
            with self.subTest(value=value):
                self.assertEqual(weapon.validate_elements(self.info(), value), value)
        for value in (-1, 1, 2, 3, 12, 20, 60, 64, 128, 256, True, False, 4.0, '4', None):
            with self.subTest(value=value), self.assertRaises(SaveError):
                weapon.validate_elements(self.info(), value)

    def test_existing_combination_can_be_preserved_but_not_created(self):
        self.assertEqual(weapon.validate_elements(self.info(12), 12), 12)
        self.assertEqual(weapon.validate_elements(self.info(12), 32), 32)
        with self.assertRaises(SaveError):
            weapon.validate_elements(self.info(4), 12)

    def test_existing_element_cannot_be_removed_without_a_verified_native_path(self):
        self.assertEqual(weapon.validate_elements(self.info(0), 0), 0)
        for original in (4, 8, 16, 32, 12):
            with self.subTest(original=original), self.assertRaises(SaveError):
                weapon.validate_elements(self.info(original), 0)

    def test_rare_donor_pool_excludes_nontransferable_items(self):
        expected = set(range(13, 25)) | set(range(28, 40))
        self.assertEqual(set(weapon.RARE_ITEMS), expected)
        for item in expected:
            self.assertEqual(weapon.allowed_values(self.info(), item), [0])
        for item in (40, 41, 42, 43, 99, 100, True):
            with self.subTest(item=item), self.assertRaises(SaveError):
                weapon.allowed_values(self.info(), item)

    def test_adding_a_rare_skill_canonicalizes_normal_order_and_red_slot(self):
        skills = blank_skills()
        skills[1] = {'id': 2, 'value': 1}
        skills[4] = {'id': 14, 'value': 0}
        skills[7] = {'id': 4, 'value': 1}
        expected = [{'id': 2, 'value': 1}, {'id': 4, 'value': 1}]
        expected += [{'id': None, 'value': 0} for _ in range(6)]
        expected += [{'id': 14, 'value': 0}]
        self.assertEqual(weapon.validate_skills(self.info(), skills), expected)

    def test_duplicate_or_multiple_red_skills_are_refused(self):
        for pair in ((13, 14), (14, 14)):
            skills = blank_skills()
            skills[0] = {'id': pair[0], 'value': 0}
            skills[8] = {'id': pair[1], 'value': 0}
            with self.subTest(pair=pair), self.assertRaises(SaveError):
                weapon.validate_skills(self.info(), skills)

    def test_new_red_values_are_zero_even_for_hex_mark_saddle(self):
        for value in (-1, 1, 20, True, 0.0):
            skills = blank_skills()
            skills[8] = {'id': 14, 'value': value}
            with self.subTest(value=value), self.assertRaises(SaveError):
                weapon.validate_skills(self.info(), skills)

    def test_existing_red_skill_cannot_be_removed(self):
        info = self.info()
        info['skills'][6] = {'id': 14, 'value': 0}
        info['red_minimum'] = 1
        with self.assertRaises(SaveError):
            weapon.validate_skills(info, blank_skills())

    def test_unchanged_known_nonzero_red_value_is_preserved_only(self):
        info = self.info()
        info['skills'][6] = {'id': 14, 'value': 7}
        info['red_minimum'] = 1
        self.assertEqual(weapon.validate_skills(info, clone_skills(info)), info['skills'])
        skills = clone_skills(info)
        skills[6]['value'] = 8
        with self.assertRaises(SaveError):
            weapon.validate_skills(info, skills)
        added = blank_skills()
        added[8] = {'id': 14, 'value': 7}
        with self.assertRaises(SaveError):
            weapon.validate_skills(self.info(), added)

    def test_numeric_only_changes_do_not_move_an_existing_rare_skill(self):
        info = self.info()
        info['skills'][0] = {'id': 2, 'value': 1}
        info['skills'][6] = {'id': 14, 'value': 0}
        info['red_minimum'] = 1
        skills = clone_skills(info)
        skills[0]['value'] = 2
        self.assertEqual(weapon.validate_skills(info, skills), skills)

    def test_replacing_or_moving_a_rare_skill_uses_the_native_red_slot(self):
        info = self.info()
        info['skills'][0] = {'id': 2, 'value': 1}
        info['skills'][6] = {'id': 14, 'value': 0}
        info['red_minimum'] = 1
        for wanted in (13, 14):
            skills = clone_skills(info)
            skills[6] = {'id': None, 'value': 0}
            skills[3] = {'id': wanted, 'value': 0}
            validated = weapon.validate_skills(info, skills)
            self.assertEqual(validated[0], {'id': 2, 'value': 1})
            self.assertEqual(validated[8], {'id': wanted, 'value': 0})
            self.assertTrue(all(s['id'] is None for s in validated[1:8]))

    def test_red_additions_do_not_expand_the_normal_bonus_cap(self):
        info = self.info()
        skills = [{'id': i, 'value': 1} for i in range(6)] + blank_skills()[:2] + [{'id': 14, 'value': 0}]
        self.assertEqual(weapon.validate_skills(info, skills), skills)
        skills[6] = {'id': 6, 'value': 1}
        with self.assertRaises(SaveError):
            weapon.validate_skills(info, skills)


@unittest.skipUnless(FIXTURE.exists(), 'The explicitly supplied private workspace fixture is required.')
class WeaponAttributeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read_save(FIXTURE)
        cls.fixture_hash = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == cls.fixture_hash

    def assert_other_properties_unchanged(self, source, edited, allowed):
        for name, prop in source.properties.items():
            if name not in allowed:
                self.assertEqual(tag_bytes(edited, edited.properties[name]), tag_bytes(source, prop), name)

    def test_element_edit_changes_only_the_selected_attr_and_expected_aes_blocks(self):
        source = self.document
        raw, audit = serialize(source, [Change('weapon_element', 36, 'Elements', 4)])
        edited = parse_bytes(raw)
        record = fields(source.records('WeaponDataArray')[36])
        prop = record['Attr']
        expected = (record['Attr']['value'] & ~weapon.ELEMENT_MASK) | 4
        self.assertEqual(weapon.state(edited, 36)['attr'], expected)
        changed = [i for i, (a, b) in enumerate(zip(source.plaintext, edited.plaintext)) if a != b]
        self.assertTrue(changed)
        self.assertTrue(all(prop['data_offset'] <= i < prop['data_offset'] + 8 for i in changed))
        self.assertEqual(audit['changed_aes_blocks'], sorted({i // 16 for i in changed}))
        self.assertFalse(audit['resized'])
        self.assert_other_properties_unchanged(source, edited, {'WeaponDataArray'})
        for i in range(len(source.records('WeaponDataArray'))):
            if i != 36:
                self.assertEqual(record_bytes(edited, 'WeaponDataArray', i), record_bytes(source, 'WeaponDataArray', i))
        after = fields(edited.records('WeaponDataArray')[36])
        for name in record:
            if name != 'Attr':
                self.assertEqual(tag_bytes(edited, after[name]), tag_bytes(source, record[name]), name)

    def test_element_edit_preserves_all_other_int64_bits(self):
        prop = fields(self.document.records('WeaponDataArray')[36])['Attr']
        for before in ((1 << 45) | 0xc3 | 4, -(1 << 63) | 0xc3 | 4):
            with self.subTest(negative=before < 0):
                source = parse_bytes(edited_fixture_bytes(self.document, [(prop, struct.pack('<q', before))]))
                edited = parse_bytes(serialize(source, [Change('weapon_element', 36, 'Elements', 32)])[0])
                self.assertEqual(weapon.state(edited, 36)['attr'], (before & ~weapon.ELEMENT_MASK) | 32)
                self.assertEqual(weapon.state(edited, 36)['attr'] & ~weapon.ELEMENT_MASK, before & ~weapon.ELEMENT_MASK)

    def test_addition_on_a_starter_preserves_its_hit_flags(self):
        candidate = next(row for row in weapon.states(self.document)
                         if row['array'] == 'WeaponDataArray' and row['metadata'].get('initial_possession'))
        edited = parse_bytes(serialize(self.document, [Change('weapon_element', candidate['data_id'], 'Elements', 16)])[0])
        after = weapon.state(edited, candidate['data_id'])
        self.assertEqual(after['elements'], 16)
        self.assertEqual(after['attr'] & 3, candidate['attr'] & 3)

    def test_existing_element_cannot_be_cleared_by_writer(self):
        source = parse_bytes(serialize(self.document, [Change('weapon_element', 36, 'Elements', 4)])[0])
        with self.assertRaises(SaveError):
            serialize(source, [Change('weapon_element', 36, 'Elements', 0)])
        self.assertEqual(serialize(source, [Change('weapon_element', 36, 'Elements', 4)])[0], source.encrypted)

    def test_invalid_element_fields_references_duplicates_and_types_are_rejected(self):
        cases = [[Change('weapon_element', 36, 'Attr', 4)],
                 [Change('weapon_element', -1, 'Elements', 4)],
                 [Change('weapon_element', 500, 'Elements', 4)],
                 [Change('weapon_element', True, 'Elements', 4)],
                 [Change('weapon_element', 36, 'Elements', True)],
                 [Change('weapon_element', 36, 'Elements', 12)],
                 [Change('weapon_element', 36, 'Elements', 4), Change('weapon_element', 36, 'Elements', 8)]]
        empty = next(i for i, row in enumerate(self.document.records('WeaponDataArray'))
                     if fields(row)['WeaponID']['value'] == 'EWeaponID::NUM')
        cases.append([Change('weapon_element', empty, 'Elements', 4)])
        for i, changes in enumerate(cases):
            with self.subTest(case=i), self.assertRaises(SaveError):
                serialize(self.document, changes)

    def test_rare_replacement_moves_only_bonus_fields_preserves_attr_cache_and_story(self):
        source = self.document
        skills = clone_skills(weapon.state(source, 36))
        skills[6] = {'id': 13, 'value': 0}
        edited = parse_bytes(serialize(source, [Change('weapon_roll', 36, 'Skills', skills)])[0])
        state = weapon.state(edited, 36)
        self.assertEqual(state['skills'][8], {'id': 13, 'value': 0})
        self.assertEqual(state['skills'][:6], skills[:6])
        self.assertTrue(all(s['id'] is None for s in state['skills'][6:8]))
        before = fields(source.records('WeaponDataArray')[36])
        after = fields(edited.records('WeaponDataArray')[36])
        for name in before:
            if name != 'Skill':
                self.assertEqual(tag_bytes(edited, after[name]), tag_bytes(source, before[name]), name)
        self.assert_other_properties_unchanged(source, edited, {'WeaponDataArray'})
        self.assertEqual(serialize(edited)[0], edited.encrypted)

    def test_numeric_only_max_keeps_the_original_rare_slot(self):
        source = self.document
        original = weapon.state(source, 36)
        skills = weapon.max_existing_skills(source, 36)
        edited = parse_bytes(serialize(source, [Change('weapon_roll', 36, 'Skills', skills)])[0])
        self.assertEqual(weapon.state(edited, 36)['skills'][6], original['skills'][6])
        self.assertEqual(serialize(source)[0], source.encrypted)

    def test_known_nonzero_saved_rare_value_is_not_silently_rewritten(self):
        slot = fields(fields(self.document.records('WeaponDataArray')[36])['Skill']['value']['records'][6])
        source = parse_bytes(edited_fixture_bytes(self.document, [(slot['Value'], struct.pack('<i', 7))]))
        state = weapon.state(source, 36)
        self.assertEqual(state['skills'][6], {'id': 14, 'value': 7})
        self.assertEqual(serialize(source)[0], source.encrypted)
        skills = weapon.max_existing_skills(source, 36)
        edited = parse_bytes(serialize(source, [Change('weapon_roll', 36, 'Skills', skills)])[0])
        self.assertEqual(weapon.state(edited, 36)['skills'][6], {'id': 14, 'value': 7})
        skills[6]['value'] = 8
        with self.assertRaises(SaveError):
            serialize(source, [Change('weapon_roll', 36, 'Skills', skills)])

    def test_pending_unique_acquisition_and_element_and_rare_edit_are_combined_safely(self):
        template = UNIQUE_WEAPONS[116]
        data_id = template['data_id']
        acquired = [Change('unique_weapon', 116, 'Owned', True)]
        stock = weapon.state(self.document, data_id, acquired)
        skills = clone_skills(stock)
        empty = next(i for i, skill in enumerate(skills) if skill['id'] is None)
        skills[empty] = {'id': 14, 'value': 0}
        changes = acquired + [Change('weapon_roll', data_id, 'Skills', skills),
                              Change('weapon_element', data_id, 'Elements', 32)]
        edited = parse_bytes(serialize(self.document, changes)[0])
        result = weapon.state(edited, data_id)
        self.assertEqual(result['attr'], (template['attribute_bitmask'] & ~weapon.ELEMENT_MASK) | 32)
        self.assertEqual(result['skills'][8], {'id': 14, 'value': 0})
        self.assertEqual(next(s['value'] for s in result['skills'] if s['id'] == 4), 43)
        cached = fields(edited.records('CollectedWeaponDataArray')[116])
        self.assertEqual(cached['Attr']['value'], template['attribute_bitmask'])
        cached_skills = [{'id': weapon.ITEM_IDS.get(fields(s)['EquipItemID']['value']),
                          'value': fields(s)['Value']['value']}
                         for s in cached['Skill']['value']['records']]
        self.assertEqual([{'id': s['item_id'] if s['item_id'] in weapon.ITEMS else None, 'value': s['value']}
                          for s in template['skill_slots']], cached_skills)
        self.assert_other_properties_unchanged(self.document, edited, {'UniqueWeaponDataArray', 'CollectedWeaponDataArray'})

    def test_existing_combined_element_mask_roundtrips_and_can_be_replaced(self):
        prop = fields(self.document.records('WeaponDataArray')[36])['Attr']
        source = parse_bytes(edited_fixture_bytes(self.document, [(prop, struct.pack('<q', 3 | 12))]))
        self.assertEqual(serialize(source, [Change('weapon_element', 36, 'Elements', 12)])[0], source.encrypted)
        edited = parse_bytes(serialize(source, [Change('weapon_element', 36, 'Elements', 8)])[0])
        self.assertEqual(weapon.state(edited, 36)['attr'], 3 | 8)


@unittest.skipUnless(FIXTURE.exists(), 'The explicitly supplied private workspace fixture is required.')
class WeaponAttributeGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read_save(FIXTURE)
        cls.fixture_hash = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == cls.fixture_hash

    def setUp(self):
        import tkinter as tk
        import gui
        self.tk = tk
        self.gui = gui
        self.errors = []
        GUI_RUNS.mkdir(parents=True, exist_ok=True)
        self.folder = GUI_RUNS / uuid.uuid4().hex
        self.folder.mkdir()
        self.copy = self.folder / 'input-copy.sav'
        self.copy.write_bytes(self.document.encrypted)
        self.root = tk.Tk()
        self.root.withdraw()
        self.editor = gui.Editor(self.root)
        self.dialogs = ExitStack()
        self.dialogs.enter_context(patch.object(gui.messagebox, 'showerror', side_effect=lambda *a, **kw: self.errors.append(a)))
        self.dialogs.enter_context(patch.object(gui.messagebox, 'askyesno', return_value=True))
        with patch.object(gui.filedialog, 'askopenfilename', return_value=str(self.copy)):
            self.editor.open()
        self.assertFalse(self.errors)
        self.assertEqual(self.editor.backup.read_bytes(), self.document.encrypted)

    def tearDown(self):
        try:
            self.assertEqual(self.copy.read_bytes(), self.document.encrypted)
        finally:
            self.dialogs.close()
            self.root.destroy()
            assert self.folder.resolve().is_relative_to(GUI_RUNS.resolve())
            shutil.rmtree(self.folder)

    def select(self, key):
        self.editor.weapons.selection_set(key)
        self.editor.select_weapon()

    def test_existing_rare_identity_can_be_replaced_but_has_no_numeric_editor(self):
        app = self.editor
        self.select('WeaponDataArray:36')
        self.assertEqual(app.weapon_bonus_names[6].get(), weapon.ITEMS[14]['name'])
        self.assertEqual(str(app.weapon_bonus_boxes[6]['state']), 'readonly')
        self.assertEqual(str(app.weapon_bonus_value_boxes[6]['state']), 'disabled')
        self.assertEqual(app.weapon_bonus_values[6].get(), '—')
        app.weapon_bonus_names[6].set(weapon.ITEMS[18]['name'])
        app.change_weapon_bonus(6)
        app.apply_weapon_rolls()
        self.assertFalse(self.errors)
        self.assertEqual(set(app.changes), {('weapon_roll', 36, 'Skills')})
        state = weapon.state(app.document, 36, list(app.changes.values()))
        self.assertEqual(state['skills'][8], {'id': 18, 'value': 0})
        self.assertEqual(app.weapon_bonus_names[6].get(), 'None')
        self.assertEqual(app.weapon_bonus_names[8].get(), weapon.ITEMS[18]['name'])
        self.assertEqual(str(app.weapon_bonus_value_boxes[8]['state']), 'disabled')
        reread = parse_bytes(serialize(app.document, list(app.changes.values()))[0])
        self.assertEqual(weapon.state(reread, 36)['skills'][8], {'id': 18, 'value': 0})

    def test_pending_unique_element_is_reviewed_and_undo_keeps_the_unlock(self):
        app = self.editor
        template = UNIQUE_WEAPONS[116]
        app.stage_many([Change('unique_weapon', 116, 'Owned', True)])
        self.select('unique:116')
        self.assertEqual(app.current_weapon_data_id, template['data_id'])
        self.assertEqual(str(app.weapon_element_box['state']), 'readonly')
        app.weapon_element.set('Wind')
        app.apply_weapon_element()
        self.assertFalse(self.errors)
        key = ('weapon_element', template['data_id'], 'Elements')
        self.assertEqual(app.changes[key].value, 32)
        label, fieldname, before, after = app.review_change(app.changes[key])
        self.assertIn(template['weapon_name'], label)
        self.assertEqual((fieldname, before, after), ('Element', 'None', 'Wind'))
        app.review()
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        texts = [widget.get('1.0', 'end') for widget in descendants(self.root)
                 if isinstance(widget, self.tk.Text)]
        self.assertTrue(any('Wind' in text and template['weapon_name'] in text for text in texts))
        reread = parse_bytes(serialize(app.document, list(app.changes.values()))[0])
        state = weapon.state(reread, template['data_id'])
        self.assertEqual(state['attr'], (template['attribute_bitmask'] & ~weapon.ELEMENT_MASK) | 32)
        app.undo()
        self.assertEqual(set(app.changes), {('unique_weapon', 116, 'Owned')})
        stock_label = next(label for label, mask in weapon.ELEMENTS.items()
                           if mask == template['attribute_bitmask'] & weapon.ELEMENT_MASK)
        self.assertEqual(app.weapon_element.get(), stock_label)
        self.assertTrue(weapon.state(app.document, template['data_id'], list(app.changes.values()))['owned'])

    def test_empty_search_and_view_only_copies_keep_controls_disabled_after_loading(self):
        app = self.editor
        app.weapon_filter.set('no possible weapon name matches this text')
        self.assertIsNone(app.current_weapon_data_id)
        app.set_loaded(True)
        for button in (app.weapon_roll_button, app.weapon_max_button, app.weapon_element_button):
            self.assertEqual(str(button['state']), 'disabled')
        self.assertEqual(str(app.weapon_element_box['state']), 'disabled')
        app.weapon_filter.set('')
        slot = fields(fields(self.document.records('WeaponDataArray')[36])['Skill']['value']['records'][6])
        path = self.folder / 'reserved-bonus-copy.sav'
        raw = edited_fixture_bytes(self.document, [(slot['EquipItemID'], enum_bytes('EEquipItemID::EquipItemID_099'))])
        path.write_bytes(raw)
        with patch.object(self.gui.filedialog, 'askopenfilename', return_value=str(path)):
            app.open()
        self.assertFalse(self.errors)
        self.select('WeaponDataArray:36')
        self.assertFalse(weapon.state(app.document, 36)['editable'])
        self.assertFalse(weapon.state(app.document, 36)['element_editable'])
        app.set_loaded(True)
        for button in (app.weapon_roll_button, app.weapon_max_button, app.weapon_element_button):
            self.assertEqual(str(button['state']), 'disabled')
        self.assertEqual(str(app.weapon_element_box['state']), 'disabled')
        self.assertEqual(str(app.weapon_bonus_boxes[6]['state']), 'disabled')
        self.assertEqual(str(app.weapon_bonus_value_boxes[6]['state']), 'disabled')
        self.assertEqual(path.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
