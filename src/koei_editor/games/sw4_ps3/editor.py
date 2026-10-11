"""Samurai Warriors 4 (PS3, US decrypted export) workspace."""
from koei_editor.games.sw4_ps3 import parser
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = parser.GAME_ID
    backend = parser
    save_extension = '.bin'
    subtitle = 'PS3 decrypted export; Apollo reimport/resign required'
    summary = 'Gold and eight gem quantities, with read-only proficiency and named weapon-skill inspection. Native section checksums are verified and regenerated.'


def read_save(path):
    return parser.read_save(path)
