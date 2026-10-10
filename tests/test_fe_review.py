"""Independent adversarial FE Warriors review; no console execution."""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.fire_emblem_warriors import parser as fe
from koei_editor.games.fire_emblem_warriors.catalog import MATERIALS
from tests.test_fire_emblem_warriors import procedural_fe


class FireEmblemIndependentReviewTests(unittest.TestCase):
    def test_snapshot_subclasses_and_mutable_forged_payload_reject(self):
        class ForeignDocument(fe.Document):
            pass
        raw = procedural_fe()
        document = fe.decode(raw)
        for bad in (ForeignDocument(document.format, document.source, raw, raw),
                    replace(document, raw=bytearray(raw)),
                    replace(document, payload=bytearray(raw)),
                    replace(document, payload=raw[:-1] + bytes([raw[-1] ^ 1]))):
            with self.subTest(kind=type(bad).__name__), self.assertRaises(SaveError):
                fe.maximums(bad, {})

    def test_all_pending_changes_reject_before_bulk_and_no_slot_fabrication(self):
        document = fe.decode(procedural_fe())
        for changes in ({'gold': False}, {'gold': -1}, {'gold': 10000000},
                        {'gold': '1'}, {'weapon_1_seal_1_kos': 1001},
                        {'weapon_2_stars': 5}, {'weapon_600_stars': 5},
                        {'material_48': 999}, {'story_complete': 1}):
            for operation in (lambda: fe.maximums(document, changes),
                              lambda: fe.limit_values(document, changes, ['gold']),
                              lambda: fe.review(document, changes)):
                with self.subTest(changes=changes), self.assertRaises(SaveError):
                    operation()

    def test_high_opened_values_unchanged_by_max_and_original_can_be_unstaged(self):
        raw = bytearray(procedural_fe())
        raw[fe.GOLD_OFFSET:fe.GOLD_OFFSET + 4] = (10000001).to_bytes(4, 'little')
        raw = bytes(raw)
        document = fe.decode(raw)
        changes = fe.maximums(document, {})
        self.assertNotIn('gold', changes)
        self.assertNotIn('material_46', changes)
        self.assertNotIn('weapon_3_stars', changes)
        output = fe.serialize(document, changes)
        for field_id in ('gold', 'material_46', 'weapon_3_stars'):
            field = fe.field_map(document)[field_id]
            self.assertEqual(field.value(output), field.value(raw))
            smaller = fe.stage(document, {}, field_id, field.minimum)
            self.assertEqual(fe.stage(document, smaller, field_id, field.value(raw)), {})

    def test_unique_amiibo_weapons_special_seals_and_header_remain_opaque(self):
        raw = bytearray(procedural_fe())
        # Recognized unique sword; its scroll/opus power progression is not stars.
        raw[fe.WEAPON_OFFSET + 24:fe.WEAPON_OFFSET + 26] = (5).to_bytes(2, 'little')
        raw[8:40] = bytes((index * 37 + 61) & 255 for index in range(32))
        raw = bytes(raw)
        document = fe.decode(raw)
        self.assertNotIn('weapon_1_stars', fe.field_map(document))
        self.assertNotIn('weapon_1_seal_2_kos', fe.field_map(document))
        self.assertNotIn('weapon_1_seal_3_kos', fe.field_map(document))
        output = fe.serialize(document, fe.maximums(document, {}))
        self.assertEqual(output[:40], raw[:40])
        self.assertEqual(output[fe.WEAPON_OFFSET + 2:fe.WEAPON_OFFSET + 32],
                         raw[fe.WEAPON_OFFSET + 2:fe.WEAPON_OFFSET + 32])
        for offset, name in MATERIALS:
            if not fe._ordinary(name):
                self.assertEqual(output[offset:offset + 2], raw[offset:offset + 2])

    def test_stars_preserve_other_weapon_fields_and_seals_only_decrease(self):
        raw = procedural_fe()
        document = fe.decode(raw)
        stars = fe.serialize(document, {'weapon_1_stars': 5})
        self.assertEqual(stars[:fe.WEAPON_OFFSET + 26], raw[:fe.WEAPON_OFFSET + 26])
        self.assertEqual(stars[fe.WEAPON_OFFSET + 27:], raw[fe.WEAPON_OFFSET + 27:])
        reduced = fe.serialize(document, {'weapon_1_seal_1_kos': 0})
        self.assertEqual(reduced[:fe.WEAPON_OFFSET], raw[:fe.WEAPON_OFFSET])
        self.assertEqual(reduced[fe.WEAPON_OFFSET + 2:], raw[fe.WEAPON_OFFSET + 2:])
        for value in (-1, True, 1001):
            with self.assertRaises(SaveError):
                fe.serialize(document, {'weapon_1_seal_1_kos': value})

    def test_source_transplant_suffix_existing_destination_and_backup_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / 'scenario0'
            raw = procedural_fe()
            source.write_bytes(raw)
            document = fe.read_save(source)
            foreign = folder / 'foreign'
            foreign.write_bytes(raw[:100] + bytes([raw[100] ^ 1]) + raw[101:])
            with self.assertRaises(SaveError):
                fe.save_as(replace(document, source=foreign), {'gold': 123}, folder / 'transplanted')
            self.assertFalse((folder / 'transplanted').exists())
            with self.assertRaises(SaveError):
                fe.save_as(document, {}, folder / 'edited.bin')
            destination = folder / 'edited'
            reopened = fe.save_as(document, {'gold': 123}, destination)
            self.assertEqual(reopened.raw, destination.read_bytes())
            with self.assertRaises(FileExistsError):
                fe.save_as(document, {'gold': 456}, destination)
            snapshot = fe.backup(document)
            self.assertEqual(fe.restore(snapshot, folder / 'restored').read_bytes(), raw)
            self.assertEqual(source.read_bytes(), raw)

    def test_restore_rejects_same_size_foreign_bytes_even_after_manifest_rehash(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / 'scenario0'
            source.write_bytes(procedural_fe())
            snapshot = fe.backup(fe.read_save(source))
            wrong = b'\0' * fe.SAVE_SIZE
            snapshot.write_bytes(wrong)
            manifest_path = snapshot.with_suffix('.json')
            manifest = json.loads(manifest_path.read_text())
            manifest['sha256'] = hashlib.sha256(wrong).hexdigest()
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaises(SaveError):
                fe.restore(snapshot, folder / 'restored')
            self.assertFalse((folder / 'restored').exists())

    @unittest.skipUnless(os.environ.get('FE_WARRIORS_SAVE_COPY'), 'No private genuine FE Warriors export')
    def test_genuine_all_positive_fields_surgical_without_changing_player_copy(self):
        path = Path(os.environ['FE_WARRIORS_SAVE_COPY'])
        raw = path.read_bytes()
        document = fe.decode(raw)
        self.assertEqual(fe.serialize(document, {}), raw)
        count = 0
        for field in fe.fields_for(document):
            original = field.value(raw)
            if original <= 0:
                continue
            value = max(field.minimum, min(original - 1, field.maximum))
            output = fe.serialize(document, fe.stage(document, {}, field.id, value))
            touched = {i for i, (before, after) in enumerate(zip(raw, output)) if before != after}
            self.assertLessEqual(touched, set(range(field.offset, field.offset + field.size)))
            self.assertEqual(output[:40], raw[:40])
            self.assertEqual(field.value(fe.decode(output).payload), value)
            count += 1
        self.assertGreater(count, 100)
        self.assertEqual(path.read_bytes(), raw)
