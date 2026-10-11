"""Slot and named inventory inspection without returning player names or IDs."""
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation


class Presentation(ScalarPresentation):
    def inspection_tables(self, document):
        characters, personas = self.backend.progression_records(document)
        rows = tuple((record['slot'], 'Qualified occupied slot' if record['qualified'] else 'Preserved / not editable',
                      *(value for _, value in record['resources']))
                     for record in self.backend.slot_records(document))
        return (
            InspectionTable('Save-slot resources',
                            ('Slot', 'State', 'Money', 'Persona points', 'Unspent BOND points'), rows,
                            'Reserved slot 0 and empty/unknown slots are preserved. Player names and account context are not exported.'),
            InspectionTable('Named ordinary item stacks',
                            ('Save slot', 'Category', 'Item', 'Quantity byte', 'Preserved adjacent byte', 'Availability'),
                            self.backend.item_records(document),
                            'Existing positive consumable, ingredient, incense, remedy and skill-card stacks. Incense application and Persona teaching remain under game control.'),
            InspectionTable('Character growth', ('Save slot', 'Character', 'Stored level byte'), characters,
                            'Read only. EXP, derived stats and unlock prerequisites remain unchanged.'),
            InspectionTable('Held Persona records', ('Save slot', 'Held slot', 'Raw Persona ID word'), personas,
                            'Read only. Empty FFFF records omitted; IDs, compendium, slot capacity and skill dependencies remain unchanged.'),
        )
