"""Explicit DW8 Xtreme Legends PC adapter; no cross-game fallback."""
import verified_editor
from verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = 'dw8xl'


def read_save(path):
    return verified_editor.read_save(path, 'dw8xl')
