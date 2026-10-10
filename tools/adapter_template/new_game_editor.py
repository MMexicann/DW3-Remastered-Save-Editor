"""Copy into a game package and rename the qualified backend module."""
from . import new_game_parser
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = new_game_parser.GAME_ID
    backend = new_game_parser
    save_extension = new_game_parser.EXTENSION
    subtitle = 'Exact platform / revision'
    summary = 'Describe only mapped editable fields.'
    # Optional presentation_type = YourPresentation (see scalar_presentation).


def read_save(path):
    return new_game_parser.read_save(path)
