"""Independent adversarial review of original Windows classic Musou adapters."""
from dataclasses import replace
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.application import Application
from koei_editor.games.dw3.models import SaveError
from koei_editor.games.sw2 import sw2_parser as sw2
from koei_editor.games.wo1_pc import wo1_codec, wo1_parser as wo1
from tests.test_sw2_pc_format import procedural_raw as sw2_fixture, checksum as sw2_checksum
from tests.test_wo1_pc_format import procedural_raw as wo1_fixture


class FrozenClassicSnapshotReview:
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / 'input-copy.dat'
        self.raw = self.fixture_bytes()
        self.source.write_bytes(self.raw)
        self.document = self.backend.read_save(self.source)
        self.field = self.backend.fields_for(self.document)[0]
        before = self.field.value(self.document.payload)
        self.edit = self.field.minimum if before != self.field.minimum else self.field.maximum

    def test_equal_format_and_mutable_or_changed_snapshots_reject_all_edit_operations(self):
        altered = self.document.payload[:-1] + bytes([self.document.payload[-1] ^ 1])
        for forged in (
            replace(self.document, format=replace(self.document.format)),
            replace(self.document, raw=bytearray(self.document.raw)),
            replace(self.document, payload=bytearray(self.document.payload)),
            replace(self.document, payload=altered),
        ):
            actions = (
                lambda: self.backend.fields_for(forged),
                lambda: self.backend.stage(forged, {}, self.field.id, self.edit),
                lambda: self.backend.serialize(forged, {}),
                lambda: self.backend.maximums(forged, {}),
                lambda: self.backend.review(forged, {}),
                lambda: self.backend.save_as(forged, {}, self.folder / 'forged.dat'),
            )
            for action in actions:
                with self.subTest(forged=type(forged.payload).__name__, action=action), self.assertRaises(SaveError):
                    action()
        self.assertFalse((self.folder / 'forged.dat').exists())
        self.assertEqual(self.source.read_bytes(), self.raw)

    def test_invalid_pending_batches_fail_before_valid_stage_or_any_output(self):
        for pending in ({'unmapped_review_field': 1}, {self.field.id: True},
                        {self.field.id: self.field.maximum + 1}, {None: 0}, {12: 0}):
            original = dict(pending)
            for action in (
                lambda: self.backend.stage(self.document, pending, self.field.id, self.edit),
                lambda: self.backend.serialize(self.document, pending),
                lambda: self.backend.maximums(self.document, pending),
                lambda: self.backend.save_as(self.document, pending, self.folder / 'bad-batch.dat'),
            ):
                with self.subTest(pending=original, action=action), self.assertRaises(SaveError):
                    action()
            self.assertEqual(pending, original)
        self.assertFalse((self.folder / 'bad-batch.dat').exists())
        self.assertEqual(self.source.read_bytes(), self.raw)

    def test_nonmapping_changes_and_nonstring_field_ids_are_validation_errors(self):
        for pending in (None, [], [(self.field.id, self.edit)], 1):
            for action in (
                lambda: self.backend.stage(self.document, pending, self.field.id, self.edit),
                lambda: self.backend.serialize(self.document, pending),
                lambda: self.backend.maximums(self.document, pending),
            ):
                with self.subTest(pending=pending, action=action), self.assertRaises(SaveError):
                    action()
        for key in (None, 12, [], {}):
            with self.subTest(key=key), self.assertRaises(SaveError):
                self.backend.stage(self.document, {}, key, self.edit)

    def test_native_unchecked_header_words_and_trailer_survive_qualified_edits(self):
        raw = bytearray(self.raw)
        raw[:4] = b'\xE1\x94\xB7\xC2'
        raw[6:8] = b'\xA7\xD3'
        raw[8:12] = b'\x69\xC1\xA5\xE7'
        raw[-28:] = bytes(range(28))
        document = self.backend.decode(self.with_checksum(raw))
        self.assertEqual(self.backend.serialize(document, {}), document.raw)
        changed = self.backend.serialize(document, {self.field.id: self.edit})
        self.assertEqual(changed[:4], document.raw[:4])
        self.assertEqual(changed[6:8], document.raw[6:8])
        self.assertEqual(changed[8:12], document.raw[8:12])
        self.assertEqual(changed[-28:], document.raw[-28:])


class SW2IndependentReviewTests(FrozenClassicSnapshotReview, unittest.TestCase):
    backend = sw2
    fixture_bytes = staticmethod(sw2_fixture)
    with_checksum = staticmethod(sw2_checksum)

    def test_unusual_skill_rank_keeps_high_bit_and_unstages_original(self):
        document = self.backend.decode(self.raw)
        field = next(field for field in self.backend.fields_for(document)
                     if field.group == 'Acquired skills')
        raw = bytearray(document.raw)
        raw[field.offset] = 0xFF
        document = self.backend.decode(self.with_checksum(raw))
        changes = self.backend.stage(document, {}, field.id, 1)
        self.assertEqual(self.backend.stage(document, changes, field.id, 127), {})
        changed = self.backend.serialize(document, changes)
        self.assertEqual(changed[field.offset], 0x81)
        self.assertEqual(self.backend.maximums(document, changes), changes)
        self.assertEqual(self.backend.serialize(document, {}), document.raw)


class OrochiIndependentReviewTests(FrozenClassicSnapshotReview, unittest.TestCase):
    backend = wo1
    fixture_bytes = staticmethod(wo1_fixture)
    with_checksum = staticmethod(wo1_codec.encode)

    def test_higher_owned_ranks_unstage_and_max_preserves_unknown_effects_and_capacity(self):
        fields = self.backend.field_map(self.document)
        rank = fields['officer_0_weapon_0_attribute_14_level']
        original = rank.value(self.document.payload)
        self.assertGreater(original, rank.maximum)
        changes = self.backend.stage(self.document, {}, rank.id, rank.maximum)
        self.assertEqual(self.backend.stage(self.document, changes, rank.id, original), {})
        maximums = self.backend.maximums(self.document, {})
        self.assertNotIn(rank.id, maximums)
        self.assertEqual(set(maximums), {'officer_0_weapon_0_attribute_0_level'})
        encoded = self.backend.serialize(self.document, maximums)
        weapon = self.backend._weapon_offset(0, 0)
        self.assertEqual(encoded[weapon:weapon + 6], self.raw[weapon:weapon + 6])
        self.assertEqual(encoded[weapon + 11], self.raw[weapon + 11])
        self.assertEqual(encoded[rank.offset], self.raw[rank.offset])
        self.assertEqual(self.backend.field_map(self.backend.decode(encoded))[rank.id].value(encoded), original)

    def test_existing_effect_capacity_prerequisite_is_checked_in_mixed_batches(self):
        key = 'officer_0_weapon_0_attribute_slots'
        field = self.backend.field_map(self.document)[key]
        pending = {'stock_exp': 1000, key: field.minimum - 1}
        before = dict(pending)
        with self.assertRaises(SaveError):
            self.backend.stage(self.document, pending, 'stock_exp', 2000)
        with self.assertRaises(SaveError):
            self.backend.serialize(self.document, pending)
        self.assertEqual(pending, before)
        self.assertEqual(self.source.read_bytes(), self.raw)


class SW2RegisteredGuiReviewTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.source = self.folder / 'sw2-copy.dat'
        self.raw = sw2_fixture()
        self.source.write_bytes(self.raw)
        self.app = Application(self.root, persist_preferences=False)
        self.editor = self.app.select_game('sw2')
        self.errors = []
        errors = patch('koei_editor.shared.verified_gui.messagebox.showerror',
                       side_effect=lambda *args: self.errors.append(args))
        errors.start()
        self.addCleanup(errors.stop)
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename',
                   return_value=str(self.source)):
            self.editor.open()
        self.assertEqual(self.errors, [])

    def test_registered_search_review_undo_retained_session_backup_save_and_restore(self):
        editor = self.editor
        self.assertEqual(editor.backup.read_bytes(), self.raw)
        editor.group.set('Resources')
        editor.search.set('money')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('money',))
        editor.fields.selection_set('money')
        editor.value.set('54321')
        editor.apply_selected()
        self.assertEqual(editor.changes, {'money': 54321})
        editor.max_visible()
        self.assertEqual(editor.changes, {'money': 54321})
        self.app.select_game('wo1')
        self.assertIs(self.app.select_game('sw2'), editor)
        self.assertEqual(editor.changes, {'money': 54321})
        self.app.apply_theme('Dark')
        self.app.apply_theme('Light')
        editor.review()
        self.assertTrue(any(isinstance(child, tk.Toplevel) for child in self.root.winfo_children()))
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.fields.selection_set('money')
        editor.value.set('54321')
        editor.apply_selected()
        editor.show_inspector()
        self.assertEqual(tuple(table.title for table in editor.presentation.inspection_tables(editor.document)),
                         ('Officers', 'Weapons', 'Guards'))
        destination = self.folder / 'sw2-edited.dat'
        with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename',
                   return_value=str(destination)):
            editor.save_as()
        self.assertEqual(self.errors, [])
        written = sw2.read_save(destination)
        self.assertEqual(sw2.field_map(written)['money'].value(written.payload), 54321)
        self.assertEqual(self.source.read_bytes(), self.raw)
        self.assertEqual(editor.changes, {})
        restored = self.folder / 'sw2-restored.dat'
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename',
                   return_value=str(editor.backup)), \
                patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename',
                      return_value=str(restored)):
            editor.restore()
        self.assertEqual(self.errors, [])
        self.assertEqual(restored.read_bytes(), self.raw)

    def test_foreign_original_failed_open_and_unsafe_save_preserve_pending_session(self):
        editor = self.editor
        opened = editor.document
        editor.group.set('Resources')
        editor.refresh()
        editor.fields.selection_set('money')
        editor.value.set('54321')
        editor.apply_selected()
        foreign = self.folder / 'original-orochi-copy.dat'
        foreign.write_bytes(wo1_fixture())
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename',
                   return_value=str(foreign)):
            editor.open()
        self.assertEqual(len(self.errors), 1)
        self.assertIs(editor.document, opened)
        self.assertEqual(editor.changes, {'money': 54321})
        self.errors.clear()
        destination = self.folder / 'Documents' / 'KOEI' / 'SENGOKU MUSOU 2 TW' / 'Savedata' / 'save.dat'
        with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename',
                   return_value=str(destination)):
            editor.save_as()
        self.assertEqual(len(self.errors), 1)
        self.assertFalse(destination.exists())
        self.assertIs(editor.document, opened)
        self.assertEqual(editor.changes, {'money': 54321})
        self.errors.clear()
        altered = self.raw[:-1] + bytes([self.raw[-1] ^ 1])
        self.source.write_bytes(altered)
        destination = self.folder / 'changed-source-output.dat'
        with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename',
                   return_value=str(destination)):
            editor.save_as()
        self.assertEqual(len(self.errors), 1)
        self.assertFalse(destination.exists())
        self.assertIs(editor.document, opened)
        self.assertEqual(editor.changes, {'money': 54321})
        self.assertEqual(self.source.read_bytes(), altered)


if __name__ == '__main__':
    unittest.main()
