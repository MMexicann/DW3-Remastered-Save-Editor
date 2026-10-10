"""Customization tests use immutable private workspace copies when available."""
from copy import deepcopy
from pathlib import Path
import hashlib
import struct
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / 'tests'))
import koei_editor.games.dw3.bodyguard_customization as customization
import koei_editor.games.dw3.progression_editor as progression
from koei_editor.games.dw3.models import Change, SaveError
from koei_editor.games.dw3.save_parser import parse_bytes, read_save
from koei_editor.games.dw3.save_writer import serialize
from test_bodyguards import edited_fixture_bytes, tag_bytes

ORIGINAL = WORKSPACE / 'work/original-upload/GameStatusData.sav'
REPORTS = WORKSPACE / 'work/received-v034'
MODEL_ARRAYS = ('CanUseSecretGuardModelArray', 'NewCanUseSecretGuardModelArray')
COLOR_ARRAYS = ('CanUseSecretGuardColorArray', 'NewCanUseSecretGuardColorArray')
ARRAYS = MODEL_ARRAYS + COLOR_ARRAYS


class CustomizationMetadataTests(unittest.TestCase):
    def test_only_known_content_ids_are_authored(self):
        changes = customization.customization_unlock_changes()
        self.assertEqual([(c.field, c.index) for c in changes],
                         [('AppearanceUnlocked', 2), ('AppearanceUnlocked', 3),
                          ('OutfitUnlocked', 5), ('OutfitUnlocked', 6),
                          ('OutfitUnlocked', 7), ('OutfitUnlocked', 8)])
        self.assertEqual([x['name'] for x in customization.OUTFITS],
                         ['Normal', 'Blue', 'Red', 'Green', 'Purple', 'Yellow', 'White', 'Black', 'Pink'])

    def test_single_choice_and_family_helpers(self):
        self.assertEqual(customization.customization_unlock_changes('koei_editor.shared.appearance', 3),
                         [Change('guard_customization', 3, 'AppearanceUnlocked', True)])
        self.assertEqual(len(customization.customization_unlock_changes('outfit')), 4)
        for kind, ident in [('koei_editor.shared.appearance', 1), ('koei_editor.shared.appearance', 4), ('outfit', 4),
                            ('outfit', 9), ('koei_editor.shared.appearance', True), ('outfit', 5.0),
                            (None, 2), ('unknown', None), ([], None), (False, None)]:
            with self.subTest(kind=kind, ident=ident), self.assertRaises(SaveError):
                customization.customization_unlock_changes(kind, ident)


@unittest.skipUnless(ORIGINAL.exists(), 'The explicitly supplied workspace fixture is required.')
class CustomizationWriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read_save(ORIGINAL)
        cls.original_hash = hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == cls.original_hash

    def edited(self, changes, document=None):
        raw, audit = serialize(document or self.document, changes)
        return parse_bytes(raw), audit

    def zeroed_arrays(self):
        base, _ = self.edited(customization.customization_unlock_changes())
        replacements = [(base.properties[name], struct.pack('<i', 2 if name in MODEL_ARRAYS else 4)
                         + bytes(2 if name in MODEL_ARRAYS else 4)) for name in ARRAYS]
        return parse_bytes(edited_fixture_bytes(base, replacements))

    def test_reading_and_unchanged_save_preserve_every_byte(self):
        before = self.document.plaintext
        state = customization.customization_state(self.document)
        self.assertEqual(len(state['appearances']), 4)
        self.assertEqual(len(state['outfits']), 9)
        self.assertTrue(state['editable'])
        self.assertTrue(all(row['unlocked'] for row in state['appearances'][:2]))
        self.assertTrue(all(row['unlocked'] for row in state['outfits'][:5]))
        self.assertEqual(self.document.plaintext, before)
        self.assertEqual(serialize(self.document)[0], self.document.encrypted)

    def test_missing_arrays_are_native_lazy_defaults(self):
        self.assertTrue(all(name not in self.document.properties for name in ARRAYS))
        state = customization.customization_state(self.document)
        self.assertFalse(any(row['unlocked'] for row in state['appearances'][2:]))
        self.assertFalse(any(row['unlocked'] for row in state['outfits'][5:]))
        result, audit = self.edited(customization.customization_unlock_changes())
        for name in ARRAYS:
            self.assertEqual(result.properties[name]['value']['values'], [1] * (2 if name in MODEL_ARRAYS else 4))
        self.assertTrue(audit['resized'])
        self.assertEqual(sum(p['old_length'] == 0 for p in audit['plaintext_changes']), 1)
        self.assertEqual(serialize(result)[0], result.encrypted)

    def test_selected_unlock_changes_only_native_availability_and_notification(self):
        document = self.zeroed_arrays()
        result, audit = self.edited(customization.customization_unlock_changes('outfit', 7), document)
        self.assertEqual(result.properties[COLOR_ARRAYS[0]]['value']['values'], [0, 0, 1, 0])
        self.assertEqual(result.properties[COLOR_ARRAYS[1]]['value']['values'], [0, 0, 1, 0])
        for name, prop in document.properties.items():
            if name not in COLOR_ARRAYS:
                self.assertEqual(tag_bytes(document, prop), tag_bytes(result, result.properties[name]), name)
        self.assertFalse(audit['resized'])
        self.assertEqual(len(audit['plaintext_changes']), 2)
        self.assertTrue(audit['unchanged_bytes_preserved'])

    def test_unlocks_do_not_touch_story_merit_equipped_appearance_or_entitlements(self):
        result, _ = self.edited(customization.customization_unlock_changes())
        for name, prop in self.document.properties.items():
            if name not in ARRAYS:
                self.assertEqual(tag_bytes(self.document, prop), tag_bytes(result, result.properties[name]), name)

    def test_notification_is_only_set_for_a_fresh_unlock(self):
        document = self.zeroed_arrays()
        prop = document.properties[MODEL_ARRAYS[0]]
        owned = parse_bytes(edited_fixture_bytes(document, [(prop, struct.pack('<i', 2) + bytes([1, 0]))]))
        result, _ = self.edited(customization.customization_unlock_changes('koei_editor.shared.appearance'), owned)
        self.assertEqual(result.properties[MODEL_ARRAYS[0]]['value']['values'], [1, 1])
        self.assertEqual(result.properties[MODEL_ARRAYS[1]]['value']['values'], [0, 1])

    def test_unlock_all_is_idempotent(self):
        result, _ = self.edited(customization.customization_unlock_changes())
        raw, audit = serialize(result, customization.customization_unlock_changes())
        self.assertEqual(raw, result.encrypted)
        self.assertEqual(audit['plaintext_changes'], [])

    def test_native_short_empty_arrays_extend_with_zero_defaults(self):
        document = self.zeroed_arrays()
        replacements = [(document.properties[name], struct.pack('<i', 0)) for name in ARRAYS]
        empty = parse_bytes(edited_fixture_bytes(document, replacements))
        result, _ = self.edited(customization.customization_unlock_changes('koei_editor.shared.appearance', 3), empty)
        for name in MODEL_ARRAYS:
            self.assertEqual(result.properties[name]['value']['values'], [0, 1])
        for name in COLOR_ARRAYS:
            self.assertEqual(result.properties[name]['value']['values'], [])
        replacements = [(document.properties[name], struct.pack('<i', 1) + bytes([1])) for name in COLOR_ARRAYS]
        short = parse_bytes(edited_fixture_bytes(document, replacements))
        result, _ = self.edited(customization.customization_unlock_changes('outfit', 8), short)
        for name in COLOR_ARRAYS:
            self.assertEqual(result.properties[name]['value']['values'], [1, 0, 0, 1])

    def test_extra_future_entries_are_preserved(self):
        document = self.zeroed_arrays()
        replacements = [(document.properties[name], struct.pack('<i', 6) + bytes([0, 0, 0, 0, 1, 0]))
                        for name in ARRAYS]
        extended = parse_bytes(edited_fixture_bytes(document, replacements))
        result, _ = self.edited(customization.customization_unlock_changes(), extended)
        for name in ARRAYS:
            expected = [1, 1, 0, 0, 1, 0] if name in MODEL_ARRAYS else [1, 1, 1, 1, 1, 0]
            self.assertEqual(result.properties[name]['value']['values'], expected)

    def test_pending_state_matches_written_state_without_mutating_the_document(self):
        document = self.zeroed_arrays()
        changes = customization.customization_unlock_changes('koei_editor.shared.appearance', 2)
        before = deepcopy(document.parsed)
        preview = customization.customization_state(document, changes)
        result, _ = self.edited(changes, document)
        self.assertEqual(preview, customization.customization_state(result))
        self.assertEqual(before, document.parsed)

    def test_missing_tags_can_combine_with_other_lazy_story_tag_insertions(self):
        changes = customization.customization_unlock_changes() + progression.side_story_changes()
        result, _ = self.edited(changes)
        for name in ARRAYS:
            self.assertTrue(all(result.properties[name]['value']['values']))
        self.assertEqual(result.properties['CanUseReMusouArray']['value']['values'], [1, 1, 1])
        self.assertEqual(serialize(result)[0], result.encrypted)

    def test_unknown_ids_relocks_wrong_types_and_duplicates_are_rejected(self):
        requests = [[Change('guard_customization', 4, 'AppearanceUnlocked', True)],
                    [Change('guard_customization', 9, 'OutfitUnlocked', True)],
                    [Change('guard_customization', 2, 'AppearanceUnlocked', False)],
                    [Change('guard_customization', 2, 'AppearanceUnlocked', 1)],
                    [Change('guard_customization', 2, 'Unknown', True)],
                    customization.customization_unlock_changes('koei_editor.shared.appearance', 2) * 2]
        for changes in requests:
            with self.subTest(changes=changes), self.assertRaises(SaveError):
                serialize(self.document, changes)

    def test_unsupported_flag_layout_is_view_only_and_refuses_its_actions(self):
        document = self.zeroed_arrays()
        for mutate in (lambda p: p.update(type='ArrayProperty(IntProperty)'),
                       lambda p: p.update(flags=1),
                       lambda p: p['value']['values'].__setitem__(0, 2),
                       lambda p: p.update(data_size=100),
                       lambda p: p.update(data_offset=-1)):
            altered = deepcopy(document)
            mutate(altered.properties[MODEL_ARRAYS[0]])
            state = customization.customization_state(altered)
            self.assertFalse(state['editable'])
            self.assertFalse(state['appearances'][2]['editable'])
            self.assertTrue(state['outfits'][5]['editable'])
            with self.assertRaises(SaveError):
                customization.plan_customization_changes(altered,
                    customization.customization_unlock_changes('koei_editor.shared.appearance'),
                    lambda *args: None, lambda *args: None)

    def test_each_reported_variant_unlocks_without_changing_the_input_file(self):
        for path in sorted(REPORTS.glob('*.sav')):
            with self.subTest(path=path.name):
                original_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                document = read_save(path)
                result, _ = self.edited(customization.customization_unlock_changes(), document)
                self.assertTrue(all(row['unlocked'] for row in customization.customization_state(result)['appearances']))
                self.assertTrue(all(row['unlocked'] for row in customization.customization_state(result)['outfits']))
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), original_hash)


if __name__ == '__main__':
    unittest.main()
