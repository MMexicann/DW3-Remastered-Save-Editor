"""Nintendo Switch Fire Emblem Warriors workspace."""
from koei_editor.games.fire_emblem_warriors import parser
from koei_editor.games.fire_emblem_warriors.catalog import SEALS
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class Presentation(ScalarPresentation):
    extra_groups = ('Characters', 'Special items (read only)', 'Weapons', 'Weapon attributes')

    def inspection_tables(self, document):
        weapons = self.backend.weapons(document)
        rows = tuple((r['slot'], r['name'], r['stars'], r['bonus']) for r in weapons)
        seals = tuple((r['slot'], r['name'], i + 1, SEALS.get(a, f'Unknown ID {a}'), ko)
                      for r in weapons for i, (a, ko) in enumerate(zip(r['attributes'], r['kos']))
                      if a not in (0, 255))
        return super().inspection_tables(document) + (
            InspectionTable('Weapons', ('Physical slot', 'Weapon', 'Stars', 'Slayer bitmask'), rows,
                'Existing recognized weapons: stars 0–5. Identity, equipped references, slayer '
                'flags, forging attributes and unusual records are preserved.'),
            InspectionTable('Weapon attributes', ('Weapon slot', 'Weapon', 'Attribute slot',
                'Attribute', 'Remaining KOs'), seals,
                'Ordinary existing sealed attributes allow remaining-KO decreases. True Power '
                'and Legendary require progression prerequisites and remain read only.'),)


class Editor(ScalarEditor):
    game_id = 'fire_emblem_warriors'
    backend = parser
    save_extension = ''
    presentation_type = Presentation
    subtitle = 'Nintendo Switch — decrypted extensionless scenario0/1/2 export (1.5.0 layout)'
    summary = ('Gold; existing ordinary drop materials; recognized weapon stars and ordinary seal KOs. '
               'Named character/weapon/item inspection; special rewards and story preserved.')
