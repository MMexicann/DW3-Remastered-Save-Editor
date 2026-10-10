"""Explicit source-backed native PC DW9 Empires SYSTEMDATA adapter."""
from koei_editor.games.dw9emp import dw9emp_parser as backend
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class DW9EmpPresentation(ScalarPresentation):
    def inspection_tables(self, document):
        rows = tuple((row['id'], row['quantity'],
                      'Editable' if 1 <= row['quantity'] <= backend.ITEM_MAXIMUM
                      else 'Empty / preserved' if row['quantity'] == 0
                      else 'Unusual / preserved') for row in backend.items(document))
        custom = tuple((row['id'], row['name_preview'],
                        ' / '.join(f'0x{flag:02X}' for flag in row['flags']),
                        ', '.join(str(value) for value in row['stored_values']))
                       for row in backend.custom_officers(document))
        return (InspectionTable('Stored inventory', ('Item ID', 'Quantity', 'Status'), rows,
                                'Search by item ID. Edit existing ordinary quantities individually; '
                                'bulk Max leaves unnamed categories unchanged.'),
                InspectionTable('Custom officer records',
                                ('Record ID', 'Name preview', 'Stored flags', 'Stored values (8)'),
                                custom, 'Read only. Search by name preview or record ID. '
                                'Stored flags and values remain unchanged.'))


class Editor(ScalarEditor):
    game_id = 'dw9emp'
    save_extension = '.bin'
    backend = backend
    presentation_type = DW9EmpPresentation
    subtitle = 'Windows PC SYSTEMDATA editor'
    summary = 'Existing item quantities and searchable inventory and custom officer records.'


def read_save(path):
    return backend.read_save(path)
