"""Console registrations stay separate from related PC and research profiles."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from koei_editor.game_registry import GAMES, get_game
from koei_editor.games.dw3.models import SaveError
from koei_editor.games.dw8e_ps3 import parser as dw8e
from koei_editor.games.wo3u_ps3 import parser as wo3u
from koei_editor.shared import verified_self_test
from koei_editor.shared.support_catalog import load_catalog
from tests.test_dw8e_ps3_horses import procedural_raw as ps3_system
from tests.test_wo3u_format import procedural_raw as pc_ultimate
from tests.test_wo3u_ps3 import fixture as ps3_ultimate, metadata


class ConsoleExpansionRegistryTests(unittest.TestCase):
    def test_exact_platforms_and_research_do_not_create_editor_cards(self):
        registered = {game.id for game in GAMES}
        catalog = {entry['id']: entry for entry in load_catalog()}
        for key, backend in (('dw8e_ps3', dw8e), ('wo3u_ps3', wo3u)):
            game = get_game(key)
            self.assertEqual(game.platform, 'PlayStation 3')
            self.assertEqual(game.extension, '.bin')
            self.assertIs(game.get_scalar_adapter().backend, backend)
            self.assertTrue(catalog[key]['editing_verified'])
        for key in ('sw2hd_ps3', 'strikeforce_ps3', 'dw5e_xbox360',
                    'dw6e_xbox360', 'dw7_xbox360', 'sw2_xbox360',
                    'sw2xl_xbox360', 'wo1_xbox360', 'wo2_xbox360'):
            self.assertNotIn(key, registered)
            self.assertFalse(catalog[key]['editing_verified'])
            with self.assertRaises(SaveError):
                get_game(key)

    def test_equal_wo3_length_and_revision_do_not_cross_platforms(self):
        pc = get_game('wo3u').get_scalar_adapter()
        console = get_game('wo3u_ps3').get_scalar_adapter()
        with self.assertRaises(SaveError):
            pc.decode(ps3_ultimate())
        with self.assertRaises(SaveError):
            console.decode(pc_ultimate())
        with self.assertRaises(SaveError):
            console.decode(ps3_system())
        with self.assertRaises(SaveError):
            get_game('dw8e_ps3').get_scalar_adapter().decode(ps3_ultimate())

    def test_nonempty_selftest_output_rejects_before_context_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'APP.BIN'
            source.write_bytes(ps3_ultimate())
            companion = source.with_name('PARAM.SFO')
            original_context = metadata()
            companion.write_bytes(original_context)
            output = Path(folder) / 'occupied-output'
            output.mkdir()
            sentinel = output / 'keep.txt'
            sentinel.write_text('Existing files must remain untouched.')
            with patch.object(wo3u, 'prepare_copy_context') as prepare:
                with self.assertRaises(SaveError):
                    verified_self_test.run('wo3u_ps3', source, output)
                prepare.assert_not_called()
            self.assertEqual(set(path.name for path in output.iterdir()), {'keep.txt'})
            self.assertEqual(companion.read_bytes(), original_context)
            self.assertEqual(source.read_bytes(), ps3_ultimate())
