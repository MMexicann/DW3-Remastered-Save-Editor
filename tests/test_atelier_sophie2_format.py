"""Published Sophie 2 format tests; procedural saves are not game evidence."""
from dataclasses import replace
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import atelier_sophie2_codec as codec
import atelier_sophie2_parser as editor
from models import SaveError


REFERENCE_PAYLOAD = bytes.fromhex('4174656c69657220536f706869652032207265666572656e636500017f80ff21')
# Frozen output of upstream sophie2_codec.encode_body at commit 93d8070,
# generated separately before adapter implementation; synthetic, not a game save.
REFERENCE_ENCRYPTED = bytes.fromhex(
    'f53c8ee0fd0fd74ff4723c7e1bb3657c14dfd71ee4428a9f8b12c670b83a87cb5'
    'bbc8582eea77b40562134138b37da0f45ad8fbeb1d33fc70d2ece228ce387ee3'
    '00a95ad38ddd4faa90e50d8bb81db60')


def _item(identity=-1, quality=10, instance=0):
    record = bytearray((i * 13 + 17) % 256 for i in range(44))
    struct.pack_into('<H', record, 0, instance)
    struct.pack_into('<hH', record, 4, identity, quality)
    return bytes(record)


def _node(name, value):
    marker = name + b'\0'
    return struct.pack('<I', len(marker) + 11) + marker + b'\x01\x22\x33' + struct.pack('<I', value)


@lru_cache(maxsize=1)
def procedural_payload():
    """Build published structural facts independently, with distinctive unknown data."""
    result = bytearray(b'unknown-envelope-body\x19\x87')
    # Capacities and record widths come from upstream self_test.py; this is not
    # an actual save nor a supported new-game save generator.
    for marker, count in ((b'm_unitContainer\0', 9999), (b'm_unitContainerImportant\0', 150),
                          (b'm_unitContainerExpendable\0', 50)):
        result.extend(struct.pack('<I', len(marker) + 8 + 44 * count))
        result.extend(marker + struct.pack('<I', count))
        for index in range(count):
            # Keep most slots empty; one higher existing quality proves that
            # Max preserves unusual values and no empty slot is manufactured.
            identity = 37 + index if index < 2 and count != 50 else -1
            result.extend(_item(identity, 1200 if index == 1 else 100, 150 + index))
    result.extend(_node(b'limitSize', 123))
    for marker, count in ((b'explore_equip_item\0', 15), (b'adventure_equip_item\0', 25)):
        result.extend(struct.pack('<I', len(marker) + 8 + 44 * count))
        result.extend(marker + struct.pack('<I', count))
        for index in range(count):
            result.extend(_item(61 if index == 0 else -1, 44, 300 + index))
    result.extend(_node(b'bonus', 998))
    result.extend(_node(b'mix_lv', 7))
    result.extend(_node(b'lv', 8))
    result.extend(_node(b'exp', 1234))
    result.extend(_node(b'plachta_lv', 9))
    result.extend(_node(b'plachta_exp', 2345))
    marker = b'm_mixGem\0'
    result.extend(struct.pack('<I', len(marker) + 3 + 4 + 4))
    result.extend(marker + b'\x02\x44\x66' + struct.pack('<I', 4))
    result.extend(_node(b'm_mixMistList', 567))
    result.extend(_node(b'party', 666))
    for identity in range(6):
        party = bytearray((i * 17 + identity * 19 + 3) % 256 for i in range(0x314))
        party[:6] = b'Party\0'
        struct.pack_into('<i', party, 9, identity)
        for index in range(8):
            offset = 0x176 + index * 44
            party[offset:offset + 44] = _item(101 + identity if index == 0 else -1, 70 + identity, 500 + identity)
        result.extend(party)
    result.extend(_node(b'm_squad', 42))
    result.extend(b'opaque-story-and-dlc-bytes\x16\xf3\xff\0\0\0')
    return bytes(result)


@lru_cache(maxsize=1)
def procedural_raw():
    return codec.encode_file(bytes(range(256)), procedural_payload(), 0x12345678) + bytes(32)


class Sophie2CodecTests(unittest.TestCase):
    def test_frozen_upstream_known_answer_both_directions(self):
        decoded, envelope = codec.decode_body(REFERENCE_ENCRYPTED)
        self.assertEqual(decoded, REFERENCE_PAYLOAD)
        self.assertEqual(envelope.seed, 0x12345678)
        self.assertEqual(codec.encode_body(REFERENCE_PAYLOAD, envelope.seed), REFERENCE_ENCRYPTED)

    def test_all_byte_reference_matches_upstream_digest(self):
        payload = bytes((i * 37) % 256 for i in range(8192))
        raw = codec.encode_file(bytes(range(256)), payload, 0x12345678)
        self.assertEqual(len(raw), 14064)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         '99102de2fed87b7d3b6f06c933e6a946becf27ace604f17f2f98c4422039514f')
        header, decoded, _ = codec.decode_file(raw)
        self.assertEqual(header, bytes(range(256)))
        self.assertEqual(decoded, payload)

    def test_compression_all_values_and_trailing_zeros(self):
        for payload in (bytes(range(256)), b'A\0\0\0', bytes(101), b'\xff'):
            with self.subTest(size=len(payload)):
                raw = codec.encode_file(bytes(256), payload, 7)
                self.assertEqual(codec.decode_file(raw)[1], payload)

    def test_malformed_compressed_streams_and_processing_bounds(self):
        zero_code = codec._decode_zero_code
        palette = codec._decode_palette
        for value in (b'', b'\0', struct.pack('>I', codec.MAX_DECODED_SIZE + 262),
                      struct.pack('>I', 1)):
            with self.subTest(zero=value), self.assertRaises(codec.SaveFormatError):
                zero_code(value)
        for value in (b'', b'\x01A', b'\x01A' + struct.pack('>I', 1),
                      b'\x01A' + struct.pack('>I', 1) + b'\x02',
                      codec._encode_palette(b'hello') + b'UNMAPPED',
                      b'\x01A' + struct.pack('>I', codec.MAX_DECODED_SIZE + 1)):
            with self.subTest(palette=value), self.assertRaises(codec.SaveFormatError):
                palette(value)
        for seed in (-1, 2 ** 32, True):
            with self.assertRaises(codec.SaveFormatError):
                codec.encode_body(b'x', seed)
        for footer in (b'', b'1234', 'XYZ'):
            with self.assertRaises(codec.SaveFormatError):
                codec.encode_body(b'x', 7, footer)

    def test_foreign_truncated_and_corrupt_encrypted_data_rejected(self):
        for raw in (b'', bytes(256), bytes(1024), b'\xff' * 512,
                    bytes(256) + REFERENCE_ENCRYPTED[:-1]):
            with self.assertRaises(codec.SaveFormatError):
                codec.decode_file(raw)
        for offset in (0, 17, len(REFERENCE_ENCRYPTED) - 1):
            raw = bytearray(REFERENCE_ENCRYPTED)
            raw[offset] ^= 0x08
            with self.assertRaises(codec.SaveFormatError):
                codec.decode_body(raw)


class Sophie2PublishedFormatTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.source = self.folder / 'copy.dat'
        self.source.write_bytes(procedural_raw())
        self.document = editor.read_save(self.source)

    def tearDown(self):
        self.temp.cleanup()

    def test_published_status_dynamic_existing_fields_and_inspection(self):
        self.assertFalse(editor.FORMAT.sample_verified)
        self.assertIn('checks pending', editor.FORMAT.note)
        fields = editor.field_map(self.document)
        self.assertEqual(len(fields), 14)
        self.assertNotIn('materials_2_quality', fields)
        self.assertNotIn('expendable_0_quality', fields)
        self.assertNotIn('character_0_1_quality', fields)
        self.assertEqual(fields['sophie_exp'].value(self.document.payload), 1234)
        self.assertEqual(fields['plachta_exp'].value(self.document.payload), 2345)
        rows = editor.inspection_rows(self.document)
        self.assertEqual(rows[0]['value'], 9)
        self.assertEqual(rows[1]['value'], 4)
        self.assertEqual(len(rows), 15)

    def test_no_edit_exact_original_container_and_compression(self):
        self.assertEqual(editor.serialize(self.document, {}), procedural_raw())
        self.assertEqual(self.document.header, bytes(range(256)))
        self.assertEqual(self.document.trailer, bytes(32))
        self.assertTrue(self.document.payload.endswith(bytes(3)))
        self.assertEqual(self.document.seed, 0x12345678)

    def test_quality_and_exp_changes_preserve_every_other_decoded_byte(self):
        changes = {'materials_0_quality': 999, 'sophie_exp': 3456,
                   'character_3_0_quality': 111, 'adventure_0_quality': 321}
        raw = editor.serialize(self.document, changes)
        output = editor.decode(raw)
        fields = editor.field_map(self.document)
        allowed = {i for key in changes for i in range(fields[key].offset, fields[key].offset + fields[key].size)}
        changed = {i for i, (old, new) in enumerate(zip(self.document.payload, output.payload)) if old != new}
        self.assertLessEqual(changed, allowed)
        self.assertEqual(len(output.payload), len(self.document.payload))
        for key, expected in changes.items():
            self.assertEqual(fields[key].value(output.payload), expected)
        self.assertEqual(output.header, self.document.header)
        self.assertEqual(output.trailer, self.document.trailer)
        self.assertEqual(output.seed, self.document.seed)
        self.assertEqual(output.payload[-32:], self.document.payload[-32:])
        self.assertEqual(self.source.read_bytes(), procedural_raw())

    def test_opaque_envelope_footer_preserved_in_edited_encoding(self):
        raw = codec.encode_file(self.document.header, self.document.payload, self.document.seed, b'XYZ')
        document = editor.decode(raw + bytes(32))
        self.assertEqual(document.footer, b'XYZ')
        self.assertEqual(editor.serialize(document, {}), raw + bytes(32))
        output = editor.decode(editor.serialize(document, {'materials_0_quality': 222}))
        self.assertEqual(output.footer, b'XYZ')
        self.assertEqual(output.header, document.header)
        self.assertEqual(output.trailer, document.trailer)
        self.assertEqual(output.payload, editor.changed_payload(document, {'materials_0_quality': 222}))

    def test_max_only_quality_never_reduces_unusual_existing_values(self):
        maximums = editor.maximums(self.document, {})
        self.assertNotIn('sophie_exp', maximums)
        self.assertNotIn('plachta_exp', maximums)
        self.assertNotIn('materials_1_quality', maximums)
        self.assertNotIn('important_1_quality', maximums)
        self.assertEqual(editor.limit_values(self.document, {}, ['sophie_exp']), {})
        output = editor.decode(editor.serialize(self.document, maximums))
        for field in editor.fields_for(output):
            before = field.value(self.document.payload)
            self.assertEqual(field.value(output.payload), 999 if field.maxable and before <= 999 else before)
        self.assertEqual(editor.maximums(self.document, {}, 'Alchemy'), {})

    def test_stage_review_unstage_and_invalid_fields(self):
        original = {'plachta_exp': 4567}
        after = editor.stage(self.document, original, 'materials_0_quality', 998)
        self.assertEqual(original, {'plachta_exp': 4567})
        self.assertEqual(editor.stage(self.document, after, 'materials_0_quality', 100), original)
        high = editor.stage(self.document, {}, 'materials_1_quality', 999)
        self.assertEqual(editor.stage(self.document, high, 'materials_1_quality', 1200), {})
        self.assertEqual([field.id for field, _, _ in editor.review(self.document, after)],
                         ['plachta_exp', 'materials_0_quality'])
        for key, values in (('materials_0_quality', (-1, 1000, True, 1.5, '1')),
                            ('sophie_exp', (-1, 2 ** 31, True))):
            for value in values:
                with self.subTest(key=key, value=value), self.assertRaises(SaveError):
                    editor.serialize(self.document, {key: value})
        for key in ('materials_2_quality', 'item_id', 'm_mixGem', 'sophie_lv', 'traits'):
            with self.assertRaises(SaveError):
                editor.stage(self.document, {}, key, 1)
            with self.assertRaises(SaveError):
                editor.serialize(self.document, {key: 1})

    def test_wrong_game_tags_capacities_and_duplicate_characters_rejected(self):
        payload = self.document.payload
        cases = [payload.replace(b'plachta_lv\0', b'unknown_lv\0'),
                 payload.replace(b'm_unitContainerImportant\0', b'x_unitContainerImportant\0'),
                 payload.replace(b'plachta_lv\0', b'plachta_lv\0' * 2)]
        first_item = editor.field_map(self.document)['materials_0_quality'].offset - 6
        cases.append(payload[:first_item] + payload[first_item + 44:])
        party_positions = [i for i in range(len(payload)) if payload.startswith(b'Party\0', i)]
        duplicate = bytearray(payload)
        struct.pack_into('<i', duplicate, party_positions[-1] + 9, 0)
        cases.append(bytes(duplicate))
        gem = payload.index(b'm_mixGem\0')
        bad_distance = bytearray(payload)
        bad_distance[gem - 4:gem] = bytes(4)
        cases.append(bytes(bad_distance))
        for index, altered in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(SaveError):
                editor.decode(codec.encode_file(self.document.header, altered, self.document.seed))
        with self.assertRaises(SaveError):
            editor.decode(procedural_raw(), 'atelier_ryza')
        with self.assertRaises(SaveError):
            editor.decode(bytes(700))

    def test_corruption_is_not_silently_repaired(self):
        raw = bytearray(self.document.raw)
        raw[500] ^= 1
        with self.assertRaisesRegex(SaveError, 'integrity/codec'):
            editor.decode(raw)

    def test_scalar_start_before_item_record_cannot_write_identity_bytes(self):
        payload = bytearray(self.document.payload)
        # Move the unique alchemy tags into otherwise opaque Party bytes. EXP
        # begins two bytes before equipment and would overlap its instance ID.
        for marker in (b'mix_lv\0', b'exp\0', b'plachta_lv\0', b'plachta_exp\0'):
            position = payload.find(marker)
            payload[position] = ord('x')
        equipment = editor.field_map(self.document)['character_0_0_quality'].offset - 6
        equipment_end = equipment + 8 * 44
        for position, marker in ((equipment - 28, b'mix_lv\0'),
                                 (equipment - 9, b'exp\0'),
                                 (equipment_end - 40, b'plachta_lv\0'),
                                 (equipment_end - 15, b'plachta_exp\0')):
            payload[position:position + len(marker)] = marker
        raw = codec.encode_file(self.document.header, bytes(payload), self.document.seed)
        with self.assertRaisesRegex(SaveError, 'overlap'):
            editor.decode(raw)

    def test_forged_immutable_snapshot_rejected(self):
        for forged in (replace(self.document, payload=b'changed'), replace(self.document, seed=7),
                       replace(self.document, header=bytes(256)), replace(self.document, trailer=b'bad'),
                       replace(self.document, footer=b'bad'),
                       replace(self.document, format=replace(editor.FORMAT, sample_verified=True))):
            with self.assertRaises(SaveError):
                editor.serialize(forged, {})
        with self.assertRaises(TypeError):
            editor.field_map(self.document)['bad'] = None

    def test_save_backup_restore_and_source_preservation(self):
        backup = editor.backup(self.document)
        self.assertEqual(backup.read_bytes(), self.document.raw)
        metadata = json.loads(backup.with_suffix('.json').read_text())
        self.assertEqual(metadata['game_id'], editor.GAME_ID)
        output = editor.save_as(self.document, {'sophie_exp': 4444}, self.folder / 'edited.dat')
        self.assertEqual(editor.field_map(output)['sophie_exp'].value(output.payload), 4444)
        restored = editor.restore(backup, self.folder / 'restored.dat')
        self.assertEqual(restored.read_bytes(), self.document.raw)
        self.assertEqual(self.source.read_bytes(), self.document.raw)
        for target in (self.source, restored):
            before = target.read_bytes()
            with self.assertRaises(FileExistsError):
                editor.save_as(self.document, {}, target)
            with self.assertRaises(FileExistsError):
                editor.restore(backup, target)
            self.assertEqual(target.read_bytes(), before)

    def test_source_change_and_bad_restore_manifest_rejected(self):
        self.source.write_bytes(b'changed')
        destination = self.folder / 'edited.dat'
        with self.assertRaisesRegex(SaveError, 'changed on disk'):
            editor.save_as(self.document, {}, destination)
        self.assertFalse(destination.exists())
        self.assertFalse((self.folder / 'WarriorsEditorBackups').exists())
        self.source.write_bytes(self.document.raw)
        backup = editor.backup(self.document)
        metadata = json.loads(backup.with_suffix('.json').read_text())
        metadata['game_id'] = 'atelier_ryza'
        backup.with_suffix('.json').write_text(json.dumps(metadata))
        with self.assertRaises(SaveError):
            editor.restore(backup, destination)
        self.assertFalse(destination.exists())

    def test_extension_live_paths_and_resolved_aliases_rejected(self):
        other = self.folder / 'copy.bin'
        other.write_bytes(self.document.raw)
        with self.assertRaises(SaveError):
            editor.read_save(other)
        with self.assertRaises(SaveError):
            editor.save_as(self.document, {}, other)
        live = self.folder / 'Documents' / 'KoeiTecmo' / 'Atelier Sophie 2' / 'GameData00'
        live.mkdir(parents=True)
        source = live / 'data.dat'
        source.write_bytes(self.document.raw)
        with self.assertRaises(SaveError):
            editor.read_save(source)
        with self.assertRaises(SaveError):
            editor.save_as(self.document, {}, live / 'other.dat')
        with self.assertRaises(SaveError):
            editor.read_save(r'C:\Users\Player\Documents\KoeiTecmo\Atelier Sophie 2\AutoSave\data.dat')
        alias = self.folder / 'alias.dat'
        try:
            alias.symlink_to(source)
        except (OSError, NotImplementedError):
            return
        with self.assertRaises(SaveError):
            editor.read_save(alias)
        with self.assertRaises(SaveError):
            editor.save_as(self.document, {}, alias)

    def test_backup_folder_alias_to_live_directory_rejected(self):
        live = self.folder / 'KoeiTecmo' / 'Atelier Sophie 2' / 'AutoSave'
        live.mkdir(parents=True)
        alias = self.folder / 'WarriorsEditorBackups'
        try:
            alias.symlink_to(live, target_is_directory=True)
        except (OSError, NotImplementedError):
            return
        with self.assertRaises(SaveError):
            editor.backup(self.document)
        with self.assertRaises(SaveError):
            editor.save_as(self.document, {'sophie_exp': 4444}, self.folder / 'edited.dat')
        self.assertEqual(list(live.iterdir()), [])
        self.assertFalse((self.folder / 'edited.dat').exists())


@unittest.skipUnless(os.environ.get('SOPHIE2_SAVE_COPY'), 'No explicit Steam Sophie 2 save copy provided')
class ExplicitSophie2SampleTests(unittest.TestCase):
    def test_native_copy_roundtrip_and_targeted_quality_edit(self):
        document = editor.read_save(os.environ['SOPHIE2_SAVE_COPY'])
        self.assertEqual(editor.serialize(document, {}), document.raw)
        fields = editor.fields_for(document)
        field = next((field for field in fields if field.maxable), None)
        self.assertIsNotNone(field, 'Provided copy has no existing quality record')
        changes = {field.id: min(field.value(document.payload) + 1, field.maximum)}
        output = editor.decode(editor.serialize(document, changes))
        self.assertEqual(output.payload, editor.changed_payload(document, changes))
        self.assertEqual(output.header, document.header)
        self.assertEqual(output.seed, document.seed)


if __name__ == '__main__':
    unittest.main()
