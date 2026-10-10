"""Independent PW4 ownership, preservation and restore adversarial checks.

All fixtures in this module are procedural, not player saves.
"""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

import copy_storage
from models import SaveError
import pw4_parser as parser
from tests.test_pw4_format import encoded, native_integrity, procedural_raw
from pw4_editor import Editor


class PW4ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original = parser.decode(procedural_raw())
        payload = bytearray(original.payload)
        for identity in range(parser.COIN_ID_COUNT):
            base = parser.COIN_BODY + identity * parser.COIN_STRIDE
            payload[base:base + 13] = bytes(13)
        # Earned/spent counters, quantity and obtained flags are independent.
        cases = ((20, 20, 0, 0x81), (0, 0, 5, 1), (5, 0, 5, 0),
                 (1001, 0, 1001, 0x81), (5, 0, 5, 1), (8, 0, 10, 0xFE))
        for identity, (earned, spent, quantity, flags) in enumerate(cases):
            base = parser.COIN_BODY + identity * parser.COIN_STRIDE
            struct.pack_into('<III', payload, base, earned, spent, quantity)
            payload[base + 12] = flags
        cls.raw = encoded(native_integrity(payload), seed=0)
        cls.document = parser.decode(cls.raw)

    def test_only_proven_obtained_records_are_editable(self):
        fields = parser.field_map(self.document)
        self.assertEqual({key for key in fields if key.startswith('coin_')},
                         {'coin_0_quantity', 'coin_3_quantity', 'coin_4_quantity'})
        for identity in (1, 2, 5, 400):
            with self.subTest(identity=identity), self.assertRaises(SaveError):
                parser.stage(self.document, {}, f'coin_{identity}_quantity', 999)

    def test_coin_max_preserves_history_unknown_bytes_and_higher_quantities(self):
        changes = parser.maximums(self.document, {}, 'Owned coins')
        self.assertEqual(changes, {'coin_0_quantity': 999, 'coin_4_quantity': 999})
        updated = parser.decode(parser.serialize(self.document, changes))
        allowed = set(range(parser.COIN_HEADER, parser.COIN_HEADER + 4))
        for identity in (0, 4):
            base = parser.COIN_BODY + identity * parser.COIN_STRIDE
            allowed.update(range(base + 8, base + 12))
        touched = {i for i, (old, new) in enumerate(zip(self.document.payload, updated.payload))
                   if old != new}
        self.assertTrue(touched <= allowed)
        rows = {row['id']: row for row in parser.coins(updated)}
        self.assertEqual(rows[0], {'id': 0, 'earned': 20, 'spent': 20,
                                  'quantity': 999, 'flags': 0x81})
        self.assertEqual(rows[3]['quantity'], 1001)
        self.assertEqual(parser.serialize(self.document, {}), self.raw)

    def test_mutable_snapshot_and_boolean_seed_are_rejected(self):
        for doc in (replace(self.document, raw=bytearray(self.raw)),
                    replace(self.document, payload=bytearray(self.document.payload)),
                    replace(self.document, seed=False)):
            with self.subTest(seed_type=type(doc.seed)), self.assertRaises(SaveError):
                parser.serialize(doc, {})

    def test_restore_qualifies_the_exact_bytes_written(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            source = folder / 'copy.dat'
            source.write_bytes(self.raw)
            backup = parser.backup(parser.read_save(source))
            destination = folder / 'restored.dat'
            genuine_restore = copy_storage.restore_snapshot

            def replace_backup_after_any_precheck(*args, **kwargs):
                malformed = bytes([self.raw[0] ^ 1]) + self.raw[1:]
                backup.write_bytes(malformed)
                manifest = backup.with_suffix('.json')
                metadata = json.loads(manifest.read_text())
                metadata['sha256'] = hashlib.sha256(malformed).hexdigest()
                manifest.write_text(json.dumps(metadata))
                return genuine_restore(*args, **kwargs)

            with patch.object(parser, 'restore_snapshot',
                              side_effect=replace_backup_after_any_precheck):
                with self.assertRaises(SaveError):
                    parser.restore(backup, destination)
            self.assertFalse(destination.exists())


class PW4GuiReviewTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        PW4ReviewTests.setUpClass()
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        self.source = self.folder / 'copy.dat'
        self.source.write_bytes(PW4ReviewTests.raw)
        self.editor = Editor(self.root)
        self.errors = []
        mocked_error = patch('verified_gui.messagebox.showerror',
                             side_effect=lambda *args: self.errors.append(args))
        mocked_error.start()
        self.addCleanup(mocked_error.stop)
        with patch('verified_gui.filedialog.askopenfilename', return_value=str(self.source)):
            self.editor.open()
        self.assertFalse(self.errors)

    def test_owned_coin_search_review_undo_and_safe_copy_save(self):
        editor = self.editor
        editor.group.set('Owned coins')
        editor.search.set('Coin ID 000')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('coin_0_quantity',))
        editor.fields.selection_set('coin_0_quantity')
        editor.value.set('50')
        editor.apply_selected()
        self.assertEqual(editor.changes, {'coin_0_quantity': 50})
        editor.review()
        self.assertTrue(any(isinstance(child, tk.Toplevel) for child in self.root.winfo_children()))
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.stage_values({'coin_0_quantity': 50})
        destination = self.folder / 'edited.dat'
        editor.save_to(destination)
        self.assertFalse(self.errors)
        self.assertTrue(editor.backup.exists())
        self.assertEqual(self.source.read_bytes(), PW4ReviewTests.raw)
        doc = parser.read_save(destination)
        row = {row['id']: row for row in parser.coins(doc)}[0]
        self.assertEqual((row['quantity'], row['earned'], row['spent'], row['flags']),
                         (50, 20, 20, 0x81))
        tables = editor.presentation.inspection_tables(doc)
        self.assertTrue(any(table.title == 'Owned coins' for table in tables))


if __name__ == '__main__':
    unittest.main()
