"""Explicit Pirate Warriors 3 PC adapter; no cross-game fallback."""
import verified_editor
from verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = 'pw3'


def read_save(path):
    return verified_editor.read_save(path, 'pw3')
