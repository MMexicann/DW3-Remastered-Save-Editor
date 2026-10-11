"""Original Atelier Sophie PC workspace using the shared safe-copy workflow."""
from koei_editor.games.sophie import parser
from koei_editor.games.sophie.presentation import SophiePresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    save_extension = parser.EXTENSION
    game_id = parser.GAME_ID
    backend = parser
    presentation_type = SophiePresentation
    subtitle = 'Original Steam PC · observed tagged GAMEDATA profile'
    summary = 'Cole, Tess tickets and existing basket/container quality. Max disabled.'


def read_save(path):
    return parser.read_save(path)
