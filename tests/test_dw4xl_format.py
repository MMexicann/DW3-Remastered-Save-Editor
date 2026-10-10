"""Procedural PS2 USA PSU tests; genuine exported-save testing stays explicit."""
from dataclasses import replace
from functools import lru_cache
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import koei_editor.games.dw4xl.dw4xl_parser as editor
from koei_editor.games.dw3.models import SaveError


def repair_inner(inner):
    output = bytearray(inner)
    checksum = sum(output[index] for index in range(4, len(output))) % 65536
    output[:2] = checksum.to_bytes(2, 'little')
    return bytes(output)


@lru_cache(maxsize=1)
def procedural_inner():
    inner = bytearray((index * 31 + 17) % 256 for index in range(34064))
    inner[2:4] = b'\x03\x00'
    inner[0x9A] = 2
    for officer in range(42):
        base = 0xB8 + 24 * officer
        inner[base] = 1
        inner[base + 1:base + 5] = bytes([145, 165, 50, 50])
        inner[base + 5] = officer
        inner[base + 8:base + 16] = bytes([22, 15, 12, 4, 29, 41, 41, 41])
        inner[base + 16:base + 18] = (1200 + officer).to_bytes(2, 'little')
        inner[0x798 + 2 * officer:0x79A + 2 * officer] = (2300 + officer).to_bytes(2, 'little')
    inner[0x7F6:0x7F6 + 41] = bytes([255] * 41)
    for team in range(4):
        base = 0x508 + team * 96
        for member in range(9):
            name = f'T{team + 1}M{member}'.encode()
            inner[base + member * 9:base + member * 9 + 9] = name.ljust(9, b'\0')
        inner[base + 94:base + 96] = (150 + team).to_bytes(2, 'little')
    return repair_inner(inner)


def directory_entry(name, mode, length, tag=0):
    # Unknown directory fields contain distinctive bytes to catch normalization.
    result = bytearray((index * 19 + tag) % 256 for index in range(512))
    result[:2] = mode.to_bytes(2, 'little')
    result[4:8] = length.to_bytes(4, 'little')
    result[64:96] = name.encode('ascii').ljust(32, b'\0')
    return bytes(result)


def procedural_psu(inner=None, order=('metadata', 'icon', 'save', 'extra'), root_name='BASLUS-20812'):
    inner = procedural_inner() if inner is None else inner
    files = {
        'metadata': ('BASLUS-20812.sys', bytes((i * 7) % 256 for i in range(1023))),
        'icon': ('u.ico', bytes((i * 13 + 8) % 256 for i in range(2800))),
        'save': ('BASLUS-20812', inner),
        'extra': ('unknown.txt', b'Unrelated file bytes must remain unchanged.'),
    }
    count = 2 + len(order)
    result = bytearray(directory_entry(root_name, 0x8427, count, 3))
    result.extend(directory_entry('.', 0x8427, count, 4))
    result.extend(directory_entry('..', 0x8427, 0, 5))
    for index, key in enumerate(order):
        name, data = files[key]
        result.extend(directory_entry(name, 0x8497, len(data), 10 + index))
        result.extend(data)
        result.extend(bytes([193 + index]) * ((-len(data)) % 1024))
    return bytes(result)


class DW4XLPS2Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.folder = Path(self.temporary.name)
        self.source = self.folder / 'export-copy.psu'
        self.source.write_bytes(procedural_psu())
        self.document = editor.read_save(self.source)

    def tearDown(self):
        self.temporary.cleanup()

    def test_platform_identity_and_qualified_real_sample_status(self):
        self.assertEqual(editor.GAME_ID, 'dw4xl_ps2')
        self.assertTrue(editor.FORMAT.sample_verified)
        self.assertEqual(editor.FORMAT.inner_size, 34064)
        self.assertEqual(editor.FORMAT.size, 8 * 1024 * 1024)
        self.assertEqual(len(editor.fields_for(self.document)), 382)
        self.assertEqual(editor.record_label(1), 'Zhao Yun')
        self.assertEqual(editor.record_label(42, 'Weapons'), 'Yue Ying')

    def test_unchanged_roundtrip_preserves_complete_export(self):
        self.assertEqual(editor.serialize(self.document, {}), procedural_psu())
        self.assertEqual(self.document.payload, procedural_inner())
        self.assertEqual(self.document.raw[self.document.payload_offset:
                                         self.document.payload_offset + 34064], procedural_inner())

    def test_payload_location_is_walked_across_different_file_orders(self):
        offsets = set()
        for order in (('save', 'metadata', 'icon', 'extra'), ('icon', 'save', 'extra', 'metadata'),
                      ('metadata', 'icon', 'extra', 'save')):
            document = editor.decode(procedural_psu(order=order))
            offsets.add(document.payload_offset)
            self.assertNotEqual(document.payload_offset, 0x1C000)
            self.assertEqual(document.payload, procedural_inner())
            output = editor.decode(editor.serialize(document, {'officer_0_attack': 123}))
            self.assertEqual(output.payload_offset, document.payload_offset)
            self.assertEqual(output.payload[0xBB], 123)
        self.assertEqual(len(offsets), 3)

    def test_one_stat_edit_only_changes_field_and_native_checksum(self):
        output_raw = editor.serialize(self.document, {'officer_0_attack': 123})
        output = editor.decode(output_raw)
        start = self.document.payload_offset
        changed = {index for index, pair in enumerate(zip(self.document.raw, output_raw)) if pair[0] != pair[1]}
        self.assertLessEqual(changed, {start, start + 1, start + 0xBB})
        self.assertTrue(changed)
        self.assertEqual(output.payload[0xBB], 123)
        self.assertEqual(int.from_bytes(output.payload[:2], 'little'), sum(output.payload[4:]) % 65536)
        self.assertEqual(output.payload[2:4], b'\x03\x00')

    def test_bulk_max_respects_gameplay_limits_and_preserves_export(self):
        changes = editor.maximums(self.document, {})
        self.assertEqual(len(changes), 83)
        output = editor.decode(editor.serialize(self.document, changes))
        self.assertEqual(output.payload, editor.changed_payload(self.document, changes))
        allowed = {0, 1, *(offset for field in editor.FORMAT.fields if field.id in changes
                          for offset in range(field.offset, field.offset + field.size))}
        changed = {index for index, pair in enumerate(zip(self.document.payload, output.payload))
                   if pair[0] != pair[1]}
        self.assertLessEqual(changed, allowed)
        start, end = self.document.payload_offset, self.document.payload_offset + 34064
        self.assertEqual(output.raw[:start], self.document.raw[:start])
        self.assertEqual(output.raw[end:], self.document.raw[end:])
        self.assertEqual(output.entries, self.document.entries)
        for field in editor.FORMAT.fields:
            self.assertEqual(field.value(output.payload),
                             field.maximum if field.maxable else field.value(self.document.payload))

    def test_storage_bounds_and_difficulty_excluded_from_max(self):
        for key in ('difficulty', 'officer_0_life', 'officer_0_musou', 'officer_0_attack',
                    'officer_0_defense', 'officer_0_points', 'team_0_points'):
            self.assertFalse(editor.field_map(self.document)[key].maxable)
            self.assertEqual(editor.limit_values(self.document, {}, [key]), {})
        self.assertEqual(editor.stage(self.document, {}, 'officer_0_points', 65535),
                         {'officer_0_points': 65535})

    def test_items_translate_semantic_levels_to_bytes(self):
        for key, value, stored in (('item_0', 20, 19), ('item_13', 4, 3),
                                   ('item_19', 1, 0), ('item_40', 1, 0), ('item_40', 0, 255)):
            output = editor.decode(editor.serialize(self.document, {key: value}))
            field = editor.field_map(output)[key]
            self.assertEqual(field.value(output.payload), value)
            self.assertEqual(output.payload[field.offset], stored)

    def test_lv10_and_lv11_weapon_exp_are_distinct(self):
        key = 'officer_0_weapon_experience'
        for experience in (36000, 36001, 36002):
            output = editor.decode(editor.serialize(self.document, {key: experience}))
            self.assertEqual(editor.field_map(output)[key].value(output.payload), experience)
        self.assertEqual(editor.maximums(self.document, {}, 'Weapons')[key], 36002)
        with self.assertRaises(SaveError):
            editor.stage(self.document, {}, key, 36003)

    def test_higher_existing_values_survive_bulk_and_undo(self):
        inner = bytearray(procedural_inner())
        inner[0x798:0x79A] = (65535).to_bytes(2, 'little')
        inner[0x7F6] = 29
        document = editor.decode(procedural_psu(repair_inner(inner)))
        maxima = editor.maximums(document, {})
        self.assertNotIn('officer_0_weapon_experience', maxima)
        self.assertNotIn('item_0', maxima)
        staged = editor.stage(document, {}, 'officer_0_weapon_experience', 36002)
        self.assertEqual(editor.stage(document, staged, 'officer_0_weapon_experience', 65535), {})
        output = editor.decode(editor.serialize(document, maxima))
        self.assertEqual(output.payload[0x798:0x79A], b'\xff\xff')
        self.assertEqual(output.payload[0x7F6], 29)

    def test_equipped_items_names_record_identity_and_unknowns_unchanged(self):
        output = editor.decode(editor.serialize(self.document, editor.maximums(self.document, {})))
        for officer in range(42):
            base = 0xB8 + 24 * officer
            self.assertEqual(output.payload[base:base + 16], self.document.payload[base:base + 16])
            self.assertEqual(output.payload[base + 18:base + 24], self.document.payload[base + 18:base + 24])
        for team in range(4):
            base = 0x508 + 96 * team
            self.assertEqual(output.payload[base:base + 96], self.document.payload[base:base + 96])
        self.assertEqual(output.payload[0x820:], self.document.payload[0x820:])

    def test_named_read_only_inspection(self):
        rows = editor.inspection_rows(self.document)
        self.assertEqual(rows[0]['value'], 'PS2 / USA SLUS-20812')
        officer = next(row for row in rows if row['label'] == 'Zhao Yun')
        self.assertIn('Shadow Harness', officer['value'])
        self.assertIn('Vorpal Orb', officer['value'])
        self.assertIn('Empty', officer['value'])
        self.assertEqual(next(row for row in rows if row['label'] == 'Team 1')['value'], 'T1M0')
        self.assertEqual(editor.ITEM_NAMES[40], 'Horseshoes')
        self.assertIn('Lv.11=36002', editor.field_hint(self.document, 'officer_0_weapon_experience'))

    def test_review_layout_order_and_history(self):
        original = {'item_40': 1}
        changes = editor.stage(self.document, original, 'officer_0_attack', 99)
        self.assertEqual(original, {'item_40': 1})
        self.assertEqual(editor.stage(self.document, changes, 'officer_0_attack', 50), original)
        self.assertEqual([(field.id, before, after) for field, before, after in editor.review(self.document, changes)],
                         [('officer_0_attack', 50, 99), ('item_40', 0, 1)])

    def test_invalid_values_and_unmapped_fields_rejected(self):
        for key, values in (('officer_0_attack', (-1, 256, True, '5', 1.5, None)),
                            ('officer_0_points', (-1, 65536)), ('item_0', (21,)),
                            ('item_13', (5,)), ('item_40', (2,)), ('difficulty', (5,))):
            for value in values:
                with self.subTest(key=key, value=value), self.assertRaises(SaveError):
                    editor.stage(self.document, {}, key, value)
        for key in ('officer_0_unlocked', 'officer_42_attack', 'equipment', 'team_0_name', 'raw_byte'):
            with self.assertRaises(SaveError):
                editor.serialize(self.document, {key: 1})

    def test_inner_version_checksum_difficulty_and_markers_rejected(self):
        for offset, value, message in ((2, 4, 'version'), (0x9A, 5, 'difficulty'),
                                        (0xB8, 0, 'markers'), (0xBD, 1, 'markers')):
            inner = bytearray(procedural_inner())
            inner[offset] = value
            with self.subTest(offset=offset), self.assertRaisesRegex(SaveError, message):
                editor.decode(procedural_psu(repair_inner(inner)))
        inner = bytearray(procedural_inner())
        inner[0xBB] ^= 1
        with self.assertRaisesRegex(SaveError, 'checksum'):
            editor.decode(procedural_psu(inner))

    def test_all_officer_identity_sentinels_checked(self):
        for officer in range(42):
            inner = bytearray(procedural_inner())
            inner[0xB8 + 24 * officer + 5] ^= 1
            with self.subTest(officer=officer), self.assertRaisesRegex(SaveError, 'markers'):
                editor.decode(procedural_psu(repair_inner(inner)))

    def test_wrong_platform_region_raw_inner_and_invalid_container_rejected(self):
        for raw in (b'', b'\0' * 512, procedural_inner(), self.document.raw[:-1],
                    self.document.raw + b'\0', procedural_psu(root_name='BESLES-51888')):
            with self.assertRaises(SaveError):
                editor.decode(raw)
        for game_id in ('dw4hyper', 'dw8xl', 'pw3', 'origins'):
            with self.assertRaises(SaveError):
                editor.decode(self.document.raw, game_id)

    def test_wrong_gameplay_size_and_missing_payload_rejected(self):
        with self.assertRaisesRegex(SaveError, '34,064'):
            editor.decode(procedural_psu(procedural_inner()[:-1]))
        with self.assertRaisesRegex(SaveError, 'missing'):
            editor.decode(procedural_psu(order=('metadata', 'icon', 'extra')))

    def test_directory_count_modes_names_and_file_bounds_validated(self):
        modifications = (
            (4, (0).to_bytes(4, 'little')),
            (4, (0xFFFFFFFF).to_bytes(4, 'little')),
            (0, (0x8497).to_bytes(2, 'little')),
            (512, (0x8497).to_bytes(2, 'little')),
            (512 + 64, b'/' + bytes(31)),
        )
        for offset, value in modifications:
            raw = bytearray(self.document.raw)
            raw[offset:offset + len(value)] = value
            with self.subTest(offset=offset), self.assertRaises(SaveError):
                editor.decode(raw)
        entry = next(entry for entry in self.document.entries if entry.name == 'u.ico')
        raw = bytearray(self.document.raw)
        raw[entry.header_offset + 4:entry.header_offset + 8] = (0xFFFFFFFF).to_bytes(4, 'little')
        with self.assertRaises(SaveError):
            editor.decode(raw)

    def test_duplicate_payload_and_ambiguous_metadata_names_rejected(self):
        metadata = next(entry for entry in self.document.entries if entry.name == 'BASLUS-20812.sys')
        raw = bytearray(self.document.raw)
        raw[metadata.header_offset + 64:metadata.header_offset + 96] = b'BASLUS-20812'.ljust(32, b'\0')
        with self.assertRaises(SaveError):
            editor.decode(raw)
        icon = next(entry for entry in self.document.entries if entry.name == 'u.ico')
        raw = bytearray(self.document.raw)
        raw[icon.header_offset + 64:icon.header_offset + 96] = b'BASLUS-20812.sys'.ljust(32, b'\0')
        with self.assertRaisesRegex(SaveError, 'duplicate'):
            editor.decode(raw)

    def test_forged_snapshot_offset_entries_payload_and_layout_rejected(self):
        for document in (replace(self.document, payload=b'bad'), replace(self.document, payload_offset=0),
                         replace(self.document, entries=()), replace(self.document, seed=1),
                         replace(self.document, format=replace(editor.FORMAT, sample_verified=False))):
            with self.assertRaises(SaveError):
                editor.serialize(document, {})
        with self.assertRaises(TypeError):
            editor.field_map(self.document)['new'] = editor.FORMAT.fields[0]

    def test_backup_edit_restore_original_and_wrapper_preservation(self):
        snapshot = editor.backup(self.document)
        self.assertEqual(snapshot.suffix, '.psu')
        self.assertEqual(json.loads(snapshot.with_suffix('.json').read_text())['game_id'], 'dw4xl_ps2')
        output = editor.save_as(self.document, {'officer_0_attack': 99, 'item_40': 1}, self.folder / 'edited.psu')
        self.assertEqual(output.payload[0xBB], 99)
        self.assertEqual(output.payload[0x7F6 + 40], 0)
        restored = editor.restore(snapshot, self.folder / 'restored.psu')
        self.assertEqual(restored.read_bytes(), self.document.raw)
        self.assertEqual(self.source.read_bytes(), self.document.raw)

    def test_overwrite_changed_source_and_foreign_manifest_rejected(self):
        snapshot = editor.backup(self.document)
        with self.assertRaises(FileExistsError):
            editor.save_as(self.document, {}, self.source)
        with self.assertRaises(FileExistsError):
            editor.restore(snapshot, self.source)
        manifest = snapshot.with_suffix('.json')
        data = json.loads(manifest.read_text())
        data['game_id'] = 'dw4hyper'
        manifest.write_text(json.dumps(data))
        with self.assertRaises(SaveError):
            editor.restore(snapshot, self.folder / 'foreign.psu')
        self.assertFalse((self.folder / 'foreign.psu').exists())
        self.source.write_bytes(self.document.raw[:-1])
        with self.assertRaisesRegex(SaveError, 'changed on disk'):
            editor.save_as(self.document, {}, self.folder / 'changed.psu')
        self.assertFalse((self.folder / 'changed.psu').exists())

    def test_only_psu_extension_and_copy_safe_paths_allowed(self):
        for suffix in ('.sys', '.ico', '.dat', '.ps2'):
            path = self.folder / ('copy' + suffix)
            path.write_bytes(self.document.raw)
            with self.assertRaises(SaveError):
                editor.read_save(path)
            with self.assertRaises(SaveError):
                editor.save_as(self.document, {}, self.folder / ('edited' + suffix))
        live = self.folder / 'Steam' / 'userdata' / '1' / '2' / 'remote'
        live.mkdir(parents=True)
        with self.assertRaises(SaveError):
            editor.save_as(self.document, {}, live / 'edited.psu')


@unittest.skipUnless(os.environ.get('DW4XL_PSU_COPY'), 'No explicit genuine PS2 USA DW4 XL PSU export provided')
class ExplicitNativePS2SampleTests(unittest.TestCase):
    def test_native_export_noop_and_mapped_edits(self):
        document = editor.read_save(os.environ['DW4XL_PSU_COPY'])
        self.assertEqual(editor.serialize(document, {}), document.raw)
        changes = editor.maximums(document, {})
        output = editor.decode(editor.serialize(document, changes))
        self.assertEqual(output.payload, editor.changed_payload(document, changes))
        start, end = document.payload_offset, document.payload_offset + 34064
        self.assertEqual(output.raw[:start], document.raw[:start])
        self.assertEqual(output.raw[end:], document.raw[end:])
        for key, value in changes.items():
            self.assertEqual(editor.field_map(output)[key].value(output.payload), value)


if __name__ == '__main__':
    unittest.main()
