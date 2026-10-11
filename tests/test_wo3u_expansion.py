"""Native rank categories and conservative reinforcement edits."""
import os
from pathlib import Path
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.wo3u import wo3u_parser as parser
from tests.test_wo3u_format import procedural_raw


class ExpandedWeaponTests(unittest.TestCase):
    def test_all_ranked_native_ids_and_binary_categories(self):
        raw = bytearray(procedural_raw())
        for identity in range(58):
            raw[parser.WEAPON_BASE + 4] = identity
            raw[parser.WEAPON_BASE + 12] = 1
            document = parser.decode(raw)
            field = parser.field_map(document).get('weapon_0_rank_0')
            with self.subTest(identity=identity):
                if identity in parser.BINARY_ATTRIBUTE_IDS and identity != 31:
                    self.assertIsNone(field)
                else:
                    self.assertIsNotNone(field)
                    self.assertEqual(field.maximum, 1 if identity == 31 else 10)
                    value = field.maximum
                    edited = parser.serialize(document, parser.stage(document, {}, field.id, value))
                    expected = bytearray(raw)
                    expected[field.offset] = value
                    self.assertEqual(edited, expected)

    def test_unknown_zero_and_dormant_attributes_remain_preserved(self):
        raw = bytearray(procedural_raw())
        for identity, rank, slots in ((58, 1, 2), (127, 10, 2), (255, 1, 2),
                                     (16, 0, 2), (17, 1, 0)):
            raw[parser.WEAPON_BASE + 2] = slots
            raw[parser.WEAPON_BASE + 4] = identity
            raw[parser.WEAPON_BASE + 12] = rank
            document = parser.decode(raw)
            with self.subTest(identity=identity, rank=rank, slots=slots):
                self.assertNotIn('weapon_0_rank_0', parser.field_map(document))
                result = parser.serialize(document, parser.maximums(document, {}))
                self.assertEqual(result[parser.WEAPON_BASE + 4:parser.WEAPON_BASE + 20],
                                 raw[parser.WEAPON_BASE + 4:parser.WEAPON_BASE + 20])

    def test_existing_reinforcement_can_only_decrease_and_unstage(self):
        raw = bytearray(procedural_raw())
        raw[parser.WEAPON_BASE + 3] = 81
        document = parser.decode(raw)
        field = parser.field_map(document)['weapon_0_reinforcement']
        self.assertFalse(field.maxable)
        changes = parser.stage(document, {}, field.id, 20)
        expected = bytearray(raw)
        expected[field.offset] = 20
        self.assertEqual(parser.serialize(document, changes), expected)
        self.assertEqual(parser.stage(document, changes, field.id, 81), {})
        for value in (True, -1, 82, 99, 100):
            with self.subTest(value=value), self.assertRaises(SaveError):
                parser.stage(document, {}, field.id, value)
        self.assertNotIn(field.id, parser.maximums(document, {}, 'Weapons'))

    def test_empty_unusual_or_malformed_weapons_have_no_reinforcement_writer(self):
        raw = bytearray(procedural_raw())
        for identity, value, slots in ((65535, 81, 2), (1400, 81, 2),
                                      (2, 0, 2), (2, 100, 2), (2, 81, 9)):
            raw[parser.WEAPON_BASE:parser.WEAPON_BASE + 2] = identity.to_bytes(2, 'little')
            raw[parser.WEAPON_BASE + 2:parser.WEAPON_BASE + 4] = bytes((slots, value))
            document = parser.decode(raw)
            with self.subTest(identity=identity, value=value, slots=slots):
                self.assertNotIn('weapon_0_reinforcement', parser.field_map(document))
                self.assertEqual(parser.serialize(document, {})[parser.WEAPON_BASE + 3], value)

    def test_native_structure_is_not_reported_as_a_checksum(self):
        self.assertEqual(parser.INTEGRITY_KIND, 'none')
        raw = bytearray(procedural_raw())
        # A structural profile cannot detect arbitrary unrelated byte damage.
        raw[-1] ^= 1
        self.assertEqual(parser.serialize(parser.decode(raw), {}), raw)


@unittest.skipUnless(os.environ.get('WO3U_SAVE_COPY'), 'Private native WO3 copy unavailable')
class ExpandedNativeTests(unittest.TestCase):
    def test_all_new_fields_are_surgical_on_native_copy(self):
        document = parser.read_save(os.environ['WO3U_SAVE_COPY'])
        self.assertEqual(parser.serialize(document, {}), document.raw)
        fields = [field for field in parser.fields_for(document)
                  if field.id.endswith('_reinforcement')
                  or ('_rank_' in field.id and 'Attribute ID' in field.label)]
        for field in fields:
            original = field.value(document.payload)
            value = max(field.minimum, min(original - 1, field.maximum))
            changed = parser.stage(document, {}, field.id, value)
            result = parser.serialize(document, changed)
            expected = bytearray(document.raw)
            expected[field.offset:field.offset + field.size] = field.encoded(value)
            with self.subTest(field=field.id):
                self.assertEqual(result, expected)
                self.assertEqual(field.value(parser.decode(result).payload), value)
        self.assertEqual(Path(document.source).read_bytes(), document.raw)
