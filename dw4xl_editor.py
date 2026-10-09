"""Explicit PS2 USA DW4 XL adapter; distinct from native PC DW4 Hyper."""
import dw4xl_parser
from verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = 'dw4xl_ps2'
    backend = dw4xl_parser
    save_extension = '.psu'
    subtitle = 'PlayStation 2 save export · USA'
    summary = 'Officers, Lv.11 weapons, items and bodyguards.'


def read_save(path):
    return dw4xl_parser.read_save(path)
