"""Procedural safety and optional complete privately decrypted player exports.

Native fixture checks verify published literal Cole amounts; no player data or
console keys are bundled and no edited PS3 game-load validation is claimed.
"""
from dataclasses import replace
from functools import lru_cache
import os
from pathlib import Path
import struct
import tempfile
import unittest

from koei_editor.games.ayesha_ps3 import parser
from koei_editor.games.dw3.models import SaveError
from tests import test_ps3_expansion as context_tests


@lru_cache(maxsize=1)
def procedural_save():
    raw = bytearray(parser.SAVE_SIZE)
    raw[:8] = parser.HEADER
    raw[0x392B4:0x392B8] = bytes.fromhex('0004fd98')
    raw[0x883C0:0x883C4] = (100).to_bytes(4, 'big')
    for _, base, count in parser.POOLS:
        raw[base - 4:base] = count.to_bytes(4, 'big')
        for slot in range(count): raw[base + slot * 32 + 2:base + slot * 32 + 4] = b'\xff\xff'
    raw[parser.GOLD_OFFSET:parser.GOLD_OFFSET + 4] = (9999999).to_bytes(4, 'big')
    base = parser.POOLS[1][1]
    for index, (identity, quantity, quality, appraisal) in enumerate(
            ((16, 106, 45.555557, 0), (139, 9, 100.0, 0), (100, 1, 120.0, 0),
             (77, 500, 120.0, 0), (88, 8, float('nan'), 0), (99, 8, 130.0, 0),
             (80, 8, 100.0, 0xFFFF))):
        offset = base + index * 32
        struct.pack_into('>HHf5HH4HHH', raw, offset, index + 17, identity, quality,
                         1, 2, 3, 0xFFFF, 0xFFFF, appraisal,
                         4, 5, 0xFFFF, 0xFFFF, 0x1234, quantity)
    # A dormant record after the first sentinel never becomes editable.
    offset = base + 9 * 32
    struct.pack_into('>HHf', raw, offset, 37, 16, 50.0)
    raw[offset + 30:offset + 32] = (10).to_bytes(2, 'big')
    raw[0x9D381:0x9D385] = (1889).to_bytes(4, 'big')
    raw[0x9D385:0x9D389] = (9339).to_bytes(4, 'big')
    raw[500:516] = b'unknown original'
    return bytes(raw)


class AyeshaSafetyTests(unittest.TestCase):
    def setUp(self): self.doc = parser.decode(procedural_save())

    def test_native_size_profile_arrays_and_noop(self):
        self.assertEqual(parser.serialize(self.doc, {}), procedural_save())
        for index in (0, 0x392B8, 0x3A1BC, 0x883C0):
            raw = bytearray(self.doc.raw); raw[index] ^= 1
            with self.subTest(index=index), self.assertRaises(SaveError): parser.decode(bytes(raw))
        for raw in (b'', self.doc.raw[:-1], self.doc.raw + b'\0', bytearray(self.doc.raw)):
            with self.assertRaises(SaveError): parser.decode(raw)
        self.assertEqual(parser.INTEGRITY_KIND, 'external')
        self.assertFalse(parser.FORMAT.game_load_verified)

    def test_only_existing_ordinary_stacks_reduce_without_ownership_deletion(self):
        mapping = parser.field_map(self.doc)
        self.assertEqual(set(mapping), {'cole', 'container_1_quantity', 'container_2_quantity'})
        self.assertEqual(mapping['container_1_quantity'].maximum, 106)
        for key, value in [('container_1_quantity', 0), ('container_1_quantity', 107),
                           ('container_3_quantity', 1), ('container_4_quantity', 1),
                           ('container_5_quantity', 1), ('container_6_quantity', 1),
                           ('container_7_quantity', 1), ('container_10_quantity', 1),
                           ('quality', 120), ('memory_points', 9)]:
            with self.subTest(key=key), self.assertRaises(SaveError): parser.stage(self.doc, {}, key, value)

    def test_exact_target_bytes_float_quality_traits_and_distinct_memory_words_preserved(self):
        changes = {'cole': 304204, 'container_1_quantity': 1}
        edited = parser.serialize(self.doc, changes)
        allowed = set(range(parser.GOLD_OFFSET, parser.GOLD_OFFSET + 4))
        field = parser.field_map(self.doc)['container_1_quantity']
        allowed.update(range(field.offset, field.offset + field.size))
        self.assertTrue({i for i, (a, b) in enumerate(zip(self.doc.raw, edited)) if a != b} <= allowed)
        base = parser.POOLS[1][1]
        self.assertEqual(edited[base:base + 30], self.doc.raw[base:base + 30])
        self.assertEqual(parser.memory_records(parser.decode(edited)),
                         (('Memory-related word 1', 1889), ('Memory-related word 2', 9339)))
        rows = parser.item_records(self.doc)
        self.assertEqual(rows[0][2:5], (16, 17, 106))
        self.assertEqual(rows[0][6:8], ('1, 2, 3', '4, 5'))
        self.assertIn('45.555', rows[0][5])

    def test_pending_validation_max_manual_bounds_and_restore_higher_original(self):
        changes = parser.stage(self.doc, {}, 'cole', 1)
        self.assertEqual(parser.maximums(self.doc, changes), changes)
        self.assertEqual(parser.stage(self.doc, changes, 'cole', 9999999), {})
        self.assertEqual(parser.limit_values(self.doc, {}, ['cole']), {})
        for bad in (True, -1, 1000000, '1'):
            with self.assertRaises(SaveError): parser.stage(self.doc, {}, 'cole', bad)
        for changes in ({'cole': True}, {'unknown': 1}, None, []):
            with self.assertRaises(SaveError): parser.maximums(self.doc, changes)
        self.assertEqual([(f.id, a, b) for f, a, b in parser.review(self.doc, {'cole': 1})], [('cole', 9999999, 1)])

    def test_frozen_equal_mutable_snapshot_rejected(self):
        for doc in (replace(self.doc, raw=bytearray(self.doc.raw)),
                    replace(self.doc, payload=memoryview(self.doc.payload)),
                    replace(self.doc, format=replace(parser.FORMAT))):
            with self.assertRaises(SaveError): parser.serialize(doc, {})

    def test_safe_copy_backup_restore_conflicting_region_and_stale_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);source = root / 'copy.bin';source.write_bytes(self.doc.raw)
            sfo = root / 'PARAM.SFO';sfo.write_bytes(context_tests.PS3ContextTests.metadata('BLJM60486-LIST-15'))
            doc = parser.read_save(source)
            output = parser.save_as(doc, {'cole': 8}, root / 'edited.bin')
            self.assertEqual(parser.field_map(output)['cole'].value(output.payload), 8)
            self.assertEqual(source.read_bytes(), doc.raw)
            backup = parser.backup(doc)
            self.assertEqual(parser.restore(backup, root / 'restored.bin').read_bytes(), doc.raw)
            with self.assertRaises(FileExistsError): parser.save_as(doc, {}, source)
            sfo.write_bytes(context_tests.PS3ContextTests.metadata('BLAS50502-LIST-15'))
            for operation in (lambda: parser.read_save(source), lambda: parser.save_as(doc, {}, root / 'foreign.bin'),
                              lambda: parser.restore(backup, root / 'foreign-restore.bin')):
                with self.assertRaises(SaveError): operation()
            sfo.unlink();source.write_bytes(doc.raw[:-1])
            with self.assertRaises(SaveError): parser.save_as(doc, {}, root / 'stale.bin')
            self.assertFalse((root / 'stale.bin').exists())


@unittest.skipUnless(os.environ.get('AYESHA_PS3_SAVE_COPIES'), 'No private native decrypted PS3 copies')
class GenuineAyeshaTests(unittest.TestCase):
    def test_native_known_answers_roundtrips_stack_edits_and_memory_word_distinction(self):
        files = os.environ['AYESHA_PS3_SAVE_COPIES'].split(os.pathsep)
        self.assertEqual(len(files), 3)
        # Native author descriptions are independently published on GameFAQs.
        for filename, amount in zip(files, (9999999, 110999, 304204)):
            raw = Path(filename).read_bytes();doc = parser.decode(raw)
            self.assertEqual(parser.field_map(doc)['cole'].value(doc.payload), amount)
            self.assertEqual(parser.serialize(doc, {}), raw)
            field = next(field for field in parser.fields_for(doc) if field.group.endswith(' stacks'))
            output = parser.serialize(doc, {field.id: 1, 'cole': 110998})
            allowed = set(range(field.offset, field.offset + field.size)) | set(range(parser.GOLD_OFFSET, parser.GOLD_OFFSET + 4))
            self.assertTrue({i for i, (a, b) in enumerate(zip(raw, output)) if a != b} <= allowed)
            self.assertEqual(parser.maximums(doc, {}), {})
        jp = parser.decode(Path(files[1]).read_bytes())
        self.assertNotEqual(*[value for _, value in parser.memory_records(jp)])
