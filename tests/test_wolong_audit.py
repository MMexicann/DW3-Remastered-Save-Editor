"""Independent lexical, foreign-schema and unusual-record safety review.

Procedural checks only; player-derived checks live in test_wolong_format.
"""
from dataclasses import replace
import json
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.wolong import wolong_parser as parser, wolong_json
from tests.test_wolong_format import procedural_payload, seal


class WolongIndependentAuditTests(unittest.TestCase):
    def _doc_with_body(self, body):
        original = procedural_payload()
        self.assertLess(len(body), parser.SAVE_SIZE - parser.JSON_OFFSET)
        raw = original[:parser.JSON_OFFSET] + body + bytes(parser.SAVE_SIZE - parser.JSON_OFFSET - len(body))
        return parser.decode(seal(raw))

    def test_unknown_escaped_keys_numbers_whitespace_and_owner_tokens_preserved(self):
        body = procedural_payload()[parser.JSON_OFFSET:].rstrip(b'\0')
        body = body[:-1] + (b', "OpaqueOwnerContext": {"account": "procedural-placeholder", '
                           b'"scientific": 1.2300e+03, "negativeZero": -0, '
                           b'"quoted": "\\\"PlayerData\\\": {\\\"sen\\\": 1}", '
                           b'"slash": "\\u002f", "unknown": [true, null]}}')
        doc = self._doc_with_body(body)
        edited = parser.changed_payload(doc, {'sen': 9, 'senki': 10000, 'storage_items_8_num': 1})
        old_body = doc.payload[parser.JSON_OFFSET:].rstrip(b'\0')
        replacements = []
        for key, value in {'sen': 9, 'senki': 10000, 'storage_items_8_num': 1}.items():
            field = parser.field_map(doc)[key]
            replacements.append((field.offset - parser.JSON_OFFSET, field.size, str(value).encode()))
        for start, size, token in sorted(replacements, reverse=True):
            old_body = old_body[:start] + token + old_body[start + size:]
        self.assertEqual(edited[parser.JSON_OFFSET:].rstrip(b'\0'), old_body)
        self.assertIn(b'"scientific": 1.2300e+03', edited)
        self.assertIn(b'"negativeZero": -0', edited)
        self.assertIn(b'"slash": "\\u002f"', edited)
        self.assertFalse(any('account' in str(row).lower() for row in parser.inspection_rows(doc)))

    def test_equipped_special_empty_and_higher_stacks_never_writable(self):
        body = procedural_payload()[parser.JSON_OFFSET:].rstrip(b'\0')
        for old, new in ((b'"equipment_slot": -1', b'"equipment_slot": 0'),
                         (b'"equipment_part": 0', b'"equipment_part": 1'),
                         (b'"weapon_skill_level": 0', b'"weapon_skill_level": 5'),
                         (b'"item_level": 1', b'"item_level": 2'),
                         (b'"flag": 8', b'"flag": 10'),
                         (b'"num": 123', b'"num": 2147483648'),
                         (b'"num": 123', b'"num": 0')):
            doc = self._doc_with_body(body.replace(old, new))
            self.assertNotIn('storage_items_8_num', parser.field_map(doc))
            self.assertEqual(parser.serialize(doc, {}), doc.raw)
            self.assertEqual(parser.maximums(doc, {}), {})
            with self.assertRaises(SaveError): parser.stage(doc, {}, 'storage_items_8_num', 1)

    def test_foreign_numeric_spellings_duplicate_aliases_and_inventory_counts_rejected(self):
        body = procedural_payload()[parser.JSON_OFFSET:].rstrip(b'\0')
        for old, new in ((b'"sen": 5678', b'"sen": 5.678e3'),
                         (b'"sen": 5678', b'"sen": true'),
                         (b'"sen": 5678', b'"sen": 5678, "s\\u0065n": 1'),
                         (b'"possession_items": [', b'"possession_items": [] , "unused": [')):
            with self.subTest(change=new), self.assertRaises(SaveError): self._doc_with_body(body.replace(old, new, 1))
        with self.assertRaises(SaveError): wolong_json.parse(b'{"a":"x","\\u0061":"y"}')

    def test_forged_equal_mutable_payload_cannot_enter_max_or_restore_pipeline(self):
        doc = parser.decode(procedural_payload())
        for forged in (replace(doc, payload=bytearray(doc.payload)), replace(doc, payload=memoryview(doc.payload))):
            with self.assertRaises(SaveError): parser.maximums(forged, {})
            with self.assertRaises(SaveError): parser.changed_payload(forged, {})

    def test_unqualified_optional_companions_preserve_copy_and_do_not_break_inspection(self):
        root = json.loads(procedural_payload()[parser.JSON_OFFSET:].rstrip(b'\0'))
        for companions in (None, 17, True, 'unknown', {'opaque': 1}):
            with self.subTest(optional_type=type(companions).__name__):
                root['PlayerData']['fellow_character_info'] = companions
                doc = self._doc_with_body(json.dumps(root).encode('utf-8'))
                self.assertEqual(parser.serialize(doc, {}), doc.raw)
                rows = parser.inspection_rows(doc)
                self.assertFalse(any(row['group'] == 'Companions' for row in rows))
                self.assertTrue(any(row['group'] == 'Inventory' for row in rows))
                edited = parser.decode(parser.serialize(doc, {'sen': 1}))
                expected = json.loads(json.dumps(root))
                expected['PlayerData']['sen'] = 1
                self.assertEqual(json.loads(edited.payload[parser.JSON_OFFSET:].rstrip(b'\0')), expected)
