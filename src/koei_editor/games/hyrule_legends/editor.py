"""Nintendo 3DS Legends resource workspace."""
from koei_editor.games.hyrule_legends import parser
from koei_editor.games.hyrule_legends.catalog import SKILLS
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Presentation(ScalarPresentation):
    extra_groups = ('Characters', 'Fairy food', 'My Fairy', 'Adventure map cards', 'Weapons', 'Weapon skill records')

    def inspection_tables(self, document):
        weapons = self.backend.weapons(document)
        rows = tuple((row['slot'], row['name'], row['id'], row['power'],
                      row['stars'], f"0x{row['state']:02X}") for row in weapons)
        skills = tuple((row['slot'], row['name'], index + 1, SKILLS.get(identity, f'Unknown ID {identity}'), kos)
                       for row in weapons
                       for index, (identity, kos) in enumerate(row['skills'])
                       if identity != 0xFF)
        return super().inspection_tables(document) + (
            InspectionTable('Weapons', ('Physical slot', 'Weapon', 'Native ID',
                'Stored power', 'Stars', 'Raw state'), rows,
                'Stars 0–5 for recognized normal/Legendary records. Unknown IDs/states, equipment, Master Sword '
                'and collection prerequisites are preserved.'),
            InspectionTable('Weapon skill records', ('Weapon slot', 'Weapon',
                'Skill slot', 'Skill', 'Saved KO counter'), skills,
                'Existing ordinary seals allow remaining-KO decreases. Skill identities, collection prerequisites '
                'and KO counters are preserved.'),
        )


class Editor(ScalarEditor):
    game_id = 'hyrule_legends'
    backend = parser
    save_extension = '.bin'
    presentation_type = Presentation
    subtitle = 'Nintendo 3DS — extracted zmha.bin (1.0.0 profile)'
    summary = ('Rupees, owned materials, weapon stars, ordinary seal KOs, map cards and owned fairy names; searchable inventory. '
               'Character growth, equipment, ownership and story are preserved.')
