"""PC XIII revision-14 native city profile; public fixtures are procedural."""
from dataclasses import replace
from functools import lru_cache
import hashlib
import os
from pathlib import Path
import struct
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.rotk13 import codec, parser as backend
from tests.scalar_contract import ScalarContractTests


@lru_cache(maxsize=1)
def procedural_raw():
    header = bytearray((index * 19 + 37) & 255 for index in range(codec.HEADER_SIZE))
    header[:len(codec.MAGIC)] = codec.MAGIC
    struct.pack_into('<H', header, 0x16, codec.REVISION)
    struct.pack_into('<H', header, codec.CHECKSUM_OFFSET, codec.header_checksum(header))
    body = bytearray((index * 17 + 29) & 255 for index in range(codec.SAVE_SIZE - codec.HEADER_SIZE))
    struct.pack_into('<I', body, 0, codec.REVISION)
    for offset, name in backend.SECTION_TAGS:
        tag = name.encode('ascii')
        body[offset:offset + 32] = tag + bytes(32 - len(tag))
    for city in range(backend.CITY_COUNT):
        start = backend.CITY_BASE + city * backend.CITY_STRIDE
        body[start] = 0xFF if city == 59 else city % backend.CITY_COUNT
        for index, (_name, _label, offset, width, _group) in enumerate(backend.CITY_MEMBERS):
            value = (10000 * index + city * 101 + 23) % (1 << (width * 8))
            body[start + offset:start + offset + width] = value.to_bytes(width, 'little')
    # Deliberately preserve values beyond ordinary play, without a guessed cap.
    struct.pack_into('<I', body, backend.CITY_BASE + 0x36, 0xF0000000)
    struct.pack_into('<I', body, backend.CITY_BASE + 0x3E, 7)
    struct.pack_into('<I', body, backend.CITY_BASE + 0x42, 987654321)
    return codec.encode_layers(bytes(header), bytes(body))


class XIIIFormatTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / 'campaign-copy.s13'
        self.source.write_bytes(procedural_raw())
        self.document = backend.read_save(self.source)

    def test_native_identity_size_preview_integrity_and_sections(self):
        doc = self.document
        self.assertEqual(backend.serialize(doc, {}), doc.raw)
        self.assertEqual(codec.encode_layers(doc.header, doc.payload), doc.raw)
        # Frozen arithmetic vector from the native generator, independent of
        # the procedural fixture's call to the production encoder. Both layers
        # restart at zero; addition must not become XOR.
        masks = bytes.fromhex('00dc0465aa1fad1d5adae5ac1b1e5f13'
                              '70796cfd10ff19af601d04acb41d022b')
        for offset, plain in ((0, doc.header), (codec.HEADER_SIZE, doc.payload)):
            expected = bytes((value + mask) % 256 for value, mask in zip(plain, masks))
            self.assertEqual(doc.raw[offset:offset + len(masks)], expected)
        self.assertTrue(doc.format.sample_verified)
        self.assertFalse(doc.format.game_load_verified)
        for raw in (b'', doc.raw[:-1], doc.raw + b'\0', bytearray(doc.raw),
                    memoryview(doc.raw), bytes(codec.SAVE_SIZE), None):
            with self.subTest(kind=type(raw).__name__), self.assertRaises(SaveError):
                backend.decode(raw)
        for offset in (0, codec.CHECKSUM_OFFSET, 0x16, 0x3FF):
            raw = bytearray(doc.raw)
            raw[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(SaveError):
                backend.decode(bytes(raw))
        for offset, _name in backend.SECTION_TAGS:
            body = bytearray(doc.payload)
            body[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(SaveError):
                backend.decode(codec.encode_layers(doc.header, bytes(body)))
        body = bytearray(doc.payload)
        struct.pack_into('<I', body, 0, 15)
        with self.assertRaises(SaveError):
            codec.encode_layers(doc.header, bytes(body))
        header = bytearray(doc.header)
        header[:len(codec.MAGIC)] = b'SAN13 EDITDATA'
        struct.pack_into('<H', header, codec.CHECKSUM_OFFSET, codec.header_checksum(header))
        with self.assertRaises(SaveError):
            codec.encode_layers(bytes(header), doc.payload)
        body = bytearray(doc.payload)
        offset = dict((name, offset) for offset, name in backend.SECTION_TAGS)['Force']
        body[offset:offset + 32] = b'City' + bytes(28)
        with self.assertRaises(SaveError):
            backend.decode(codec.encode_layers(doc.header, bytes(body)))

    def test_field_identity_width_bounds_and_unusual_values(self):
        doc = self.document
        mapping = backend.field_map(doc)
        self.assertEqual(len(mapping), 720)
        self.assertEqual({field.size for field in mapping.values()}, {2, 4})
        self.assertFalse(any(field.maxable for field in mapping.values()))
        self.assertEqual(mapping['city_0_money'].value(doc.payload), 0xF0000000)
        self.assertEqual(backend.maximums(doc, {}), {})
        self.assertEqual(backend.limit_values(doc, {}, mapping), {})
        self.assertEqual(backend.serialize(doc, backend.maximums(doc, {})), doc.raw)
        for city in (0, 1, 59):
            for name, _label, relative, width, _group in backend.CITY_MEMBERS:
                field = mapping[f'city_{city}_{name}']
                self.assertEqual(field.offset, backend.CITY_BASE + city * backend.CITY_STRIDE + relative)
                self.assertEqual(field.size, width)
                for value in (-1, field.maximum + 1, True, 2.0, '2'):
                    with self.subTest(key=field.id, value=value), self.assertRaises(SaveError):
                        backend.stage(doc, {}, field.id, value)
        for key in ('city_0_owner', 'city_0_revenue', 'officer_0_leadership', 'story_complete'):
            with self.subTest(key=key), self.assertRaises(SaveError):
                backend.stage(doc, {}, key, 1)
        body = bytearray(doc.payload)
        body[backend.CITY_BASE + backend.CITY_STRIDE] = 200
        unusual = backend.decode(codec.encode_layers(doc.header, bytes(body)))
        self.assertEqual(len(backend.fields_for(unusual)), 708)
        self.assertEqual(backend.serialize(unusual, {}), unusual.raw)
        self.assertEqual(backend.cities(unusual)[1]['district_reference'], 200)
        with self.assertRaises(SaveError):
            backend.stage(unusual, {}, 'city_1_money', 123)
        body[backend.CITY_BASE + backend.CITY_STRIDE] = 119
        high_district = backend.decode(codec.encode_layers(doc.header, bytes(body)))
        self.assertEqual(len(backend.fields_for(high_district)), 720)

    def test_population_components_and_surgical_last_city_edits(self):
        doc = self.document
        changes = {}
        for name, _label, _offset, _width, _group in backend.CITY_MEMBERS:
            key = f'city_59_{name}'
            changes = backend.stage(doc, changes, key, backend.field_map(doc)[key].maximum)
        changes = backend.stage(doc, changes, 'city_0_civilian_population', 1)
        changes = backend.stage(doc, changes, 'city_0_military_population', 999999999)
        result = backend.serialize(doc, changes)
        reopened = backend.decode(result)
        self.assertEqual(result[:codec.HEADER_SIZE], doc.raw[:codec.HEADER_SIZE])
        allowed = set()
        for key in changes:
            field = backend.field_map(doc)[key]
            allowed.update(range(codec.HEADER_SIZE + field.offset,
                                 codec.HEADER_SIZE + field.offset + field.size))
        touched = {index for index, (before, after) in enumerate(zip(doc.raw, result)) if before != after}
        self.assertLessEqual(touched, allowed)
        self.assertEqual(reopened.payload, backend.changed_payload(doc, changes))
        self.assertEqual(backend.cities(reopened)[59]['district_reference'], 0xFF)
        self.assertEqual(backend.cities(reopened)[0]['military_population'], 999999999)
        self.assertEqual(self.source.read_bytes(), doc.raw)
        self.assertEqual(len(backend.review(doc, changes)), len(changes))
        pending = backend.stage(doc, {}, 'city_0_money', 23)
        self.assertEqual(backend.stage(doc, pending, 'city_0_money', 0xF0000000), {})
        self.assertEqual(backend.maximums(doc, pending), pending)

    def test_snapshot_and_changes_are_validated_before_saving(self):
        doc = self.document
        for bad in (replace(doc, header=bytearray(doc.header)),
                    replace(doc, raw=bytearray(doc.raw)),
                    replace(doc, payload=doc.payload[:-1] + bytes([doc.payload[-1] ^ 1])),
                    replace(doc, header=doc.header[:-1] + bytes([doc.header[-1] ^ 1])),
                    replace(doc, format=replace(doc.format, id='rotk13_switch'))):
            with self.subTest(kind=type(bad).__name__), self.assertRaises(SaveError):
                backend.serialize(bad, {})
        for action in (backend.changed_payload, backend.serialize, backend.review, backend.maximums):
            with self.subTest(action=action.__name__), self.assertRaises(SaveError):
                action(doc, {'__unmapped__': 4})

    def test_backup_restore_source_alias_and_changed_copy(self):
        doc = self.document
        snapshot = backend.backup(doc)
        self.assertEqual(snapshot.read_bytes(), doc.raw)
        destination = self.folder / 'edited.s13'
        updated = backend.save_as(doc, {'city_59_supplies': 31}, destination)
        self.assertEqual(backend.field_map(updated)['city_59_supplies'].value(updated.payload), 31)
        self.assertEqual(self.source.read_bytes(), doc.raw)
        self.assertEqual(backend.restore(snapshot, self.folder / 'restored.s13').read_bytes(), doc.raw)
        for path in (destination, self.source):
            with self.subTest(path=path.name), self.assertRaises(FileExistsError):
                backend.save_as(doc, {}, path)
        alias = self.folder / 'alias.s13'
        try:
            alias.symlink_to(self.source)
        except (OSError, NotImplementedError):
            pass
        else:
            with self.assertRaises(FileExistsError):
                backend.save_as(doc, {}, alias)
        self.source.write_bytes(doc.raw[:-1] + bytes([doc.raw[-1] ^ 1]))
        with self.assertRaises(SaveError):
            backend.save_as(doc, {}, self.folder / 'changed-source.s13')
        self.assertFalse((self.folder / 'changed-source.s13').exists())
        # A self-consistent backup manifest does not authorize foreign save data.
        from koei_editor.shared.copy_storage import snapshot_backup
        foreign = snapshot_backup(bytes(codec.SAVE_SIZE), self.folder / 'foreign.s13', backend.GAME_ID)
        with self.assertRaises(SaveError):
            backend.restore(foreign, self.folder / 'foreign-restored.s13')
        self.assertFalse((self.folder / 'foreign-restored.s13').exists())

    def test_live_xiii_folders_and_resolved_aliases_are_rejected(self):
        from koei_editor.shared.save_safety import safe_path
        for path in ('/Documents/KoeiTecmo/San13',
                     '/Documents/KoeiTecmo/San13/EN_SAVEDATA/savedata01.s13',
                     r'C:\Users\Player\Documents\KoeiTecmo\San13\TC_SAVEDATA\savedata01.s13'):
            with self.subTest(path=path), self.assertRaises(SaveError):
                safe_path(path)
        live = self.folder / 'KoeiTecmo' / 'San13' / 'TC_SAVEDATA'
        live.mkdir(parents=True)
        campaign = live / 'savedata01.s13'
        campaign.write_bytes(self.document.raw)
        snapshot = backend.backup(self.document)
        for action in (lambda: backend.read_save(campaign),
                       lambda: backend.save_as(self.document, {}, live / 'new.s13'),
                       lambda: backend.restore(snapshot, live / 'restored.s13')):
            with self.assertRaises(SaveError):
                action()
        alias = self.folder / 'live-alias'
        try:
            alias.symlink_to(live, target_is_directory=True)
        except (OSError, NotImplementedError):
            pass
        else:
            with self.assertRaises(SaveError):
                backend.read_save(alias / 'savedata01.s13')
        self.assertEqual(campaign.read_bytes(), self.document.raw)
        self.assertEqual(list(live.iterdir()), [campaign])

    def test_registered_copied_save_self_test_preserves_all_fields(self):
        from koei_editor.shared.verified_self_test import run
        report = run(backend.GAME_ID, self.source, self.folder / 'self-test')
        self.assertTrue(report['success'])
        self.assertTrue(report['input_preserved'])
        self.assertTrue(report['backup_restored'])
        self.assertTrue(report['checksum_verified'])
        self.assertFalse(report['in_game_load_tested'])
        self.assertEqual(report['fields_checked'], 720)
        # No field has a demonstrated natural Max; this workflow tests copies,
        # while surgical manual edits are exercised separately above.
        self.assertEqual(report['fields_changed'], 0)


class XIIIContractTests(ScalarContractTests, unittest.TestCase):
    game_id = backend.GAME_ID

    def fixture_bytes(self):
        return procedural_raw()


class XIIINativeCopies(unittest.TestCase):
    def test_copied_native_unchanged_and_each_city_quantity(self):
        folder = os.environ.get('ROTK13_SAVE_COPIES')
        if not folder:
            self.skipTest('Set ROTK13_SAVE_COPIES to a folder of reviewed original PC campaign copies.')
        paths = sorted(Path(folder).glob('savedata*.s13'))
        self.assertTrue(paths, 'No copied native savedata*.s13 files found.')
        for path in paths:
            before_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            doc = backend.read_save(path)
            self.assertEqual(backend.serialize(doc, {}), doc.raw)
            self.assertEqual(codec.encode_layers(doc.header, doc.payload), doc.raw)
            fields = backend.field_map(doc)
            self.assertEqual(len(fields), 720)
            for name, _label, _offset, _width, _group in backend.CITY_MEMBERS:
                field = fields[f'city_0_{name}']
                value = field.value(doc.payload)
                target = value + 1 if value < field.maximum else value - 1
                changes = backend.stage(doc, {}, field.id, target)
                raw = backend.serialize(doc, changes)
                output = backend.decode(raw)
                self.assertEqual(field.value(output.payload), target)
                self.assertEqual(raw[:codec.HEADER_SIZE], doc.raw[:codec.HEADER_SIZE])
                touched = {index for index, (a, b) in enumerate(zip(doc.payload, output.payload)) if a != b}
                self.assertLessEqual(touched, set(range(field.offset, field.offset + field.size)))
                self.assertEqual(backend.stage(doc, changes, field.id, value), {})
            with tempfile.TemporaryDirectory() as temp:
                source = Path(temp) / 'native-copy.s13'
                source.write_bytes(doc.raw)
                copy = backend.read_save(source)
                updated = backend.save_as(copy, {'city_0_money': 1234}, Path(temp) / 'native-edit.s13')
                self.assertEqual(backend.field_map(updated)['city_0_money'].value(updated.payload), 1234)
                backups = list((Path(temp) / 'UniversalEditorBackups').glob('*.s13'))
                self.assertEqual(len(backups), 1)
                self.assertEqual(backups[0].read_bytes(), doc.raw)
                restored = backend.restore(backups[0], Path(temp) / 'native-restored.s13')
                self.assertEqual(restored.read_bytes(), doc.raw)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before_hash)
