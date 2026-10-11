"""Original Steam Ryza sessions using the shared Undo/review/safe-saving UI."""
from koei_editor.games.ryza import parser
from koei_editor.shared.scalar_presentation import InspectionTable, ScalarPresentation
from koei_editor.shared.verified_gui import Editor as ScalarEditor


class RyzaPresentation(ScalarPresentation):
    def inspection_tables(self, document):
        rows = tuple((r['group'], r['label'], r['item_id'], r['instance_id'], r['quality'], r['neighbor'])
                     for r in self.backend.item_records(document))
        return (InspectionTable('Existing inventory and equipment',
                                ('Location', 'Slot', 'Item ID', 'Instance ID', 'Quality', 'Adjacent raw u16'),
                                rows, 'Opened records. Important items and unknown adjacent values are read only.'),)


class Editor(ScalarEditor):
    game_id = 'atelier_ryza'
    backend = parser
    presentation_type = RyzaPresentation
    subtitle = 'Original Steam PC · native 66-byte item layout'
    summary = 'Existing ordinary item and equipment quality (1–999).'


class Ryza2Editor(Editor):
    game_id = 'atelier_ryza2'
    subtitle = 'Original Steam PC · native 100-byte item layout'
    summary = ('Existing item/equipment quality (1–100) and unspent skill-tree SP reductions. '
               'Higher quality caps and learned skills remain unmapped.')
