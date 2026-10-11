"""Independent 3DS native ownership, opaque-state and pending-edit review."""
from dataclasses import replace
import os
from pathlib import Path
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.hyrule_legends import parser as p
from tests.test_hyrule_legends import procedural_legends


class IndependentLegendsAudit(unittest.TestCase):
    def setUp(self):
        self.raw = procedural_legends()
        self.document = p.decode(self.raw)

    def test_false_fairy_ownership_and_nonascii_stale_padding_inspection_only(self):
        at = p.FAIRY_BASE + p.FAIRY_NAME_DIFF
        for flag, name in ((0, b'Valid\0xx'), (2, b'Valid\0xx'), (255, b'Valid\0xx'),
                           (1, b'Valid\0\xff\xfe'), (1, b'A\x7f'+bytes(6)),
                           (1, bytes(8)), (1, b'A\x01'+bytes(6))):
            data = bytearray(self.raw)
            data[p.FAIRY_BASE] = flag
            data[at:at + 8] = name
            document = p.decode(data)
            self.assertNotIn('fairy_1_name', p.field_map(document))
            out = p.serialize(document, p.maximums(document, {}, 'My Fairy'))
            self.assertEqual(out, bytes(data))
            with self.assertRaises(SaveError):
                p.stage(document, {}, 'fairy_1_name', 'Navi')

    def test_renaming_last_fairy_does_not_touch_food_or_unknown_record_bytes(self):
        data = bytearray(self.raw)
        offset = p.FAIRY_BASE + (p.FAIRY_COUNT - 1) * p.FAIRY_STRIDE
        data[offset] = 1
        at = offset + p.FAIRY_NAME_DIFF
        data[at:at + 8] = b'ABCDEFGH'
        document = p.decode(data)
        self.assertEqual(offset + p.FAIRY_STRIDE, 0x233A)
        changed = p.serialize(document, {'fairy_14_name': 'Navi'})
        self.assertEqual(changed[:at], bytes(data[:at]))
        self.assertEqual(changed[at:at + 8], b'Navi'+bytes(4))
        self.assertEqual(changed[at + 8:], bytes(data[at + 8:]))
        self.assertEqual(p.serialize(document, {'fairy_14_name': 'ABCDEFGH'}), bytes(data))
        self.assertNotIn('fairy_14_name', p.maximums(document, {}, 'My Fairy'))

    def test_opaque_weapon_identity_state_and_seals_survive_other_edits(self):
        data = bytearray(self.raw)
        offset = p.WEAPON_BASE + (p.WEAPON_COUNT - 1) * p.WEAPON_STRIDE
        self.assertEqual(offset + p.WEAPON_STRIDE, len(data))
        data[offset:offset + p.WEAPON_STRIDE] = bytes((index * 9 + 11) % 256 for index in range(p.WEAPON_STRIDE))
        data[offset + 0x10:offset + 0x12] = (0xFFE0).to_bytes(2, 'little')
        document = p.decode(data)
        self.assertFalse(any(field.id.startswith('weapon_1030_') for field in p.fields_for(document)))
        self.assertEqual(p.weapons(document)[-1]['id'], 0xFFE0)
        edited = p.serialize(document, {'rupees': 200, 'fairy_1_name': 'Navi', 'map_card_2efa': 3})
        self.assertEqual(edited[offset:], bytes(data[offset:]))
        # Legendary-state weapons may change star quality, not seal counters.
        data[p.WEAPON_BASE + 0x1E] = 19
        document = p.decode(data)
        self.assertIn('weapon_1_stars', p.field_map(document))
        self.assertNotIn('weapon_1_skill_1_kos', p.field_map(document))

    def test_failed_multi_field_edit_is_atomic_and_never_mutates_pending(self):
        pending = {'rupees': 55, 'fairy_1_name': 'Navi', 'map_card_2efa': 0}
        original = dict(pending)
        with self.assertRaises(SaveError):
            p.serialize(self.document, pending)
        self.assertEqual(pending, original)
        self.assertEqual(self.document.raw, self.raw)
        self.assertEqual(p.serialize(self.document, {}), self.raw)
        for pending in (None, [], True, {'unknown': 1}, {'rupees': True}):
            for operation in (lambda: p.serialize(self.document, pending),
                              lambda: p.stage(self.document, pending, 'rupees', 12345),
                              lambda: p.maximums(self.document, pending)):
                with self.assertRaises(SaveError):
                    operation()

    def test_pending_original_higher_values_preserve_bytes_and_allow_other_edits(self):
        data = bytearray(self.raw)
        data[p.RUPEES_OFFSET:p.RUPEES_OFFSET + 3] = (12_000_000).to_bytes(3, 'little')
        stars = p.WEAPON_BASE + 0x14
        data[stars:stars + 2] = (8).to_bytes(2, 'little')
        document = p.decode(data)
        pending = {'rupees': 12_000_000, 'weapon_1_stars': 8}
        self.assertEqual(p.serialize(document, pending), bytes(data))
        self.assertEqual(p.maximums(document, pending), pending)
        self.assertEqual(p.stage(document, pending, 'rupees', 12_000_000), {'weapon_1_stars': 8})
        self.assertEqual(p.stage(document, pending, 'weapon_1_stars', 8), {'rupees': 12_000_000})
        changed = p.serialize(document, {**pending, 'fairy_1_name': 'Navi'})
        name = p.FAIRY_BASE + p.FAIRY_NAME_DIFF
        expected = bytearray(data)
        expected[name:name + p.FAIRY_NAME_SIZE] = b'Navi' + bytes(4)
        self.assertEqual(changed, bytes(expected))
        self.assertEqual(document.raw, bytes(data))
        for edits in ({'rupees': 12_000_001}, {'weapon_1_stars': 9},
                      {'rupees': True}, {'weapon_1_stars': 8.0}):
            with self.subTest(edits=edits), self.assertRaises(SaveError):
                p.serialize(document, edits)

    def test_exact_native_size_and_canonical_format_cannot_be_spoofed(self):
        class PermissiveFormat:
            def __eq__(self, other):
                return True
        class OversizedBytes(bytes):
            def __len__(self):
                return p.SAVE_SIZE
        for operation in (p.fields_for,
                          lambda doc: p.serialize(doc, {}),
                          lambda doc: p.maximums(doc, {})):
            with self.assertRaises(SaveError):
                operation(replace(self.document, format=PermissiveFormat()))
        with self.assertRaises(SaveError):
            p.decode(OversizedBytes(self.raw + b'extra'))

    @unittest.skipUnless(os.environ.get('HYRULE_LEGENDS_COPY'), 'No private native 3DS export')
    def test_native_combined_ordinary_edits_confined_to_disjoint_fields(self):
        source = Path(os.environ['HYRULE_LEGENDS_COPY'])
        raw = source.read_bytes()
        document = p.decode(raw)
        mapping = p.field_map(document)
        changes = {}
        allowed = set()
        for group in ('Material inventory', 'Adventure map cards', 'My Fairy', 'Ordinary skill seals'):
            field = next(field for field in mapping.values() if field.group == group)
            value = ('Navi' if field.kind == 'text' else max(field.minimum, field.value(raw) - 1))
            changes = p.stage(document, changes, field.id, value)
            allowed.update(range(field.offset, field.offset + field.size))
        edited = p.serialize(document, changes)
        self.assertLessEqual({index for index, (old, new) in enumerate(zip(raw, edited)) if old != new}, allowed)
        for key, value in changes.items():
            self.assertEqual(mapping[key].value(p.decode(edited).payload), value)
        for weapon in p.weapons(document):
            if weapon['id'] == 60:
                start = weapon['offset']
                self.assertEqual(edited[start:start + p.WEAPON_STRIDE], raw[start:start + p.WEAPON_STRIDE])
        self.assertEqual(source.read_bytes(), raw)
