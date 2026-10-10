"""Inspect the qualified native records without inventing names or ownership."""
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation


class Presentation(ScalarPresentation):
    def inspection_tables(self, document):
        tables = list(super().inspection_tables(document))
        tables.append(InspectionTable('Gameplay inventory (read only)',
            ('Pool', 'Slot', 'Item key', 'Key number', 'Quantity', 'Flags', 'Entry', 'Equipment slot', 'Charm level'),
            self.backend.item_records(document),
            'Item keys are not independently named. Films have capacity dependencies; '
            'camera upgrades consume/refund beads. Items, charms and story keys remain unchanged.'))
        return tuple(tables)
