"""Explicit Steam PC Atelier Sophie 2 adapter for the shared editing session."""
import atelier_sophie2_parser
from verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = 'atelier_sophie2'
    backend = atelier_sophie2_parser
    subtitle = 'Steam PC save editor · 1.08 layout'
    summary = 'Existing item/equipment quality and Sophie/Plachta alchemy EXP.'


def read_save(path):
    return atelier_sophie2_parser.read_save(path)
