"""DW8/PW3 read-only presentation, outside the shared scalar GUI."""
from game_content import record_label
from scalar_presentation import InspectionTable, ScalarPresentation


class DW8Presentation(ScalarPresentation):
    extra_groups = ('Weapon attributes',)

    def record_name(self, field):
        return record_label(self.game_id, field.slot, field.group) if field.slot else field.group

    def field_hint(self, document, field):
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
                    'Only supported existing attribute ranks change. Identity, affinity and attack stay intact.')
        return super().field_hint(document, field)

    def inspection_tables(self, document):
        progression = tuple((record_label(self.game_id, slot, 'Officers'),
                             row['level'], f"{row['experience']:,}", row['leadership'],
                             row['leadership_experience'], str(row['weapon_slots']))
                            for slot, row in enumerate(self.backend.progressions(document), 1))
        weapons = tuple((row['slot'], row['id'], row['affinity'], row['attack'],
                         ', '.join(f'{identity}:{rank}' for identity, rank in row['attributes'] if identity != 255))
                        for row in self.backend.weapons(document))
        return (InspectionTable('Progression', ('Record', 'Level', 'XP', 'Leadership', 'Leadership XP', 'Weapon slots'), progression),
                InspectionTable('Existing weapons', ('Slot', 'Weapon ID', 'Affinity ID', 'Stored attack', 'Attribute ID:rank'), weapons))


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
