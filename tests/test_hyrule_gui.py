"""Real Tk copy workflows using procedural console exports; no game-load claim."""
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from koei_editor.games.hyrule_warriors.editor import Editor as HyruleEditor
from koei_editor.games.hyrule_warriors import parser as hw
from koei_editor.games.age_of_calamity.editor import Editor as CalamityEditor
from koei_editor.games.age_of_calamity import parser as aoc
from tests.test_hyrule_formats import procedural_hw, procedural_aoc


class GuiWorkflow:
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / ('copy' + self.backend.EXTENSION)
        self.raw = self.fixture()
        self.source.write_bytes(self.raw)
        self.editor = self.editor_type(self.root)
        self.errors = []
        mock = patch('koei_editor.shared.verified_gui.messagebox.showerror',
                     side_effect=lambda *args: self.errors.append(args))
        mock.start()
        self.addCleanup(mock.stop)
        with patch('koei_editor.shared.verified_gui.filedialog.askopenfilename', return_value=str(self.source)):
            self.editor.open()
        self.assertFalse(self.errors)

    def test_named_search_edit_review_undo_inspect_theme_safe_save_and_restore(self):
        editor = self.editor
        editor.group.set(self.group)
        editor.search.set(self.search)
        editor.refresh()
        self.assertIn(self.field, editor.fields.get_children())
        editor.fields.selection_set(self.field)
        editor.value.set(str(self.value))
        editor.apply_selected()
        self.assertEqual(editor.changes, {self.field: self.value})
        editor.review()
        self.assertTrue(any(isinstance(child, tk.Toplevel) for child in self.root.winfo_children()))
        editor.undo()
        self.assertEqual(editor.changes, {})
        editor.fields.selection_set(self.field)
        editor.value.set(str(self.value))
        editor.apply_selected()
        editor.show_inspector()
        titles = [table.title for table in editor.presentation.inspection_tables(editor.document)]
        self.assertIn('Weapons', titles)
        editor.apply_theme('Dark')
        editor.apply_theme('Light')
        destination = self.source.with_name('edited' + self.backend.EXTENSION)
        editor.save_to(destination)
        self.assertFalse(self.errors)
        self.assertEqual(self.source.read_bytes(), self.raw)
        self.assertTrue(editor.backup.exists())
        restored = self.backend.restore(editor.backup, self.source.with_name('restored' + self.backend.EXTENSION))
        self.assertEqual(restored.read_bytes(), self.raw)
        output = self.backend.read_save(destination)
        self.assertEqual(self.backend.field_map(output)[self.field].value(output.payload), self.value)


class HyruleGuiTests(GuiWorkflow, unittest.TestCase):
    backend = hw
    editor_type = HyruleEditor
    fixture = staticmethod(procedural_hw)
    group, search, field, value = 'Weapon stars', 'Knight', 'weapon_1_stars', 5

    def test_ordinary_seal_counter_excluded_from_visible_max(self):
        editor = self.editor
        editor.group.set('Ordinary skill seals')
        editor.search.set('Boomerang')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('weapon_1_skill_0_kos',))
        editor.max_visible()
        self.assertEqual(editor.changes, {})
        editor.fields.selection_set('weapon_1_skill_0_kos')
        editor.value.set('0')
        editor.apply_selected()
        self.assertEqual(editor.changes, {'weapon_1_skill_0_kos': 0})


class CalamityGuiTests(GuiWorkflow, unittest.TestCase):
    backend = aoc
    editor_type = CalamityEditor
    fixture = staticmethod(procedural_aoc)
    group, search, field, value = 'Weapon protection', 'Tree Branch', 'weapon_0_1_protected', 1

    def test_extensionless_dialog_and_named_discovered_inventory_max(self):
        editor = self.editor
        editor.group.set('Fruit')
        editor.search.set('Hearty Durian')
        editor.refresh()
        self.assertEqual(editor.fields.get_children(), ('material_0',))
        editor.max_visible()
        self.assertEqual(editor.changes, {'material_0': 999})
        calls = []
        with patch('koei_editor.shared.verified_gui.filedialog.asksaveasfilename',
                   side_effect=lambda **kwargs: calls.append(kwargs) or ''):
            editor.save_as()
        self.assertEqual(calls[0]['initialfile'], 'copy-edited')
        self.assertEqual(calls[0]['defaultextension'], '')
