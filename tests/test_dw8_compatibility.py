"""Procedural regressions for the published native PC aptitude and ally map.

An optional private fixture strengthens file validation; no test here claims a
Windows game-load check or packages a save.
"""
import os
from pathlib import Path
import unittest

import verified_editor as editor
from models import SaveError
from musou_presentations import DW8Presentation
from tests.test_verified_editors import synthetic_raw


class DW8CompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = editor.decode(synthetic_raw('dw8xl'), 'dw8xl')

    def test_four_valid_values_roundtrip_without_other_gameplay_changes(self):
        document = self.document
        for value in (25, 50, 75, 100):
            changes = editor.stage(document, {}, 'officer_0_compatibility_0', value)
            reopened = editor.decode(editor.serialize(document, changes), 'dw8xl')
            expected = bytearray(document.payload)
            expected[0x7fdb] = value
            self.assertEqual(reopened.payload, bytes(expected))
            self.assertEqual(reopened.seed, document.seed)

    def test_arbitrary_percentages_and_non_integer_values_rejected(self):
        for value in (0, 1, 24, 26, 49, 51, 99, 101, 255, True, 50.0, '50'):
            with self.subTest(value=value), self.assertRaises(SaveError):
                editor.stage(self.document, {}, 'officer_0_compatibility_0', value)

    def test_group_max_preserves_unknown_and_higher_aptitude_bytes(self):
        payload = bytearray(self.document.payload)
        payload[0x7fdb] = 13
        payload[0x7fdc] = 201
        # Native payload creation is deliberately confined to this procedural test.
        inner = editor.byte_cipher(bytes(payload), self.document.format.inner_seed)
        raw = (editor.struct.pack('<HH', editor.word_sum(inner), self.document.seed)
               + editor.word_cipher(inner, self.document.seed)
               + bytes([(sum(payload) & 255) ^ (editor.mix_word(self.document.seed) & 255)]))
        unusual = editor.decode(raw, 'dw8xl')
        self.assertEqual(editor.serialize(unusual, {}), raw)
        changes = editor.maximums(unusual, {}, 'Weapon compatibility')
        self.assertEqual(len(changes), 82 * 4 - 2)
        self.assertNotIn('officer_0_compatibility_0', changes)
        self.assertNotIn('officer_0_compatibility_1', changes)
        reopened = editor.decode(editor.serialize(unusual, changes), 'dw8xl')
        allowed = {0x7fdb + slot * 0x48 + index for slot in range(82) for index in range(4)}
        differences = {index for index, (before, after) in enumerate(zip(unusual.payload, reopened.payload))
                       if before != after}
        self.assertLessEqual(differences, allowed)
        self.assertEqual(reopened.payload[0x7fdb:0x7fdd], bytes([13, 201]))
        self.assertEqual(editor.stage(unusual, {'officer_0_compatibility_0':100},
                                      'officer_0_compatibility_0', 13), {})

    def test_ally_progression_is_read_only_and_inspection_keeps_physical_slots(self):
        rows = editor.bodyguards(self.document)
        self.assertEqual(len(rows), 838)
        self.assertEqual((rows[0]['slot'], rows[-1]['slot']), (1, 838))
        self.assertEqual(rows[0]['skill_level'], self.document.payload[0x9be9] + 1)
        self.assertEqual(rows[0]['male_bond'], self.document.payload[0x9bf1])
        self.assertEqual(rows[0]['female_bond'], self.document.payload[0x9bf2])
        with self.assertRaises(SaveError):
            editor.stage(self.document, {}, 'bodyguard_0_male_bond', 99)
        tables = DW8Presentation(editor, 'dw8xl').inspection_tables(self.document)
        by_title = {table.title:table for table in tables}
        self.assertEqual(len(by_title['Weapon compatibility'].rows), 82)
        self.assertEqual(len(by_title['Ally progression'].rows), 838)
        self.assertIn('ownership', by_title['Ally progression'].note)

    @unittest.skipUnless(os.environ.get('DW8XL_SAVE_COPY'), 'Private genuine DW8 PC fixture not configured.')
    def test_genuine_copy_noop_and_compatibility_only_edit(self):
        document = editor.read_save(Path(os.environ['DW8XL_SAVE_COPY']), 'dw8xl')
        self.assertEqual(editor.serialize(document, {}), document.raw)
        changes = editor.maximums(document, {}, 'Weapon compatibility')
        reopened = editor.decode(editor.serialize(document, changes), 'dw8xl')
        allowed = {field.offset for field in editor.fields_for(document)
                   if field.group == 'Weapon compatibility'}
        differences = {index for index, (before, after) in enumerate(zip(document.payload, reopened.payload))
                       if before != after}
        self.assertLessEqual(differences, allowed)
        self.assertEqual(editor.progressions(reopened), editor.progressions(document))
        self.assertEqual(editor.weapons(reopened), editor.weapons(document))
        self.assertEqual(editor.bodyguards(reopened), editor.bodyguards(document))


if __name__ == '__main__':
    unittest.main()
