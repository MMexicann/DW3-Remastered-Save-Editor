"""Numeric inventory identity, exact float quality and distinct memory words."""
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation


class Presentation(ScalarPresentation):
    def inspection_tables(self, document):
        return (
            InspectionTable('Existing inventory records',
                            ('Container', 'Slot', 'Item ID', 'Instance word', 'Quantity',
                             'Float quality', 'Potential IDs', 'Effect IDs', 'Raw appraisal word', 'Availability'),
                            self.backend.item_records(document),
                            'Unknown IDs and property applicability remain numeric and inspection only. Float qualities retain their original bytes.'),
            InspectionTable('Memory-related words', ('Stored field', 'Opened value'),
                            self.backend.memory_records(document),
                            'These words differ in genuine saves. Their roles are unresolved; neither is rewritten or treated as a duplicate.'),
        )
