"""Gundam PS3 learned-skill workspace using the existing shared GUI."""
from koei_editor.games.gundam1_ps3 import parser
from koei_editor.shared.scalar_presentation import ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Presentation(ScalarPresentation):
    extra_groups = ('Pilots', 'Mobile suits')


class Editor(ScalarEditor):
    game_id = parser.GAME_ID
    backend = parser
    save_extension = '.bin'
    presentation_type = Presentation
    subtitle = 'PS3 US/EU decrypted DATA.BIN + original PARAM.SFO; Apollo resign required'
    summary = ('Learn native skills for six qualified existing level-30 pilots. Pilot/mobile suit '
               'EXP and levels and equipped skill IDs are read only. Existing learned '
               'skills cannot be removed; automatic Max is disabled.')


def read_save(path):
    return parser.read_save(path)
