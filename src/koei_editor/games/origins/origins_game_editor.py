"""Origins presentation; all decoding and writing live in origins_parser."""
import koei_editor.games.origins.origins_parser as backend
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Editor(ScalarEditor):
    game_id = 'origins'
    backend = backend
    subtitle = 'Steam PC slot saves · native revisions 16, 17 and 29'
    summary = ('Edit Gold, Skill Points, existing bonds, provincial peace and eligible '
               'weapon upgrades up to +99. Battle clear history is separate from your '
               'current campaign. Choose a category or search for a field, review '
               'your changes and use Save As. Open a copied SLOT0000–SLOT0008.dat; '
               'USER.dat is system data.')
