"""Switch Definitive Edition resource workspace."""
from koei_editor.games.hyrule_definitive import parser
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Presentation(ScalarPresentation):
    extra_groups = ('Characters', 'Fairy food', 'Weapons', 'Weapon skill records')

    def inspection_tables(self, document):
        weapons = self.backend.weapons(document)
        rows = tuple((row['slot'], row['name'], row['id'], row['power'],
                      row['stars'], f"0x{row['state']:02X}") for row in weapons)
        skills = tuple((row['slot'], row['name'], index + 1, identity, kos)
                       for row in weapons
                       for index, (identity, kos) in enumerate(row['skills'])
                       if identity != 0xFF)
        return super().inspection_tables(document) + (
            InspectionTable('Weapons', ('Physical slot', 'Weapon', 'Native ID',
                'Stored power', 'Stars', 'Raw state'), rows,
                'Read-only inventory. Unknown IDs/states, equipment, Master Sword '
                'and collection prerequisites are preserved.'),
            InspectionTable('Weapon skill records', ('Weapon slot', 'Weapon',
                'Skill slot', 'Native skill ID', 'Saved KO counter'), skills,
                'Read-only records. Skill identities, collection prerequisites '
                'and KO counters are preserved.'),
        )


class Editor(ScalarEditor):
    game_id = 'hyrule_definitive'
    backend = parser
    save_extension = '.bin'
    presentation_type = Presentation
    subtitle = 'Nintendo Switch — extracted zmha.bin'
    summary = ('Rupees and existing named materials; searchable characters, fairy food and weapons. '
               'Character growth, equipment, ownership and story are preserved.')
