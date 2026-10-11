"""Generated contract fixtures and opt-in genuine decrypted-file validation."""
from dataclasses import replace
import os
from pathlib import Path
import struct
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.kens_rage1_ps3 import parser
from tests.scalar_contract import ScalarContractTests


def metadata(directory='BLUS30504-00'):
    key = b'SAVEDATA_DIRECTORY\0'
    value = directory.encode('ascii') + b'\0'
    return (struct.pack('<5I', 0x46535000, 0x101, 36, 36 + len(key), 1)
            + struct.pack('<HH3I', 0, 0x204, len(value), len(value), 0)
            + key + value)


def procedural_save():
    data = bytearray((index * 37 + 11) % 256 for index in range(parser.SAVE_SIZE))
    data[:32] = parser.HEADER
    for index, field in enumerate(parser.FIELDS):
        data[field.offset - 2:field.offset] = bytes(2)
        data[field.offset:field.offset + 2] = (100 + index).to_bytes(2, 'big')
    return bytes(data)


class KenRage1ContractTests(ScalarContractTests, unittest.TestCase):
    game_id = parser.GAME_ID

    def fixture_bytes(self):
        (self.folder / 'PARAM.SFO').write_bytes(metadata())
        return procedural_save()


class KenRage1FormatTests(unittest.TestCase):
    def test_manual_bounds_high_original_unstage_and_no_max(self):
        raw = bytearray(procedural_save());field = parser.FIELDS[0]
        raw[field.offset:field.offset + 2] = (60000).to_bytes(2, 'big')
        doc = parser.decode(bytes(raw));changes = parser.stage(doc, {}, field.id, 123)
        self.assertEqual(parser.stage(doc, changes, field.id, 60000), {})
        self.assertEqual(parser.serialize(doc, {}), bytes(raw))
        self.assertEqual(parser.maximums(doc, changes), changes)
        self.assertEqual(parser.limit_values(doc, changes, [field.id]), {})
        self.assertTrue(all(not f.maxable for f in parser.FIELDS))
        for value in (-1, 10000, True, 1.0, '123'):
            with self.subTest(value=value), self.assertRaises(SaveError):
                parser.stage(doc, {}, field.id, value)
        # An original higher resource is preserved on a no-op, not normalized.
        self.assertEqual(field.value(parser.decode(parser.serialize(doc, {})).payload), 60000)

    def test_anomalous_upper_word_is_read_only_and_unknown_bytes_preserved(self):
        raw = bytearray(procedural_save());field = parser.FIELDS[1]
        raw[field.offset - 2] = 1;doc = parser.decode(bytes(raw))
        self.assertNotIn(field.id, parser.field_map(doc))
        with self.assertRaises(SaveError): parser.stage(doc, {}, field.id, 0)
        with self.assertRaises(SaveError): parser.serialize(doc, {field.id: 0})
        self.assertIn('read only', parser.inspection_rows(doc)[1]['value'])
        supported = parser.FIELDS[0]
        edited = parser.serialize(doc, {supported.id: 2345})
        touched = {i for i, pair in enumerate(zip(raw, edited)) if pair[0] != pair[1]}
        self.assertLessEqual(touched, set(range(supported.offset, supported.offset + 2)))
        self.assertEqual(edited[field.offset - 2:field.offset + 2], raw[field.offset - 2:field.offset + 2])
        self.assertEqual(edited[0x132F:], raw[0x132F:])  # Unmapped DLC and tail stay intact.

    def test_foreign_header_size_mutable_and_document_identity(self):
        raw = procedural_save()
        for broken in (raw[:-1], raw + b'\0', bytes(len(raw)), bytearray(raw)):
            with self.assertRaises(SaveError): parser.decode(broken)
        for position in range(32):
            broken = bytearray(raw);broken[position] ^= 1
            with self.subTest(position=position), self.assertRaises(SaveError):
                parser.decode(bytes(broken))
        doc = parser.decode(raw)
        with self.assertRaises(SaveError): parser.decode(raw, 'kens_rage2_ps3')
        with self.assertRaises(SaveError): parser.serialize(replace(doc, format=replace(doc.format)), {})
        with self.assertRaises(SaveError): parser.serialize(replace(doc, payload=raw[:-1]), {})

    def test_exact_identity_required_for_input_output_restore(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder);source = base / 'DATA.BIN';source.write_bytes(procedural_save())
            for context in (None, metadata('BLES01801-00'), metadata('BLUS30504-01'), b'bad'):
                companion = base / 'PARAM.SFO'
                if context is None:
                    if companion.exists(): companion.unlink()
                else: companion.write_bytes(context)
                with self.subTest(context=context is None), self.assertRaises(SaveError):
                    parser.read_save(source)
            companion.write_bytes(metadata());doc = parser.read_save(source)
            target = base / 'separate' / 'edited.bin';target.parent.mkdir()
            with self.assertRaises(SaveError): parser.save_as(doc, {}, target)
            self.assertFalse(target.exists())
            snapshot = parser.backup(doc)
            with self.assertRaises(SaveError): parser.restore(snapshot, target)
            parser.prepare_self_test_copy(doc, target)
            identity = (target.parent / 'PARAM.SFO').read_bytes()
            self.assertEqual(identity, metadata())
            self.assertEqual(parser.save_as(doc, {}, target).raw, doc.raw)
            self.assertEqual(parser.restore(snapshot, target.parent / 'restored.bin').read_bytes(), doc.raw)

    def test_no_native_integrity_claim(self):
        self.assertEqual(parser.INTEGRITY_KIND, 'external')
        self.assertIn('not been independently proved', parser.field_hint(parser.decode(procedural_save()), parser.FIELDS[0]))

    def test_zero_budget_and_malformed_maps_rejected(self):
        raw = bytearray(procedural_save());field = parser.FIELDS[0]
        raw[field.offset:field.offset + 2] = bytes(2)
        doc = parser.decode(bytes(raw))
        self.assertNotIn(field.id, parser.field_map(doc))
        with self.assertRaises(SaveError): parser.stage(doc, {}, field.id, 123)
        with self.assertRaises(SaveError): parser.serialize(doc, {field.id: 123})
        key = parser.FIELDS[1].id
        for invalid in (None, [], [('bad', 1)], {'bad': 1}, {key: True}, {key: 10000}):
            with self.subTest(kind=type(invalid).__name__), self.assertRaises(SaveError):
                parser.stage(doc, invalid, key, 1)
            with self.assertRaises(SaveError): parser.serialize(doc, invalid)
        changed = parser.stage(doc, {}, key, 0)
        reopened = parser.decode(parser.serialize(doc, changed))
        self.assertNotIn(key, parser.field_map(reopened))
        self.assertEqual(parser.stage(doc, changed, key, parser.FIELDS[1].value(doc.payload)), {})


class GenuineKenRage1Tests(unittest.TestCase):
    def test_genuine_unchanged_and_each_surgical_skill_edit(self):
        copies = os.environ.get('KENS_RAGE1_PS3_SAVE_COPIES')
        if not copies: self.skipTest('No genuine copied decrypted US/EU gameplay exports')
        for filename in copies.split(os.pathsep):
            source = Path(filename);doc = parser.read_save(source);original = source.read_bytes()
            self.assertEqual(parser.serialize(doc, {}), original)
            self.assertEqual(len(parser.fields_for(doc)), 8)
            for field in parser.fields_for(doc):
                value = 1 if field.value(doc.payload) == 0 else field.value(doc.payload) - 1
                edited = parser.serialize(doc, {field.id: value});reopened = parser.decode(edited)
                self.assertEqual(field.value(reopened.payload), value)
                touched = {i for i, pair in enumerate(zip(original, edited)) if pair[0] != pair[1]}
                self.assertTrue(touched)
                self.assertLessEqual(touched, set(range(field.offset, field.offset + 2)))
            self.assertEqual(source.read_bytes(), original)
            with tempfile.TemporaryDirectory() as folder:
                target = Path(folder) / 'edited.bin';parser.prepare_self_test_copy(doc, target)
                saved = parser.save_as(doc, {parser.FIELDS[0].id: 123}, target)
                self.assertEqual(parser.read_save(target).raw, saved.raw)
                snapshot = parser.backup(doc)
                restored = parser.restore(snapshot, target.parent / 'restored.bin')
                self.assertEqual(restored.read_bytes(), original)
