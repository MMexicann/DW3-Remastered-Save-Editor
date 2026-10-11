"""Native equipped-weapon choices never grant or guess inventory identities."""
import os
from pathlib import Path
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.dw7xl import dw7xl_parser as backend
from tests.test_dw7xl_format import reference_encode, synthetic_raw


class EquippedChoiceTests(unittest.TestCase):
    def setUp(self):
        payload = bytearray(backend.decode(synthetic_raw()).payload)
        self.start = backend.OFFICER_BASE
        payload[self.start + 18:self.start + 22] = b'\x02\0\x04\0'
        for identity in (2, 4):
            at = backend.WEAPON_BASE + identity * backend.WEAPON_STRIDE + 4
            payload[at:at + 2] = b'\xA5\x80'  # owned plus unusual preserved bits
        self.document = backend.decode(reference_encode(payload))

    def test_named_first_second_choices_and_staged_native_value(self):
        key = 'officer_0_active_weapon'
        self.assertEqual(backend.field_options(self.document, key),
                         ((0, 'First equipped weapon · inventory slot 3'),
                          (1, 'Second equipped weapon · inventory slot 5')))
        staged = backend.stage(self.document, {}, key, 1)
        result = backend.decode(backend.serialize(self.document, staged))
        offset = backend.FIELD_MAP[key].offset
        self.assertEqual(result.payload[offset:offset + 2], b'\x01\0')
        self.assertEqual(result.payload[:offset], self.document.payload[:offset])
        self.assertEqual(result.payload[offset + 2:], self.document.payload[offset + 2:])
        self.assertEqual(backend.field_options(self.document, 'gold'), ())

    def test_unowned_and_empty_choice_hidden_using_same_stage_dependency(self):
        for reference, flags in ((4, 0x80A4), (backend.WEAPON_COUNT, 0x80A5)):
            payload = bytearray(self.document.payload)
            payload[self.start + 20:self.start + 22] = reference.to_bytes(2, 'little')
            if reference < backend.WEAPON_COUNT:
                at = backend.WEAPON_BASE + reference * backend.WEAPON_STRIDE + 4
                payload[at:at + 2] = flags.to_bytes(2, 'little')
            doc = backend.decode(reference_encode(payload))
            self.assertEqual(backend.field_options(doc, 'officer_0_active_weapon'),
                             ((0, 'First equipped weapon · inventory slot 3'),))
            with self.assertRaises(SaveError):
                backend.stage(doc, {}, 'officer_0_active_weapon', 1)

    def test_unknown_and_nonstring_metadata_keys_rejected(self):
        for key in ('weapon_2_name', [], None, True, 0):
            with self.subTest(key=key), self.assertRaises(SaveError):
                backend.field_options(self.document, key)

    @unittest.skipUnless(os.environ.get('DW7XL_SAVE'), 'Private native DW7XL fixture not supplied')
    def test_genuine_officer_choices_only_point_to_existing_owned_equipped_records(self):
        source = Path(os.environ['DW7XL_SAVE'])
        raw = source.read_bytes()
        doc = backend.decode(raw)
        for identity in range(backend.OFFICER_COUNT):
            key = f'officer_{identity}_active_weapon'
            field = backend.FIELD_MAP[key]
            for value, label in backend.field_options(doc, key):
                self.assertIn('inventory slot', label)
                backend._validate_active_weapon(doc, field, value)
        self.assertEqual(source.read_bytes(), raw)
