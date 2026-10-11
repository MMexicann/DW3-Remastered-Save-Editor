"""Optional separately held native source qualification, never game-load claims.

TEAM_NINJA_NATIVE_DIR contains nioh1{a,b}-{user,system}.bin and
wolong-{user,backup,system}.bin copies. No source files are distributed.
"""
import os
from pathlib import Path
import struct
import unittest

from koei_editor.research.katana import katana_codec as codec
from koei_editor.games.dw3.models import SaveError
from koei_editor.games.wolong import wolong_parser


@unittest.skipUnless(os.environ.get('TEAM_NINJA_NATIVE_DIR'), 'Separately held native Team Ninja copies unavailable.')
class NativeTeamNinjaTests(unittest.TestCase):
    def test_two_nioh_pc_pairs_preserve_active_integrity_flags_without_authorizing_writes(self):
        folder = Path(os.environ['TEAM_NINJA_NATIVE_DIR'])
        for letter in ('a', 'b'):
            for kind, size, magic in (('user', 2043288, b'NIOHUSR\0'), ('system', 9824, b'NIOHSYS\0')):
                raw = (folder / f'nioh1{letter}-{kind}.bin').read_bytes()
                document = codec.decode(raw, 'nioh')
                self.assertEqual(len(raw), size)
                self.assertEqual(document.payload[:8], magic)
                self.assertEqual(struct.unpack_from('<I', document.payload, 8)[0], 0x17091200)
                self.assertEqual(codec.encode(document.payload, raw, 'nioh'), raw)
                self.assertFalse(document.integrity_verified)
                self.assertFalse(document.writable)
                if kind == 'user':
                    flags = (0x16938D, 0x16934C, 0x169390, 0x1693B4, 0x1693BF, 0x17CE54, 0x1DE8DC)
                    self.assertEqual([document.payload[offset] for offset in flags], [1] * 7)
                    modified = bytearray(document.payload)
                    modified[-1] ^= 1
                    with self.assertRaisesRegex(ValueError, 'inspection-only'):
                        codec.encode(modified, raw, 'nioh')

    def test_wolong_native_user_backup_system_checksums_and_title_selection(self):
        folder = Path(os.environ['TEAM_NINJA_NATIVE_DIR'])
        for kind in ('user', 'backup', 'system'):
            raw = (folder / f'wolong-{kind}.bin').read_bytes()
            document = codec.decode(raw, 'wolong')
            self.assertEqual(len(raw), 5120272)
            self.assertTrue(document.integrity_verified)
            self.assertEqual(codec.encode(document.payload, raw, 'wolong'), raw)
            if kind == 'system':
                with self.assertRaises(SaveError):
                    wolong_parser.decode(raw)
            else:
                native = wolong_parser.decode(raw)
                self.assertEqual(wolong_parser.serialize(native, {}), raw)
                self.assertEqual(set(field.id for field in wolong_parser.fields_for(native)
                                     if field.group == 'Available currencies'), {'senki', 'sen', 'bukun'})
