"""Data-only occupied item/equipment inspector for the Sophie 2 adapter."""
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation


class Sophie2Presentation(ScalarPresentation):
    def record_name(self, field):
        if field.group.endswith(' equipment') and field.slot:
            return field.group.removesuffix(' equipment') + ': ' + self.backend.EQUIPMENT_SLOTS[field.slot - 1]
        return super().record_name(field)

    def inspection_tables(self, document):
        records = self.backend.item_records(document)
        rows = tuple((r['group'], r['label'], r['item_id'], r['instance_id'], r['quality'],
                      f"{r['uses']} / {r['capacity']}", ', '.join(map(str, r['traits'])),
                      ', '.join(map(str, r['effects'])), ', '.join(map(str, r['stat_bytes'])))
                     for r in records)
        return (InspectionTable(
            'Occupied inventory and equipment',
            ('Container / character', 'Slot', 'Item ID', 'Instance ID', 'Quality',
             'Uses / capacity', 'Trait IDs', 'Effect IDs', 'Raw stat bytes'), rows,
            'Opened values. Unmapped IDs and raw stat bytes are inspection only. '
            'Empty records are omitted; no new items are created.'),) + super().inspection_tables(document)
