"""PW4 native structure/resource tests; generated data is not game-load evidence."""
from dataclasses import replace
from functools import lru_cache
import os
from pathlib import Path
import struct
import tempfile
import unittest

from koei_editor.shared.koei_codec import word_sum
from koei_editor.games.dw3.models import SaveError
import koei_editor.games.pw4.pw4_candidate_codec as cipher
import koei_editor.games.pw4.pw4_parser as editor


def encoded(payload, seed=0x2345):
    return struct.pack('<HH', word_sum(payload), seed) + cipher._cipher(payload, seed, 1)


def native_integrity(payload):
    result = bytearray(payload)
    offset = 0x618
    sizes = (0x290, 0x6294, 0x106DC, 0x420, 0x180, 0x1DBD0,
             0x3880, 0x19480, 0x66880, 0x19480) + (0xA90,) * 132 + (0x100094, 0x2080)
    for index, size in enumerate(sizes):
        body_end = offset + (0x80 + 0x1D730 if index == 5 else size)
        struct.pack_into('<III', result, offset, sum(result[offset + 128:body_end]), size, 15)
        if index == 5:
            child = body_end
            struct.pack_into('<III', result, child, sum(result[child + 128:child + 0x420]), 0x420, 15)
        offset += size
    return bytes(result)


@lru_cache(maxsize=1)
def procedural_raw():
    # Distinctive unknown bytes exercise preservation, including unused capacity.
    payload = bytearray((index * 29 + 17) & 255 for index in range(0x271618))
    prefix = b'084 19 025 050 075\0'
    payload[:len(prefix)] = prefix
    struct.pack_into('<6I', payload, 0x600, 1, 84, 19, 25, 50, 75)
    struct.pack_into('<I', payload, 0x698, 15)
    struct.pack_into('<I', payload, 0x6BC0, 12345)
    struct.pack_into('<I', payload, 0x734C, 67890)
    payload[0xB8988:0xB8988 + 400 * 48] = bytes(400 * 48)
    for identity, quantity in ((0, 123), (7, 0), (399, 4000000001)):
        struct.pack_into('<III', payload, 0xB8988 + identity * 48, 300, 22, quantity)
        payload[0xB8988 + identity * 48 + 12] = 5
    return encoded(native_integrity(payload))


class PW4FormatTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / 'slot-copy.dat'
        self.source.write_bytes(procedural_raw())
        self.document = editor.read_save(self.source)

    def test_noop_staging_review_and_surgical_profile_integrity(self):
        doc = self.document
        self.assertEqual(editor.serialize(doc, {}), doc.raw)
        changes = editor.stage(doc, {}, 'beli', 999999999)
        self.assertEqual(editor.stage(doc, changes, 'beli', 12345), {})
        self.assertEqual([(f.id, a, b) for f, a, b in editor.review(doc, changes)],
                         [('beli', 12345, 999999999)])
        updated = editor.decode(editor.serialize(doc, changes))
        self.assertEqual(editor.FIELD_MAP['beli'].value(updated.payload), 999999999)
        self.assertEqual(struct.unpack_from('<I', updated.payload, 0x734C)[0], 67890)
        touched = {i for i, (a, b) in enumerate(zip(doc.payload, updated.payload)) if a != b}
        self.assertLessEqual(touched, set(range(0x6BC0, 0x6BC4)) | set(range(0x6B3C, 0x6B40)))
        self.assertEqual(doc.payload[0x177B8:], updated.payload[0x177B8:])
        self.assertEqual(doc.seed, updated.seed)
        self.assertEqual(self.source.read_bytes(), doc.raw)

    def test_lifetime_earnings_read_only_and_preserved_by_max(self):
        maxima = editor.maximums(self.document, {}, 'Resources')
        self.assertEqual(maxima, {'beli': 999999999})
        self.assertEqual(editor.maximums(self.document, {}, 'Records'), {})
        with self.assertRaises(SaveError):
            editor.serialize(self.document, {'lifetime_beli': 4000000000})
        edited = editor.decode(editor.serialize(self.document, maxima))
        self.assertEqual(struct.unpack_from('<I', edited.payload, 0x734C)[0], 67890)
        row = next(row for row in editor.inspection_rows(self.document) if row['group'] == 'Records')
        self.assertEqual(row['value'], 67890)

    def test_higher_existing_values_preserved_by_max_and_unstage(self):
        payload = bytearray(self.document.payload)
        struct.pack_into('<I', payload, 0x6BC0, 4000000001)
        struct.pack_into('<I', payload, 0x734C, 4200000000)
        doc = editor.decode(encoded(native_integrity(payload)))
        self.assertEqual(editor.maximums(doc, {}, 'Resources'), {})
        changes = editor.stage(doc, {}, 'beli', 99)
        self.assertEqual(editor.stage(doc, changes, 'beli', 4000000001), {})
        self.assertEqual(editor.serialize(doc, {}), doc.raw)

    def test_bad_native_object_checksum_rejected_even_if_outer_checksum_repaired(self):
        for offset in (0x6BC0, 0x177B8 + 128 + 10, 0x34F68 + 128 + 8,
                       0xD1D88 + 128 + 4):
            payload = bytearray(self.document.payload)
            payload[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(SaveError):
                editor.decode(encoded(payload))

    def test_foreign_system_region_revision_size_and_summary_rejected(self):
        raw = self.document.raw
        for malformed in (raw[:-1], raw + b'\0', raw[:0x2804], bytes([raw[0] ^ 1]) + raw[1:]):
            with self.assertRaises(SaveError):
                editor.decode(malformed)
        payload = self.document.payload
        wrong_region = struct.pack('<HH', word_sum(payload), 0x2345) + cipher._cipher(payload, 0x2345, 4)
        with self.assertRaises(SaveError):
            editor.decode(wrong_region)
        for offset in (0, 0x600, 0x6B40, 0x6B44, 0x698):
            changed = bytearray(payload)
            changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(SaveError):
                editor.decode(encoded(changed))
        with self.assertRaises(SaveError):
            editor.decode(raw, 'pw3')

    def test_invalid_fields_bounds_and_forged_snapshot_rejected(self):
        for key, value in (('unmapped', 1), ('beli', True), ('beli', -1),
                           ('beli', 1000000000), ('lifetime_beli', 4000000001)):
            with self.subTest(key=key, value=value), self.assertRaises(SaveError):
                editor.stage(self.document, {}, key, value)
        for doc in (replace(self.document, payload=self.document.payload[:-1]),
                    replace(self.document, payload=bytearray(self.document.payload)),
                    replace(self.document, format=replace(editor.FORMAT, id='pw3')),
                    replace(self.document, seed=42), replace(self.document, seed=True)):
            with self.assertRaises(SaveError):
                editor.serialize(doc, {})

    def test_qualified_owned_coin_quantities_surgical_edits_and_history(self):
        doc = self.document
        keys = {field.id for field in editor.fields_for(doc)}
        self.assertEqual(keys, {'beli', 'coin_0_quantity', 'coin_7_quantity', 'coin_399_quantity'})
        changes = editor.stage(doc, {}, 'coin_7_quantity', 999)
        self.assertEqual([(f.id, old, new) for f, old, new in editor.review(doc, changes)],
                         [('coin_7_quantity', 0, 999)])
        updated = editor.decode(editor.serialize(doc, changes))
        touched = {i for i, (a, b) in enumerate(zip(doc.payload, updated.payload)) if a != b}
        allowed = set(range(0xB8908, 0xB890C)) | set(range(0xB8988 + 7 * 48 + 8, 0xB8988 + 7 * 48 + 12))
        self.assertLessEqual(touched, allowed)
        before = editor.coins(doc)[1]
        after = editor.coins(updated)[1]
        self.assertEqual({k: v for k, v in before.items() if k != 'quantity'},
                         {k: v for k, v in after.items() if k != 'quantity'})
        self.assertEqual(editor.maximums(doc, {}, 'Owned coins'),
                         {'coin_0_quantity': 999, 'coin_7_quantity': 999})
        self.assertEqual(editor.stage(doc, {'coin_399_quantity': 2}, 'coin_399_quantity', 4000000001), {})
        self.assertEqual(editor.record_label(8, 'Owned coins'), 'Coin ID 007')
        for key, value in (('coin_1_quantity', 1), ('coin_400_quantity', 1),
                           ('coin_0_quantity', 1000), ('coin_0_quantity', True)):
            with self.subTest(key=key, value=value), self.assertRaises(SaveError):
                editor.stage(doc, {}, key, value)

    def test_coin_ownership_requires_both_obtained_bit_and_earned_history(self):
        payload = bytearray(self.document.payload)
        payload[0xB8988 + 12] = 4  # Earned history but no obtained flag.
        struct.pack_into('<I', payload, 0xB8988 + 7 * 48, 0)  # Flag but no earned history.
        # An apparently populated physical entry outside native IDs 0..399 is excluded.
        struct.pack_into('<III', payload, 0xB8988 + 400 * 48, 8, 0, 8)
        payload[0xB8988 + 400 * 48 + 12] = 5
        doc = editor.decode(encoded(native_integrity(payload)))
        self.assertEqual({field.id for field in editor.fields_for(doc)}, {'beli', 'coin_399_quantity'})
        with self.assertRaises(SaveError):
            editor.serialize(doc, {'coin_0_quantity': 1})

    def test_backup_save_as_restore_and_source_change_protection(self):
        doc = self.document
        snapshot = editor.backup(doc)
        self.assertEqual(snapshot.read_bytes(), doc.raw)
        result = editor.save_as(doc, {'beli': 22222}, self.folder / 'edited.dat')
        self.assertEqual(editor.FIELD_MAP['beli'].value(result.payload), 22222)
        self.assertEqual(self.source.read_bytes(), doc.raw)
        with self.assertRaises(FileExistsError):
            editor.save_as(doc, {}, result.source)
        restored = editor.restore(snapshot, self.folder / 'restored.dat')
        self.assertEqual(restored.read_bytes(), doc.raw)
        self.source.write_bytes(doc.raw[:-1] + bytes([doc.raw[-1] ^ 1]))
        target = self.folder / 'changed-source.dat'
        with self.assertRaises(SaveError):
            editor.save_as(doc, {}, target)
        self.assertFalse(target.exists())

    @unittest.skipUnless(os.environ.get('PW4_SAVE_COPY'), 'No copied native PW4 slot supplied.')
    def test_optional_native_copy_roundtrip_and_targeted_resource_edit_in_memory(self):
        doc = editor.read_save(Path(os.environ['PW4_SAVE_COPY']))
        self.assertEqual(editor.serialize(doc, {}), doc.raw)
        original = editor.FIELD_MAP['beli'].value(doc.payload)
        changes = {'beli': 12345 if original != 12345 else 12346}
        reopened = editor.decode(editor.serialize(doc, changes))
        self.assertEqual(editor.FIELD_MAP['beli'].value(reopened.payload), changes['beli'])
        allowed = set(range(0x6B3C, 0x6B40)) | set(range(0x6BC0, 0x6BC4))
        touched = {i for i, (a, b) in enumerate(zip(doc.payload, reopened.payload)) if a != b}
        self.assertLessEqual(touched, allowed)
        self.assertEqual(doc.source.read_bytes(), doc.raw)
        rows = editor.coins(doc)
        self.assertTrue(rows, 'The native fixture must corroborate obtained coin records.')
        row = rows[0]
        quantity = 998 if row['quantity'] != 998 else 997
        reopened = editor.decode(editor.serialize(doc, {f"coin_{row['id']}_quantity": quantity}))
        modified = next(r for r in editor.coins(reopened) if r['id'] == row['id'])
        self.assertEqual(modified, dict(row, quantity=quantity))
        allowed = set(range(0xB8908, 0xB890C)) | set(range(0xB8988 + row['id'] * 48 + 8,
                                                       0xB8988 + row['id'] * 48 + 12))
        touched = {i for i, (a, b) in enumerate(zip(doc.payload, reopened.payload)) if a != b}
        self.assertLessEqual(touched, allowed)
