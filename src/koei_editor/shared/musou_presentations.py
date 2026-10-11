"""DW8/PW3 read-only presentation, outside the shared scalar GUI."""
from koei_editor.games.dw3.game_content import record_label
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation


class DW8Presentation(ScalarPresentation):
    extra_groups = ('Weapon attributes', 'Weapon affinity', 'Weapon order')

    def record_name(self, field):
        if field.group == 'Weapon affinity':
            return f'Weapon slot {field.slot:04}'
        if field.group == 'Weapon order':
            return record_label(self.game_id, field.slot, 'Officers')
        return record_label(self.game_id, field.slot, field.group) if field.slot else field.group

    def field_hint(self, document, field):
        if field.group == 'Weapon order':
            return ('Choose which of the two already equipped weapons comes first. '
                    'The other moves to the second slot automatically. '
                    'This keeps the same weapons and their properties; Max excludes ordering.')
        if field.group == 'Weapon affinity':
            record = self.backend.weapon(document, field.slot)
            return (f"Weapon slot {field.slot}: ID {record['id']}; choose affinity ID 0, 1 or 2. "
                    'The IDs for Heaven/Earth/Man remain unnamed pending independent corroboration. '
                    'Affinity is a choice, so Max excludes it. Weapon identity, attack, attributes '
                    'and equipped references remain unchanged.')
        if field.group == 'Weapon compatibility':
            return ('Stored aptitude: 25 = one star, 50 = two, 75 = three, 100 = four. '
                    'Choose one of those four values. This affects the named weapon action; '
                    'it does not change weapon attributes, officer EXP, skills or story progress. '
                    'Max preserves higher existing values. Edited in-game loading remains untested.')
        if field.group == 'Officers' and field.slot:
            progress = self.backend.progression(document, field.slot)
            model = (f"Observed health curve: {progress['observed_health']:,}. "
                     if progress['observed_health'] is not None else '')
            return (f"Record {field.slot}: level {progress['level']} and XP "
                    f"{progress['experience']:,} (read only). {model}"
                    f"Leadership {progress['leadership']}, XP {progress['leadership_experience']:,}; "
                    f"equipped weapon slots {progress['weapon_slots']} (read only).")
        if field.group == 'Weapon attributes':
            record = self.backend.weapon(document, field.slot)
            return (f"Weapon slot {field.slot}: ID {record['id']}; stored attack {record['attack']}. "
                    'Attribute edits change only supported existing ranks. Identity, affinity and attack stay intact.')
        return super().field_hint(document, field)

    def inspection_tables(self, document):
        progression = tuple((record_label(self.game_id, slot, 'Officers'),
                             row['level'], f"{row['experience']:,}", row['leadership'],
                             row['leadership_experience'], str(row['weapon_slots']))
                            for slot, row in enumerate(self.backend.progressions(document), 1))
        weapons = tuple((row['slot'], row['id'], row['affinity'], row['attack'],
                         ', '.join(f'{identity}:{rank}' for identity, rank in row['attributes'] if identity != 255))
                        for row in self.backend.weapons(document))
        compatibility = tuple((record_label(self.game_id, slot, 'Officers'), *row)
                              for slot, row in enumerate(self.backend.compatibilities(document), 1))
        allies = tuple((row['slot'], row['skill_level'], row['skill_experience'],
                        ', '.join(str(identity) for identity in row['support_skill_ids']),
                        row['male_bond'], row['female_bond'])
                       for row in self.backend.bodyguards(document))
        return (InspectionTable('Progression', ('Record', 'Level', 'XP', 'Leadership', 'Leadership XP', 'Weapon slots'), progression),
                InspectionTable('Weapon compatibility', ('Record', 'Dash', 'Dive', 'Shadow Sprint', 'Whirlwind'),
                                compatibility, 'Stored units: 25/50/75/100 = one/two/three/four stars; unusual values are preserved.'),
                InspectionTable('Existing weapons', ('Slot', 'Weapon ID', 'Affinity ID', 'Stored attack', 'Attribute ID:rank'), weapons),
                InspectionTable('Ally progression', ('Physical slot', 'Skill level', 'Skill XP', 'Support skill IDs', 'Male bond', 'Female bond'),
                                allies, 'Read only. Records do not prove recruitment or ownership. Names, max skill levels and reward dependencies remain unmapped.'))


class PW3Presentation(ScalarPresentation):
    def record_name(self, field):
        return record_label(self.game_id, field.slot, field.group) if field.slot else field.group

    def filename_suffix(self, document):
        return f' · Observed Beli: {self.backend.observed_beli(document):,} (read only)'

    def field_hint(self, document, field):
        if field.group == 'Characters' and field.slot:
            progress = self.backend.progression(document, field.slot)
            model = (f"Observed health curve: {progress['observed_health']:,}. "
                     if progress['observed_health'] is not None else '')
            return (f"Record {field.slot}: level {progress['level']} and XP "
                    f"{progress['experience']:,} (read only). {model}"
                    'Direct stat boosts may reset on level-up.')
        return super().field_hint(document, field)

    def inspection_tables(self, document):
        progression = tuple((record_label(self.game_id, slot, 'Characters'), row['level'], f"{row['experience']:,}")
                            for slot, row in enumerate(self.backend.progressions(document), 1))
        costumes = tuple((record_label(self.game_id, row['slot'], 'Characters'), row['local_slot'],
                          row['asset_costume_id'], 'Absent (255)' if row['stored_id'] == 255 else str(row['stored_id']))
                         for row in self.backend.costume_associations(document))
        return (InspectionTable('Progression', ('Record', 'Level', 'XP'), progression),
                InspectionTable('Costume associations', ('Character', 'Local slot', 'Asset costume ID', 'Stored ID'),
                                costumes, 'Costume associations do not prove ownership, unlock or equipped state.'))
