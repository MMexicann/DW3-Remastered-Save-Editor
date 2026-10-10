"""Switch Age of Calamity named inventory/equipment workspace."""
from koei_editor.games.age_of_calamity import parser
from koei_editor.games.age_of_calamity.catalog import SEALS
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Presentation(ScalarPresentation):
    extra_groups = ('Characters', 'Special collectibles (read only)', 'Weapons', 'Weapon seals')

    def inspection_tables(self, document):
        weapons = self.backend.weapons(document)
        rows = tuple((row['character'], row['slot'], row['name'], row['level'], row['exp'],
                      row['bonus_power'], row['level_power'], row['protected'], row['rusty'])
                     for row in weapons)
        seals = []
        for row in weapons:
            for slot, (identity, parameter1, parameter2) in enumerate(row['seals'], 1):
                if not identity:
                    continue
                name = SEALS.get(identity, f'Unknown seal ID {identity}')
                seals.append((row['character'], row['slot'], row['name'], slot, name,
                              parameter1, parameter2))
        return super().inspection_tables(document) + (
            InspectionTable('Weapons', ('Character', 'Physical slot', 'Weapon', 'Stored level',
                'Stored EXP', 'Bonus power', 'Level power', 'Protected', 'Rusty'), rows,
                'Protect existing recognized weapons from fusion with 0/1. Levels, EXP, power terms, '
                'rusty state, identity, ordering and equipped references remain read only. '
                '1.3.0 layout: 71 physical records per character, including temporary battle capacity.'),
            InspectionTable('Weapon seals', ('Character', 'Weapon slot', 'Weapon', 'Seal slot',
                'Seal', 'Saved parameter 1', 'Saved parameter 2'), tuple(seals),
                'Seal names are source mapped; parameter units/legitimate ranges and hidden seal '
                'prerequisites are unqualified. Every seal byte is preserved.'),
        )


class Editor(ScalarEditor):
    game_id = 'age_of_calamity'
    backend = parser
    save_extension = ''
    presentation_type = Presentation
    subtitle = 'Nintendo Switch — decrypted extensionless svdt export (1.3.0 layout)'
    summary = ('Rupees bounded by preserved lifetime total; discovered materials/trophies/DLC reports; '
               'existing weapon protection. Named weapon/seal inspection; story and collectibles preserved.')
