"""Dynasty Warriors 7 (PS3, US/EU decrypted export) workspace."""
from koei_editor.games.dw7_ps3 import parser
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = parser.GAME_ID
    backend = parser
    save_extension = '.bin'
    subtitle = 'PS3 decrypted export; Apollo reimport/resign required'
    summary = 'Gold and 62 officer health, attack, defense, power, speed and skill points. Manual controls; progression and equipment remain unchanged.'


def read_save(path):
    return parser.read_save(path)
