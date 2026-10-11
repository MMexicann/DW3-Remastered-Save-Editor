"""Explicit DW4 Hyper PC adapter."""
import koei_editor.games.dw4hyper.dw4hyper_parser as dw4hyper_parser
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = 'dw4hyper'
    backend = dw4hyper_parser
    subtitle = 'Windows PC save editor'
    summary = 'Officers, weapons, items, bodyguards and existing custom characters.'


def read_save(path):
    return dw4hyper_parser.read_save(path)
