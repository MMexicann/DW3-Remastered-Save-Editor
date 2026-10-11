"""Searchable occupied-item inspection, without invented item names/ownership."""
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation


class SophiePresentation(ScalarPresentation):
    def inspection_tables(self, document):
        mapping = self.backend.field_map(document)
        rows = tuple((label, slot, instance, identity, quality,
                      'Whole-number quality editing' if f'{key}_{slot}_quality' in mapping
                      else 'Read only')
                     for key, label, slot, offset, instance, identity, quality, editable
                     in self.backend.item_records(document))
        return (InspectionTable('Existing items', ('Pool', 'Slot', 'Instance ID', 'Item ID', 'Quality', 'Eligibility'), rows,
                                'Unknown item IDs and every property byte are preserved. '
                                'Important items and synthesis buffers are read only; no items are created.'),
                InspectionTable('Progression', ('Field', 'Opened value'),
                                self.backend.progression_rows(document),
                                'Alchemy EXP/level, recipes, skills, friendships and event/calendar state need controlled native pairs.'))
