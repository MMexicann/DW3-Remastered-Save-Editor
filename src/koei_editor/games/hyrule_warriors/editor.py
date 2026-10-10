"""Wii U Hyrule Warriors resource/equipment workspace."""
from koei_editor.games.hyrule_warriors import parser
from koei_editor.games.hyrule_warriors.catalog import SKILLS
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Presentation(ScalarPresentation):
    extra_groups = ('Characters', 'Weapons', 'Weapon skills')

    def inspection_tables(self, document):
        weapons = self.backend.weapons(document)
        rows = tuple((row['slot'], row['name'], row['stars'], row['base_power'],
                      f"0x{row['state']:02X}") for row in weapons)
        skills = []
        for row in weapons:
            for slot, (identity, remaining) in enumerate(row['skills'], 1):
                if identity == 0xFFFFFFFF:
                    continue
                name = SKILLS[identity] if identity < len(SKILLS) else f'Unknown skill ID {identity}'
                skills.append((row['slot'], row['name'], slot, name, remaining))
        return super().inspection_tables(document) + (
            InspectionTable('Weapons', ('Physical slot', 'Named weapon', 'Stars', 'Base power',
                                        'Preserved state'), rows,
                            'Stars apply to existing known ordinary/Legendary weapon records. '
                            'Master Sword, empty/unknown records, base power, identities and state are preserved.'),
            InspectionTable('Weapon skills', ('Weapon slot', 'Weapon', 'Skill slot', 'Skill',
                                              'Remaining KOs'), tuple(skills),
                            'Only ordinary seals on existing normal weapons can be decreased. '
                            'Legendary/Evil\'s Bane prerequisites and skill identities are read only.'),
        )


class Editor(ScalarEditor):
    game_id = 'hyrule_warriors'
    backend = parser
    save_extension = '.bin'
    presentation_type = Presentation
    subtitle = 'Wii U — decrypted APP.BIN export'
    summary = ('Rupees, existing materials/map cards, weapon stars and ordinary skill seal KOs. '
               'Character levels/EXP and special seals are inspected; story is preserved.')
