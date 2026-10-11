"""Native Windows Special equipment editor and searchable named records."""
from koei_editor.games.dw5special import dw5special_parser as backend
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class SpecialPresentation(ScalarPresentation):
    def inspection_tables(self, document):
        records = backend.inspection_records(document)
        return (
            InspectionTable('Officers',
                            ('ID', 'Officer', 'Unlocked byte', 'Outfit', 'Life', 'Musou',
                             'Attack', 'Defense', 'Merit', 'Title ID', 'Weapon slot', 'KO count'),
                            records['officers'],
                            'Officer growth and titles are separate stored values. Stored Attack/Defense are manually editable on playable officers; unlocks, merit/title, Life/Musou, equipment selections and story stay read only.'),
            InspectionTable('Weapons',
                            ('Officer ID', 'Officer', 'Slot', 'Weapon ID', 'Identity high byte',
                             'Weight', 'Evolution byte', 'Stored attack adjustment', 'Attribute ranks (0 = level 1)', 'Unknown byte'),
                            records['weapons'],
                            'Search by officer or effect. Edit only existing qualified attack, weight and attribute ranks; no weapon creation or attribute replacement.'),
            InspectionTable('Items', ('ID', 'Item', 'Stored byte'), records['items'],
                            'Only ten existing ordinary item ranks are editable. Orbs, harnesses and special items have different ownership semantics and stay unchanged.'),
            InspectionTable('Bodyguards',
                            ('Slot', 'Occupied byte', 'Name bytes', 'Type ID', 'Appearance ID',
                             'Talent ID', 'Skill mask', 'Merit', 'Life', 'Musou', 'Attack', 'Defense', 'Title ID'),
                            records['bodyguards'],
                            'Name bytes, growth, skills, talent and title are inspected only; prerequisites and region-specific text encoding remain unresolved.'),
            InspectionTable('Shura resources', ('Stored resource', 'Value'), records['shura'],
                            'Shura session activation and companion/progression dependencies remain unresolved; no session or resource changes.'),
        )


class Editor(ScalarEditor):
    game_id = 'dw5special'
    save_extension = '.dat'
    backend = backend
    presentation_type = SpecialPresentation
    subtitle = 'Shin Sangokumusou 4 Special · Windows PC'
    summary = 'Stored officer Attack/Defense, existing item ranks, stored attack adjustment, attribute ranks and named weight choices, with searchable officers and equipment.'


def read_save(path):
    return backend.read_save(path)
