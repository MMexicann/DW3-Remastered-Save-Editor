"""Original Warriors Orochi PC integration with the shared scalar GUI."""
from koei_editor.games.wo1_pc import wo1_parser as backend
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class OrochiPresentation(ScalarPresentation):
    def inspection_tables(self, document):
        rows = []
        for weapon in backend.weapons(document):
            officer, slot = weapon['officer'], weapon['slot']
            qualified = backend._qualified_weapon(document.payload, officer, slot)
            effects = ', '.join(
                f'{backend.ATTRIBUTE_NAMES[identity] or "Unqualified ID 5"}:{weapon["ranks"][identity] + 1}'
                for identity in range(15) if weapon['mask'] & (1 << identity))
            rows.append((officer, slot + 1, weapon['id'],
                         'Qualified existing weapon' if qualified else 'Unqualified / empty',
                         weapon['capacity'], weapon['bonus'], f"0x{weapon['mask']:04X}", effects))
        officers = tuple((row['id'], row['stored_level'] + 1,
                          ' / '.join(str(value) for value in row['stats']),
                          row['exp'], row['proficiency'])
                         for row in backend.officers(document))
        return (InspectionTable('Officer growth',
                                ('Officer record', 'Stored level + 1', 'Stored stat words',
                                 'Stored EXP', 'Stored proficiency'), officers,
                                'Read only. Level, stats, proficiency, skills, ownership and rewards '
                                'are preserved. Shared Growth Points are separate from officer EXP.'),
                InspectionTable('Existing weapons',
                                ('Officer record', 'Slot', 'Weapon ID', 'Status', 'Capacity',
                                 'Attack bonus', 'Ownership mask', 'Owned effects'), tuple(rows),
                                'Only qualified existing weapons in the original officer family offer '
                                'controls. Unqualified IDs, masks and capacity layouts are preserved. '
                                'No weapon or effect is acquired or consumed.'))


class Editor(ScalarEditor):
    game_id = 'wo1'
    save_extension = '.dat'
    backend = backend
    presentation_type = OrochiPresentation
    subtitle = 'Original 2008 Windows PC save.dat editor'
    summary = 'Shared Growth Points, existing weapon properties and owned-weapon equipment.'


def read_save(path):
    return backend.read_save(path)
