"""Independent native-envelope and existing-record adversarial checks.

Procedural fixtures test behavior; the optional private file establishes native
parse/reconstruction evidence, never game-load validation.
"""
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.stars import stars_codec as codec, stars_parser as backend
from koei_editor.shared.verified_self_test import run
from tests.test_stars_format import procedural_raw


class StarsAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = procedural_raw()
        cls.document = backend.decode(cls.raw)

    def test_native_key_known_answers_and_strict_indices(self):
        # Independently compiled literal double/uint32 C arithmetic matching
        # native SSE2 evaluation order, coefficient 3.66, ten iterations, and
        # high-byte MSVC LCG output. The former 4.0 candidate cannot match.
        answers = (
            '830284a809ce8f8865cc668dd3cf29bd',
            '5be14b776cd2874c39c8b8dfd589ef2a',
            'a6e91cf59f1abbe34d35706e8192fb33',
            'fa8deb7eab636da8edf8c5eb8df310fc',
            '6670844046ee5039b33cc94838527da1',
            'd648917b3ecc55b69b9436e24a212fca',
            'b149152e749dee1975f30431553e3cbb',
            '2625e9a0664601a062c6cd5317141a46',
            'f3a06c0e5210e4f2c546bb96b6d11542',
            '685e72a485f9b2fe4dbe386a94b2a921',
        )
        self.assertEqual(tuple(codec.key_for_block(i).hex() for i in range(10)), answers)
        for invalid in (-1, 10, True, 0.0, '0', None):
            with self.subTest(index=invalid), self.assertRaises(ValueError):
                codec.key_for_block(invalid)
        for invalid in (-1, 0x100000000, True, 1.0, None):
            with self.subTest(seed=invalid), self.assertRaises(ValueError):
                codec.iv_from_seed(invalid)

    def test_encrypted_trailer_does_not_authenticate_gameplay_payload(self):
        # CBC corruption away from both the header and final fingerprint can
        # remain undetectable. Do not advertise these trailers as checksums.
        raw = bytearray(self.raw)
        raw[0x79B84 + 0x180] ^= 0x20
        decoded = backend.decode(bytes(raw))
        self.assertNotEqual(decoded.payload, self.document.payload)
        self.assertEqual(backend.INTEGRITY_KIND, 'none')
        self.assertEqual(backend.serialize(decoded, {}), bytes(raw))
        self.assertEqual([(b.iv_seed, b.padding) for b in codec.decode(bytes(raw))[1]],
                         [(b.iv_seed, b.padding) for b in codec.decode(self.raw)[1]])

    def test_max_and_stage_reject_invalid_pending_materials_before_any_action(self):
        invalid_changes = ({'slot_0_material_0': 0}, {'slot_0_material_0': 10000},
                           {'slot_0_material_0': True}, {'slot_0_material_1': 1},
                           {'slot_0_gold': -1}, {'lifetime_gold': 9})
        for changes in invalid_changes:
            for operation in (
                    lambda: backend.maximums(self.document, changes, 'Materials'),
                    lambda: backend.limit_values(self.document, changes, ['slot_0_gold']),
                    lambda: backend.stage(self.document, changes, 'slot_0_gold', 100)):
                with self.subTest(changes=changes), self.assertRaises(SaveError):
                    operation()
        changes = backend.stage(self.document, {}, 'slot_0_material_0', 123)
        maximum = backend.maximums(self.document, changes)
        self.assertEqual(maximum['slot_0_material_0'], 123)
        self.assertNotIn('slot_1_gold', maximum)

    def test_last_material_and_campaign_boundaries_do_not_touch_gold_or_neighbors(self):
        payload = bytearray(self.document.payload)
        struct.pack_into('<H', payload, 0x79B66 + 8 * 0x78E41 + 0x2F10 + 44 * 2, 7)
        document = backend.decode(codec.encode(self.raw, bytes(payload)))
        key = 'slot_8_material_44'
        field = backend.field_map(document)[key]
        self.assertEqual(field.offset + field.size, backend.FIELDS[8].offset)
        updated = backend.decode(backend.serialize(document, {key: 9999}))
        self.assertEqual(updated.payload[:field.offset], document.payload[:field.offset])
        self.assertEqual(updated.payload[field.offset + 2:], document.payload[field.offset + 2:])
        self.assertEqual(backend.FIELDS[8].value(updated.payload), 508)
        for hero in (-32768, -2, -1, 100, 32767):
            altered = bytearray(document.payload)
            struct.pack_into('<h', altered, 0x79B66 + 8 * 0x78E41 + 0xA3C, hero)
            unqualified = backend.decode(codec.encode(document.raw, bytes(altered)))
            mapping = backend.field_map(unqualified)
            self.assertNotIn(key, mapping)
            self.assertNotIn('slot_8_gold', mapping)
            with self.subTest(hero=hero), self.assertRaises(SaveError):
                backend.stage(unqualified, {}, key, 100)

    def test_unknown_integrity_profile_is_rejected_before_creating_any_copies(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            source, output = folder / 'copy.bin', folder / 'report'
            source.write_bytes(self.raw)
            with patch.object(backend, 'INTEGRITY_KIND', 'encrypted-fingerprint'):
                with self.assertRaises(SaveError):
                    run('stars', source, output)
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), self.raw)
            self.assertEqual(tuple(folder.iterdir()), (source,))

    @unittest.skipUnless(os.environ.get('STARS_SAVE_COPY'),
                         'Set STARS_SAVE_COPY to a private genuine native copy.')
    def test_private_native_each_slot_surgical_edits_preserve_history_and_envelope(self):
        raw = Path(os.environ['STARS_SAVE_COPY']).read_bytes()
        document = backend.decode(raw)
        original_blocks = codec.decode(raw)[1]
        self.assertEqual(backend.serialize(document, {}), raw)
        self.assertFalse(document.format.game_load_verified)
        gold = [field for field in backend.fields_for(document) if field.group == 'Campaign gold']
        self.assertEqual(len(gold), 9)
        changes = {field.id: 1000 + field.slot for field in gold}
        updated_raw = backend.serialize(document, changes)
        updated = backend.decode(updated_raw)
        expected = bytearray(document.payload)
        for field in gold:
            expected[field.offset:field.offset + 4] = struct.pack('<I', changes[field.id])
        self.assertEqual(updated.payload, bytes(expected))
        self.assertEqual(updated_raw[:0x79B84], raw[:0x79B84])
        updated_blocks = codec.decode(updated_raw)[1]
        for before, after in zip(original_blocks, updated_blocks):
            self.assertEqual((before.index, before.file_offset, before.iv_seed, before.padding),
                             (after.index, after.file_offset, after.iv_seed, after.padding))
        self.assertEqual(updated.payload[0x1CE:0x1D2], document.payload[0x1CE:0x1D2])


if __name__ == '__main__':
    unittest.main()
