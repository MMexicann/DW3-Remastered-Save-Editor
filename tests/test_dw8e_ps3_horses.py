"""DW8E US PS3 SYSTEM controls; public fixtures are procedural, never player saves."""
from dataclasses import replace
from functools import lru_cache
import os
from pathlib import Path
import struct
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.dw8e_ps3 import codec
from koei_editor.games.dw8e_ps3 import parser as backend
from koei_editor.shared.koei_codec import byte_cipher
from koei_editor.shared.adapter_contract import BoundScalarAdapter
from tests import test_ps3_expansion as context_tests


def procedural_envelope(payload, damage_inner=False):
    return byte_cipher(payload, codec.SYSTEM_SEED) + bytes([(sum(payload) + int(damage_inner)) & 255])


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
        payload[start + 16:start + 23] = bytes([0, 1, 2, 3, 4, 0, 2])
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
        self.source = self.folder / 'APP.BIN'
        (self.folder / 'PARAM.SFO').write_bytes(context_tests.PS3ContextTests.metadata('NPUB31656-SYSTEM'))
        self.source.write_bytes(procedural_raw())
        self.document = backend.read_save(self.source)

    def test_strict_system_title_size_checksum_and_row_identities(self):
        raw = self.document.raw
        self.assertEqual(backend.serialize(self.document, {}), raw)
        for bad in (None, [], b'', raw[:-1], raw + b'\0', bytes(1083236), bytes(len(raw))):
            with self.subTest(kind=type(bad).__name__), self.assertRaises(SaveError):
                codec.decode(bad)
        damaged = bytearray(raw)
        damaged[20] ^= 1
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
        self.assertEqual(len(fields), 2)
        self.assertEqual(fields['horse_0_body'].offset, 0x39BA4)
        self.assertEqual(fields['horse_149_body'].offset,
                         backend.HORSE_BASE + 149 * 76 + 16)
        self.assertNotIn('horse_0_head', fields)
        self.assertIn('Test Horse', fields['horse_0_body'].label)
        rows = backend.horses(self.document)
        self.assertEqual(len(rows), 150)
        self.assertEqual(rows[0]['ordinal'], 30)
        self.assertEqual(rows[-1]['ordinal'], 179)
        self.assertEqual(rows[-1]['name'], 'Final Horse')

    def test_each_body_field_surgical_all_stats_names_models_abilities_and_seed_retained(self):
        before = self.document
        for field in backend.fields_for(before):
            value = (field.value(before.payload) + 1) % 5
            result = backend.decode(backend.serialize(before, {field.id: value}))
            self.assertEqual(result.seed, before.seed)
            self.assertEqual(field.value(result.payload), value)
            self.assertEqual(result.payload[:field.offset], before.payload[:field.offset])
            self.assertEqual(result.payload[field.offset + 1:], before.payload[field.offset + 1:])
        self.assertEqual(self.source.read_bytes(), before.raw)

    def test_empty_unknown_flags_and_unusual_slider_preserved_without_manufacture(self):
        for relative, value in ((0, 0), (0, 2), (0, 255), (16, 9), (15, 19), (30, 62)):
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
                    'horse_0_abilities', 'horse_0_head', 'horse_0_muscle'):
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

    def test_backup_restored_exact_original_new_copy_and_changed_source(self):
        backup = backend.backup(self.document)
        changed = backend.save_as(self.document, {'horse_0_body': 4}, self.folder / 'edited.bin')
        self.assertEqual(backend.field_map(changed)['horse_0_body'].value(changed.payload), 4)
        self.assertEqual(self.source.read_bytes(), self.document.raw)
        restored = backend.restore(backup, self.folder / 'restored.bin')
        self.assertEqual(restored.read_bytes(), self.document.raw)
        with self.assertRaises(FileExistsError):
            backend.save_as(self.document, {}, changed.source)
        self.source.write_bytes(self.document.raw[:-1] + bytes([self.document.raw[-1] ^ 1]))
        with self.assertRaises(SaveError):
            backend.save_as(self.document, {}, self.folder / 'changed-source.bin')

    @unittest.skipUnless(os.environ.get('DW8E_PS3_SYSTEM_COPY'), 'Private genuine US PS3 SYSTEM export not supplied')
    def test_genuine_native_system_every_qualified_body_field_only_and_exact_roundtrip(self):
        source = Path(os.environ['DW8E_PS3_SYSTEM_COPY'])
        raw = source.read_bytes()
        backend._context(source, required=True)
        doc = backend.decode(raw)
        self.assertEqual(backend.serialize(doc, {}), raw)
        self.assertEqual(len(backend.horses(doc)), 150)
        self.assertGreater(len(backend.fields_for(doc)), 0)
        for field in backend.fields_for(doc):
            value = (field.value(doc.payload) + 1) % 5
            result = backend.decode(backend.serialize(doc, {field.id: value}))
            self.assertEqual(result.payload[:field.offset], doc.payload[:field.offset])
            self.assertEqual(result.payload[field.offset + 1:], doc.payload[field.offset + 1:])
            self.assertEqual(result.seed, doc.seed)
        self.assertEqual(source.read_bytes(), raw)

    def test_mandatory_exact_us_system_context_and_changed_context_rejection(self):
        companion = self.folder / 'PARAM.SFO'
        for identity in ('NPUB31656-EMPIRE3', 'NPEB02103-SYSTEM', 'NPJB00686-SYSTEM'):
            companion.write_bytes(context_tests.PS3ContextTests.metadata(identity))
            with self.assertRaises(SaveError):
                backend.read_save(self.source)
            with self.assertRaises(SaveError):
                backend.save_as(self.document, {}, self.folder / 'rejected.bin')
        companion.unlink()
        with self.assertRaises(SaveError):
            backend.read_save(self.source)
        with self.assertRaises(SaveError):
            backend.restore(backend.backup(self.document), self.folder / 'missing-context.bin')

    def test_bound_adapter_identity_contract_and_unknown_original_preservation(self):
        adapter = BoundScalarAdapter('dw8e_ps3', '.bin', backend)
        self.assertEqual(adapter.serialize(self.document, {}), self.document.raw)
        with self.assertRaises(SaveError):
            adapter.decode(self.document.raw, 'dw8e')
        with self.assertRaises(SaveError):
            adapter.decode(self.document.raw, 'dw8e_ps3', Path('SystemSave.dat'))
        with self.assertRaises(SaveError):
            adapter.stage(self.document, {}, 'campaign_gold', 99999)

    def test_save_destination_without_exact_metadata_rejected_before_write(self):
        folder = self.folder / 'other-output-folder'
        folder.mkdir()
        destination = folder / 'edited.bin'
        with self.assertRaises(SaveError):
            backend.save_as(self.document, {'horse_0_body': 4}, destination)
        self.assertFalse(destination.exists())
        self.assertEqual(self.source.read_bytes(), self.document.raw)
        (folder / 'PARAM.SFO').write_bytes(context_tests.PS3ContextTests.metadata('NPUB31656-SYSTEM'))
        backend.save_as(self.document, {'horse_0_body': 4}, destination)
        self.assertEqual(backend.field_map(backend.read_save(destination))['horse_0_body'].value(
            backend.read_save(destination).payload), 4)

    def test_private_copy_context_preserves_opaque_original_and_rejects_existing_output(self):
        metadata_path = self.folder / 'PARAM.SFO'
        # Extra private metadata bytes stay opaque and are copied byte-exact.
        metadata = metadata_path.read_bytes() + b'opaque-test-context\0\xAA\xBB'
        metadata_path.write_bytes(metadata)
        self.document = backend.read_save(self.source)
        folder = self.folder / 'context-only'
        prepared = backend.prepare_copy_context(self.document, folder)
        self.assertEqual(prepared.read_bytes(), metadata)
        self.assertEqual(metadata_path.read_bytes(), metadata)
        with self.assertRaises(FileExistsError):
            backend.prepare_copy_context(self.document, folder)
        metadata_path.write_bytes(context_tests.PS3ContextTests.metadata('NPUB31656-EMPIRE3'))
        with self.assertRaises(SaveError):
            backend.prepare_copy_context(self.document, self.folder / 'foreign-context')
        self.assertFalse((self.folder / 'foreign-context' / 'PARAM.SFO').exists())

    def test_registered_self_test_propagates_original_context_without_game_load_claim(self):
        from koei_editor.shared.verified_self_test import run
        metadata = (self.folder / 'PARAM.SFO').read_bytes()
        output = self.folder / 'self-test'
        report = run('dw8e_ps3', self.source, output)
        self.assertTrue(report['success'])
        self.assertTrue(report['native_integrity_verified'])
        self.assertTrue(report['checksum_verified'])
        self.assertFalse(report['in_game_load_tested'])
        self.assertEqual((output / 'PARAM.SFO').read_bytes(), metadata)
        self.assertEqual((self.folder / 'PARAM.SFO').read_bytes(), metadata)
        self.assertEqual(self.source.read_bytes(), self.document.raw)
        self.assertEqual((output / 'restored.BIN').read_bytes(), self.document.raw)
