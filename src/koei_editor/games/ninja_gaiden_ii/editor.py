"""Shared safe-copy UI for the original NGII qualified extracted story profile."""
from koei_editor.games.ninja_gaiden_ii import parser as backend
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class StoryPresentation(ScalarPresentation):
    def inspection_tables(self, document):
        inventory, resources = backend.inspection_records(document)
        return (InspectionTable('Inventory', ('Slot', 'Native ID', 'Name', 'Quantity', 'Variant', 'Editing'),
                                inventory, 'Existing unique ordinary consumables may be reduced. '
                                'Unknown IDs, weapon variants and duplicates are preserved.'),
                InspectionTable('Resources and score', ('Stored value', 'Opened value'), resources,
                                'Karma is separate from spendable essence. Health/Ninpo, unlocks and story remain unchanged.'))


class Editor(ScalarEditor):
    game_id = backend.GAME_ID
    save_extension = '.dat'
    backend = backend
    presentation_type = StoryPresentation
    subtitle = 'Original Xbox 360 · revision-6 extracted story profile'
    summary = 'Manual Yellow Essence and existing-stack reductions, with native word checksum and inventory inspection.'


def read_save(path):
    return backend.read_save(path)
