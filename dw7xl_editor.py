"""Explicit native Windows DW7 XL Definitive Edition adapter."""
import dw7xl_parser
from scalar_presentation import InspectionTable, ScalarPresentation
from verified_gui import Editor as ScalarEditor


class DW7Presentation(ScalarPresentation):
    def inspection_tables(self, document):
        rows = self.backend.inspection_rows(document)
        inventory = tuple((row['slot'], 'Owned' if row['owned'] else 'Unowned',
                           row['seal_meter'], f"0x{row['flags']:04X}")
                          for row in self.backend.weapons(document))
        return (InspectionTable('Equipment', ('Officer slot', 'Equipped records / guardian'),
                                tuple((row['label'], row['value']) for row in rows if row['group'] == 'Equipment'),
                                'Switch the active equipped weapon in the Equipment edit group; guardian ownership is not inferred.'),
                InspectionTable('Purchased skills', ('Officer slot', 'Stored skill bits'),
                                tuple((row['label'], row['value']) for row in rows if row['group'] == 'Purchased skills'),
                                'Read only. Officer-specific skill definitions and prerequisites require game parameter data.'),
                InspectionTable('Weapon inventory', ('Physical record', 'Ownership', 'Seal learning meter', 'Stored flags'),
                                inventory, 'Read only. Weapon names and seal rewards require game parameter data; meter maxima depend on the weapon.'))


class Editor(ScalarEditor):
    game_id = 'dw7xl'
    backend = dw7xl_parser
    presentation_type = DW7Presentation
    subtitle = 'Windows PC save editor'
    summary = 'Gold, officer stats, skill points and active equipment; searchable weapon and skill inspection.'


def read_save(path):
    return dw7xl_parser.read_save(path)
