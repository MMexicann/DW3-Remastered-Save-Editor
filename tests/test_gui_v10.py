"""Music and bulk element GUI actions use the same validated save writer."""
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
import koei_editor.games.dw3.gui as gui
import koei_editor.games.dw3.collection_editor as collections
import koei_editor.games.dw3.officer_weapon_editor as weapons
from koei_editor.games.dw3.save_parser import read_save, parse_bytes
from koei_editor.games.dw3.save_writer import serialize

FIXTURE = PROJECT / 'work/original-upload/GameStatusData.sav'


@unittest.skipUnless(FIXTURE.exists(), 'An explicitly supplied save copy is required.')
class ReleaseGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = read_save(FIXTURE)

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.editor = gui.Editor(self.root)
        self.errors = []
        self.errors_patch = patch.object(gui.messagebox, 'showerror', side_effect=lambda *a, **k: self.errors.append(a))
        self.errors_patch.start()
        self.editor.document = self.original
        self.editor.set_loaded(True)
        self.editor.refresh()

    def tearDown(self):
        self.errors_patch.stop()
        self.root.destroy()

    def test_music_search_apply_and_undo(self):
        g = self.editor
        g.notebook.select(g.tabs['Collections'])
        g.collection_filter.set('YELLOW STORM')
        self.assertEqual(g.collection_tree.get_children(), ('music:0',))
        g.unlock_music()
        self.assertFalse(self.errors)
        self.assertEqual(g.collection_tree.item('music:0', 'values')[-1], 'Yes')
        result = parse_bytes(serialize(g.document, list(g.changes.values()))[0])
        self.assertEqual(collections.collection_state(result)['music']['owned'], 42)
        self.assertEqual(result.properties['EngiClearCharaArray']['value'], self.original.properties['EngiClearCharaArray']['value'])
        g.undo()
        self.assertFalse(g.changes)
        self.assertEqual(collections.collection_state(g.document)['music'], collections.collection_state(self.original)['music'])

    def test_bulk_elements_after_pending_acquisition_and_undo(self):
        g = self.editor
        g.unlock_weapons()
        acquisition = g.changes.copy()
        g.unique_weapon_element.set('Fire')
        g.apply_unique_weapon_elements()
        self.assertFalse(self.errors)
        rows = [row for row in weapons.states(g.document, list(g.changes.values())) if row['array'] == 'UniqueWeaponDataArray']
        self.assertEqual(len(rows), 84)
        self.assertTrue(all(row['elements'] == 4 for row in rows))
        g.undo()
        self.assertEqual(g.changes, acquisition)
        g.unique_weapon_element.set('Unknown')
        before = g.changes.copy()
        g.apply_unique_weapon_elements()
        self.assertEqual(g.changes, before)
        self.assertEqual(len(self.errors), 1)

    def test_review_separates_existing_notes_and_compact_file_labels(self):
        g = self.editor
        g.update_paths()
        self.assertEqual(g.filename.get(), 'Opened copy: GameStatusData.sav')
        self.assertNotIn(str(PROJECT), g.filename.get())
        g.review()
        window = next(child for child in self.root.winfo_children() if isinstance(child, tk.Toplevel))
        pages = next(child for child in window.winfo_children() if isinstance(child, ttk.Notebook))
        labels = [pages.tab(tab, 'text') for tab in pages.tabs()]
        self.assertEqual(labels[0], 'Pending Changes')
        if g.document.compatibility_warnings:
            self.assertTrue(labels[1].startswith('Saved-value Notes'))
        self.assertEqual(gui.VERSION, '1.1')
        self.assertEqual(g.author_label.cget('text'), 'Made by Mexican')

    def test_contact_available_without_a_save_and_opens_only_the_requested_link(self):
        self.editor.document = None
        self.editor.set_loaded(False)
        self.editor.show_contact()
        dialog = next(child for child in self.root.winfo_children() if isinstance(child, tk.Toplevel))
        widgets = []
        stack = [dialog]
        while stack:
            widget = stack.pop()
            widgets.append(widget)
            stack.extend(widget.winfo_children())
        entry = next(widget for widget in widgets if isinstance(widget, ttk.Entry))
        self.assertEqual(entry.get(), 'mexicannn')
        steam_button = next(widget for widget in widgets if isinstance(widget, ttk.Button) and widget.cget('text') == 'Open Steam Profile')
        with patch.object(gui.webbrowser, 'open') as opened:
            steam_button.invoke()
            opened.assert_called_once_with('https://steamcommunity.com/id/theonlyjuandeagingmexican/')


if __name__ == '__main__':
    unittest.main()
