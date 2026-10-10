"""Actual Tk save/backup/restore workflow on generated or private native copies."""
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from tests.test_sw4ii_format import procedural_raw
from koei_editor.games.sw4ii.sw4ii_editor import Editor
from koei_editor.games.sw4ii import sw4ii_parser as parser


class SW4IIGuiTests(unittest.TestCase):
    def test_review_undo_theme_save_backup_restore_and_manual_max(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(root.destroy); root.withdraw()
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder); source = folder / 'copy.dat'
            # Genuine test input, when provided, is copied into a disposable safe directory.
            path = os.environ.get('SW4II_SECOND_SAVE_COPY') or os.environ.get('SW4II_SAVE_COPY')
            raw = Path(path).read_bytes() if path else procedural_raw()
            source.write_bytes(raw)
            editor = Editor(root); errors = []
            with patch('koei_editor.shared.verified_gui.messagebox.showerror', side_effect=lambda *args: errors.append(args)):
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(source)):
                    editor.open()
                self.assertFalse(errors)
                editor.make_backup()
                original_backup = editor.backup
                self.assertTrue(original_backup.exists())
                editor.group.set('Officers'); editor.search.set('Stored base attack'); editor.refresh()
                self.assertEqual(len(editor.fields.get_children()), parser.OFFICER_COUNT)
                editor.fields.selection_set('officer_0_attack'); editor.value.set('337'); editor.apply_selected()
                editor.review(); editor.undo(); self.assertEqual(editor.changes, {})
                editor.max_visible(); self.assertEqual(editor.changes, {})
                editor.group.set('Equipment'); editor.search.set(''); editor.refresh()
                editor.fields.selection_set('officer_0_equipped_weapon'); editor.selected()
                options = parser.field_options(editor.document, 'officer_0_equipped_weapon')
                original = parser.field_map(editor.document)['officer_0_equipped_weapon'].value(editor.document.payload)
                target = next((number for number, _ in options if number != original), original)
                label = next(label for label, number in editor._choice_values.items() if number == target)
                editor.choice_value.set(label); editor.selected_choice(); editor.apply_selected()
                self.assertEqual(editor.changes.get('officer_0_equipped_weapon', original), target)
                editor.review(); editor.undo(); self.assertEqual(editor.changes, {})
                editor.stage_values({'officer_0_equipped_weapon': target})
                editor.stage_values({'gold': 15231, 'tome_3': 234, 'officer_0_attack': 337})
                # Exercise dynamically qualified records through the real GUI,
                # including the genuine-file path when its private copy exists.
                mapped = parser.field_map(editor.document)
                for group in ('Weapons', 'Mounts'):
                    field = next(field for field in mapped.values() if field.group == group)
                    editor.group.set(group); editor.search.set(''); editor.refresh()
                    editor.fields.selection_set(field.id)
                    value = max(field.minimum, (field.value(editor.document.payload) + 1) % (field.maximum + 1))
                    editor.value.set(str(value)); editor.apply_selected()
                    self.assertEqual(editor.changes[field.id], value)
                editor.show_inspector(); editor.apply_theme('Dark'); editor.apply_theme('Light')
                destination = folder / 'edited.dat'; editor.save_to(destination)
                self.assertFalse(errors); self.assertEqual(source.read_bytes(), raw)
                self.assertTrue(editor.backup.exists())
                reopened = parser.read_save(destination)
                self.assertEqual(parser.field_map(reopened)['gold'].value(reopened.payload), 15231)
                self.assertEqual(parser.field_map(reopened)['officer_0_equipped_weapon'].value(reopened.payload), target)
                restored = folder / 'restored.dat'
                with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(original_backup)), patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename', return_value=str(restored)):
                    editor.restore()
                self.assertFalse(errors)
                self.assertEqual(restored.read_bytes(), raw)
