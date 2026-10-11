"""Focused unreleased DW4 expansion and Samurai pending-edit regressions.

Generated custom records exercise invariants; they are not player-save evidence.
Native fixture checks are opt-in and never execute a game.
"""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.dw4hyper import dw4hyper_parser as hyper
from koei_editor.games.dw4xl import dw4xl_parser as xl
from koei_editor.games.sw4dx import samurai4dx_parser as sw
from koei_editor.games.sw4_ps3 import parser as sw_ps3
from tests.test_dw4hyper_format import procedural_raw, repair_checksum
from tests.test_dw4xl_format import procedural_psu
from tests.test_samurai4dx_format import procedural_raw as samurai_raw
from tests.test_ps3_expansion import fixture as ps3_raw


def custom_raw():
    raw = bytearray(procedural_raw())
    for slot in range(4):
        base = 0x688 + slot * 64
        roster = 0x4A8 + slot * 24
        raw[base] = 1
        raw[base + 1:base + 5] = bytes([140, 160, 45, 55])
        raw[base + 5] = raw[base + 0x2D] = 0x2C
        raw[base + 0x18] = 0x60 + slot
        raw[base + 0x1B] = raw[base + 0x1C] = 0x2A if slot % 2 == 0 else 0x2B
        raw[base + 0x1D] = slot
        raw[base + 0x1E] = 6
        raw[base + 0x20:base + 0x22] = bytes([45, 55])
        raw[base + 0x30:base + 0x34] = bytes([0, 1, 2, 0])
        raw[roster:roster + 24] = raw[base:base + 24]
    return repair_checksum(raw)


class DW4ExpansionTests(unittest.TestCase):
    def test_ps3_weapon_inspection_preserves_unknown_ids_flags_and_proficiency(self):
        raw = bytearray(ps3_raw(sw_ps3))
        raw[0x3882:0x3884] = (65535).to_bytes(2, 'big')
        raw[0x3884] = 255
        raw[0x388C] = 250
        raw[0x3894] = 255
        raw[0x389C] = 0xA5
        document = sw_ps3.decode(sw_ps3.seal(bytes(raw)))
        record = sw_ps3.weapon_records(document)[0]
        self.assertEqual(record['id'], 65535)
        self.assertEqual(record['skills'][0], {'id': 250, 'rank': 255, 'ceiling': 255, 'flags': 0xA5})
        row = next(row for row in sw_ps3.inspection_rows(document) if row['group'] == 'Weapon inspection')
        self.assertIn('Unknown skill ID 250', row['value'])
        self.assertIn('0xA5', row['value'])
        output = sw_ps3.serialize(document, {'gold': 12345})
        self.assertEqual(output[0x3882:0x7842], document.raw[0x3882:0x7842])
        self.assertEqual(sw_ps3.weapon_records(sw_ps3.decode(output)), sw_ps3.weapon_records(document))

    def test_existing_custom_fields_synchronize_only_proven_mirrors(self):
        document = hyper.decode(custom_raw())
        fields = [field for field in hyper.fields_for(document) if field.group == 'Custom characters']
        self.assertEqual(len(fields), 40)
        self.assertTrue(all(not field.maxable for field in fields))
        self.assertEqual(hyper.serialize(document, {}), document.raw)
        for field in fields:
            value = 1 if field.value(document.payload) != 1 else field.maximum
            edited = hyper.decode(hyper.serialize(document, {field.id: value}))
            allowed = {offset + i for offset in (field.offset, *field.mirrors) for i in range(field.size)}
            differences = {i for i, (a, b) in enumerate(zip(document.payload, edited.payload)) if a != b}
            self.assertLessEqual(differences, allowed)
            self.assertEqual(field.value(edited.payload), value)
            for mirror in field.mirrors:
                self.assertEqual(edited.payload[mirror:mirror + field.size], field.encoded(value))
            self.assertEqual(len(hyper.fields_for(edited)), 455)
        changes = hyper.maximums(document, {})
        self.assertFalse(any(key.startswith('custom_') for key in changes))
        self.assertEqual(hyper.decode(hyper.serialize(document, changes)).payload[0x688:0x788],
                         document.payload[0x688:0x788])

    def test_absent_inconsistent_and_unknown_custom_records_are_preserved(self):
        for relative, value in ((0, 0), (0x18, 0x61), (0x1C, 0), (0x2D, 0), (0x20, 44)):
            raw = bytearray(custom_raw())
            raw[0x688 + relative] = value
            document = hyper.decode(repair_checksum(raw))
            self.assertNotIn('custom_0_attack', hyper.field_map(document))
            if relative in (0, 0x18, 0x1C):
                self.assertFalse(any(field.id.startswith('custom_0_') for field in hyper.fields_for(document)))
            else:
                self.assertIn('custom_0_color', hyper.field_map(document))
            with self.assertRaises(SaveError):
                hyper.serialize(document, {'custom_0_attack': 99})
            self.assertEqual(hyper.serialize(document, {}), bytes(repair_checksum(raw)))
        raw = bytearray(custom_raw())
        raw[0x688 + 0x30] = 255
        document = hyper.decode(repair_checksum(raw))
        self.assertNotIn('custom_0_head', hyper.field_map(document))
        self.assertEqual(hyper.decode(hyper.serialize(document, {'custom_0_color': 5})).payload[0x6B8], 255)
        self.assertIn('Ponytail', hyper.field_hint(document, 'custom_1_head'))
        self.assertIn('Turban', hyper.field_hint(hyper.decode(custom_raw()), 'custom_0_head'))

    def test_equipment_category_ownership_pending_grants_and_removal_dependencies(self):
        for parser, raw, empty in ((hyper, procedural_raw(), 32), (xl, procedural_psu(), 41)):
            document = parser.decode(raw)
            for changes in ({'officer_0_harness': 13}, {'officer_0_orb': 19},
                            {'officer_0_harness': 21}, {'officer_0_orb': 16}):
                with self.subTest(game=parser.GAME_ID, changes=changes), self.assertRaises(SaveError):
                    parser.serialize(document, changes)
            changes = parser.stage(document, {}, 'item_21', 1)
            changes = parser.stage(document, changes, 'officer_0_harness', 21)
            changes = parser.stage(document, changes, 'item_16', 4)
            changes = parser.stage(document, changes, 'officer_0_orb', 16)
            equipped = parser.decode(parser.serialize(document, changes))
            for key in ('item_21', 'item_16'):
                with self.assertRaisesRegex(SaveError, 'Unequip'):
                    parser.stage(equipped, {}, key, 0)
            cleared = parser.stage(equipped, {}, 'officer_0_harness', empty)
            cleared = parser.stage(equipped, cleared, 'item_21', 0)
            output = parser.decode(parser.serialize(equipped, cleared))
            self.assertEqual(output.payload[0xC0], empty)
            self.assertEqual(output.payload[0x80B], 255)
            for index in range(42):
                base = 0xB8 + 24 * index
                self.assertEqual(output.payload[base + 10:base + 16], document.payload[base + 10:base + 16])

    def test_frozen_snapshot_types_pending_bulk_validation_and_above_original_values(self):
        for parser, raw in ((hyper, procedural_raw()), (xl, procedural_psu()), (sw, samurai_raw())):
            document = parser.decode(raw)
            key = 'gold' if parser is sw else 'item_0'
            for changes in ({key: -1}, {key: True}, {key: '1'}, {'unmapped_story': 1}):
                for operation in (parser.maximums, lambda d, c: parser.limit_values(d, c, [key])):
                    with self.subTest(game=parser.GAME_ID, changes=changes), self.assertRaises(SaveError):
                        operation(document, changes)
            for bad in (replace(document, raw=bytearray(document.raw)),
                        replace(document, payload=bytearray(document.payload)),
                        replace(document, seed=True), replace(document, format=replace(document.format))):
                with self.assertRaises(SaveError):
                    parser.maximums(bad, {})

    def test_restore_rejects_format_corruption_even_with_matching_manifest_hash(self):
        for parser, raw, suffix in ((hyper, procedural_raw(), '.dat'), (xl, procedural_psu(), '.psu')):
            with tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                source = folder / ('copy' + suffix)
                source.write_bytes(raw)
                document = parser.read_save(source)
                snapshot = parser.backup(document)
                bad = bytearray(snapshot.read_bytes())
                bad[0x9A if parser is hyper else document.payload_offset + 2] ^= 1
                snapshot.write_bytes(bad)
                metadata_path = snapshot.with_suffix('.json')
                metadata = json.loads(metadata_path.read_text())
                metadata['sha256'] = hashlib.sha256(bad).hexdigest()
                metadata_path.write_text(json.dumps(metadata))
                destination = folder / ('restored' + suffix)
                with self.assertRaises(SaveError):
                    parser.restore(snapshot, destination)
                self.assertFalse(destination.exists())
                self.assertEqual(source.read_bytes(), raw)

    @unittest.skipUnless(os.environ.get('DW4XL_PSU_COPY'), 'No private genuine DW4XL export')
    def test_genuine_xl_every_writable_field_surgical_and_source_unchanged(self):
        path = Path(os.environ['DW4XL_PSU_COPY'])
        raw = path.read_bytes()
        document = xl.read_save(path)
        self.assertEqual(xl.serialize(document, {}), raw)
        count = 0
        for field in xl.fields_for(document):
            before = field.value(document.payload)
            value = (41 if field.group in ('Equipment', 'General equipment') else
                     max(1, min(before - 1, field.maximum)) if field.group == 'Items' else
                     field.minimum if before != field.minimum else field.maximum)
            edited_raw = xl.serialize(document, {field.id: value})
            edited = xl.decode(edited_raw)
            allowed = {document.payload_offset + field.offset + i for i in range(field.size)}
            allowed.update((document.payload_offset, document.payload_offset + 1))
            self.assertLessEqual({i for i, (a, b) in enumerate(zip(raw, edited_raw)) if a != b}, allowed)
            self.assertEqual(field.value(edited.payload), value)
            count += 1
        self.assertGreaterEqual(count, 382)
        self.assertEqual(path.read_bytes(), raw)

    @unittest.skipUnless(os.environ.get('DW4HYPER_SAVE_COPY'), 'No private genuine DW4 Hyper copy')
    def test_genuine_hyper_every_available_field_surgical_with_template_preservation(self):
        path = Path(os.environ['DW4HYPER_SAVE_COPY'])
        raw = path.read_bytes()
        document = hyper.read_save(path)
        self.assertEqual(hyper.serialize(document, {}), raw)
        count = 0
        for field in hyper.fields_for(document):
            before = field.value(document.payload)
            value = (32 if field.group in ('Equipment', 'General equipment') else
                     max(1, min(before - 1, field.maximum)) if field.group == 'Items' else
                     field.minimum if before != field.minimum else field.maximum)
            edited_raw = hyper.serialize(document, {field.id: value})
            edited = hyper.decode(edited_raw)
            allowed = {offset + i for offset in (field.offset, *field.mirrors) for i in range(field.size)}
            allowed.update(range(0x10FA8, 0x10FAC))
            self.assertLessEqual({i for i, (a, b) in enumerate(zip(raw, edited_raw)) if a != b}, allowed)
            self.assertEqual(field.value(edited.payload), value)
            count += 1
        self.assertGreaterEqual(count, 415)
        # This public reference has different appearance templates and grown
        # roster values; cosmetics must never reconcile those differences.
        changes = {field.id: 5 if field.id.endswith('_color') else 2
                   for field in hyper.fields_for(document)
                   if field.group == 'Custom characters' and not field.mirrors}
        changed = hyper.decode(hyper.serialize(document, changes))
        for slot in range(4):
            appearance, roster = 0x688 + slot * 64, 0x4A8 + slot * 24
            self.assertEqual(changed.payload[appearance:appearance + 24], document.payload[appearance:appearance + 24])
            self.assertEqual(changed.payload[roster:roster + 24], document.payload[roster:roster + 24])
        self.assertEqual(path.read_bytes(), raw)

    def test_hyper_custom_tk_search_review_undo_save_and_restore(self):
        import tkinter as tk
        from unittest.mock import patch
        from koei_editor.games.dw4hyper.dw4hyper_editor import Editor
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'copy.dat'
            source.write_bytes(custom_raw())
            editor = Editor(root)
            with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                editor.open()
            editor.group.set('Custom characters')
            editor.search.set('custom_0')
            editor.refresh()
            self.assertEqual(len(editor.fields.get_children()), 10)
            editor.fields.selection_set('custom_0_attack')
            editor.value.set('123')
            editor.apply_selected()
            self.assertEqual(editor.changes, {'custom_0_attack': 123})
            editor.review()
            editor.undo()
            self.assertEqual(editor.changes, {})
            editor.max_visible()
            self.assertEqual(editor.changes, {})
            editor.fields.selection_set('custom_0_color')
            editor.value.set('5')
            editor.apply_selected()
            expected = hyper.serialize(editor.document, editor.changes)
            destination = Path(directory) / 'edited.dat'
            editor.save_to(destination)
            self.assertEqual(destination.read_bytes(), expected)
            self.assertEqual(source.read_bytes(), custom_raw())
            restored = hyper.restore(editor.backup, Path(directory) / 'restored.dat')
            self.assertEqual(restored.read_bytes(), custom_raw())

    @unittest.skipUnless(os.environ.get('DW4XL_PSU_COPY'), 'No private genuine DW4XL export')
    def test_genuine_xl_tk_named_equipment_review_undo_save_and_restore(self):
        import tkinter as tk
        from unittest.mock import patch
        from koei_editor.games.dw4xl.dw4xl_editor import Editor
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        original = Path(os.environ['DW4XL_PSU_COPY'])
        raw = original.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'copy.psu'
            source.write_bytes(raw)
            editor = Editor(root)
            with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                editor.open()
            editor.group.set('Equipment')
            editor.search.set('Harness')
            editor.refresh()
            self.assertEqual(len(editor.fields.get_children()), 42)
            self.assertIn((19, 'Red Hare Harness'), editor.field_options(xl.field_map(editor.document)['officer_0_harness']))
            editor.fields.selection_set('officer_0_harness')
            editor.value.set('41')
            editor.apply_selected()
            editor.review()
            editor.undo()
            self.assertEqual(editor.changes, {})
            editor.max_visible()
            self.assertEqual(editor.changes, {})
            editor.fields.selection_set('officer_0_harness')
            editor.value.set('19')
            editor.apply_selected()
            expected = xl.serialize(editor.document, editor.changes)
            destination = Path(directory) / 'edited.psu'
            editor.save_to(destination)
            self.assertEqual(destination.read_bytes(), expected)
            self.assertEqual(xl.restore(editor.backup, Path(directory) / 'restored.psu').read_bytes(), raw)
            self.assertEqual(source.read_bytes(), raw)
        self.assertEqual(original.read_bytes(), raw)

    @unittest.skipUnless(os.environ.get('SW4_PS3_US_COPY'), 'No private genuine SW4 PS3 US export')
    def test_genuine_sw4_ps3_weapon_records_inspect_without_writes(self):
        path = Path(os.environ['SW4_PS3_US_COPY'])
        raw = path.read_bytes()
        document = sw_ps3.decode(raw)
        records = sw_ps3.weapon_records(document)
        self.assertEqual(len(records), 480)
        self.assertEqual((records[0]['pool'], records[0]['slot']), (1, 1))
        self.assertEqual((records[-1]['pool'], records[-1]['slot']), (60, 8))
        self.assertEqual(len(sw_ps3.fields_for(document)), 9)
        rows = [row for row in sw_ps3.inspection_rows(document) if row['group'] == 'Weapon inspection']
        self.assertEqual(len(rows), sum(record['id'] != 180 for record in records))
        self.assertTrue(all('read only' in row['value'] for row in rows))
        before = sw_ps3.serialize(document, {})
        for key in ('weapon_0_0_skill_0_rank', 'weapon_0_0_skill_0_active', 'weapon_0_id'):
            with self.assertRaises(SaveError):
                sw_ps3.serialize(document, {key: 1})
        self.assertEqual(before, raw)
        self.assertEqual(path.read_bytes(), raw)
