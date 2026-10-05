"""Story edits against private copied fixtures; no supplied save is changed."""
from pathlib import Path
import hashlib
import struct
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / 'tests'))
from models import Change, SaveError, fields
import progression_editor as story
from save_parser import parse_bytes, read_save
from save_writer import serialize
from test_bodyguards import edited_fixture_bytes, tag_bytes

ORIGINAL = WORKSPACE / 'work/original-upload/GameStatusData.sav'
REPORTS = WORKSPACE / 'work/received-v034'


class RouteMetadataTests(unittest.TestCase):
    def test_actual_routes_and_rulers(self):
        self.assertEqual({i for i, r in story.ROUTES.items() if r['route_length']}, set(range(39)))
        self.assertEqual({i for i, r in story.ROUTES.items() if r['route_length'] == 10}, {11, 14, 15})
        for row in story.ROUTES.values():
            self.assertEqual(row['route_length'], len(row['scenario_ids']))
        self.assertEqual([(r['id'], r['ruler_id'], r['free_mode_scenario_ids'])
                          for r in story.SIDE_STORIES.values()],
                         [(0, 11, [101, 102]), (1, 16, [103, 104]), (2, 14, [105, 106])])


@unittest.skipUnless(ORIGINAL.exists(), 'The explicitly supplied workspace fixture is required.')
class StoryWriteTests(unittest.TestCase):
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

    def test_state_is_read_only_and_excludes_nonstory_officers_from_all_action(self):
        old = self.document.plaintext
        state = story.progression_state(self.document)
        self.assertEqual([r['officer_id'] for r in state['officers'] if r['can_clear']], list(range(39)))
        self.assertEqual([c.index for c in story.musou_clear_changes(self.document)], list(range(39)))
        self.assertEqual(self.document.plaintext, old)
        for index in (39, 40, 41, -1, True, 50):
            with self.subTest(index=index), self.assertRaises(SaveError):
                story.musou_clear_changes(self.document, index)

    def test_selected_clear_updates_only_completion_progress_and_first_clear_award(self):
        result, audit = self.edited(story.musou_clear_changes(self.document, 1))
        self.assertEqual(result.properties['EngiClearCharaArray']['value']['values'][1], 1)
        before = fields(self.document.records('PCSaveDataArray')[1])
        after = fields(result.records('PCSaveDataArray')[1])
        self.assertEqual(after['Progress']['value'], 7)
        for name in before:
            if name != 'Progress':
                self.assertEqual(before[name]['value'], after[name]['value'], name)
        self.assertEqual(result.properties['BeansNum']['value'], self.document.properties['BeansNum']['value'] + 3)
        for name, prop in self.document.properties.items():
            if name not in {'PCSaveDataArray', 'EngiClearCharaArray', 'BeansNum'}:
                self.assertEqual(tag_bytes(self.document, prop), tag_bytes(result, result.properties[name]), name)
        self.assertFalse(audit['resized'])
        self.assertTrue(audit['unchanged_bytes_preserved'])

    def test_ruler_stories_use_ten_stages(self):
        result, _ = self.edited(story.musou_clear_changes(self.document, 11))
        self.assertEqual(fields(result.records('PCSaveDataArray')[11])['Progress']['value'], 10)

    def test_all_clear_skips_nonstory_records_preserves_stage_and_active_run_data(self):
        result, _ = self.edited(story.musou_clear_changes(self.document))
        self.assertTrue(all(result.properties['EngiClearCharaArray']['value']['values'][:39]))
        for index, route in story.ROUTES.items():
            original = fields(self.document.records('PCSaveDataArray')[index])
            edited = fields(result.records('PCSaveDataArray')[index])
            self.assertEqual(edited['Progress']['value'], max(original['Progress']['value'], route['route_length']))
            if not route['route_length']:
                self.assertEqual(original['Progress']['value'], edited['Progress']['value'])
        for name in ('EngiSaveDataArray', 'ClearScenarioArray', 'CanUseScenarioArray',
                     'RecordSaveData', 'DLCPermissionSaveData'):
            self.assertEqual(tag_bytes(self.document, self.document.properties[name]),
                             tag_bytes(result, result.properties[name]))
        raw, audit = serialize(result, story.musou_clear_changes(result))
        self.assertEqual(raw, result.encrypted)
        self.assertEqual(audit['plaintext_changes'], [])

    def test_first_clear_award_caps_at999_and_does_not_repeat(self):
        prop = self.document.properties['BeansNum']
        near_cap = parse_bytes(edited_fixture_bytes(self.document, [(prop, struct.pack('<i', 998))]))
        result, _ = self.edited(story.musou_clear_changes(near_cap, 1), near_cap)
        self.assertEqual(result.properties['BeansNum']['value'], 999)
        repeated, _ = self.edited(story.musou_clear_changes(result, 1), result)
        self.assertEqual(repeated.encrypted, result.encrypted)

    def test_side_unlock_adds_two_known_native_tags_without_marking_story_clear(self):
        self.assertNotIn('CanUseReMusouArray', self.document.properties)
        result, audit = self.edited(story.side_story_changes(0))
        self.assertEqual(result.properties['CanUseReMusouArray']['value']['values'], [1, 0, 0])
        self.assertEqual(result.properties['NewCanUseReMusouArray']['value']['values'], [1, 0, 0])
        self.assertEqual(result.properties['CanUseScenarioArray']['value']['values'][101:103], [1, 1])
        self.assertTrue(result.properties['CanUseCharaArray']['value']['values'][11])
        self.assertEqual(result.properties['ClearScenarioArray']['value'], self.document.properties['ClearScenarioArray']['value'])
        self.assertEqual(result.properties['EngiClearCharaArray']['value'], self.document.properties['EngiClearCharaArray']['value'])
        self.assertNotIn('ClearReMusouFirstConditionArray', result.properties)
        self.assertTrue(audit['resized'])
        self.assertEqual(sum(p['old_length'] == 0 for p in audit['plaintext_changes']), 1)
        self.assertEqual(serialize(result)[0], result.encrypted)

    def test_all_side_unlocks_are_idempotent_and_can_combine_with_other_unlocks(self):
        changes = story.side_story_changes() + [Change('unlock', i, 'CanUseScenarioArray', True) for i in range(108)]
        changes += [Change('unlock', i, 'CanUseCharaArray', True) for i in range(42)]
        result, _ = self.edited(changes)
        self.assertEqual(result.properties['CanUseReMusouArray']['value']['values'], [1, 1, 1])
        self.assertEqual(result.properties['NewCanUseReMusouArray']['value']['values'], [1, 1, 1])
        self.assertEqual(serialize(result, story.side_story_changes())[0], result.encrypted)
        with self.assertRaises(SaveError):
            serialize(self.document, story.side_story_changes(0) + [Change('unlock', 101, 'CanUseScenarioArray', False)])

    def test_completion_refuses_invented_routes_relocks_and_duplicate_actions(self):
        for changes in ([Change('progression', 41, 'MusouCleared', True)],
                        [Change('progression', 0, 'MusouCleared', False)],
                        [Change('progression', 3, 'SideStoryUnlocked', True)],
                        story.side_story_changes(0) * 2):
            with self.subTest(changes=changes), self.assertRaises(SaveError):
                serialize(self.document, changes)

    def test_progress_never_decreases_and_saved_runs_are_not_rewritten(self):
        prop = fields(self.document.records('PCSaveDataArray')[1])['Progress']
        later = parse_bytes(edited_fixture_bytes(self.document, [(prop, struct.pack('<i', 12))]))
        result, _ = self.edited(story.musou_clear_changes(later, 1), later)
        self.assertEqual(fields(result.records('PCSaveDataArray')[1])['Progress']['value'], 12)
        self.assertEqual(result.properties['EngiSaveDataArray']['value'], later.properties['EngiSaveDataArray']['value'])

    def test_short_content_arrays_fail_the_requested_action_cleanly(self):
        prop = self.document.properties['CanUseCharaArray']
        short = parse_bytes(edited_fixture_bytes(self.document, [(prop, struct.pack('<i', 12) + bytes(prop['value']['values'][:12]))]))
        with self.assertRaises(SaveError):
            serialize(short, story.side_story_changes())
        self.assertEqual(serialize(short)[0], short.encrypted)
        prop = self.document.properties['EngiClearCharaArray']
        short = parse_bytes(edited_fixture_bytes(self.document, [(prop, struct.pack('<i', 1) + bytes(prop['value']['values'][:1]))]))
        self.assertEqual([c.index for c in story.musou_clear_changes(short)], [0])
        with self.assertRaises(SaveError):
            serialize(short, [Change('progression', i, 'MusouCleared', True) for i in (0, 1)])

    def test_side_array_extensions_are_preserved_and_native_empty_arrays_can_initialize(self):
        base, _ = self.edited(story.side_story_changes(0))
        replacements = []
        for name in story.SIDE_ARRAYS:
            prop = base.properties[name]
            replacements.append((prop, struct.pack('<i', 5) + bytes([1, 0, 0, 1, 0])))
        extended = parse_bytes(edited_fixture_bytes(base, replacements))
        result, _ = self.edited(story.side_story_changes(1), extended)
        for name in story.SIDE_ARRAYS:
            self.assertEqual(result.properties[name]['value']['values'], [1, 1, 0, 1, 0])
        empty = parse_bytes(edited_fixture_bytes(base, [(base.properties[name], struct.pack('<i', 0)) for name in story.SIDE_ARRAYS]))
        result, _ = self.edited(story.side_story_changes(2), empty)
        for name in story.SIDE_ARRAYS:
            self.assertEqual(result.properties[name]['value']['values'], [0, 0, 1])

    def test_reported_fixtures_can_apply_story_actions_without_source_changes(self):
        for path in sorted(REPORTS.glob('*.sav')):
            with self.subTest(path=path.name):
                before_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                document = read_save(path)
                result, _ = self.edited(story.side_story_changes() + story.musou_clear_changes(document), document)
                self.assertEqual(serialize(result)[0], result.encrypted)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before_hash)


if __name__ == '__main__':
    unittest.main()
