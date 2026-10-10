"""Explicit DW8 Xtreme Legends PC adapter; no cross-game fallback."""
import koei_editor.shared.verified_editor as verified_editor
from koei_editor.shared.verified_gui import Editor as ScalarEditor
from koei_editor.shared.musou_presentations import DW8Presentation


class Editor(ScalarEditor):
    game_id = 'dw8xl'
    summary = 'Resources, officer stats, weapon compatibility and attribute ranks.'
    presentation_type = DW8Presentation


def read_save(path):
    return verified_editor.read_save(path, 'dw8xl')
