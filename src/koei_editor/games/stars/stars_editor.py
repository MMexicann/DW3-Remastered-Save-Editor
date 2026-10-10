"""Campaign balances with separate read-only lifetime earnings inspection."""
from koei_editor.games.stars import stars_parser
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class StarsPresentation(ScalarPresentation):
    def inspection_tables(self, document):
        rows = self.backend.inspection_rows(document)
        return tuple(InspectionTable(group, ('Record', 'Opened value'),
                                     tuple((row['label'], row['value']) for row in rows
                                           if row['group'] == group),
                                     'Balance edits preserve lifetime earnings, rewards and story.')
                     for group in ('Campaign gold', 'Materials', 'System history'))


class Editor(ScalarEditor):
    game_id = 'stars'
    save_extension = '.bin'
    backend = stars_parser
    presentation_type = StarsPresentation
    subtitle = 'Windows PC campaign gold editor'
    summary = ('Available campaign gold and existing material quantities by ID; '
               'inspect lifetime earned gold separately.')


def read_save(path):
    return stars_parser.read_save(path)
