"""Regional product evidence and read-only research never register writers."""
import unittest

from koei_editor.game_registry import GAMES, get_game
from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.support_catalog import load_catalog
from koei_editor.supported_games import SUPPORTED_GAMES


class SpecialRegionalScopeTests(unittest.TestCase):
    def test_psp_candidates_cannot_select_a_gameplay_backend(self):
        candidates = {'dw6special_psp', 'dw7special_psp',
                      'wo3special_psp', 'sw3zspecial_psp'}
        catalog = {entry['id']: entry for entry in load_catalog()}
        registered = {game.id for game in GAMES}
        supported = {game.id for game in SUPPORTED_GAMES}
        self.assertTrue(candidates.issubset(catalog))
        for identity in candidates:
            with self.subTest(identity=identity):
                self.assertFalse(catalog[identity]['editing_verified'])
                self.assertEqual(catalog[identity]['platform'], 'PlayStation Portable')
                self.assertNotIn(identity, registered)
                self.assertNotIn(identity, supported)
                with self.assertRaises(SaveError):
                    get_game(identity)

    def test_regional_aliases_do_not_create_compatibility_fallbacks(self):
        for identity in ('dw6special_windows', 'dw5special_jp',
                         'dw5special_simplified_chinese', 'dw7special_vita'):
            with self.subTest(identity=identity), self.assertRaises(SaveError):
                get_game(identity)
        self.assertEqual(sum(game.id == 'dw5special' for game in GAMES), 1)
        self.assertEqual(get_game('dw5special').platform, 'Windows PC')


if __name__ == '__main__':
    unittest.main()
