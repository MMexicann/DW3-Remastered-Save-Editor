"""Native-schema procedural tests and optional private copied-save checks."""
from dataclasses import replace
from functools import lru_cache
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.scalar_contract import ScalarContractTests
import origins_codec as codec
import origins_parser as parser
from models import SaveError
from save_safety import safe_path


@lru_cache(maxsize=6)
def fixture(revision=29, gold=3456, skill_points=123):
    # Generated data proves preservation and error handling, not game loading.
    size = codec.SLOT_FILE_SIZE - 4
    payload = bytearray((bytes(range(256)) * ((size + 255) // 256))[:size])
    struct.pack_into('<II', payload, 0x660, parser.REVISION_LENGTHS[revision], revision)
    payload[0x668:0x66a] = b'\1\3'
    struct.pack_into('<I', payload, 0x69b, gold)
    struct.pack_into('<H', payload, 0xa87, skill_points)
    if revision == 29:
        struct.pack_into('<H', payload, 0x21f1a, 20)
    return codec.encode(bytes(payload), 0x719b, 'slot')


class OriginsContractTests(ScalarContractTests, unittest.TestCase):
    game_id = 'origins'

    def fixture_bytes(self):
        return fixture()


class NativeOriginsTests(unittest.TestCase):
    def test_all_native_revision_lengths_and_fields(self):
        for revision in (16, 17, 29):
            with self.subTest(revision=revision):
                document = parser.decode(fixture(revision))
                self.assertEqual(document.revision, revision)
                self.assertEqual(parser.serialize(document, {}), document.raw)
                self.assertEqual(parser.field_map(document)['gold'].value(document.payload), 3456)
                self.assertEqual(parser.field_map(document)['skill_points'].value(document.payload), 123)

    def test_legitimate_maxima_only_change_field_and_checksum_bytes(self):
        for revision in (16, 17, 29):
            document = parser.decode(fixture(revision))
            changes = parser.maximums(document, {}, 'Resources')
            expected = {'gold': 999999, 'skill_points': 999}
            if revision == 29:
                expected['dlc_skill_points'] = 999
            self.assertEqual(changes, expected)
            raw = parser.serialize(document, changes)
            reopened = parser.decode(raw)
            allowed_body = set(range(0x69b, 0x69f)) | set(range(0xa87, 0xa89))
            if revision == 29:
                allowed_body.update(range(0x21f1a, 0x21f1c))
            touched_body = {i for i, (a, b) in enumerate(zip(document.payload, reopened.payload)) if a != b}
            self.assertLessEqual(touched_body, allowed_body)
            allowed_raw = {0, 1} | {i + 4 for i in allowed_body}
            touched_raw = {i for i, (a, b) in enumerate(zip(document.raw, raw)) if a != b}
            self.assertLessEqual(touched_raw, allowed_raw)
            self.assertEqual(reopened.seed, document.seed)
            self.assertEqual(parser.maximums(reopened, {}, 'Resources'), {})

    def test_high_existing_values_preserved_and_can_be_unstaged(self):
        document = parser.decode(fixture(gold=1000001, skill_points=1001))
        self.assertNotIn('gold', parser.maximums(document, {}))
        self.assertNotIn('skill_points', parser.maximums(document, {}))
        self.assertEqual(parser.serialize(document, {}), document.raw)
        pending = parser.stage(document, {}, 'gold', 10)
        self.assertEqual(parser.stage(document, pending, 'gold', 1000001), {})
        with self.assertRaises(SaveError):
            parser.stage(document, {}, 'skill_points', 1000)

    def test_old_revisions_do_not_expose_or_modify_dlc_pool(self):
        for revision in (16, 17):
            document = parser.decode(fixture(revision))
            self.assertNotIn('dlc_skill_points', parser.field_map(document))
            with self.assertRaises(SaveError):
                parser.stage(document, {}, 'dlc_skill_points', 999)

    def test_integrity_valid_foreign_schema_is_rejected(self):
        document = parser.decode(fixture())
        for offset, value in ((0x660, 0), (0x660, 0x214ed), (0x664, 28), (0x664, 0xffffffff)):
            payload = bytearray(document.payload)
            struct.pack_into('<I', payload, offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaises(SaveError):
                parser.decode(codec.encode(payload, document.seed, 'slot'))
        user = codec.encode(bytes(codec.USER_FILE_SIZE - 4), 1, 'user')
        with self.assertRaisesRegex(SaveError, 'USER.dat'):
            parser.decode(user)

    def test_malformed_identity_and_forged_snapshot_refused(self):
        document = parser.decode(fixture())
        for raw in (document.raw[:-1], document.raw + b'\x00', b'GVAS' + document.raw):
            with self.assertRaises(SaveError):
                parser.decode(raw)
        for raw in (bytes([document.raw[0] ^ 1]) + document.raw[1:], document.raw[:7] + bytes([document.raw[7] ^ 1]) + document.raw[8:]):
            with self.assertRaises(SaveError):
                parser.decode(raw)
        with self.assertRaises(SaveError):
            parser.decode(document.raw, 'dw8xl')
        for fake in (replace(document, seed=document.seed ^ 1),
                     replace(document, revision=17), replace(document, format=replace(document.format, id='dw8xl'))):
            with self.assertRaises(SaveError):
                parser.serialize(fake, {})

    def test_live_paths_and_cloud_files_blocked(self):
        for path in ('C:/GameDocuments/KoeiTecmo/DYNASTY WARRIORS ORIGINS/Saved/SaveGames/1/SLOT0000.dat',
                     'C:/Steam/userdata/1/2384580/remote/SLOT0001.dat', 'steam_autocloud.vdf'):
            with self.subTest(path=path), self.assertRaises(SaveError):
                safe_path(path)

    def test_private_copied_slots(self):
        value = os.environ.get('ORIGINS_SAVE_COPIES')
        if not value:
            self.skipTest('Set ORIGINS_SAVE_COPIES to a folder of copied native slot saves.')
        files = sorted(safe_path(value).glob('SLOT*.dat'))
        self.assertTrue(files)
        for path in files:
            with self.subTest(slot=path.name):
                document = parser.read_save(path)
                self.assertEqual(parser.serialize(document, {}), document.raw)
                raw = parser.serialize(document, parser.maximums(document, {}))
                edited = parser.decode(raw)
                allowed = {i for field in parser.fields_for(document)
                           for i in range(field.offset, field.offset + field.size)}
                self.assertTrue(all(a == b or index in allowed
                                    for index, (a, b) in enumerate(zip(document.payload, edited.payload))))
                self.assertEqual(path.read_bytes(), document.raw)


if __name__ == '__main__':
    unittest.main()
