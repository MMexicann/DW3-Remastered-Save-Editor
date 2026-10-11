"""Samurai Warriors 4-II Windows PC shared workspace."""
from koei_editor.games.sw4ii import sw4ii_parser
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = 'sw4ii'
    backend = sw4ii_parser
    subtitle = 'Windows PC save editor'
    summary = ('Manual current gold, five strategy tomes, officer base stats, existing '
               'weapon attributes, own-pool weapon selection, existing mount selection and mount stats. '
               'Level, EXP, growth, skills, acquisition and rewards remain separate.')


def read_save(path):
    return sw4ii_parser.read_save(path)
