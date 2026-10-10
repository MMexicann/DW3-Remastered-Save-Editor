"""Independent adversarial checks; procedural records are not game-load evidence."""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import koei_editor.games.sophie2.atelier_sophie2_codec as codec
import koei_editor.games.sophie2.atelier_sophie2_parser as backend
import koei_editor.shared.copy_storage as copy_storage
from koei_editor.games.dw3.models import SaveError
from tests.test_atelier_sophie2_format import procedural_payload
from tests.test_sophie2_inventory import inventory_raw


def encoded(payload, seed=0):
    return codec.encode_file(bytes(256), bytes(payload), seed)


class Sophie2IndependentAuditTests(unittest.TestCase):
    def test_usage_boundaries_and_empty_records_are_not_manufactured(self):
        payload = bytearray(procedural_payload())
        groups, equipment, _, _, _ = backend._structure(bytes(payload))
        start = next(start for key, _, start, _ in groups if key == 'expendable')
        pairs = ((0, 1), (1, 1), (0, 255), (255, 255), (255, 254), (1, 0), (0, 0))
        for index, pair in enumerate(pairs):
            offset = start + index * backend.RECORD_SIZE
            struct.pack_into('<h', payload, offset + 4, 200 + index)
            payload[offset + 0x24:offset + 0x26] = bytes(pair)
        # Negative item identity is an empty/unused record even if uses look valid.
        empty = start + 7 * backend.RECORD_SIZE
        payload[empty + 0x24:empty + 0x26] = b'\0\xff'
        # Valid-looking usage in a weapon slot is never treated as a battle item.
        weapon = dict(equipment)[0]
        payload[weapon + 0x24:weapon + 0x26] = b'\0\xff'
        document = backend.decode(encoded(payload))
        fields = backend.field_map(document)
        self.assertEqual({key: field.maximum for key, field in fields.items() if key.endswith('_uses')},
                         {'expendable_0_uses': 1, 'expendable_1_uses': 1,
                          'expendable_2_uses': 255, 'expendable_3_uses': 255})
        changes = backend.maximums(document, {}, 'Consumable container')
        output = backend.changed_payload(document, changes)
        allowed = {fields[key].offset + byte for key in changes for byte in range(fields[key].size)}
        self.assertTrue(all(a == b or index in allowed
                            for index, (a, b) in enumerate(zip(document.payload, output))))
        for index in range(8):
            offset = start + index * backend.RECORD_SIZE
            self.assertEqual(output[offset + 0x25], payload[offset + 0x25])
        for index in (4, 5, 6, 7):
            offset = start + index * backend.RECORD_SIZE
            self.assertEqual(output[offset + 0x24], payload[offset + 0x24])

    def test_tagged_locations_and_character_identity_determine_field_offsets(self):
        payload = bytearray(procedural_payload())
        _, equipment, _, _, _ = backend._structure(bytes(payload))
        positions = [start - 0x176 for _, start in equipment]
        # Party order is not character identity; move existing complete records.
        parties = [bytes(payload[position:position + 0x314]) for position in positions]
        for position, party in zip(positions, reversed(parties)):
            payload[position:position + 0x314] = party
        # Shift every tag and record by an arbitrary opaque envelope prefix.
        payload = bytearray(b'opaque-prefix\x87\x13\x01' + payload)
        _, equipment, _, _, _ = backend._structure(bytes(payload))
        item = dict(equipment)[3] + 7 * backend.RECORD_SIZE
        struct.pack_into('<h', payload, item + 4, 314)
        payload[item + 0x24:item + 0x26] = b'\x02\x06'
        document = backend.decode(encoded(payload))
        field = backend.field_map(document)['character_3_7_uses']
        self.assertEqual((field.offset, field.group, field.maximum),
                         (item + 0x24, 'Alette equipment', 6))
        output = backend.changed_payload(document, {'character_3_7_uses': 6})
        self.assertEqual([index for index, (a, b) in enumerate(zip(document.payload, output)) if a != b],
                         [item + 0x24])
        record = next(row for row in backend.item_records(document)
                      if row['group'] == 'Alette equipment' and row['slot'] == 8)
        self.assertEqual((record['label'], record['item_id'], record['uses'], record['capacity']),
                         ('Battle item 4', 314, 2, 6))

    def test_forged_mutable_snapshot_metadata_is_rejected(self):
        document = backend.decode(inventory_raw())
        variants = [replace(document, **{name: bytearray(getattr(document, name))})
                    for name in ('raw', 'payload', 'header', 'trailer', 'footer')]
        zero_seed = backend.decode(encoded(procedural_payload()))
        variants.extend((replace(zero_seed, seed=False), replace(zero_seed, seed=0.0)))
        for document in variants:
            with self.subTest(raw_type=type(document.raw), seed_type=type(document.seed)):
                with self.assertRaises(SaveError):
                    backend.serialize(document, {})

    def test_restore_requalifies_the_exact_bytes_written(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            source = folder / 'copy.dat'
            source.write_bytes(inventory_raw())
            backup = backend.backup(backend.read_save(source))
            destination = folder / 'restored.dat'
            actual_restore = copy_storage.restore_snapshot

            def replace_backup_after_earlier_read(*args, **kwargs):
                damaged = bytearray(backup.read_bytes())
                # Header is opaque; damage the encrypted body instead.
                damaged[codec.HEADER_SIZE + 17] ^= 8
                damaged = bytes(damaged)
                backup.write_bytes(damaged)
                metadata_path = backup.with_suffix('.json')
                metadata = json.loads(metadata_path.read_text())
                metadata['sha256'] = hashlib.sha256(damaged).hexdigest()
                metadata_path.write_text(json.dumps(metadata))
                return actual_restore(*args, **kwargs)

            with patch.object(backend, 'restore_snapshot', side_effect=replace_backup_after_earlier_read):
                with self.assertRaises(SaveError):
                    backend.restore(backup, destination)
            self.assertFalse(destination.exists())


@unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'A display is required')
class InspectorFilterAuditTests(unittest.TestCase):
    def test_each_tab_filters_all_cells_independently_and_restores_order(self):
        import tkinter as tk
        from tkinter import ttk
        from koei_editor.games.sophie2.atelier_sophie2_editor import Editor

        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)

        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'copy.dat'
            source.write_bytes(inventory_raw())
            root = tk.Tk()
            root.withdraw()
            try:
                editor = Editor(root)
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                    editor.open()
                editor.show_inspector()
                dialog = next(w for w in root.winfo_children() if isinstance(w, tk.Toplevel))
                notebook = next(w for w in descendants(dialog) if isinstance(w, ttk.Notebook))
                tabs = [notebook.nametowidget(name) for name in notebook.tabs()]
                pairs = [(next(w for w in descendants(tab) if isinstance(w, ttk.Entry)),
                          next(w for w in descendants(tab) if isinstance(w, ttk.Treeview)))
                         for tab in tabs]
                original = [tuple(view.get_children()) for _, view in pairs]
                first_search, first_view = pairs[0]
                second_search, second_view = pairs[1]
                # Record ID is in a later cell; token search spans the complete row.
                first_search.insert(0, 'CONSUMABLE\t71')
                root.update()
                first_rows = tuple(first_view.get_children())
                self.assertEqual(len(first_rows), 1)
                self.assertEqual(first_view.item(first_rows[0], 'values')[5], '9 / 5')
                self.assertEqual(tuple(second_view.get_children()), original[1])
                second_search.insert(0, 'Alchemy Plachta')
                root.update()
                self.assertEqual(len(second_view.get_children()), 2)
                self.assertEqual(tuple(first_view.get_children()), first_rows)
                for search, view in pairs:
                    search.delete(0, 'end')
                root.update()
                self.assertEqual([tuple(view.get_children()) for _, view in pairs], original)
                first_search.insert(0, 'no-such-item')
                root.update()
                self.assertEqual(tuple(first_view.get_children()), ())
                first_search.delete(0, 'end')
                root.update()
                self.assertEqual(tuple(first_view.get_children()), original[0])
                self.assertEqual(editor.changes, {})
                self.assertEqual(backend.serialize(editor.document, {}), inventory_raw())
            finally:
                root.destroy()


if __name__ == '__main__':
    unittest.main()
