"""Explicit Pirate Warriors 3 PC adapter; no cross-game fallback."""
import koei_editor.shared.verified_editor as verified_editor
from koei_editor.shared.verified_gui import Editor as ScalarEditor
from koei_editor.shared.musou_presentations import PW3Presentation


class Editor(ScalarEditor):
    game_id = 'pw3'
    summary = 'Character stats, special bars and skill slots.'
    presentation_type = PW3Presentation


def read_save(path):
    return verified_editor.read_save(path, 'pw3')
