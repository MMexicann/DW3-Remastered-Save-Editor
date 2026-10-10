"""PS3 SYSTEM custom-horse controls in the standard safe scalar interface."""
from koei_editor.games.dw8e_ps3 import parser as backend
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class PS3HorsePresentation(ScalarPresentation):
    def inspection_tables(self, document):
        rows = tuple((row['slot'], row['name'], row['occupied'], row['ordinal'],
                      ' / '.join(str(value) for value in row['sliders']), row['menu_type'],
                      row['model_byte'], row['speed'], row['power'],
                      ' / '.join(str(value) for value in row['abilities']))
                     for row in backend.horses(document))
        return (InspectionTable('Existing custom horses',
                                ('Slot', 'Name preview', 'Occupied flag', 'Record ID',
                                 'Appearance sliders (7)', 'Type ID', 'Model byte',
                                 'Speed', 'Power', 'Ability IDs (4)'), rows,
                                'Body Type is manually editable on qualified occupied rows. '
                                'Other appearance positions, identity, ownership, type, model, '
                                'stats and abilities are read-only.'),)


class Editor(ScalarEditor):
    game_id = backend.GAME_ID
    save_extension = '.bin'
    backend = backend
    presentation_type = PS3HorsePresentation
    subtitle = 'US PS3 SYSTEM custom-horse editor'
    summary = ('Existing custom-horse Body Type only. Open a decrypted SYSTEM APP.BIN '
               'copy with matching PARAM.SFO, then reimport and resign with Apollo.')


def read_save(path):
    return backend.read_save(path)
