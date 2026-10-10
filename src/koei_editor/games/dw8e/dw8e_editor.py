"""Native PC DW8 Empires SYSTEM custom-horse appearance editor."""
from koei_editor.games.dw8e import dw8e_parser as backend
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class DW8EmpiresPresentation(ScalarPresentation):
    def inspection_tables(self, document):
        rows = tuple((row['slot'], row['name'], row['occupied'], row['ordinal'],
                      ' / '.join(str(value) for value in row['sliders']), row['menu_type'],
                      row['model_byte'], row['speed'], row['power'],
                      ' / '.join(str(value) for value in row['abilities']))
                     for row in backend.horses(document))
        return (InspectionTable('Custom horses',
                                ('Slot', 'Name preview', 'Occupied flag', 'Record ID', 'Appearance sliders (7)',
                                 'Type ID', 'Model byte', 'Speed', 'Power', 'Ability IDs (4)'), rows,
                                'Search by horse name or slot. Existing body type can be edited; '
                                'identity, names, ownership, type, model, stats and abilities remain unchanged.'),)


class Editor(ScalarEditor):
    game_id = 'dw8e'
    save_extension = '.dat'
    backend = backend
    presentation_type = DW8EmpiresPresentation
    subtitle = 'Windows PC SYSTEM custom-horse editor'
    summary = 'Existing custom-horse body type and searchable records in SystemSave.dat.'


def read_save(path):
    return backend.read_save(path)
