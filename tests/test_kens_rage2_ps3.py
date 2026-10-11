"""Procedural unlock tests and optional genuine no-edit qualification."""
from dataclasses import replace
import os
from pathlib import Path
import tempfile
import struct
import unittest
import zlib

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.kens_rage2_ps3 import parser
from tests.scalar_contract import ScalarContractTests


def metadata(directory='BLES01801-00'):
    key = b'SAVEDATA_DIRECTORY\0'
    value = directory.encode('ascii') + b'\0'
    return (struct.pack('<5I', 0x46535000, 0x101, 36, 36 + len(key), 1)
            + struct.pack('<HH3I', 0, 0x204, len(value), len(value), 0)
            + key + value)


def procedural_save():
    data = bytearray((index * 53 + 7) % 256 for index in range(parser.SAVE_SIZE))
    for offset, value in parser.STRUCTURE:
        data[offset:offset + 4] = value.to_bytes(4, 'big')
    for field in parser.FIELDS:
        data[field.offset] = 0
    data[parser.FIELDS[1].offset] = 1
    data[parser.FIELDS[2].offset] = 2
    data[parser.FIELDS[3].offset] = 255
    return parser.seal(bytes(data))


class KenRage2ContractTests(ScalarContractTests, unittest.TestCase):
    game_id = parser.GAME_ID
    payload_integrity_offsets = frozenset(i for offset in parser.CHECKSUM_OFFSETS
                                          for i in range(offset, offset + 4))
    fixture_bytes = staticmethod(procedural_save)

    def setUp(self):
        from koei_editor.game_registry import get_game
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        (self.folder / 'PARAM.SFO').write_bytes(metadata())
        self.game = get_game(self.game_id)
        self.adapter = self.game.get_scalar_adapter()
        self.raw = self.fixture_bytes()
        self.source = self.folder / 'input-copy.bin'
        self.source.write_bytes(self.raw)
        self.document = self.adapter.read_save(self.source)


class KenRage2FormatTests(unittest.TestCase):
    def test_unlock_dependency_status_preservation_unstage_and_no_bulk_max(self):
        raw = procedural_save();doc = parser.decode(raw)
        fields = parser.field_map(doc);key = parser.FIELDS[0].id
        self.assertIn(key, fields)
        for field in parser.FIELDS[1:4]:
            self.assertNotIn(field.id, fields)
            for value in (0, 1, 2, 255):
                with self.assertRaises(SaveError): parser.stage(doc, {}, field.id, value)
                with self.assertRaises(SaveError): parser.serialize(doc, {field.id: value})
        changed = parser.stage(doc, {}, key, 1)
        self.assertEqual(parser.stage(doc, changed, key, 0), {})
        self.assertEqual(parser.maximums(doc, changed), changed)
        self.assertEqual(parser.limit_values(doc, changed, [key]), {})
        edited = parser.serialize(doc, changed);reopened = parser.decode(edited)
        self.assertEqual(reopened.payload[parser.FIELDS[0].offset], 1)
        self.assertNotIn(key, parser.field_map(reopened))
        touched = {i for i, pair in enumerate(zip(raw, edited)) if pair[0] != pair[1]}
        allowed = {parser.FIELDS[0].offset} | set(KenRage2ContractTests.payload_integrity_offsets)
        self.assertLessEqual(touched, allowed)
        self.assertEqual(edited[0x54E4:], raw[0x54E4:])
        self.assertEqual([row['value'] for row in parser.inspection_rows(doc)][1:4],
                         ['Native collection status 1 (preserved; read only)',
                          'Native collection status 2 (preserved; read only)',
                          'Native collection status 255 (preserved; read only)'])

    def test_all_six_integrity_regions_and_structures_rejected_when_corrupt(self):
        raw = procedural_save()
        for offset, start, end in parser.CRC_REGIONS:
            for position in (offset, start, end - 1):
                broken = bytearray(raw);broken[position] ^= 1
                with self.subTest(position=position), self.assertRaises(SaveError):
                    parser.decode(bytes(broken))
        # Global CRC alone must not conceal a damaged native sub-section.
        broken = bytearray(raw);broken[0x1FFC] ^= 1
        broken[0xC:0x10] = zlib.crc32(broken[0x20:0x54E4]).to_bytes(4, 'big')
        with self.assertRaises(SaveError): parser.decode(bytes(broken))
        for offset, _value in parser.STRUCTURE:
            broken = bytearray(raw);broken[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(SaveError):
                parser.decode(parser.seal(bytes(broken)))

    def test_bounds_foreign_mutability_and_snapshot_identity(self):
        raw = procedural_save();doc = parser.decode(raw);key = parser.FIELDS[0].id
        for broken in (raw[:-1], raw + b'\0', b'\0' * len(raw), b'\xff' * len(raw), bytearray(raw)):
            with self.assertRaises(SaveError): parser.decode(broken)
        with self.assertRaises(SaveError): parser.decode(raw, 'kens_rage_ps3')
        for value in (-1, 2, True, '1', 1.0):
            with self.assertRaises(SaveError): parser.stage(doc, {}, key, value)
            with self.assertRaises(SaveError): parser.serialize(doc, {key: value})
        for broken in (replace(doc, raw=bytearray(raw)), replace(doc, payload=raw[:-1]),
                       replace(doc, format=replace(parser.FORMAT, id='foreign'))):
            with self.assertRaises(SaveError): parser.serialize(broken, {})

    def test_malformed_pending_changes_rejected_consistently(self):
        doc = parser.decode(procedural_save());key = parser.FIELDS[0].id
        for changes in (None, [], 1, {42: 1}, {key: True}, {'unmapped': 1}):
            for action in (lambda: parser.stage(doc, changes, key, 1),
                           lambda: parser.serialize(doc, changes),
                           lambda: parser.review(doc, changes),
                           lambda: parser.maximums(doc, changes)):
                with self.subTest(changes=changes), self.assertRaises(SaveError):
                    action()

    def test_source_alias_and_restore_reject_damaged_input(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'DATA.BIN';source.write_bytes(procedural_save())
            (Path(folder) / 'PARAM.SFO').write_bytes(metadata())
            doc = parser.read_save(source)
            with self.assertRaises((FileExistsError, SaveError)):
                parser.save_as(doc, {}, source)
            backup = parser.backup(doc);data = bytearray(backup.read_bytes());data[0x212] ^= 1
            backup.write_bytes(data)
            destination = Path(folder) / 'restored.bin'
            with self.assertRaises(SaveError): parser.restore(backup, destination)
            self.assertFalse(destination.exists())

    def test_required_identity_companion_absence_foreign_and_malformed(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'DATA.BIN';source.write_bytes(procedural_save())
            companion = source.parent / 'PARAM.SFO'
            with self.assertRaises(SaveError): parser.read_save(source)
            for raw in (metadata('BLJM60553-00'), metadata('BLUS30504-00'), b'broken'):
                companion.write_bytes(raw)
                with self.assertRaises(SaveError): parser.read_save(source)
            companion.write_bytes(metadata());doc = parser.read_save(source)
            elsewhere = source.parent / 'no-context';elsewhere.mkdir()
            with self.assertRaises(SaveError): parser.save_as(doc, {}, elsewhere / 'edited.bin')
            backup = parser.backup(doc)
            with self.assertRaises(SaveError): parser.restore(backup, elsewhere / 'restored.bin')
            self.assertFalse((elsewhere / 'edited.bin').exists())
            self.assertFalse((elsewhere / 'restored.bin').exists())
            companion.unlink()
            with self.assertRaises(SaveError): parser.save_as(doc, {}, source.parent / 'edited.bin')

    def test_self_test_context_contains_only_validated_directory_identity(self):
        from koei_editor.shared.ps3_export import savedata_directory
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'DATA.BIN';source.write_bytes(procedural_save())
            sentinel = b'OWNER-CONTEXT-MUST-NOT-BE-COPIED'
            (source.parent / 'PARAM.SFO').write_bytes(metadata('BLES01801-01') + sentinel)
            doc = parser.read_save(source)
            output = source.parent / 'self-test';output.mkdir()
            destination = output / 'roundtrip.bin'
            parser.prepare_self_test_copy(doc, destination)
            identity = (output / 'PARAM.SFO').read_bytes()
            self.assertEqual(savedata_directory(identity), 'BLES01801-01')
            self.assertEqual(identity, metadata('BLES01801-01'))
            self.assertNotIn(sentinel, identity)
            written = parser.save_as(doc, {}, destination)
            self.assertEqual(parser.read_save(written.source).raw, doc.raw)
            self.assertEqual((source.parent / 'PARAM.SFO').read_bytes(), metadata('BLES01801-01') + sentinel)
            from koei_editor.shared.verified_self_test import run
            report = run(parser.GAME_ID, source, source.parent / 'cli-self-test')
            self.assertTrue(report['success'])
            self.assertTrue(report['checksum_verified'])
            self.assertFalse(report['format_sample_verified'])
            self.assertFalse(report['native_integrity_verified'])
            self.assertEqual(report['fields_changed'], 0)
            self.assertFalse(report['in_game_load_tested'])
            copied_context = source.parent / 'cli-self-test' / 'PARAM.SFO'
            self.assertEqual(copied_context.read_bytes(), metadata('BLES01801-01'))
            self.assertNotIn(sentinel, (source.parent / 'cli-self-test' / 'self-test-report.json').read_bytes())


@unittest.skipUnless(os.environ.get('KENS_RAGE2_PS3_SAVE_COPIES'),
                     'No copied genuine decrypted EU Ken\'s Rage 2 exports')
class GenuineKenRage2Tests(unittest.TestCase):
    def test_genuine_profile_and_unchanged_roundtrips(self):
        # Public samples already have all mapped galleries unlocked. These checks
        # prove unchanged native preservation; surgical unlocks are procedural.
        for name in os.environ['KENS_RAGE2_PS3_SAVE_COPIES'].split(os.pathsep):
            source = Path(name);raw = source.read_bytes()
            with self.subTest(sample=source.parent.name):
                parser.validate_context(source)
                doc = parser.decode(raw)
                self.assertEqual(parser.serialize(doc, {}), raw)
                self.assertEqual(parser.maximums(doc, {}), {})
                self.assertEqual(len(parser.inspection_rows(doc)), 271)
