"""Published item records; generated inputs are not native gameplay evidence."""
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import os

import koei_editor.games.sophie2.atelier_sophie2_codec as codec
import koei_editor.games.sophie2.atelier_sophie2_parser as backend
from koei_editor.games.sophie2.atelier_sophie2_presentation import Sophie2Presentation
from koei_editor.games.dw3.models import SaveError
from tests.test_atelier_sophie2_format import procedural_payload


def inventory_raw():
    payload = bytearray(procedural_payload())
    groups, equipment, _, _, _ = backend._structure(bytes(payload))
    start = next(start for key, _, start, _ in groups if key == 'expendable')
    for index, uses, capacity in ((0, 2, 7), (1, 9, 5), (2, 0, 0)):
        offset = start + index * 44
        struct.pack_into('<h', payload, offset + 4, 70 + index)
        payload[offset + 0x24:offset + 0x26] = bytes((uses, capacity))
    # Qualify an existing equipped battle item, without touching empty slots.
    offset = dict(equipment)[0] + 4 * 44
    struct.pack_into('<h', payload, offset + 4, 75)
    payload[offset + 0x24:offset + 0x26] = bytes((1, 3))
    return codec.encode_file(bytes(256), bytes(payload), 42)


class Sophie2InventoryTests(unittest.TestCase):
    def setUp(self):
        self.document = backend.decode(inventory_raw())

    def test_refill_is_bounded_by_existing_capacity_and_surgical(self):
        fields = backend.field_map(self.document)
        self.assertEqual(fields['expendable_0_uses'].maximum, 7)
        self.assertEqual(fields['character_0_4_uses'].maximum, 3)
        self.assertNotIn('expendable_1_uses', fields)
        self.assertNotIn('expendable_2_uses', fields)
        self.assertNotIn('character_0_5_uses', fields)
        self.assertNotIn('materials_0_uses', fields)
        changes = backend.stage(self.document, {}, 'expendable_0_uses', 7)
        changes = backend.stage(self.document, changes, 'character_0_4_uses', 3)
        raw = backend.serialize(self.document, changes)
        output = backend.decode(raw)
        offsets = {fields[key].offset for key in changes}
        actual = {i for i, (a, b) in enumerate(zip(self.document.payload, output.payload)) if a != b}
        self.assertEqual(actual, offsets)
        for offset in offsets:
            self.assertEqual(output.payload[offset + 1], self.document.payload[offset + 1])
        self.assertEqual(backend.serialize(self.document, {}), self.document.raw)
        self.assertEqual(backend.stage(self.document, changes, 'expendable_0_uses', 2),
                         {'character_0_4_uses': 3})
        for value in (-1, 8, True, 1.5):
            with self.assertRaises(SaveError):
                backend.serialize(self.document, {'expendable_0_uses': value})

    def test_max_preserves_opaque_and_inconsistent_records(self):
        changes = backend.maximums(self.document, {}, 'Consumable container')
        self.assertEqual(changes['expendable_0_uses'], 7)
        self.assertNotIn('expendable_1_uses', changes)
        self.assertNotIn('expendable_2_uses', changes)
        output = backend.decode(backend.serialize(self.document, changes))
        before = backend.item_records(self.document)
        after = backend.item_records(output)
        for original, edited in zip(before, after):
            for key in ('item_id', 'instance_id', 'traits', 'effects', 'capacity', 'stat_bytes'):
                self.assertEqual(original[key], edited[key])

    def test_inspector_reports_existing_records_and_named_equipment(self):
        presentation = Sophie2Presentation(backend, backend.GAME_ID)
        table = presentation.inspection_tables(self.document)[0]
        self.assertIn('Trait IDs', table.columns)
        self.assertIn('Raw stat bytes', table.columns)
        self.assertTrue(any(row[0] == 'Sophie equipment' and row[1] == 'Battle item 1'
                            and row[5] == '1 / 3' for row in table.rows))
        self.assertTrue(any(row[5] == '9 / 5' for row in table.rows))
        field = backend.field_map(self.document)['character_0_4_uses']
        self.assertEqual(presentation.record_name(field), 'Sophie: Battle item 1')
        self.assertIn('opened saved capacity', backend.field_hint(self.document, field.id))


@unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'A display is required')
class Sophie2InventoryGuiTests(unittest.TestCase):
    def test_search_refill_undo_review_and_copy_save(self):
        import tkinter as tk
        from koei_editor.games.sophie2.atelier_sophie2_editor import Editor
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'copy.dat'
            source.write_bytes(inventory_raw())
            root = tk.Tk()
            root.withdraw()
            try:
                editor = Editor(root)
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                    editor.open()
                editor.group.set('Consumable container')
                editor.search.set('Remaining uses')
                editor.refresh()
                self.assertEqual(tuple(editor.fields.get_children()), ('expendable_0_uses',))
                editor.max_visible()
                self.assertEqual(editor.changes, {'expendable_0_uses': 7})
                editor.undo()
                self.assertEqual(editor.changes, {})
                editor.max_visible()
                self.assertEqual(backend.review(editor.document, editor.changes)[0][2], 7)
                editor.show_inspector()
                dialog = next(w for w in root.winfo_children() if isinstance(w, tk.Toplevel))
                def descendants(widget):
                    for child in widget.winfo_children():
                        yield child
                        yield from descendants(child)
                from tkinter import ttk
                notebook = next(w for w in descendants(dialog) if isinstance(w, ttk.Notebook))
                first_tab = notebook.nametowidget(notebook.tabs()[0])
                search = next(w for w in descendants(first_tab) if isinstance(w, ttk.Entry))
                records = next(w for w in descendants(first_tab) if isinstance(w, ttk.Treeview))
                total = len(records.get_children())
                search.insert(0, 'Sophie Battle item 1')
                root.update()
                self.assertEqual(len(records.get_children()), 1)
                self.assertEqual(records.item(records.get_children()[0], 'values')[1], 'Battle item 1')
                search.delete(0, 'end')
                root.update()
                self.assertEqual(len(records.get_children()), total)
                self.assertEqual(editor.changes, {'expendable_0_uses': 7})
                dialog.destroy()
                output = Path(folder) / 'edited.dat'
                with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename', return_value=str(output)), \
                     patch('koei_editor.shared.verified_gui.messagebox.showinfo'):
                    editor.save_as()
                saved = backend.read_save(output)
                self.assertEqual(backend.field_map(saved)['expendable_0_uses'].value(saved.payload), 7)
                self.assertEqual(source.read_bytes(), inventory_raw())
                self.assertTrue(list((Path(folder) / 'WarriorsEditorBackups').glob('*.dat')))
            finally:
                root.destroy()


if __name__ == '__main__':
    unittest.main()
