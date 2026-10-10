"""Procedural and optional genuine US Strikeforce inspection qualification."""
from dataclasses import replace
import os
from pathlib import Path
import struct
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.research.strikeforce_ps3 import inspection


def metadata(directory=inspection.DIRECTORY):
    key, value = b'SAVEDATA_DIRECTORY\0', directory.encode('ascii') + b'\0'
    return (struct.pack('<5I', 0x46535000, 0x101, 36, 36 + len(key), 1)
            + struct.pack('<HH3I', 0, 0x204, len(value), len(value), 0) + key + value)


def fixture():
    raw = bytearray(inspection.SAVE_SIZE)
    for slot in range(2):
        base = slot * inspection.SLOT_STRIDE
        raw[base + 0x64:base + 0x68] = b'\0\0\0\xc8'
        name = b'Procedural' + bytes(22)
        raw[base + 0x74:base + 0x94] = name
        raw[base + 0xB1:base + 0xD1] = name
        raw[base + 0xD8] = 3
        for officer in range(42):
            start = base + 0x1874 + officer * 0x40
            raw[start + 4] = officer
            raw[start + 6:start + 8] = (officer + 1).to_bytes(2, 'big')
            raw[start + 8:start + 12] = (officer * 4321).to_bytes(4, 'big')
        raw[base + 0x9B8:base + 0xA7C] = bytes([255]) * 196
        for row, identity, flag, quantity in ((0, 197, 1, 150), (1, 7, 1, 3),
                                             (2, 255, 1, 99), (3, 7, 0, 99),
                                             (4, 7, 1, 0), (5, 188, 1, 10),
                                             (6, 7, 2, 99), (195, 8, 1, 98)):
            raw[base + 0x9B8 + row] = identity
            raw[base + 0xA7C + row] = flag
            raw[base + 0xB44 + row] = quantity
        raw[base + 0x1588:base + 0x158C] = (9999999).to_bytes(4, 'big')
    # Cheat-created money in an empty slot must not manufacture a player.
    raw[2 * inspection.SLOT_STRIDE + 0x1588:2 * inspection.SLOT_STRIDE + 0x158C] = b'\xff' * 4
    raw[0x48000:0x48064] = bytes(range(100))
    return bytes(raw)


class StrikeforcePS3Tests(unittest.TestCase):
    def test_noop_immutable_anonymous_inspection_and_no_writer(self):
        raw = fixture()
        snapshot = inspection.inspect(raw, inspection.DIRECTORY)
        self.assertEqual(inspection.unchanged_bytes(snapshot), raw)
        self.assertFalse(snapshot.editable)
        self.assertFalse(snapshot.qualified_game_profile)
        self.assertFalse(snapshot.native_integrity_qualified)
        self.assertIsNone(snapshot.native_revision)
        self.assertEqual([slot.qualified_existing_record for slot in snapshot.slots], [True, True, False])
        self.assertEqual([len(slot.officers) for slot in snapshot.slots], [42, 42, 0])
        self.assertEqual(snapshot.slots[2].candidate_gold, 0xFFFFFFFF)
        for operation in ('stage', 'serialize', 'save_as', 'restore', 'maximums'):
            self.assertFalse(hasattr(inspection, operation))
        tables = inspection.inspection_tables(snapshot)
        self.assertEqual(len(tables), 4)
        self.assertNotIn('Procedural', repr(tables))
        self.assertNotIn('Procedural', repr(snapshot))

    def test_parallel_array_alignment_last_row_and_dependencies(self):
        rows = inspection.inspect(fixture(), inspection.DIRECTORY).slots[0].storehouse
        self.assertEqual(len(rows), 196)
        self.assertEqual([row.row for row in rows if row.existing_positive_row], [1, 2, 196])
        self.assertEqual(rows[0].material_id, 197)
        self.assertEqual(rows[0].quantity, 150)
        self.assertEqual(rows[195].material_id, 8)
        self.assertEqual(rows[195].quantity, 98)
        self.assertFalse(rows[2].known_material_id)  # FF remains empty despite patched ownership.
        self.assertFalse(rows[5].known_material_id)  # Unmapped ID is not invented.
        self.assertEqual(rows[1].material_id, rows[3].material_id)  # Duplicates preserved.

    def test_reject_wrong_size_region_encryption_empty_and_mutable(self):
        raw = fixture()
        for bad in (raw[:-1], raw + b'\0', bytearray(raw), b'\xff' * inspection.SAVE_SIZE,
                    bytes(inspection.SAVE_SIZE)):
            with self.subTest(length=len(bad)), self.assertRaises(SaveError):
                inspection.inspect(bad, inspection.DIRECTORY)
        for directory in ('BLES00825-SAVEDATA', 'BLUS30471-SAVEDATA-extra', 'ULUS10416', ''):
            with self.subTest(directory=directory), self.assertRaises(SaveError):
                inspection.inspect(raw, directory)

    def test_two_slot_structural_corruption_never_hides_damaged_record(self):
        for offset, value in ((0x64, 1), (0x74, 0), (0xB1, 99), (0xD8, 42), (0x1878 + 41 * 64, 0)):
            for base in (0, inspection.SLOT_STRIDE):
                raw = bytearray(fixture())
                raw[base + offset] = value
                with self.subTest(offset=offset, base=base), self.assertRaises(SaveError):
                    inspection.inspect(bytes(raw), inspection.DIRECTORY)

    def test_required_metadata_bounded_copy_and_source_context_change(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'APP.BIN'
            source.write_bytes(fixture())
            with self.assertRaises(SaveError):
                inspection.read_copy(source)
            companion = source.with_name('PARAM.SFO')
            companion.write_bytes(metadata())
            snapshot = inspection.read_copy(source)
            self.assertTrue(inspection.source_unchanged(snapshot))
            source.write_bytes(snapshot.raw[:-1] + b'\xff')
            self.assertFalse(inspection.source_unchanged(snapshot))
            source.write_bytes(snapshot.raw)
            companion.write_bytes(metadata('BLES00825-SAVEDATA'))
            with self.assertRaises(SaveError):
                inspection.read_copy(source)
            with self.assertRaises(SaveError):
                inspection.source_unchanged(snapshot)
            companion.write_bytes(metadata() + b'\0' * 4096)
            with self.assertRaises(SaveError):
                inspection.read_copy(source)

    def test_snapshot_tampering_rejected_without_normalization(self):
        snapshot = inspection.inspect(fixture(), inspection.DIRECTORY)
        for invalid in (replace(snapshot, editable=True), replace(snapshot, native_integrity_qualified=True),
                        replace(snapshot, size=1), replace(snapshot, slots=()),
                        replace(snapshot, raw=bytearray(snapshot.raw))):
            with self.subTest(snapshot=invalid), self.assertRaises(SaveError):
                inspection.unchanged_bytes(invalid)

    def test_optional_genuine_us_exports_modified_states_not_game_load(self):
        paths = [os.environ.get('STRIKEFORCE_PS3_US_COPY'), os.environ.get('STRIKEFORCE_PS3_US_SECOND_COPY')]
        paths = [path for path in paths if path]
        if not paths:
            self.skipTest('No private genuine US PS3 Strikeforce export supplied.')
        for path in paths:
            with self.subTest(copy=Path(path).name):
                snapshot = inspection.read_copy(path)
                self.assertEqual(inspection.unchanged_bytes(snapshot), snapshot.raw)
                self.assertTrue(inspection.source_unchanged(snapshot))
                self.assertEqual(snapshot.directory, inspection.DIRECTORY)
                self.assertFalse(snapshot.native_integrity_qualified)
                for slot in snapshot.slots:
                    if slot.qualified_existing_record:
                        self.assertEqual(tuple(row.stored_id for row in slot.officers), tuple(range(42)))
                        self.assertEqual(len(slot.storehouse), 196)
