"""US PS3 Ultimate workspace using the shared safe scalar editor."""
from koei_editor.games.wo3u_ps3 import parser
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = parser.GAME_ID
    backend = parser
    save_extension = '.bin'
    subtitle = 'US PS3 decrypted export; keep PARAM.SFO alongside the copy'
    summary = ('Growth points and gems; officers, weapons and inventories inspected read only. '
               'Reimport/resign with Apollo before PS3 loading.')


def read_save(path):
    return parser.read_save(path)
