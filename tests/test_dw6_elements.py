"""Existing DW6 weapon element choices, with surgical copy-only writes."""
import os
from pathlib import Path
import struct
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.dw6 import dw6_parser as backend
from tests.test_dw6_format import procedural_raw


class DW6WeaponElementTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / 'dw6-copy.dat'
        self.source.write_bytes(procedural_raw())
        self.document = backend.read_save(self.source)

    def test_named_existing_weapon_choice_map_and_last_officer_boundary(self):
        fields = [field for field in backend.fields_for(self.document)
                  if field.group == 'Weapon elements']
        self.assertEqual(len(fields), 41)
        first = fields[0]
        self.assertEqual(first.id, 'officer_0_weapon_0_element')
        self.assertEqual(first.offset, backend.OFFICER_BASE + 16)
        self.assertIn('Rock Crusher', first.label)
        self.assertEqual(backend.record_label(first.slot, first.group), 'Xiahou Dun / weapon 1')
        last = fields[-1]
        self.assertEqual(last.id, 'officer_40_weapon_0_element')
        self.assertEqual(last.offset, backend.OFFICER_BASE + 40 * backend.OFFICER_STRIDE + 16)
        self.assertEqual(backend.field_options(self.document, first.id),
                         ((0, 'Fire'), (1, 'Ice'), (2, 'Lightning'), (3, 'No element')))
        self.assertEqual(backend.field_options(self.document, 'officer_0_unlocked'), ())

    def test_each_choice_single_word_only_progression_inventory_and_skills_preserved(self):
        key = 'officer_0_weapon_0_element'
        original = self.document.raw
        field = backend.field_map(self.document)[key]
        for value in (0, 1, 2, 3):
            with self.subTest(element=value):
                changes = backend.stage(self.document, {}, key, value)
                updated = backend.serialize(self.document, changes)
                self.assertEqual(field.value(backend.decode(updated).payload), value)
                self.assertEqual(updated[:field.offset], original[:field.offset])
                self.assertEqual(updated[field.offset + 4:], original[field.offset + 4:])
                self.assertEqual(backend.stage(self.document, changes, key, 3), {})
        self.assertEqual(self.source.read_bytes(), original)

    def test_empty_unknown_identity_and_unknown_element_excluded(self):
        offset = backend.OFFICER_BASE + 8
        key = 'officer_0_weapon_0_element'
        for relative, value in ((0, 174), (0, 123), (0, 0xFFFFFFFF), (8, 4), (8, 0xFFFFFFFF)):
            with self.subTest(relative=relative, value=value):
                raw = bytearray(self.document.raw)
                struct.pack_into('<I', raw, offset + relative, value)
                document = backend.decode(raw)
                self.assertNotIn(key, backend.field_map(document))
                with self.assertRaises(SaveError):
                    backend.stage(document, {}, key, 0)
                serialized = backend.serialize(document, backend.maximums(document, {}))
                self.assertEqual(serialized[offset:offset + 16], raw[offset:offset + 16])
        with self.assertRaises(SaveError):
            backend.stage(self.document, {}, 'officer_0_weapon_1_element', 0)

    def test_choice_never_maximized_and_staged_choice_retained(self):
        key = 'officer_0_weapon_0_element'
        self.assertTrue(all(not field.maxable for field in backend.fields_for(self.document)
                            if field.group == 'Weapon elements'))
        self.assertEqual(backend.maximums(self.document, {}, 'Weapon elements'), {})
        staged = backend.stage(self.document, {}, key, 0)
        self.assertEqual(backend.maximums(self.document, staged, 'Weapon elements'), staged)
        after = backend.maximums(self.document, staged)
        self.assertEqual(after[key], 0)
        self.assertFalse(any('_element' in item for item in after if item != key))

    def test_invalid_choices_reject_and_review_keeps_native_values(self):
        key = 'officer_0_weapon_0_element'
        for value in (-1, 4, 0xFFFFFFFF, True, 1.0, 'Fire'):
            with self.subTest(value=value), self.assertRaises(SaveError):
                backend.stage(self.document, {}, key, value)
        changes = backend.stage(self.document, {}, key, 1)
        self.assertEqual([(field.id, before, after) for field, before, after in backend.review(self.document, changes)],
                         [(key, 3, 1)])
        with self.assertRaises(SaveError):
            backend.serialize(self.document, {'officer_0_weapon_0_id': 1})

    def test_save_backup_and_reopen_preserve_original(self):
        key = 'officer_40_weapon_0_element'
        destination = self.source.with_name('edited.dat')
        result = backend.save_as(self.document, {key: 2}, destination)
        self.assertEqual(backend.field_map(result)[key].value(result.payload), 2)
        self.assertEqual(self.source.read_bytes(), self.document.raw)
        backups = tuple((self.source.parent / 'WarriorsEditorBackups').glob('*.dat'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), self.document.raw)

    @unittest.skipUnless(os.environ.get('DW6_SAVE'), 'Private genuine native DW6 fixture not supplied')
    def test_genuine_known_elements_every_existing_field_surgical(self):
        source = Path(os.environ['DW6_SAVE'])
        original = source.read_bytes()
        document = backend.decode(original)
        self.assertEqual(backend.serialize(document, {}), original)
        fields = [field for field in backend.fields_for(document) if field.group == 'Weapon elements']
        self.assertGreater(len(fields), 0)
        observed = {field.value(document.payload) for field in fields}
        self.assertGreater(len(observed), 1)
        for field in fields:
            choice = (field.value(document.payload) + 1) % 4
            changed = backend.serialize(document, {field.id: choice})
            self.assertEqual(field.value(backend.decode(changed).payload), choice)
            self.assertEqual(changed[:field.offset], original[:field.offset])
            self.assertEqual(changed[field.offset + 4:], original[field.offset + 4:])
        self.assertEqual(source.read_bytes(), original)
