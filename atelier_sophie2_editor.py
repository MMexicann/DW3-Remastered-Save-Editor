"""Explicit Steam PC Atelier Sophie 2 adapter for the shared editing session."""
import atelier_sophie2_parser
from atelier_sophie2_presentation import Sophie2Presentation
from verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = 'atelier_sophie2'
    backend = atelier_sophie2_parser
    presentation_type = Sophie2Presentation
    subtitle = 'Steam PC save editor · 1.08 layout'
    summary = 'Existing item/equipment quality, battle-item uses, and alchemy EXP.'


def read_save(path):
    return atelier_sophie2_parser.read_save(path)
