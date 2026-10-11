"""Ken Rage PS3 skill-point editor workspace."""
from koei_editor.games.kens_rage1_ps3 import parser
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = parser.GAME_ID
    backend = parser
    save_extension = '.bin'
    subtitle = 'US/EU decrypted DATA.BIN beside PARAM.SFO; Apollo reimport/resign required'
    summary = 'Unspent skill points for eight base fighters. Manual controls; Meridian Chart nodes, equipped skills, DLC, battle gauges and story flags are preserved. Edited game loading is untested.'


def read_save(path):
    return parser.read_save(path)
