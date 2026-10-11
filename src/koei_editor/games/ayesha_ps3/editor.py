"""Decrypted PS3 export workspace; separate Apollo import/resigning contract."""
from koei_editor.games.ayesha_ps3 import parser
from koei_editor.games.ayesha_ps3.presentation import Presentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = parser.GAME_ID
    backend = parser
    presentation_type = Presentation
    save_extension = '.bin'
    subtitle = 'PS3 US/Japanese decrypted export — Apollo reimport/resign required'
    summary = ('Cole and existing ordinary stack reductions; searchable numeric inventory, '
               'float qualities, potentials, effects and distinct memory words. Story and item ownership stay unchanged.')
