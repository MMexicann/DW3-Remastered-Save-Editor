"""Official Gust/FF2 directories and resolved aliases remain copy-only.

Directory evidence: ludusavi-manifest Windows paths and public native-save
instructions; files below are procedural path tests, not player saves.
"""
from pathlib import Path
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.save_safety import safe_path


class GustCopyPolicyTests(unittest.TestCase):
    def test_official_roots_and_case_variants_are_rejected(self):
        for name in ('A17/SAVEDATA/GAMEDATA00.pcsave',
                     'Atelier Sophie DX/SAVEDATA/SAVE DATA00.pcsave',
                     'Atelier Ryza/GameData00/data.dat',
                     'Atelier Ryza 2/AutoSave/data.dat',
                     'Atelier Ryza 3/GameData01/data.dat',
                     'BLUE REFLECTION/SAVEDATA/GAMEDATA00.pcsave',
                     'FatalFrameII/Savedata/123/SAVEDATA01/SAVEDATA.BIN'):
            with self.subTest(name=name):
                for root in ('Documents/KoeiTecmo/', 'AppData/Local/KOEITECMO/'):
                    with self.assertRaises(SaveError):
                        safe_path(Path(root + name))

    def test_resolved_live_alias_is_rejected_and_separate_copy_is_allowed(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            live = base / 'KoeiTecmo' / 'Atelier Ryza' / 'GameData00'
            live.mkdir(parents=True)
            (live / 'data.dat').write_bytes(b'procedural copy')
            alias = base / 'alias'
            try:
                alias.symlink_to(live, target_is_directory=True)
            except OSError as error:
                self.skipTest(f'Symlinks unavailable: {error}')
            with self.assertRaises(SaveError):
                safe_path(alias / 'data.dat')
            copy = base / 'Reviewed Gust Copies' / 'data.dat'
            self.assertEqual(safe_path(copy), copy.resolve())

    def test_similar_personal_folder_name_is_not_an_official_root(self):
        copy = Path('Reviewed Copies/Atelier Ryza/data.dat')
        self.assertEqual(safe_path(copy), copy.resolve())
