"""Native encrypted PC save-copy workspace."""
from koei_editor.games.p5strikers_pc import parser
from koei_editor.games.p5strikers_pc.presentation import Presentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = parser.GAME_ID
    backend = parser
    presentation_type = Presentation
    save_extension = '.bin'
    subtitle = 'PC — encrypted SAVEDATA.BIN copy'
    summary = ('Occupied save-slot money, persona points, unspent BOND points and existing named '
               'consumable/cooking, incense, remedy and skill-card stacks. Individual controls; '
               'item application and skill teaching remain under game control.')
