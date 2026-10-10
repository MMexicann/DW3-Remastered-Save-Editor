"""Samurai Warriors 4 DX native PC workspace."""
import samurai4dx_parser
from verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = 'samurai4dx'
    backend = samurai4dx_parser
    subtitle = 'Windows PC save editor'
    summary = ('Gold, gems, playable unlocks, officer base stats, equipped weapons and existing skill levels/activation. '
               'Search weapon skills by name; inspect progression and equipment separately.')


def read_save(path):
    return samurai4dx_parser.read_save(path)
