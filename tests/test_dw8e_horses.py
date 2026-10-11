"""DW8 Empires native SYSTEM horse sliders; public input is procedural."""
from dataclasses import replace
from functools import lru_cache
import os
from pathlib import Path
import struct
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.dw8e import dw8e_codec as codec
from koei_editor.games.dw8e import dw8e_parser as backend
from koei_editor.shared.koei_codec import byte_cipher, word_cipher, word_sum
from tests.scalar_contract import ScalarContractTests


def procedural_envelope(payload, seed=0x1234, prefix=None, damage_inner=False):
    body = byte_cipher(payload, codec.SYSTEM_SEED) + bytes([(sum(payload) + int(damage_inner)) & 255])
    header = bytearray((index * 11 + 17) & 255 for index in range(codec.BODY_OFFSET)) if prefix is None else bytearray(prefix)
    struct.pack_into('<HH', header, codec.CHECKSUM_OFFSET, word_sum(body), seed)
    return bytes(header) + word_cipher(body, seed)


@lru_cache(maxsize=1)
def procedural_raw():
    payload = bytearray((index * 19 + 13) & 255 for index in range(codec.PAYLOAD_SIZE))
    payload[:4] = codec.REVISION
    for identity in range(backend.HORSE_COUNT):
        start = backend.HORSE_BASE + identity * backend.HORSE_STRIDE
        payload[start:start + backend.HORSE_STRIDE] = bytes(backend.HORSE_STRIDE)
        struct.pack_into('<I', payload, start + 0x44, identity + 30)
    for identity, name in ((0, b'Test Horse'), (149, b'Final Horse')):
        start = backend.HORSE_BASE + identity * backend.HORSE_STRIDE
        payload[start] = 1
        payload[start + 2:start + 2 + len(name)] = name
        payload[start + 16:start + 23] = bytes([0, 1, 2, 3, 4, 0, 2] if identity == 0
                                             else [0, 3, 4, 0, 1, 4, 3])
        payload[start + 15] = 7
        payload[start + 30] = 0x9D
        struct.pack_into('<H', payload, start + 0x24, 275)
        struct.pack_into('<H', payload, start + 0x2A, 25)
        payload[start + 0x2E:start + 0x32] = bytes([0, 1, 2, 3])
    return procedural_envelope(bytes(payload))


class DW8EmpiresHorseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / 'system-copy.dat'
        self.source.write_bytes(procedural_raw())
        self.document = backend.read_save(self.source)

    def test_strict_system_title_size_both_checksums_and_row_identities(self):
        raw = self.document.raw
        self.assertEqual(backend.serialize(self.document, {}), raw)
        for bad in (None, [], b'', raw[:-1], raw + b'\0', bytes(1083236), bytes(len(raw))):
            with self.subTest(kind=type(bad).__name__), self.assertRaises(SaveError):
                codec.decode(bad)
        damaged = bytearray(raw)
        damaged[codec.BODY_OFFSET + 20] ^= 1
        with self.assertRaises(SaveError):
            backend.decode(damaged)
        with self.assertRaises(SaveError):
            backend.decode(procedural_envelope(self.document.payload, damage_inner=True))
        for offset, value in ((0, 0), (backend.HORSE_BASE + 0x44, 31),
                              (backend.HORSE_BASE + 149 * backend.HORSE_STRIDE + 0x44, 178)):
            changed = bytearray(self.document.payload)
            struct.pack_into('<I', changed, offset, value)
            with self.subTest(offset=offset), self.assertRaises(SaveError):
                backend.decode(procedural_envelope(bytes(changed)))

    def test_named_existing_body_choices_seven_inspected_sliders_and_native_boundaries(self):
        fields = backend.field_map(self.document)
        self.assertEqual(len(fields), 14)
        self.assertEqual(fields['horse_0_body'].offset, 0x38114)
        self.assertEqual(fields['horse_149_body'].offset,
                         backend.HORSE_BASE + 149 * 76 + 16)
        self.assertEqual(fields['horse_0_head'].offset, backend.HORSE_BASE + 0x11)
        self.assertIn('Test Horse', fields['horse_0_body'].label)
        rows = backend.horses(self.document)
        self.assertEqual(len(rows), 150)
        self.assertEqual(rows[0]['ordinal'], 30)
        self.assertEqual(rows[-1]['ordinal'], 179)
        self.assertEqual(rows[-1]['name'], 'Final Horse')

    def test_each_slider_surgical_all_stats_names_models_abilities_and_seed_retained(self):
        before = self.document
        for field in backend.fields_for(before):
            value = next(value for value, _ in backend.field_options(before, field.id)
                         if value != field.value(before.payload))
            result = backend.decode(backend.serialize(before, {field.id: value}))
            self.assertEqual(result.seed, before.seed)
            self.assertEqual(field.value(result.payload), value)
            self.assertEqual(result.payload[:field.offset], before.payload[:field.offset])
            self.assertEqual(result.payload[field.offset + 1:], before.payload[field.offset + 1:])
            self.assertEqual(result.raw[:codec.CHECKSUM_OFFSET], before.raw[:codec.CHECKSUM_OFFSET])
            self.assertEqual(result.raw[codec.SEED_OFFSET:codec.BODY_OFFSET],
                             before.raw[codec.SEED_OFFSET:codec.BODY_OFFSET])
        self.assertEqual(self.source.read_bytes(), before.raw)

    def test_empty_unknown_flags_and_unusual_slider_preserved_without_manufacture(self):
        for relative, value in ((0, 0), (0, 2), (0, 255), (16, 9)):
            payload = bytearray(self.document.payload)
            payload[backend.HORSE_BASE + relative] = value
            doc = backend.decode(procedural_envelope(bytes(payload)))
            self.assertNotIn('horse_0_body', backend.field_map(doc))
            with self.assertRaises(SaveError):
                backend.stage(doc, {}, 'horse_0_body', 4)
            self.assertEqual(backend.serialize(doc, {}), doc.raw)
        with self.assertRaises(SaveError):
            backend.stage(self.document, {}, 'horse_1_body', 4)
        for key in ('horse_0_used', 'horse_0_model', 'horse_0_speed', 'horse_0_name',
                    'horse_0_abilities'):
            with self.subTest(key=key), self.assertRaises(SaveError):
                backend.stage(self.document, {}, key, 1)

    def test_choices_no_max_invalid_values_and_original_unstage(self):
        doc = self.document
        staged = backend.stage(doc, {}, 'horse_0_body', 3)
        self.assertEqual(backend.stage(doc, staged, 'horse_0_body', 0), {})
        self.assertEqual(backend.maximums(doc, staged), staged)
        self.assertEqual(backend.maximums(doc, {}), {})
        self.assertTrue(all(not field.maxable for field in backend.fields_for(doc)))
        for value in (-1, 5, True, 1.0, '1'):
            with self.subTest(value=value), self.assertRaises(SaveError):
                backend.stage(doc, {}, 'horse_0_body', value)
        with self.assertRaises(SaveError):
            backend.maximums(doc, {'horse_0_body': 5})
        self.assertEqual([(field.id, before, after) for field, before, after in backend.review(doc, staged)],
                         [('horse_0_body', 0, 3)])

    def test_frozen_original_payload_seed_and_identity_before_edit(self):
        class EqualFormat:
            def __eq__(self, other):
                return True

        doc = self.document
        for forged in (replace(doc, raw=bytearray(doc.raw)), replace(doc, payload=bytearray(doc.payload)),
                       replace(doc, seed=False), replace(doc, seed=doc.seed ^ 1),
                       replace(doc, format=replace(doc.format, id='dw8xl')), replace(doc, format=EqualFormat()),
                       replace(doc, payload=doc.payload[:-1] + bytes([doc.payload[-1] ^ 1]))):
            with self.assertRaises(SaveError):
                backend.serialize(forged, {})

    def test_malformed_pending_edits_reject_before_new_stage_or_unstage(self):
        for pending in (None, [], [('horse_0_body', 1)], 'horse_0_body',
                        {'unknown': 1}, {'horse_0_body': True}, {'horse_0_body': 5}):
            for value in (0, 4):
                with self.subTest(pending=pending, value=value), self.assertRaises(SaveError):
                    backend.stage(self.document, pending, 'horse_0_body', value)
            with self.assertRaises(SaveError):
                backend.serialize(self.document, pending)

    def test_malformed_requested_field_ids_raise_save_error_without_staging(self):
        pending = {'horse_0_body': 3}
        for key in ([], {}, None, True, 1):
            with self.subTest(key=key), self.assertRaises(SaveError):
                backend.stage(self.document, pending, key, 0)
            with self.subTest(max_key=key), self.assertRaises(SaveError):
                backend.limit_values(self.document, pending, [key])
        self.assertEqual(pending, {'horse_0_body': 3})
        self.assertEqual(self.document.raw, procedural_raw())

    def test_backup_restored_exact_original_new_copy_and_changed_source(self):
        backup = backend.backup(self.document)
        changed = backend.save_as(self.document, {'horse_0_body': 4}, self.folder / 'edited.dat')
        self.assertEqual(backend.field_map(changed)['horse_0_body'].value(changed.payload), 4)
        self.assertEqual(self.source.read_bytes(), self.document.raw)
        restored = backend.restore(backup, self.folder / 'restored.dat')
        self.assertEqual(restored.read_bytes(), self.document.raw)
        with self.assertRaises(FileExistsError):
            backend.save_as(self.document, {}, changed.source)
        self.source.write_bytes(self.document.raw[:-1] + bytes([self.document.raw[-1] ^ 1]))
        with self.assertRaises(SaveError):
            backend.save_as(self.document, {}, self.folder / 'changed-source.dat')

    @unittest.skipUnless(os.environ.get('DW8E_SYSTEM_COPY'), 'Private genuine PC SystemSave not supplied')
    def test_genuine_native_system_every_existing_slider_only_and_exact_roundtrip(self):
        source = Path(os.environ['DW8E_SYSTEM_COPY'])
        raw = source.read_bytes()
        doc = backend.decode(raw)
        self.assertEqual(backend.serialize(doc, {}), raw)
        self.assertEqual(len(backend.horses(doc)), 150)
        self.assertGreater(len(backend.fields_for(doc)), 0)
        for field in backend.fields_for(doc):
            value = next((value for value, _ in backend.field_options(doc, field.id)
                          if value != field.value(doc.payload)), None)
            if value is None:
                continue  # Single witnessed positions remain unchanged.
            result = backend.decode(backend.serialize(doc, {field.id: value}))
            self.assertEqual(result.payload[:field.offset], doc.payload[:field.offset])
            self.assertEqual(result.payload[field.offset + 1:], doc.payload[field.offset + 1:])
            self.assertEqual(result.seed, doc.seed)
        self.assertEqual(source.read_bytes(), raw)


class DW8EmpiresHorseContract(ScalarContractTests, unittest.TestCase):
    game_id = 'dw8e'

    def fixture_bytes(self):
        return procedural_raw()
