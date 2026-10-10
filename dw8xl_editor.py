"""Explicit DW8 Xtreme Legends PC adapter; no cross-game fallback."""
import verified_editor
from verified_gui import Editor as ScalarEditor
from musou_presentations import DW8Presentation


class Editor(ScalarEditor):
    game_id = 'dw8xl'
    summary = 'Resources, officer stats and weapon attribute ranks.'
    presentation_type = DW8Presentation


def read_save(path):
    return verified_editor.read_save(path, 'dw8xl')
