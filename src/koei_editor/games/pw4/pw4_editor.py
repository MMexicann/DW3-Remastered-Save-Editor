"""PW4 native PC revision-15 resource workspace."""
import koei_editor.games.pw4.pw4_parser as pw4_parser
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class PW4Presentation(ScalarPresentation):
    extra_groups = ('Owned coins',)

    def inspection_tables(self, document):
        rows = tuple((f"Coin ID {row['id']:03}", row['quantity'], row['earned'],
                      row['spent'], f"0x{row['flags']:02X}")
                     for row in self.backend.coins(document))
        return super().inspection_tables(document) + (
            InspectionTable('Owned coins', ('Native coin ID', 'Current quantity', 'Lifetime earned',
                                          'Lifetime spent', 'Preserved flags'), rows,
                            'Only existing obtained records are editable. Native coin names/rarities '
                            'remain unqualified. Earned/spent counters and flags are read only.'),)


class Editor(ScalarEditor):
    game_id = 'pw4'
    backend = pw4_parser
    presentation_type = PW4Presentation
    subtitle = 'Native PC revision 15'
    summary = 'Spendable Beli and existing owned coin quantities; searchable coin IDs and read-only history.'


def read_save(path):
    return pw4_parser.read_save(path)
