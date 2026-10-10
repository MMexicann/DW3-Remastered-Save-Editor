"""Independent own-pool selection review; procedural and private native copies."""
from functools import lru_cache
import os
from pathlib import Path
import struct
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.stars import stars_codec as codec, stars_parser as backend
from tests.test_stars_format import procedural_raw


@lru_cache(maxsize=1)
def equipment_raw():
    original = procedural_raw()
    payload = bytearray(codec.decode(original)[0])
    campaign = codec.SYSTEM_PAYLOAD_SIZE
    # Independent native constants, rather than the implementation's helpers.
    for record in range(40, 60):
        struct.pack_into('<h', payload, campaign + 0x20682 + record * 0x53, -1)
    for record, identity in ((40, 47), (43, 1250), (59, 1999), (2000, 23)):
        struct.pack_into('<h', payload, campaign + 0x20682 + record * 0x53, identity)
    struct.pack_into('<i', payload, campaign + 0x3F6E + 2 * 0x48D + 0x20E, 40)
    return codec.encode(original, bytes(payload))


class StarsEquipmentIndependentReview(unittest.TestCase):
    key = 'slot_0_hero_2_equipped_card'

    def setUp(self):
        self.document = backend.decode(equipment_raw())

    def test_only_occupied_own_pool_targets_and_no_inventory_progression_effect(self):
        options = backend.field_options(self.document, self.key)
        self.assertEqual(tuple(value for value, _ in options), (40, 43, 59))
        field = backend.field_map(self.document)[self.key]
        for value in (43, 59):
            with self.subTest(value=value):
                changes = backend.stage(self.document, {}, self.key, value)
                updated = backend.decode(backend.serialize(self.document, changes))
                expected = bytearray(self.document.payload)
                struct.pack_into('<I', expected,
                                 codec.SYSTEM_PAYLOAD_SIZE + 0x3F6E + 2 * 0x48D + 0x20E,
                                 value)
                self.assertEqual(updated.payload, bytes(expected))
                self.assertEqual(field.value(updated.payload), value)
                self.assertEqual(updated.raw[:codec.SYSTEM_BLOCK_SIZE],
                                 self.document.raw[:codec.SYSTEM_BLOCK_SIZE])
                self.assertEqual(updated.raw[codec.SYSTEM_BLOCK_SIZE + codec.SLOT_BLOCK_SIZE:],
                                 self.document.raw[codec.SYSTEM_BLOCK_SIZE + codec.SLOT_BLOCK_SIZE:])
        self.assertEqual(backend.maximums(self.document, {}, 'Hero cards'), {})

    def test_empty_foreign_gift_signed_and_malformed_pending_targets_rejected(self):
        for value in (42, 20, 2000, -1, 2200, True, '43', 43.0):
            with self.subTest(value=value):
                with self.assertRaises(SaveError):
                    backend.stage(self.document, {}, self.key, value)
                with self.assertRaises(SaveError):
                    backend.maximums(self.document, {self.key: value})

    def test_unknown_original_reference_or_single_occupied_card_is_read_only(self):
        for selected in (-1, 20, 2000, 2200, 0x7FFFFFFF):
            payload = bytearray(self.document.payload)
            struct.pack_into('<i', payload,
                             codec.SYSTEM_PAYLOAD_SIZE + 0x3F6E + 2 * 0x48D + 0x20E,
                             selected)
            altered = backend.decode(codec.encode(self.document.raw, bytes(payload)))
            self.assertNotIn(self.key, backend.field_map(altered))
            self.assertEqual(backend.serialize(altered, {}), altered.raw)
        payload = bytearray(self.document.payload)
        for record in (43, 59):
            struct.pack_into('<h', payload,
                             codec.SYSTEM_PAYLOAD_SIZE + 0x20682 + record * 0x53, -1)
        altered = backend.decode(codec.encode(self.document.raw, bytes(payload)))
        self.assertNotIn(self.key, backend.field_map(altered))

    @unittest.skipUnless(os.environ.get('STARS_SAVE_COPY'),
                         'Set STARS_SAVE_COPY to a private genuine native copy.')
    def test_every_genuine_selector_has_only_native_owned_choices_and_surgical_edit(self):
        document = backend.decode(Path(os.environ['STARS_SAVE_COPY']).read_bytes())
        fields = [field for field in backend.fields_for(document) if field.group == 'Hero cards']
        self.assertGreater(len(fields), 0)
        for field in fields:
            slot, hero = divmod(field.slot - 1, 100)
            campaign = codec.SYSTEM_PAYLOAD_SIZE + slot * codec.SLOT_PAYLOAD_SIZE
            expected_options = tuple(record for record in range(hero * 20, (hero + 1) * 20)
                                     if 0 <= struct.unpack_from('<h', document.payload,
                                             campaign + 0x20682 + record * 0x53)[0] < 2000)
            actual = tuple(value for value, _ in backend.field_options(document, field.id))
            self.assertEqual(actual, expected_options)
            self.assertIn(field.value(document.payload), actual)
            target = next(value for value in actual if value != field.value(document.payload))
            updated = backend.decode(backend.serialize(document, {field.id: target}))
            expected = bytearray(document.payload)
            struct.pack_into('<I', expected,
                             campaign + 0x3F6E + hero * 0x48D + 0x20E, target)
            self.assertEqual(updated.payload, bytes(expected))
        self.assertEqual(backend.serialize(document, {}), document.raw)
        self.assertFalse(backend.FORMAT.game_load_verified)


if __name__ == '__main__':
    unittest.main()
