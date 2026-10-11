"""Ken's Rage 2 EU PS3 collection workspace."""
from koei_editor.games.kens_rage2_ps3 import parser
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = parser.GAME_ID
    backend = parser
    save_extension = '.bin'
    subtitle = 'EU PS3 decrypted DATA.BIN; Apollo reimport/resign required'
    summary = ('Unlock existing locked music, movie and event gallery entries. '
               'Existing unlocked and unusual collection states are preserved.')


def read_save(path):
    return parser.read_save(path)
