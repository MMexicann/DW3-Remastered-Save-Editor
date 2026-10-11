"""Original Windows classic Musou live-path and copied-file boundaries."""
from pathlib import Path
import tempfile
import unittest

from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.save_safety import safe_path


class ClassicMusouCopySafetyTests(unittest.TestCase):
    def test_original_pc_live_directories_and_windows_paths_rejected(self):
        for name in (
            'Documents/KOEI/Samurai Warriors 2/Savedata/save.dat',
            'Documents/KOEI/SENGOKU MUSOU 2 TW/Savedata/save.dat',
            'Documents/KOEI/Warriors Orochi/Savedata/save.dat',
            'Documents/KOEI/Musou OROCHI/Savedata/save.dat',
            r'C:\Users\Player\Documents\KOEI\SENGOKU MUSOU 2 TW\Savedata\save.dat',
            r'C:\Users\Player\Documents\KOEI\SAMURAI WARRIORS 2\Savedata\save.dat',
            r'C:\Users\Player\Documents\KOEI\WARRIORS OROCHI\Savedata\save.dat',
        ):
            with self.subTest(path=name), self.assertRaises(SaveError):
                safe_path(name)

    def test_resolved_original_pc_live_directory_alias_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            live = root / 'KOEI' / 'SENGOKU MUSOU 2 TW' / 'Savedata'
            live.mkdir(parents=True)
            alias = root / 'reviewed-copy'
            try:
                alias.symlink_to(live, target_is_directory=True)
            except OSError:
                self.skipTest('Symbolic links unavailable.')
            with self.assertRaises(SaveError):
                safe_path(alias / 'save.dat')

    def test_reviewed_copy_folder_and_similar_names_remain_usable(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in (
                'ReviewCopies/Samurai Warriors 2/save.dat',
                'ReviewCopies/Warriors Orochi/save.dat',
                'KOEI/SENGOKU MUSOU 2 TW copy/Savedata/save.dat',
            ):
                with self.subTest(path=name):
                    self.assertEqual(safe_path(root / name), (root / name).resolve())


if __name__ == '__main__':
    unittest.main()
