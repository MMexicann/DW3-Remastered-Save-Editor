"""Direct XIII snapshot/batch boundaries using procedural inputs only."""
from dataclasses import replace
from types import MappingProxyType
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.rotk13 import parser
from tests.test_rotk13_format import procedural_raw


class XIIIInputRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = parser.decode(procedural_raw())

    def test_exact_format_identity_prevents_permissive_equality_forgery(self):
        class EqualFormat:
            id = parser.GAME_ID

            def __eq__(self, other):
                return True

        for layout in (EqualFormat(), replace(parser.FORMAT)):
            document = replace(self.document, format=layout)
            for action in (lambda: parser.fields_for(document),
                           lambda: parser.stage(document, {}, 'city_0_money', 1),
                           lambda: parser.maximums(document, {}),
                           lambda: parser.serialize(document, {})):
                with self.subTest(layout=type(layout).__name__), self.assertRaises(SaveError):
                    action()

    def test_invalid_prior_same_field_rejected_before_undo_can_remove_it(self):
        document = self.document
        key = 'city_0_money'
        opened = parser.field_map(document)[key].value(document.payload)
        for pending in ({key: True}, {key: -1}, {key: 0x100000000},
                        {key: '1'}, {'unmapped': 1}, {3: 1}):
            before = dict(pending)
            for value in (opened, 1):
                with self.subTest(pending=pending, value=value), self.assertRaises(SaveError):
                    parser.stage(document, pending, key, value)
            self.assertEqual(pending, before)
        self.assertEqual(document.raw, procedural_raw())

    def test_malformed_pending_containers_raise_save_error_across_direct_api(self):
        document = self.document
        for pending in (None, [], [('city_0_money', 1)], 'city_0_money',
                        {'city_0_money': False}, {None: 1}):
            for action in (lambda: parser.stage(document, pending, 'city_0_money', 1),
                           lambda: parser.changed_payload(document, pending),
                           lambda: parser.serialize(document, pending),
                           lambda: parser.review(document, pending),
                           lambda: parser.limit_values(document, pending, []),
                           lambda: parser.maximums(document, pending, 'unmatched')):
                with self.subTest(pending=pending), self.assertRaises(SaveError):
                    action()

    def test_malformed_target_ids_and_iterables_preserve_existing_pending(self):
        document = self.document
        pending = {'city_0_money': 1}
        for key in (None, [], {}, 1, True):
            with self.subTest(key=key), self.assertRaises(SaveError):
                parser.stage(document, pending, key, 1)
            with self.subTest(key=key), self.assertRaises(SaveError):
                parser.limit_values(document, pending, [key])
            with self.subTest(key=key), self.assertRaises(SaveError):
                parser.field_hint(document, key)
        for keys in (None, 1, True):
            with self.subTest(keys=keys), self.assertRaises(SaveError):
                parser.limit_values(document, pending, keys)
        self.assertEqual(pending, {'city_0_money': 1})

    def test_readonly_mapping_valid_manual_edits_and_original_value_undo(self):
        document = self.document
        key = 'city_0_money'
        opened = parser.field_map(document)[key].value(document.payload)
        pending = MappingProxyType({key: 1})
        self.assertEqual(parser.stage(document, pending, key, opened), {})
        self.assertEqual(dict(pending), {key: 1})
        self.assertEqual(parser.maximums(document, pending), dict(pending))
        self.assertEqual(parser.limit_values(document, pending, iter([key])), {})
        preserved = {key: opened}
        self.assertEqual(parser.serialize(document, preserved), document.raw)
        edited = parser.decode(parser.serialize(document, pending))
        self.assertEqual(parser.field_map(edited)[key].value(edited.payload), 1)
        self.assertEqual(document.raw, procedural_raw())
