"""Procedural layout fixtures; these are never presented as player-save evidence."""
import os
from pathlib import Path
import struct
import tempfile
import unittest

from koei_editor.games.sophie import parser as p
from koei_editor.games.dw3.models import SaveError
from tests.scalar_contract import ScalarContractTests


def node(name, content):
    body = name.encode() + b'\0' + content
    return (len(body) + 4).to_bytes(4, 'little') + body


def fixture():
    raw = bytearray(b'\xa5' * p.SAVE_SIZE)
    raw[:32] = p.HEADER
    roots = {}
    cursor = 32
    for name, size in p.ROOTS:
        head = size.to_bytes(4, 'little') + name.encode() + b'\0'
        raw[cursor:cursor + len(head)] = head
        roots[name] = (cursor + len(head), cursor + size)
        cursor += size
    def put(root, content):
        start, end = roots[root]
        assert start + len(content) <= end
        raw[start:start + len(content)] = content
    put('money', node('money', (1043).to_bytes(4, 'big') + b'UNKN'))
    put('quest', node('numOfTickets', (4).to_bytes(4, 'big') + (21).to_bytes(4, 'big')))
    put('mix_lv', node('m_lv', (3).to_bytes(4, 'big')) + node('m_exp', (400).to_bytes(4, 'big')))
    party = node('version', b'\0\2') + (9).to_bytes(4, 'big')
    for identity in range(9):
        party += node('Party', identity.to_bytes(4, 'big') + b'\x93' * (0x3d4 - 14))
    party += node('m_squad', b'\x91' * 52) + node('m_battleMember', b'\x92' * 20)
    put('party', party)
    item = node('version', b'\0\2')
    for key, label, name, count, editable in p.POOLS:
        records = bytearray((b'\xff' * 4 + bytes(4) + b'\x98' * 48) * count)
        if editable:
            records[:8] = struct.pack('>HHf', 7, 42, 120)
            records[56:64] = struct.pack('>HHf', 8, 43, 1200)
            records[112:120] = struct.pack('>HHf', 9, 44, 12.5)
            records[168:176] = struct.pack('>HHf', 10, 45, float('nan'))
        else:
            records[:8] = struct.pack('>HHf', 11, 46, 10)
        item += node(name, len(records).to_bytes(4, 'big') + records)
    put('item', item)
    return bytes(raw)


class SophieFormatTests(unittest.TestCase):
    def setUp(self):
        self.raw = fixture()
        self.doc = p.decode(self.raw)

    def test_noop_and_surgical_fields(self):
        self.assertEqual(p.serialize(self.doc, {}), self.raw)
        mapping = p.field_map(self.doc)
        self.assertEqual(set(mapping), {'cole', 'tickets', 'basket_1_quality', 'basket_2_quality',
                                        'container_1_quality', 'container_2_quality'})
        for key, field in mapping.items():
            value = 999 if field.encoding == 'float32_be' else 123
            edited = p.serialize(self.doc, p.stage(self.doc, {}, key, value))
            self.assertEqual(edited[:field.offset], self.raw[:field.offset])
            self.assertEqual(edited[field.offset + field.size:], self.raw[field.offset + field.size:])
            self.assertEqual(field.value(edited), value)
        self.assertEqual(p.maximums(self.doc, {}), {})
        self.assertEqual(p.limit_values(self.doc, {}, mapping), {})

    def test_bounds_unusual_and_dependencies(self):
        mapping = p.field_map(self.doc)
        for key, field in mapping.items():
            for value in (True, 1.0, -1, field.maximum + 1):
                if value == field.value(self.raw) and type(value) is int:
                    continue
                with self.assertRaises(SaveError):
                    p.stage(self.doc, {}, key, value)
        for key in ('basket_2_quality', 'container_2_quality'):
            changes = p.stage(self.doc, {}, key, 999)
            self.assertEqual(p.stage(self.doc, changes, key, 1200), {})
        for key in ('basket_3_quality', 'basket_4_quality', 'important_1_quality', 'alchemy_exp', 'calendar'):
            with self.assertRaises(SaveError):
                p.stage(self.doc, {}, key, 10)
        for bad in ({'unknown': 10}, {'cole': True}, [], None):
            with self.assertRaises(SaveError):
                p.stage(self.doc, bad, 'cole', 10)
            with self.assertRaises(SaveError):
                p.limit_values(self.doc, bad, [])

    def test_malformed_foreign_profile(self):
        for raw in (self.raw[:-1], self.raw + b'\0', b'\0' * p.SAVE_SIZE):
            with self.assertRaises(SaveError):
                p.decode(raw)
        for offset in (0, 32, 32 + 4, self.raw.index(b'm_unitContainer\0') - 4,
                       self.raw.index(b'm_unitContainer\0') + len('m_unitContainer') + 1):
            bad = bytearray(self.raw)
            bad[offset] ^= 1
            with self.assertRaises(SaveError):
                p.decode(bad)
        bad = bytearray(self.raw)
        start = bad.index(b'Party\0') + len('Party') + 1
        bad[start:start + 4] = (1).to_bytes(4, 'big')
        with self.assertRaises(SaveError):
            p.decode(bad)
        for root_tag in ('item', 'party'):
            bad = bytearray(self.raw)
            root_pos = bad.index(root_tag.encode() + b'\0')
            version_pos = bad.index(b'version\0', root_pos) + len(b'version\0')
            bad[version_pos:version_pos + 2] = b'\0\3'
            with self.assertRaises(SaveError):
                p.decode(bad)
        with self.assertRaises(SaveError):
            p.decode(self.raw, 'atelier_sophie_dx')

    def test_copy_backup_restore_and_source_change(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'GAMEDATA00'
            source.write_bytes(self.raw)
            doc = p.read_save(source)
            dest = Path(folder) / 'GAMEDATA01'
            edited = p.save_as(doc, {'cole': 20}, dest)
            self.assertEqual(p.field_map(edited)['cole'].value(edited.payload), 20)
            snapshots = list((source.parent / 'WarriorsEditorBackups').glob('*'))
            self.assertTrue(snapshots)
            native = [entry for entry in snapshots if entry.is_file() and entry.suffix != '.json']
            self.assertTrue(native)
            restored = Path(folder) / 'GAMEDATA02'
            p.restore(native[0], restored)
            self.assertEqual(restored.read_bytes(), self.raw)
            with self.assertRaises(FileExistsError):
                p.save_as(doc, {}, dest)
            source.write_bytes(b'changed')
            with self.assertRaises(SaveError):
                p.save_as(doc, {}, Path(folder) / 'GAMEDATA03')
            with self.assertRaises(SaveError):
                p.read_save(Path(folder) / 'SYSTEM.DAT')
            with self.assertRaises(SaveError):
                p.save_as(doc, {}, Path(folder) / 'SAVE.pcsave')

    @unittest.skipUnless(os.environ.get('SOPHIE_SAVE_COPIES'), 'Private original Sophie copies not supplied')
    def test_genuine_original_snapshots(self):
        paths = sorted(Path(os.environ['SOPHIE_SAVE_COPIES']).glob('GAMEDATA*'))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(slot=path.name):
                doc = p.read_save(path)
                self.assertEqual(p.serialize(doc, {}), path.read_bytes())
                mapping = p.field_map(doc)
                selected = [mapping['cole'], mapping['tickets']]
                for group in ('Basket', 'Container'):
                    eligible = next((f for f in mapping.values() if f.group == group), None)
                    if eligible:
                        selected.append(eligible)
                for field in selected:
                    changed = p.serialize(doc, {field.id: min(999, field.maximum)})
                    self.assertEqual(changed[:field.offset], doc.raw[:field.offset])
                    self.assertEqual(changed[field.offset + field.size:], doc.raw[field.offset + field.size:])


class SophieScalarContractTests(ScalarContractTests, unittest.TestCase):
    game_id = p.GAME_ID

    def fixture_bytes(self):
        return fixture()


if __name__ == '__main__':
    unittest.main()
