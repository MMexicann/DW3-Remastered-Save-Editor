"""Independent adversarial review of SW4-II qualification and safe restoration.

Generated fixtures exercise contracts, not native gameplay loading. These
checks complement the adapter's field/GUI tests with edition and storage races.
"""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.sw4ii import sw4ii_codec as codec, sw4ii_parser as parser
from koei_editor.games.sw4dx import samurai4dx_parser as dx_parser
from koei_editor.shared import copy_storage
from koei_editor.shared.koei_codec import word_cipher, word_sum
from tests.test_sw4ii_format import procedural_raw, seal
from tests.test_samurai4dx_format import procedural_raw as dx_raw


class SW4IIIndependentReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = procedural_raw()
        cls.document = parser.decode(cls.raw)

    def test_same_size_distinct_native_edition_streams_rejected_both_ways(self):
        foreign = dx_raw()
        self.assertEqual(len(foreign), len(self.raw))
        self.assertEqual(dx_parser.serialize(dx_parser.decode(foreign), {}), foreign)
        with self.assertRaises(SaveError):
            parser.decode(foreign)
        with self.assertRaises(SaveError):
            dx_parser.decode(self.raw)

    def _nonzero_document(self):
        payload = bytearray(self.document.payload)
        # These opaque regions used to be incorrectly restricted to zeros.
        for start, end in ((0xA09, 0xA20), (0xCC2E, 0xCC38), (0xD92E, 0x5D86E)):
            payload[start:end] = bytes(1 + (i % 255) for i in range(end - start))
        return parser.decode(seal(payload))

    def test_exact_native_arithmetic_includes_nonzero_sixth_section(self):
        document = self._nonzero_document()
        changed = parser.changed_payload(document, {'gold': 0xFFFFFFFF, 'tome_4': 0xFFFF,
                                                    'officer_55_speed': 0xFFFF})
        for payload in (document.payload, changed):
            # Independently recovered native writer ranges, end-exclusive.
            a, b, c, d, e, f = (sum(payload[start:end]) for start, end in
                                ((8, 0xA8), (0xAC, 0xA0C), (0xA0C, 0x104E),
                                 (0x1052, 0xCC36), (0xCC36, 0xD92E), (0xD92E, 0x5D86E)))
            self.assertGreater(f, 0)
            first = ((a + d) * b + e) & 0x7FFFFFFF
            second = ((d + f + b) * a) & 0x7FFFFFFF
            third = (a + b + c + d) & 0x7FFFFFFF
            expected = (first, second, third, (first + second + third) & 0x7FFFFFFF)
            self.assertEqual(codec.checksums(payload), expected)
            self.assertEqual(tuple(struct.unpack_from('<I', payload, offset)[0]
                                   for offset in (4, 0xA8, 0x104E, 0x5D86E)), expected)

    def test_nonzero_unknown_regions_remain_exact_through_supported_edits(self):
        document = self._nonzero_document()
        self.assertEqual(parser.serialize(document, {}), document.raw)
        changes = {'gold': 321, 'officer_55_speed': 300, 'tome_4': 1}
        reopened = parser.decode(parser.serialize(document, changes))
        for start, end in ((0xA09, 0xA20), (0xCC2E, 0xCC38), (0xD92E, 0x5D86E)):
            self.assertTrue(all(document.payload[start:end]))
            self.assertEqual(reopened.payload[start:end], document.payload[start:end])
        allowed = {i for key in changes for field in (parser.field_map(document)[key],)
                   for i in range(field.offset, field.offset + field.size)}
        allowed.update(i for offset in (4, 0xA8, 0x104E, 0x5D86E)
                       for i in range(offset, offset + 4))
        self.assertTrue(all(a == b or i in allowed for i, (a, b) in
                            enumerate(zip(document.payload, reopened.payload))))

    def test_each_native_section_rejects_damage_with_outer_checksum_repaired(self):
        document = self._nonzero_document()
        for offset in (9, 0xA0A, 0xA0D, 0xCC2F, 0xCC37, 0xD92E):
            with self.subTest(section_byte=hex(offset)):
                payload = bytearray(document.payload)
                payload[offset] ^= 1
                raw = (document.raw[:codec.PAYLOAD_OFFSET - 4]
                       + struct.pack('<HH', word_sum(payload), document.seed)
                       + word_cipher(payload, document.seed))
                with self.assertRaises(SaveError):
                    parser.decode(raw)

    def test_tampered_document_rejected_by_every_public_edit_inspection_operation(self):
        mutations = (replace(self.document, seed=self.document.seed ^ 1),
                     replace(self.document, format=replace(parser.FORMAT)),
                     replace(self.document, payload=memoryview(self.document.payload)))
        operations = (lambda d: parser.fields_for(d), lambda d: parser.inspection_rows(d),
                      lambda d: parser.review(d, {}), lambda d: parser.stage(d, {}, 'gold', 1),
                      lambda d: parser.maximums(d, {}), lambda d: parser.limit_values(d, {}, ['gold']),
                      lambda d: parser.serialize(d, {}), lambda d: parser.backup(d))
        for document in mutations:
            for operation in operations:
                with self.subTest(seed=document.seed, operation=operations.index(operation)):
                    with self.assertRaises(SaveError):
                        operation(document)

    def test_higher_values_and_ineligible_original_records_remain_byte_exact(self):
        payload = bytearray(self.document.payload)
        struct.pack_into('<I', payload, parser.GOLD_OFFSET, 0xFFFFFFFF)
        struct.pack_into('<5H', payload, parser.TOME_BASE, *([0xFFFF] * 5))
        # A higher unusual level cannot be normalized into an editable officer.
        struct.pack_into('<I', payload, parser.OFFICER_BASE + 12, 999)
        document = parser.decode(seal(payload))
        original = document.payload
        self.assertNotIn('officer_0_attack', parser.field_map(document))
        self.assertEqual(parser.maximums(document, {}), {})
        self.assertEqual(parser.serialize(document, {}), document.raw)
        changes = parser.stage(document, {}, 'officer_1_attack', 400)
        changes_before = dict(changes)
        self.assertEqual(parser.maximums(document, changes), changes)
        self.assertEqual(parser.limit_values(document, changes, list(parser.field_map(document))), {})
        self.assertEqual(changes, changes_before)
        reopened = parser.decode(parser.serialize(document, changes))
        self.assertEqual(document.payload, original)
        self.assertEqual(reopened.payload[parser.GOLD_OFFSET:parser.GOLD_OFFSET + 8],
                         original[parser.GOLD_OFFSET:parser.GOLD_OFFSET + 8])
        self.assertEqual(reopened.payload[parser.TOME_BASE:parser.TOME_BASE + 10],
                         original[parser.TOME_BASE:parser.TOME_BASE + 10])
        self.assertEqual(reopened.payload[parser.OFFICER_BASE:parser.OFFICER_BASE + parser.OFFICER_STRIDE],
                         original[parser.OFFICER_BASE:parser.OFFICER_BASE + parser.OFFICER_STRIDE])

    def test_edit_cannot_silently_dequalify_an_existing_mount_record(self):
        payload = bytearray(self.document.payload)
        base = parser.MOUNT_BASE
        payload[base] = 0
        payload[base + 3:base + 5] = bytes((10, 50))
        payload[base + 10:base + 13] = bytes((20, 21, 22))
        document = parser.decode(seal(payload))
        field_ids = {field.id for field in parser.fields_for(document) if field.group == 'Mounts'}
        self.assertIn('mount_0_speed', field_ids)
        for key in ('mount_0_power', 'mount_0_stamina', 'mount_0_speed'):
            try:
                encoded = parser.serialize(document, {key: 0})
            except SaveError:
                continue  # Explicit rejection preserves the supported record.
            reopened = parser.decode(encoded)
            self.assertIn(key, parser.field_map(reopened),
                          'A successful edit must not turn an owned mount into an unqualified record.')

    def test_zero_stored_stats_retain_initialized_standard_officer(self):
        changes = {f'officer_0_{key}': 0 for key, _, _ in parser.STATS}
        reopened = parser.decode(parser.serialize(self.document, changes))
        mapped = parser.field_map(reopened)
        for key in changes:
            self.assertIn(key, mapped)
            self.assertEqual(mapped[key].value(reopened.payload), 0)
        base = parser.OFFICER_BASE
        self.assertEqual(reopened.payload[base:base + 0x20], self.document.payload[base:base + 0x20])

    def test_restore_qualifies_exact_bounded_snapshot_even_if_backup_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            source = folder / 'copy.dat'
            source.write_bytes(self.raw)
            backup = parser.backup(parser.read_save(source))
            destination = folder / 'restored.dat'
            real_decode = parser.decode
            observed = []

            def qualify_and_change_source(raw, *args, **kwargs):
                observed.append(raw)
                document = real_decode(raw, *args, **kwargs)
                # Simulate a concurrent replacement after bounded validation.
                backup.write_bytes(bytes(len(raw)))
                return document

            with patch.object(parser, 'decode', side_effect=qualify_and_change_source):
                parser.restore(backup, destination)
            self.assertEqual(observed, [self.raw])
            self.assertEqual(destination.read_bytes(), self.raw)
            self.assertEqual(source.read_bytes(), self.raw)

    def test_restore_foreign_and_oversized_matching_manifests_never_write(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            for index, raw in enumerate((dx_raw(), self.raw + b'\0')):
                backup = folder / f'backup-{index}.dat'
                backup.write_bytes(raw)
                backup.with_suffix('.json').write_text(json.dumps({
                    'game_id': parser.GAME_ID, 'kind': 'opaque-copy', 'size_bytes': len(raw),
                    'sha256': hashlib.sha256(raw).hexdigest()}))
                destination = folder / f'restored-{index}.dat'
                with patch.object(copy_storage, 'atomic_new') as write:
                    with self.assertRaises(SaveError):
                        parser.restore(backup, destination)
                    write.assert_not_called()
                self.assertFalse(destination.exists())


if __name__ == '__main__':
    unittest.main()
