"""Explicit Steam PC Warriors Orochi 3 Ultimate Definitive adapter."""
import wo3u_parser
from verified_gui import Editor as ScalarEditor
from scalar_presentation import ScalarPresentation, InspectionTable


class WO3Presentation(ScalarPresentation):
    extra_groups = ('Weapons',)

    def inspection_tables(self, document):
        rows = self.backend.inspection_rows(document)
        progression = tuple((row['label'], row['value']) for row in rows
                            if row['group'] == 'Progression')
        weapons = tuple((row['label'], row['value']) for row in rows
                        if row['group'] == 'Weapons')
        resources = tuple((field.group, field.label, field.value(document.payload))
                          for field in self.backend.fields_for(document)
                          if field.group not in ('Officers', 'Weapons'))
        return (
            InspectionTable('Progression', ('Record', 'Opened progression'), progression,
                            'Level, EXP, promotion and item-slot dependencies remain read only.'),
            InspectionTable('Weapons', ('Owner / slot', 'Opened equipment'), weapons,
                            'Search by proven attribute names or weapon IDs. Unknown IDs are preserved.'),
            InspectionTable('Resources', ('Group', 'Resource', 'Opened balance'), resources,
                            'Resource edit limits are published patch limits; bulk Max excludes them.'),
        )


class Editor(ScalarEditor):
    game_id = 'wo3u'
    save_extension = '.bin'
    presentation_type = WO3Presentation
    backend = wo3u_parser
    subtitle = 'Steam Windows PC save editor'
    summary = 'Officer stats, growth points, gems, crafting and existing weapons.'


def read_save(path):
    return wo3u_parser.read_save(path)
