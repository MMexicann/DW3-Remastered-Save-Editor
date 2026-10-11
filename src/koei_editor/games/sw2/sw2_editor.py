"""Shared safe editing workflow for original SW2 Windows PC saves."""
from koei_editor.games.sw2 import sw2_parser
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class SW2Presentation(ScalarPresentation):
    def inspection_tables(self, document):
        rows = self.backend.inspection_rows(document)
        notes = {'Officers': 'Stored growth differs from displayed skill/weapon totals. Level, EXP and ownership stay read only; existing own-pool weapon selection is available.',
                 'Weapons': 'Only existing known-owner attribute amounts are editable. Identity, element, attribute IDs and slot count are preserved.',
                 'Guards': 'Catalog growth records are inspected. Hired ownership and active equipment have not been qualified for writes.'}
        return tuple(InspectionTable(group, ('Record', 'Opened data'),
                                     tuple((row['label'], row['value']) for row in rows if row['group'] == group),
                                     notes[group]) for group in notes)


class Editor(ScalarEditor):
    game_id = 'sw2'
    save_extension = '.dat'
    backend = sw2_parser
    presentation_type = SW2Presentation
    subtitle = 'Original Windows PC revision 2'
    summary = 'Money, stored officer growth, acquired ordinary skills, existing weapon bonuses and own-pool weapon selection. Story, ownership and rewards stay separate.'


def read_save(path):
    return sw2_parser.read_save(path)
