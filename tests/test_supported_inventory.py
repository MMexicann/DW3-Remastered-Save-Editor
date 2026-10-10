"""Support inventory must match shipped adapters and work outside the checkout."""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from koei_editor.game_registry import GAMES
from koei_editor.shared.support_catalog import load_catalog
from koei_editor.supported_games import SUPPORTED_GAMES
from tools import update_supported_games


class SupportedInventoryTests(unittest.TestCase):
    def test_registered_games_have_metadata_and_loadable_bound_backends(self):
        inventory = {game.id: game for game in SUPPORTED_GAMES}
        self.assertEqual(len(inventory), len(GAMES))
        self.assertEqual(set(inventory), {game.id for game in GAMES})
        metadata = {entry['id']: entry for entry in load_catalog()}
        for game in GAMES:
            with self.subTest(game=game.id):
                self.assertIn(game.id, metadata)
                self.assertEqual(metadata[game.id]['editing_verified'], game.editing_verified)
                self.assertEqual(inventory[game.id].platform, game.platform)
                self.assertTrue(inventory[game.id].features)
                if game.scalar_backend:
                    self.assertEqual(game.get_scalar_adapter().get_format().id, game.id)

    def test_readme_document_and_code_index_are_current(self):
        for path, expected in update_supported_games.expected_files():
            with self.subTest(path=path.name):
                self.assertEqual(path.read_text(encoding='utf-8'), expected,
                                 'Run python -m tools.update_supported_games')

    def test_check_mode_rejects_stale_inventory_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'README.md'
            original = 'Old supported game list\n'
            path.write_text(original, encoding='utf-8')
            with patch.object(update_supported_games, 'ROOT', Path(folder)), \
                    patch.object(update_supported_games, 'expected_files', return_value=[(path, 'Updated\n')]), \
                    patch.object(sys, 'argv', ['update_supported_games', '--check']), \
                    contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as result:
                update_supported_games.main()
            self.assertEqual(result.exception.code, 2)
            self.assertEqual(path.read_text(encoding='utf-8'), original)

    def test_installed_package_lists_games_without_display_from_other_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, '-m', 'koei_editor', '--list-games'],
                                    cwd=folder, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        ids = {line.split(':', 1)[0] for line in result.stdout.splitlines()
               if line and not line.startswith(' ')}
        self.assertEqual(ids, {game.id for game in GAMES})
        for game in SUPPORTED_GAMES:
            self.assertIn(f'[{game.platform}]', result.stdout)


if __name__ == '__main__':
    unittest.main()
