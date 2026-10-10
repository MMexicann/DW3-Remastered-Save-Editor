"""Shared safe copied-save editor with explicit system/gameplay distinction."""
from koei_editor.games.fatal_frame2_remake import parser
from koei_editor.games.fatal_frame2_remake.presentation import Presentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = parser.GAME_ID
    backend = parser
    presentation_type = Presentation
    save_extension = '.bin'
    subtitle = 'Steam PC — shared system Photo Points; gameplay inspection'
    summary = ('Reduce shared Photo Points from a native system copy. Inspect per-slot '
               'inventory, equipment and Camera Obscura flags; preserve native checksums, '
               'photographs and ownership. Max is disabled.')
