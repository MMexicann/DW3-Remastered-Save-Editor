"""Global Huanglong Elixir edits use private copies and parsed scalar bounds."""
from pathlib import Path
import hashlib
import struct
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / 'tests'))
from models import Change, SaveError
import progression_editor as progression
from save_codec import encrypt
from save_parser import parse_bytes, read_save
from save_writer import plan_changes, serialize
from test_bodyguards import edited_fixture_bytes, tag_bytes

ORIGINAL = WORKSPACE / 'work/original-upload/GameStatusData.sav'
REPORTS = WORKSPACE / 'work/received-v034'


def replace_top_tag(document, prop, replacement):
    """Build an unsupported-field fixture in memory; never write source files."""
    size = struct.unpack_from('>I', document.plaintext)[0]
    payload = bytearray(document.plaintext[:4 + size])
    payload[prop['tag_offset']:prop['data_offset'] + prop['data_size']] = replacement
    struct.pack_into('>I', payload, 0, len(payload) - 4)
    payload.extend(bytes((-len(payload)) % 16))
    return parse_bytes(encrypt(bytes(payload)))


class ElixirInputTests(unittest.TestCase):
    def test_counter_range_and_strict_integer_factory(self):
        self.assertEqual(progression.ELIXIR_MAX, 999)
        for value in (0, 3, 999):
            self.assertEqual(progression.elixir_count_change(value),
                             Change('progression', 0, 'HuanglongElixirs', value))
        for value in (-1, 1000, True, False, 3.0, float('nan'), '3', None, [], {}):
            with self.subTest(value=value), self.assertRaises(SaveError):
                progression.elixir_count_change(value)


@unittest.skipUnless(ORIGINAL.exists(), 'The explicitly supplied workspace fixture is required.')
class ElixirWriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read_save(ORIGINAL)
        cls.source_hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest()
                             for path in [ORIGINAL, *sorted(REPORTS.glob('*.sav'))]}
        cls.new_clear_ids = [row['officer_id'] for row in progression.progression_state(cls.document)['officers']
                             if row['can_clear'] and not row['cleared']][:2]
        assert len(cls.new_clear_ids) == 2

    @classmethod
    def tearDownClass(cls):
        for path, digest in cls.source_hashes.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest

    def test_read_only_state_and_exact_noop_serialization(self):
        saved = self.document.properties['BeansNum']['value']
        self.assertEqual(progression.elixir_state(self.document),
                         {'value': saved, 'saved_value': saved, 'editable': True, 'reason': ''})
        for changes in ([], [progression.elixir_count_change(saved)]):
            raw, audit = serialize(self.document, changes)
            self.assertEqual(raw, self.document.encrypted)
            self.assertEqual(audit['plaintext_changes'], [])
            self.assertEqual(audit['changed_aes_blocks'], [])

    def test_zero_and999_change_only_counter_bytes_and_matching_aes_blocks(self):
        prop = self.document.properties['BeansNum']
        offset = prop['data_offset']
        for value in (0, 999):
            with self.subTest(value=value):
                raw, audit = serialize(self.document, [progression.elixir_count_change(value)])
                result = parse_bytes(raw)
                self.assertEqual(result.properties['BeansNum']['value'], value)
                self.assertEqual(progression.elixir_state(result)['value'], value)
                expected = bytearray(self.document.plaintext)
                expected[offset:offset + 4] = struct.pack('<i', value)
                self.assertEqual(result.plaintext, bytes(expected))
                self.assertEqual([(p['offset'], p['old_length'], p['length'])
                                  for p in audit['plaintext_changes']], [(offset, 4, 4)])
                changed_positions = [i for i, pair in enumerate(zip(self.document.plaintext, result.plaintext))
                                     if pair[0] != pair[1]]
                self.assertTrue(all(offset <= i < offset + 4 for i in changed_positions))
                self.assertEqual(audit['changed_aes_blocks'], sorted({i // 16 for i in changed_positions}))
                self.assertFalse(audit['resized'])
                self.assertTrue(audit['unchanged_bytes_preserved'])
                for name, before in self.document.properties.items():
                    if name != 'BeansNum':
                        self.assertEqual(tag_bytes(self.document, before),
                                         tag_bytes(result, result.properties[name]), name)

    def test_bad_requests_are_rejected_by_writer(self):
        bad = [Change('progression', i, 'HuanglongElixirs', 10) for i in (-1, 1, True)]
        bad += [Change('progression', 0, 'HuanglongElixirs', v)
                for v in (-1, 1000, True, 1.0, '10', None)]
        bad += [Change('progression', 0, 'UnknownCounter', 10)]
        for change in bad:
            with self.subTest(change=change), self.assertRaises(SaveError):
                plan_changes(self.document, [change])
        for values in ((1, 1), (1, 2), (1, True)):
            changes = [Change('progression', 0, 'HuanglongElixirs', v) for v in values]
            with self.subTest(values=values), self.assertRaises(SaveError):
                plan_changes(self.document, changes)
            with self.assertRaises(SaveError):
                progression.elixir_state(self.document, changes)

    def test_story_awards_and_explicit_final_override_are_order_independent(self):
        clears = [Change('progression', i, 'MusouCleared', True) for i in self.new_clear_ids]
        saved = self.document.properties['BeansNum']['value']
        self.assertEqual(progression.elixir_state(self.document, clears)['value'], saved + 6)
        raw, audit = serialize(self.document, clears)
        self.assertEqual(parse_bytes(raw).properties['BeansNum']['value'], saved + 6)
        for value in (0, 999):
            explicit = progression.elixir_count_change(value)
            first = [explicit, *clears]
            last = [*reversed(clears), explicit]
            self.assertEqual(progression.elixir_state(self.document, first)['value'], value)
            self.assertEqual(progression.elixir_state(self.document, last)['value'], value)
            first_raw, first_audit = serialize(self.document, first)
            last_raw, _ = serialize(self.document, last)
            self.assertEqual(first_raw, last_raw)
            result = parse_bytes(first_raw)
            self.assertEqual(result.properties['BeansNum']['value'], value)
            self.assertTrue(all(result.properties['EngiClearCharaArray']['value']['values'][i]
                                for i in self.new_clear_ids))
            counter_offset = self.document.properties['BeansNum']['data_offset']
            self.assertEqual(sum(p['offset'] == counter_offset for p in first_audit['plaintext_changes']), 1)

    def test_pending_award_caps_and_does_not_repeat(self):
        prop = self.document.properties['BeansNum']
        near_cap = parse_bytes(edited_fixture_bytes(self.document, [(prop, struct.pack('<i', 998))]))
        clear = progression.musou_clear_changes(near_cap, self.new_clear_ids[0])
        self.assertEqual(progression.elixir_state(near_cap, clear)['value'], 999)
        result = parse_bytes(serialize(near_cap, clear)[0])
        self.assertEqual(progression.elixir_state(result, clear)['value'], 999)
        self.assertEqual(serialize(result, clear)[0], result.encrypted)

    def test_unusual_saved_counts_remain_read_only_and_unchanged(self):
        prop = self.document.properties['BeansNum']
        for value in (-1, 1000):
            with self.subTest(value=value):
                unusual = parse_bytes(edited_fixture_bytes(self.document, [(prop, struct.pack('<i', value))]))
                state = progression.elixir_state(unusual)
                self.assertEqual(state['saved_value'], value)
                self.assertFalse(state['editable'])
                self.assertTrue(state['reason'])
                self.assertEqual(serialize(unusual)[0], unusual.encrypted)
                with self.assertRaises(SaveError):
                    plan_changes(unusual, [progression.elixir_count_change(999)])
                with self.assertRaises(SaveError):
                    plan_changes(unusual, progression.musou_clear_changes(unusual, self.new_clear_ids[0]))

    def test_missing_and_unknown_counter_layouts_do_not_break_save_open(self):
        prop = self.document.properties['BeansNum']
        missing = replace_top_tag(self.document, prop, b'')
        # Native integer tag replaced by an equally bounded FloatProperty tag.
        float_tag = (progression._fstring('BeansNum') + progression._fstring('FloatProperty') +
                     struct.pack('<iiBf', 0, 4, 0, 3.0))
        unknown = replace_top_tag(self.document, prop, float_tag)
        for document in (missing, unknown):
            with self.subTest(layout=document.properties.get('BeansNum')):
                state = progression.elixir_state(document)
                self.assertEqual(state['value'], None)
                self.assertEqual(state['saved_value'], None)
                self.assertFalse(state['editable'])
                self.assertTrue(state['reason'])
                self.assertEqual(serialize(document)[0], document.encrypted)
                with self.assertRaises(SaveError):
                    plan_changes(document, [progression.elixir_count_change(3)])
        # An indexed IntProperty is structurally valid but not this global field.
        indexed_tag = (progression._fstring('BeansNum') + progression._fstring('IntProperty') +
                       struct.pack('<iiBii', 0, 4, 1, 1, 3))
        indexed = replace_top_tag(self.document, prop, indexed_tag)
        self.assertFalse(progression.elixir_state(indexed)['editable'])
        self.assertEqual(serialize(indexed)[0], indexed.encrypted)
        with self.assertRaises(SaveError):
            plan_changes(indexed, [progression.elixir_count_change(3)])

    def test_supplied_report_copies_accept_counter_edits_without_source_writes(self):
        for path in sorted(REPORTS.glob('*.sav')):
            with self.subTest(path=path.name):
                document = read_save(path)
                self.assertTrue(progression.elixir_state(document)['editable'])
                result = parse_bytes(serialize(document, [progression.elixir_count_change(999)])[0])
                self.assertEqual(result.properties['BeansNum']['value'], 999)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), self.source_hashes[path])


if __name__ == '__main__':
    unittest.main()
