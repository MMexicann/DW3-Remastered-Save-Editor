"""US PS3 Dynasty Warriors 7 Empires system workspace."""
from koei_editor.games.dw7e_ps3 import parser
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = parser.GAME_ID
    backend = parser
    save_extension = '.bin'
    subtitle = 'PS3 decrypted system export; Apollo reimport/resign required'
    summary = 'Edit system bonus points. Campaign resources and completion remain separate.'


def read_save(path):
    return parser.read_save(path)
