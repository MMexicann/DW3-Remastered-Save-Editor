"""Candidate PC DW4 Hyper tests; procedural fixtures do not qualify real saves."""
from dataclasses import replace
from functools import lru_cache
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import koei_editor.games.dw4hyper.dw4hyper_parser as editor
from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.save_safety import safe_path


def repair_checksum(raw):
    output = bytearray(raw)
    checksum = sum(output[index] for index in range(0x10FA8))
    output[0x10FA8:0x10FAC] = checksum.to_bytes(4, 'little')
    return bytes(output)


@lru_cache(maxsize=1)
def procedural_raw():
    # Every unknown region contains distinctive data, rather than easy-to-miss
    # zero padding. Sizes/offsets here are expressed independently of the parser.
    raw = bytearray((index * 37 + 11) % 256 for index in range(69568))
    raw[0x9A] = 1
    for index in range(42):
        offset = 0xB8 + index * 24
        raw[offset] = index % 2
        raw[offset + 1:offset + 5] = bytes([145, 165, 50, 50])
        raw[offset + 5] = index
        raw[offset + 8:offset + 16] = bytes([19, 14, 2, 11, 32, 32, 32, 32])
        raw[offset + 16:offset + 18] = (1200 + index).to_bytes(2, 'little')
        raw[0x798 + index * 2:0x79A + index * 2] = (2300 + index).to_bytes(2, 'little')
    raw[0x7F6:0x7F6 + 32] = bytes([0xFF] * 32)
    for team in range(4):
        offset = 0x508 + team * 96
        for member in range(9):
            name = f'T{team + 1}M{member}'.encode('ascii')
            raw[offset + member * 9:offset + member * 9 + 9] = name.ljust(9, b'\0')
        raw[offset + 94:offset + 96] = (150 + team).to_bytes(2, 'little')
    for slot in range(4):
        offset = 0x688 + slot * 64
        raw[offset] = slot % 2
        raw[offset + 0x34:offset + 0x3D] = f'Custom{slot + 1}'.encode().ljust(9, b'\0')
    raw[0x10FAC:] = bytes(20)
    return repair_checksum(raw)


class DW4HyperCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.folder = Path(self.temporary.name)
        self.source = self.folder / 'save-copy.dat'
        self.source.write_bytes(procedural_raw())
        self.document = editor.read_save(self.source)

    def tearDown(self):
        self.temporary.cleanup()

    def test_candidate_never_claims_real_sample_qualification(self):
        self.assertFalse(editor.FORMAT.sample_verified)
        self.assertIn('genuine PC save sample', editor.FORMAT.note)
        self.assertEqual(len(editor.fields_for(self.document)), 331)
        self.assertEqual(editor.OFFICER_NAMES[0], 'Zhao Yun')
        self.assertEqual(editor.OFFICER_NAMES[-1], 'Yue Ying')
        self.assertEqual(editor.record_label(1, 'Officers'), 'Zhao Yun')
        self.assertEqual(editor.record_label(42, 'Weapons'), 'Yue Ying')
        self.assertEqual(editor.record_label(1, 'Bodyguards'), 'Bodyguard team 1')

    def test_no_edit_preserves_every_original_byte(self):
        self.assertEqual(editor.serialize(self.document, {}), procedural_raw())
        original = self.document.payload[0xB8 + 7]
        self.assertNotEqual(original, 0)
        self.assertEqual(self.document.payload, self.document.raw[:0x10FA8])

    def test_single_edit_and_integrity_preserve_other_data(self):
        field = editor.field_map(self.document)['officer_0_attack']
        edited = editor.serialize(self.document, {field.id: 123})
        reopened = editor.decode(edited)
        self.assertEqual(field.value(reopened.payload), 123)
        self.assertEqual(edited[0x10FA8:0x10FAC], sum(edited[:0x10FA8]).to_bytes(4, 'little'))
        changed = {index for index, pair in enumerate(zip(self.document.raw, edited)) if pair[0] != pair[1]}
        self.assertLessEqual(changed, {0xBB, *range(0x10FA8, 0x10FAC)})
        self.assertEqual(self.source.read_bytes(), procedural_raw())

    def test_item_level_encoding_and_locking(self):
        for key, value, stored in (('item_0', 20, 19), ('item_13', 4, 3),
                                   ('item_19', 1, 0), ('item_31', 0, 255)):
            with self.subTest(key=key, value=value):
                field = editor.field_map(self.document)[key]
                output = editor.decode(editor.serialize(self.document, {key: value}))
                self.assertEqual(field.value(output.payload), value)
                self.assertEqual(output.payload[field.offset], stored)
        owned = editor.decode(editor.serialize(self.document, {'item_19': 1}))
        locked = editor.decode(editor.serialize(owned, {'item_19': 0}))
        self.assertEqual(locked.payload[0x7F6 + 19], 0xFF)

    def test_all_declared_maxima_preserve_custom_equipment_battle_and_rankings(self):
        changes = editor.maximums(self.document, {})
        self.assertNotIn('difficulty', changes)
        output = editor.decode(editor.serialize(self.document, changes))
        self.assertEqual(output.payload, editor.changed_payload(self.document, changes))
        allowed = {offset for field in editor.FORMAT.fields if field.maxable
                   for offset in range(field.offset, field.offset + field.size)}
        changed = {index for index, pair in enumerate(zip(self.document.payload, output.payload))
                   if pair[0] != pair[1]}
        self.assertLessEqual(changed, allowed)
        for field in editor.FORMAT.fields:
            self.assertEqual(field.value(output.payload),
                             field.maximum if field.maxable else field.value(self.document.payload))
        # Custom roster/appearance, challenge ranks and suspended-battle snapshot.
        for start, end in ((0x4A8, 0x508), (0x688, 0x788), (0xBA0, 0xC68), (0xABE0, 0x10FA8)):
            self.assertEqual(output.payload[start:end], self.document.payload[start:end])
        for officer in range(42):
            start = 0xB8 + 24 * officer + 8
            self.assertEqual(output.payload[start:start + 8], self.document.payload[start:start + 8])

    def test_group_maximums_do_not_change_other_groups(self):
        changes = editor.maximums(self.document, {}, 'Items')
        self.assertEqual(set(changes), {f'item_{index}' for index in range(32)})
        output = editor.decode(editor.serialize(self.document, changes))
        self.assertEqual(output.payload[:0x7F6], self.document.payload[:0x7F6])
        self.assertEqual(output.payload[0x816:], self.document.payload[0x816:])

    def test_storage_bounds_excluded_from_bulk_max(self):
        maxima = editor.maximums(self.document, {})
        for key in ('officer_0_life', 'officer_0_musou', 'officer_0_attack',
                    'officer_0_defense', 'officer_0_experience', 'team_0_points', 'difficulty'):
            self.assertFalse(editor.field_map(self.document)[key].maxable)
            self.assertNotIn(key, maxima)
            self.assertEqual(editor.limit_values(self.document, {}, [key]), {})
        self.assertIn('officer_0_unlocked', maxima)
        self.assertEqual(maxima['officer_0_weapon_experience'], 36001)
        self.assertEqual(maxima['item_0'], 20)
        self.assertEqual(maxima['item_13'], 4)
        self.assertEqual(maxima['item_19'], 1)
        # Bounded individual edits remain supported without calling them caps.
        self.assertEqual(editor.stage(self.document, {}, 'officer_0_attack', 255),
                         {'officer_0_attack': 255})

    def test_higher_existing_values_preserved_and_can_be_unstaged(self):
        raw = bytearray(self.document.raw)
        raw[0x798:0x79A] = (65535).to_bytes(2, 'little')
        raw[0x7F6] = 29  # Existing level 30, above the published natural cap.
        high = editor.decode(repair_checksum(raw))
        limits = editor.maximums(high, {})
        self.assertNotIn('officer_0_weapon_experience', limits)
        self.assertNotIn('item_0', limits)
        staged = editor.stage(high, {}, 'officer_0_weapon_experience', 36001)
        self.assertEqual(editor.stage(high, staged, 'officer_0_weapon_experience', 65535), {})
        staged = editor.stage(high, {}, 'item_0', 20)
        self.assertEqual(editor.stage(high, staged, 'item_0', 30), {})
        output = editor.decode(editor.serialize(high, limits))
        self.assertEqual(editor.field_map(output)['officer_0_weapon_experience'].value(output.payload), 65535)
        self.assertEqual(editor.field_map(output)['item_0'].value(output.payload), 30)

    def test_stage_preserves_history_and_undo_to_original(self):
        before = {'officer_1_attack': 60}
        after = editor.stage(self.document, before, 'officer_0_attack', 99)
        self.assertEqual(before, {'officer_1_attack': 60})
        self.assertEqual(editor.stage(self.document, after, 'officer_0_attack', 50), before)

    def test_review_uses_semantic_levels_and_layout_order(self):
        changes = {'item_19': 1, 'officer_0_attack': 99, 'item_0': 20}
        self.assertEqual([(field.id, before, after) for field, before, after in editor.review(self.document, changes)],
                         [('officer_0_attack', 50, 99), ('item_0', 0, 20), ('item_19', 0, 1)])

    def test_invalid_values_and_unmapped_writes_rejected(self):
        for key, values in (
                ('officer_0_attack', (-1, 256, True, '7', 1.5, None)),
                ('officer_0_weapon_experience', (-1, 36002, 65535)),
                ('difficulty', (-1, 3)), ('item_0', (-1, 21, 255)),
                ('item_13', (5,)), ('item_19', (2,)), ('team_0_points', (65536,))):
            for value in values:
                with self.subTest(key=key, value=value), self.assertRaises(SaveError):
                    editor.stage(self.document, {}, key, value)
        for key in ('officer_42_attack', 'equipment', 'custom_0_name', 'raw_byte', 'ranking_0'):
            for operation in (
                    lambda: editor.stage(self.document, {}, key, 1),
                    lambda: editor.serialize(self.document, {key: 1}),
                    lambda: editor.limit_values(self.document, {}, [key])):
                with self.subTest(key=key), self.assertRaises(SaveError):
                    operation()

    def test_wrong_size_and_zero_or_other_game_data_rejected(self):
        for raw in (b'', self.document.raw[:-1], self.document.raw + b'\0', bytes(69568),
                    bytes([1]) * 69568):
            with self.assertRaises(SaveError):
                editor.decode(raw)
        for game_id in ('dw4xl', 'dw8xl', 'pw3', 'origins'):
            with self.assertRaises(SaveError):
                editor.decode(self.document.raw, game_id)

    def test_bad_checksum_rejected_without_repair(self):
        for offset in (0, 0xB8, 0x688, 0xB170, 0x10FA8):
            raw = bytearray(self.document.raw)
            raw[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaisesRegex(SaveError, 'checksum'):
                editor.decode(raw)

    def test_repaired_checksum_does_not_allow_bad_difficulty_or_roster(self):
        raw = bytearray(self.document.raw)
        raw[0x9A] = 3
        with self.assertRaisesRegex(SaveError, 'difficulty'):
            editor.decode(repair_checksum(raw))
        for index in range(42):
            raw = bytearray(self.document.raw)
            raw[0xB8 + 24 * index + 5] ^= 1
            with self.subTest(index=index), self.assertRaisesRegex(SaveError, 'identities'):
                editor.decode(repair_checksum(raw))

    def test_checksum_excluded_trailer_still_rejected_when_nonzero(self):
        for offset in range(0x10FAC, 0x10FC0):
            raw = bytearray(self.document.raw)
            raw[offset] = 1
            with self.subTest(offset=offset), self.assertRaisesRegex(SaveError, 'trailer'):
                editor.decode(raw)

    def test_forged_snapshot_or_format_rejected(self):
        for document in (replace(self.document, payload=b'bad'), replace(self.document, seed=1),
                         replace(self.document, format=replace(editor.FORMAT, sample_verified=True)),
                         replace(self.document, raw=self.document.raw[:-1])):
            with self.assertRaises(SaveError):
                editor.serialize(document, {})
        with self.assertRaises(TypeError):
            editor.field_map(self.document)['new'] = editor.FORMAT.fields[0]

    def test_read_only_names_equipment_and_progression_do_not_map_writes(self):
        rows = editor.inspection_rows(self.document)
        self.assertEqual(len(rows), 83)
        self.assertIn('Red Hare Harness', rows[1]['value'])
        self.assertIn('Lightning Orb', rows[1]['value'])
        self.assertEqual([row['value'] for row in rows if row['label'] == 'Team 1'], ['T1M0'])
        self.assertIn('Custom1', rows[-4]['value'])
        progress = editor.progression(self.document, 1)
        self.assertIsNone(progress['level'])
        self.assertEqual(progress['experience'], 1200)
        self.assertEqual(progress['weapon_experience'], 2300)
        self.assertEqual(len(editor.progressions(self.document)), 42)
        for slot in (0, 43, True, '1'):
            with self.assertRaises(SaveError):
                editor.progression(self.document, slot)
        self.assertIn('no Lv.11', editor.field_hint(self.document, 'officer_0_weapon_experience'))

    def test_backup_save_as_restore_preserve_original(self):
        snapshot = editor.backup(self.document)
        self.assertEqual(snapshot.read_bytes(), self.document.raw)
        metadata = json.loads(snapshot.with_suffix('.json').read_text())
        self.assertEqual(metadata['game_id'], 'dw4hyper')
        output = editor.save_as(self.document, {'officer_0_attack': 99, 'item_0': 20}, self.folder / 'edited.dat')
        self.assertEqual(editor.field_map(output)['officer_0_attack'].value(output.payload), 99)
        restored = editor.restore(snapshot, self.folder / 'restored.dat')
        self.assertEqual(restored.read_bytes(), procedural_raw())
        self.assertEqual(self.source.read_bytes(), procedural_raw())
        self.assertEqual(self.document.raw, procedural_raw())

    def test_save_and_restore_never_overwrite_existing_files(self):
        target = self.folder / 'existing.dat'
        target.write_bytes(b'keep')
        snapshot = editor.backup(self.document)
        for destination in (target, self.source):
            original = destination.read_bytes()
            with self.assertRaises(FileExistsError):
                editor.save_as(self.document, {'item_0': 20}, destination)
            with self.assertRaises(FileExistsError):
                editor.restore(snapshot, destination)
            self.assertEqual(destination.read_bytes(), original)

    def test_changed_source_rejected_without_creating_output(self):
        self.source.write_bytes(self.document.raw[:-1])
        output = self.folder / 'edited.dat'
        with self.assertRaisesRegex(SaveError, 'changed on disk'):
            editor.save_as(self.document, {'item_0': 20}, output)
        self.assertFalse(output.exists())
        self.assertFalse((self.folder / 'WarriorsEditorBackups').exists())

    def test_restore_rejects_native_integrity_and_wrong_game_manifest(self):
        snapshot = editor.backup(self.document)
        manifest_path = snapshot.with_suffix('.json')
        metadata = json.loads(manifest_path.read_text())
        metadata['game_id'] = 'dw4xl'
        manifest_path.write_text(json.dumps(metadata))
        with self.assertRaises(SaveError):
            editor.restore(snapshot, self.folder / 'restored.dat')
        self.assertFalse((self.folder / 'restored.dat').exists())
        snapshot.write_bytes(snapshot.read_bytes()[:-1])
        with self.assertRaises(SaveError):
            editor.restore(snapshot, self.folder / 'restored2.dat')
        self.assertFalse((self.folder / 'restored2.dat').exists())

    def test_native_pc_suffix_required(self):
        for suffix in ('.psu', '.sys', '.bin'):
            path = self.folder / ('copy' + suffix)
            path.write_bytes(self.document.raw)
            with self.assertRaises(SaveError):
                editor.read_save(path)
            with self.assertRaises(SaveError):
                editor.save_as(self.document, {}, self.folder / ('edited' + suffix))

    def test_live_paths_and_symlink_aliases_rejected(self):
        live = self.folder / 'KOEI' / 'Dynasty Warriors 4 Hyper' / 'Savedata'
        live.mkdir(parents=True)
        source = live / 'save.dat'
        source.write_bytes(self.document.raw)
        with self.assertRaises(SaveError):
            editor.read_save(source)
        with self.assertRaises(SaveError):
            editor.save_as(self.document, {}, live / 'edited.dat')
        with self.assertRaises(SaveError):
            safe_path(r'C:\Users\Player\Documents\KOEI\Dynasty Warriors 4 Hyper\Savedata\save.dat')
        alias = self.folder / 'alias.dat'
        try:
            alias.symlink_to(source)
        except (OSError, NotImplementedError):
            return
        with self.assertRaises(SaveError):
            editor.read_save(alias)


@unittest.skipUnless(os.environ.get('DW4HYPER_SAVE_COPY'), 'No explicit native PC DW4 Hyper sample provided')
class ExplicitNativePCSampleTests(unittest.TestCase):
    def test_declared_format_roundtrip_and_all_supported_edits(self):
        # Explicit opt-in sample validation; no real saves live in the source tree.
        document = editor.read_save(os.environ['DW4HYPER_SAVE_COPY'])
        self.assertEqual(editor.serialize(document, {}), document.raw)
        changes = editor.maximums(document, {})
        output = editor.decode(editor.serialize(document, changes))
        self.assertEqual(output.payload, editor.changed_payload(document, changes))
        allowed = {offset for field in editor.FORMAT.fields if field.id in changes
                   for offset in range(field.offset, field.offset + field.size)}
        changed = {index for index, pair in enumerate(zip(document.payload, output.payload)) if pair[0] != pair[1]}
        self.assertLessEqual(changed, allowed)
        for key, value in changes.items():
            self.assertEqual(editor.field_map(output)[key].value(output.payload), value)


if __name__ == '__main__':
    unittest.main()
