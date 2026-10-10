"""Lazy Elixir regression checks use a fully synthetic, small save in memory."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from koei_editor.games.dw3.models import Change, SaveError, fields
from koei_editor.games.dw3.save_codec import encrypt
from koei_editor.games.dw3.save_parser import ARRAY_LAYOUTS, parse_bytes
from koei_editor.games.dw3.save_writer import serialize
import koei_editor.games.dw3.progression_editor as progression


def string(value):
    raw = value.encode('utf-8') + b'\0'
    return struct.pack('<i', len(raw)) + raw


def typename(name, *children):
    return string(name) + struct.pack('<i', len(children)) + b''.join(children)


def tag(name, kind, payload, flags=0, metadata=b''):
    return string(name) + kind + struct.pack('<iB', len(payload), flags) + metadata + payload


def synthetic_reset_save(counter_tag=b''):
    """A valid test schema with one officer; no gameplay fixture is required."""
    scope = typename('/Script/Refine')
    integer = typename('IntProperty')
    boolean_array = typename('ArrayProperty', typename('BoolProperty'))
    record = b''.join(tag(name, integer, struct.pack('<i', 0)) for name in
                      ('MaxHealth', 'MaxMusou', 'Attack', 'Defence', 'WeaponDataID',
                       'SPoint', 'Progress', 'BGTeamID', 'MemCnt'))
    record += tag('BGMusouEquipItem',
                  typename('EnumProperty', typename('EGuardEquipItemID', scope),
                           typename('ByteProperty')), string('EGuardEquipItemID::NUM'))
    record += string('None')
    properties = []
    for name, struct_name in ARRAY_LAYOUTS.items():
        if struct_name is None:
            count = 42 if name == 'CanUseCharaArray' else 108
            properties.append(tag(name, boolean_array, struct.pack('<i', count) + bytes(count)))
        else:
            kind = typename('ArrayProperty', typename('StructProperty', typename(struct_name, scope)))
            count, body = (1, record) if name == 'PCSaveDataArray' else (0, b'')
            properties.append(tag(name, kind, struct.pack('<i', count) + body))
    properties.append(tag('EngiClearCharaArray', boolean_array, struct.pack('<iB', 1, 0)))
    header = (b'GVAS' + struct.pack('<iiiHHHI', 3, 522, 1017, 5, 6, 1, 0) +
              string('UE5') + struct.pack('<ii', 3, 0) +
              string('/Script/Refine.GameStatusSaveGame') + b'\0')
    payload = header + b''.join(properties) + counter_tag + string('None') + bytes(4)
    plain = struct.pack('>I', len(payload)) + payload
    plain += bytes((-len(plain)) % 16)
    return parse_bytes(encrypt(plain))


class LazyElixirSyntheticTests(unittest.TestCase):
    def test_reset_without_counter_exposes_zero_and_preserves_zero_noop(self):
        document = synthetic_reset_save()
        self.assertEqual(progression.elixir_state(document),
                         {'value': 0, 'saved_value': 0, 'editable': True, 'reason': ''})
        for changes in ([], [progression.elixir_count_change(0)]):
            raw, audit = serialize(document, changes)
            self.assertEqual(raw, document.encrypted)
            self.assertEqual(audit['plaintext_changes'], [])
            self.assertEqual(audit['changed_aes_blocks'], [])
        for value in (3, 999):
            raw, audit = serialize(document, [progression.elixir_count_change(value)])
            result = parse_bytes(raw)
            self.assertEqual(result.properties['BeansNum']['value'], value)
            self.assertEqual(audit['output_payload_size'] - audit['source_payload_size'], 42)
            self.assertEqual(result.parsed['padding_size'], (-4 - result.parsed['payload_size']) % 16)
            self.assertEqual(serialize(result)[0], raw)

    def test_first_clear_creates_three_elixirs_and_does_not_award_again(self):
        document = synthetic_reset_save()
        changes = progression.musou_clear_changes(document, 0)
        self.assertEqual(progression.elixir_state(document, changes)['value'], 3)
        raw, _ = serialize(document, changes)
        result = parse_bytes(raw)
        self.assertEqual(result.properties['BeansNum']['value'], 3)
        self.assertEqual(result.properties['EngiClearCharaArray']['value']['values'], [1])
        self.assertEqual(fields(result.records('PCSaveDataArray')[0])['Progress']['value'],
                         progression.ROUTES[0]['route_length'])
        self.assertEqual(serialize(result, changes)[0], raw)

    def test_first_clear_and_side_arrays_share_insertion_with_final_balance(self):
        document = synthetic_reset_save()
        clears = progression.musou_clear_changes(document, 0)
        sides = progression.side_story_changes()
        for value in (0, 17):
            explicit = progression.elixir_count_change(value)
            changes = [explicit, *clears, *sides]
            raw, audit = serialize(document, changes)
            self.assertEqual(raw, serialize(document, [*sides, *clears, explicit])[0])
            result = parse_bytes(raw)
            self.assertEqual(progression.elixir_state(result)['value'], value)
            self.assertEqual('BeansNum' in result.properties, value != 0)
            for name in progression.SIDE_ARRAYS:
                self.assertEqual(result.properties[name]['value']['values'], [1, 1, 1])
            self.assertEqual(sum(row['old_length'] == 0 for row in audit['plaintext_changes']), 1)
            self.assertEqual(serialize(result, changes)[0], raw)

    def test_existing_unsupported_tags_remain_view_only(self):
        tags = [
            tag('BeansNum', typename('FloatProperty'), struct.pack('<f', 3.0)),
            tag('BeansNum', typename('IntProperty'), bytes(8)),
            tag('BeansNum', typename('IntProperty'), struct.pack('<i', 3), 1, struct.pack('<i', 1)),
            tag('BeansNum', typename('IntProperty'), struct.pack('<i', 3), 2, bytes(16)),
        ]
        for counter_tag in tags:
            with self.subTest(counter_tag=counter_tag.hex()):
                document = synthetic_reset_save(counter_tag)
                self.assertFalse(progression.elixir_state(document)['editable'])
                self.assertEqual(serialize(document)[0], document.encrypted)
                for changes in ([progression.elixir_count_change(0)],
                                progression.musou_clear_changes(document, 0)):
                    with self.assertRaises(SaveError):
                        serialize(document, changes)


if __name__ == '__main__':
    unittest.main()
