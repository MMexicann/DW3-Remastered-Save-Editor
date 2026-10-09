"""Explicit DW4 Hyper PC adapter."""
import dw4hyper_parser
from verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = 'dw4hyper'
    backend = dw4hyper_parser
    subtitle = 'Windows PC save editor'
    summary = 'Officers, weapons, items and bodyguards.'


def read_save(path):
    return dw4hyper_parser.read_save(path)
