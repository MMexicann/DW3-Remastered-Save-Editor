"""DW9 Empires procedural profile checks; no independent/game-load claims."""
from dataclasses import replace
from functools import lru_cache
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.dw9emp import dw9emp_codec as codec
from koei_editor.games.dw9emp import dw9emp_parser as backend
from tests.scalar_contract import ScalarContractTests


@lru_cache(maxsize=1)
def procedural_raw():
    raw = bytearray((index * 31 + 17) & 255 for index in range(codec.SAVE_SIZE))
    struct.pack_into('<I', raw, 0, codec.REVISION)
    raw[4:1604] = bytes(1600)
    for identity, quantity in ((0, 3), (7, 999), (799, 17), (798, 65535)):
        struct.pack_into('<H', raw, 4 + 2 * identity, quantity)
    raw[backend.CAW_BASE:backend.CAW_BASE + backend.CAW_COUNT * backend.CAW_STRIDE] = bytes(
        backend.CAW_COUNT * backend.CAW_STRIDE)
    first = backend.CAW_BASE
    raw[first:first + 2] = b'\x01\x04'
    struct.pack_into('<8H', raw, first + 2, 11, 22, 33, 44, 55, 66, 77, 65535)
    raw[first + 21:first + 33] = b'Test Officer'
    last = backend.CAW_BASE + (backend.CAW_COUNT - 1) * backend.CAW_STRIDE
    raw[last + 21:last + 24] = b'\xff\n\x01'
    return bytes(raw)


class DW9EmpFormatTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / 'system-copy.bin'
        self.source.write_bytes(procedural_raw())
        self.document = backend.read_save(self.source)

    def test_current_native_component_order_and_complete_capacity_budget(self):
        # These fixed expectations record independent native cursor/count evidence.
        self.assertEqual(codec.CAW_BASE, 0x1E137F)
        self.assertEqual(codec.CAW_STRIDE, 0x212)
        self.assertEqual(codec.CAW_COUNT, 900)
        self.assertEqual(codec.SERIALIZED_END, 0x27F1C8)
        self.assertEqual(codec.CAPACITY_TAIL_SIZE, 0x72A60)
        self.assertEqual(codec.SERIALIZED_END + codec.CAPACITY_TAIL_SIZE, codec.SAVE_SIZE)
        self.assertNotIn('63ACA0', [name for name, _count, _width in codec.SERIALIZED_PREFIX])
        self.assertIn('63ACA0', [name for name, _count, _width in codec.SERIALIZED_SUFFIX])

    def test_narrow_native_profile_and_plaintext_roundtrip(self):
        self.assertEqual(codec.decode(procedural_raw()), procedural_raw())
        self.assertEqual(codec.encode(codec.decode(procedural_raw())), procedural_raw())
        self.assertFalse(codec.HAS_NATIVE_CHECKSUM)
        self.assertFalse(backend.FORMAT.sample_verified)
        self.assertFalse(backend.FORMAT.game_load_verified)
        for raw in (None, 1, [0] * codec.SAVE_SIZE, b'', procedural_raw()[:-1],
                    procedural_raw() + b'\0', bytes(codec.SAVE_SIZE),
                    bytes(0x317B03), bytes(0xFD953)):
            with self.subTest(kind=type(raw).__name__), self.assertRaises(SaveError):
                codec.decode(raw)
        for version in (0x200831F0, 0x210514F0, 0x21060200, 0x2106020F,
                        0x210602F1, 0x11080200):
            raw = bytearray(procedural_raw())
            struct.pack_into('<I', raw, 0, version)
            with self.subTest(version=hex(version)), self.assertRaises(SaveError):
                codec.decode(raw)
        # A multidimensional view's len() reports its first dimension, not bytes.
        doubled = procedural_raw() + procedural_raw()
        shaped = memoryview(doubled).cast('B', shape=(codec.SAVE_SIZE, 2))
        with self.assertRaises(SaveError):
            codec.decode(shaped)

    def test_dynamic_existing_only_quantities_and_surgical_edits(self):
        doc = self.document
        self.assertEqual({field.id for field in backend.fields_for(doc)},
                         {'item_0_quantity', 'item_7_quantity', 'item_799_quantity'})
        mapping = backend.field_map(doc)
        with self.assertRaises(TypeError):
            mapping['invented'] = mapping['item_0_quantity']
        for key in ('item_1_quantity', 'item_798_quantity', 'item_800_quantity'):
            with self.subTest(key=key), self.assertRaises(SaveError):
                backend.stage(doc, {}, key, 999)
        changes = backend.stage(doc, {}, 'item_0_quantity', 123)
        self.assertEqual(backend.stage(doc, changes, 'item_0_quantity', 3), {})
        updated = backend.serialize(doc, changes)
        self.assertEqual(updated[:4], doc.raw[:4])
        self.assertEqual(updated[6:], doc.raw[6:])
        self.assertEqual(struct.unpack_from('<H', updated, 4)[0], 123)
        self.assertEqual(backend.serialize(doc, {}), doc.raw)
        self.assertEqual(backend.decode(updated).payload, updated)
        self.assertEqual(self.source.read_bytes(), doc.raw)

    def test_manual_only_quantities_bulk_preserves_all_categories_and_bytes(self):
        doc = self.document
        changes = backend.maximums(doc, {})
        self.assertEqual(changes, {})
        self.assertTrue(all(not field.maxable for field in backend.fields_for(doc)))
        staged = {'item_0_quantity': 45}
        self.assertEqual(backend.maximums(doc, staged), staged)
        updated = backend.serialize(doc, changes)
        rows = backend.items(backend.decode(updated))
        self.assertEqual(len(rows), 800)
        self.assertEqual(rows[1]['quantity'], 0)
        self.assertEqual(rows[798]['quantity'], 65535)
        self.assertEqual(rows[799]['quantity'], 17)
        self.assertEqual(updated, doc.raw)
        self.assertEqual(updated[1604:], doc.raw[1604:])
        self.assertEqual(backend.maximums(doc, {}, 'Story'), {})
        for value in (0, -1, 1000, True, 1.0, '3'):
            with self.subTest(value=value), self.assertRaises(SaveError):
                backend.stage(doc, {}, 'item_0_quantity', value)
        with self.assertRaises(SaveError):
            backend.serialize(doc, {'item_1_quantity': 999})
        with self.assertRaises(SaveError):
            backend.maximums(doc, {'item_1_quantity': 999})

    def test_frozen_snapshot_integrity_and_boolean_seed(self):
        doc = self.document
        forged = (replace(doc, raw=bytearray(doc.raw)),
                  replace(doc, payload=bytearray(doc.payload)),
                  replace(doc, seed=False), replace(doc, seed=1),
                  replace(doc, format=replace(doc.format, id='dw9')),
                  replace(doc, payload=doc.payload[:-1] + bytes([doc.payload[-1] ^ 1])))
        for candidate in forged:
            with self.subTest(seed=candidate.seed), self.assertRaises(SaveError):
                backend.serialize(candidate, {})

    def test_custom_officer_names_flags_and_values_remain_read_only(self):
        rows = backend.custom_officers(self.document)
        self.assertEqual(len(rows), 900)
        self.assertEqual(rows[0]['name_preview'], 'Test Officer')
        self.assertEqual(rows[0]['flags'], (1, 4))
        self.assertEqual(rows[0]['stored_values'], (11, 22, 33, 44, 55, 66, 77, 65535))
        self.assertEqual(rows[1]['name_preview'], '(empty name)')
        self.assertIn('\\xff', rows[-1]['name_preview'])
        self.assertNotIn('\n', rows[-1]['name_preview'])
        for key in ('caw_0_name', 'caw_0_flags', 'caw_0_proficiency'):
            with self.subTest(key=key), self.assertRaises(SaveError):
                backend.stage(self.document, {}, key, 999)
        edited = backend.serialize(self.document, backend.maximums(self.document, {}))
        self.assertEqual(backend.custom_officers(backend.decode(edited)), rows)

    def test_copy_only_paths_aliases_and_existing_destinations(self):
        live = self.folder / 'Documents' / 'KoeiTecmo' / 'Dynasty Warriors 9 Empires' / 'SYSTEMDATA'
        live.mkdir(parents=True)
        native = live / 'SAVEDATA.BIN'
        native.write_bytes(self.document.raw)
        with self.assertRaises(SaveError):
            backend.read_save(native)
        alias = self.folder / 'alias'
        try:
            alias.symlink_to(live, target_is_directory=True)
        except OSError:
            # Windows may require developer mode or elevation for symlinks.
            pass
        else:
            with self.assertRaises(SaveError):
                backend.read_save(alias / 'SAVEDATA.BIN')
            with self.assertRaises(SaveError):
                backend.save_as(self.document, {}, alias / 'output.bin')
        with self.assertRaises(FileExistsError):
            backend.save_as(self.document, {}, self.source)
        with self.assertRaises(SaveError):
            backend.read_save(self.folder / 'wrong.dat')

    def test_backup_restore_save_as_and_changed_source(self):
        doc = self.document
        backup = backend.backup(doc)
        self.assertEqual(backup.read_bytes(), doc.raw)
        restored = backend.restore(backup, self.folder / 'restored.bin')
        self.assertEqual(restored.read_bytes(), doc.raw)
        edited = backend.save_as(doc, {'item_0_quantity': 45}, self.folder / 'edited.bin')
        self.assertEqual(backend.field_map(edited)['item_0_quantity'].value(edited.payload), 45)
        self.assertEqual(self.source.read_bytes(), doc.raw)
        self.source.write_bytes(doc.raw[:-1] + bytes([doc.raw[-1] ^ 1]))
        target = self.folder / 'changed-source.bin'
        with self.assertRaises(SaveError):
            backend.save_as(doc, {}, target)
        self.assertFalse(target.exists())

    def test_restore_validates_the_exact_bytes_used_for_write(self):
        doc = self.document
        backup = backend.backup(doc)
        real_restore = backend.restore_snapshot
        destination = self.folder / 'forged-restore.bin'

        def replace_snapshot_then_restore(*args, **kwargs):
            altered = bytearray(doc.raw)
            altered[:4] = b'junk'
            backup.write_bytes(altered)
            manifest = backup.with_suffix('.json')
            record = json.loads(manifest.read_text(encoding='utf-8'))
            import hashlib
            record['sha256'] = hashlib.sha256(altered).hexdigest()
            manifest.write_text(json.dumps(record), encoding='utf-8')
            return real_restore(*args, **kwargs)

        with patch.object(backend, 'restore_snapshot', side_effect=replace_snapshot_then_restore):
            with self.assertRaises(SaveError):
                backend.restore(backup, destination)
        self.assertFalse(destination.exists())

    @unittest.skipUnless(os.environ.get('DW9EMP_SYSTEM_COPY'),
                         'No independent native DW9 Empires SYSTEMDATA copy supplied.')
    def test_optional_native_roundtrip_and_existing_quantity_edit(self):
        doc = backend.read_save(Path(os.environ['DW9EMP_SYSTEM_COPY']))
        self.assertEqual(backend.serialize(doc, {}), doc.raw)
        fields = backend.fields_for(doc)
        self.assertTrue(fields, 'A native sample with an existing quantity is required.')
        field = fields[0]
        original = field.value(doc.payload)
        target = 998 if original != 998 else 997
        updated = backend.serialize(doc, {field.id: target})
        self.assertEqual(backend.field_map(backend.decode(updated))[field.id].value(updated), target)
        self.assertEqual(updated[:field.offset], doc.raw[:field.offset])
        self.assertEqual(updated[field.offset + field.size:], doc.raw[field.offset + field.size:])
        self.assertEqual(doc.source.read_bytes(), doc.raw)


class DW9EmpScalarContractTests(ScalarContractTests, unittest.TestCase):
    game_id = 'dw9emp'

    def fixture_bytes(self):
        return procedural_raw()
