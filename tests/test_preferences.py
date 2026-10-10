"""Theme persistence and real Tk callbacks, with settings isolated in the project."""
import json
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from application import Application
import gui
from models import Change
import preferences


AREA = Path(__file__).resolve().parents[1] / '.test-runs'


class PreferenceStorageTests(unittest.TestCase):
    def setUp(self):
        AREA.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=AREA)
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.path = self.folder / 'config' / 'preferences.json'

    def test_config_location_is_separate_from_save_copies_and_working_directory(self):
        key = 'APPDATA' if os.name == 'nt' else 'XDG_CONFIG_HOME'
        if os.name != 'nt' and preferences.sys.platform == 'darwin':
            self.skipTest('macOS uses its native Application Support directory.')
        with patch.dict(os.environ, {key: str(self.folder)}):
            self.assertEqual(preferences.preference_path(),
                             self.folder / 'UniversalKoeiTecmoSaveEditor' / 'preferences.json')
        self.assertFalse(any(self.folder.iterdir()))

    def test_valid_themes_roundtrip_and_atomic_replacement_contains_only_tiny_schema(self):
        self.assertEqual(preferences.load_theme(self.path), 'Light')
        self.assertFalse(self.path.exists())
        for name in ('Dark', 'Light', 'Dark'):
            self.assertTrue(preferences.save_theme(name, self.path))
            self.assertEqual(preferences.load_theme(self.path), name)
            self.assertEqual(json.loads(self.path.read_bytes()), {'schema': 1, 'theme': name})
            self.assertLess(len(self.path.read_bytes()), 64)
            self.assertEqual(list(self.path.parent.glob('.preferences.*')), [])

    def test_corrupt_oversized_and_foreign_schema_files_fall_back_without_rewriting(self):
        self.path.parent.mkdir()
        invalid = (b'', b'{', b'\xff', b'[]', b'{"theme":"Dark"}',
                   b'{"schema":true,"theme":"Dark"}', b'{"schema":2,"theme":"Dark"}',
                   b'{"schema":1,"theme":7}', b'{"schema":1,"theme":"unknown"}',
                   b'{"schema":1,"theme":"Dark","save":"private"}',
                   b' ' * (preferences.MAX_BYTES + 1), b'[' * 1500 + b']' * 1500)
        for raw in invalid:
            with self.subTest(length=len(raw), prefix=raw[:24]):
                self.path.write_bytes(raw)
                self.assertEqual(preferences.load_theme(self.path), 'Light')
                self.assertEqual(self.path.read_bytes(), raw)

    def test_failed_atomic_replace_preserves_previous_settings_and_cleans_temporary(self):
        self.assertTrue(preferences.save_theme('Dark', self.path))
        original = self.path.read_bytes()
        with patch.object(preferences.os, 'replace', side_effect=PermissionError('Settings read-only')):
            self.assertFalse(preferences.save_theme('Light', self.path))
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(preferences.load_theme(self.path), 'Dark')
        self.assertEqual(list(self.path.parent.glob('.preferences.*')), [])

    def test_inaccessible_storage_is_optional_and_invalid_themes_create_nothing(self):
        with patch.object(Path, 'open', side_effect=PermissionError('Settings inaccessible')):
            self.assertEqual(preferences.load_theme(self.path), 'Light')
        with patch.object(Path, 'mkdir', side_effect=PermissionError('Settings inaccessible')):
            self.assertFalse(preferences.save_theme('Dark', self.path))
        for name in (None, True, 'Unknown', ['Dark']):
            self.assertFalse(preferences.save_theme(name, self.path))
        self.assertFalse(self.path.parent.exists())


@unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'A graphical display is required.')
class PreferenceGuiTests(unittest.TestCase):
    def setUp(self):
        AREA.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=AREA)
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / 'preferences.json'

    def new_root(self):
        root = tk.Tk()
        root.withdraw()
        def destroy():
            try:
                root.destroy()
            except tk.TclError:
                pass
        self.addCleanup(destroy)
        return root

    def test_real_selectors_remember_dark_across_restart_and_dw3_propagates_light(self):
        root = self.new_root()
        app = Application(root, preferences_path=self.path)
        self.assertFalse(self.path.exists())
        dw3 = app.select_game('dw3')
        change = Change('officer', 0, 'SPoint', 999)
        dw3.changes = {('officer', 0, 'SPoint'): change}
        dw3.history = [{}]
        dw3.item_filter.set('Peacock')
        app.theme_selector.set('Dark')
        app.theme_selector.event_generate('<<ComboboxSelected>>')
        root.update()
        self.assertEqual(preferences.load_theme(self.path), 'Dark')
        self.assertEqual(dw3.theme_name.get(), 'Dark')
        self.assertEqual(list(dw3.changes.values()), [change])
        self.assertEqual(dw3.history, [{}])
        self.assertEqual(dw3.item_filter.get(), 'Peacock')
        root.destroy()
        reopened_root = self.new_root()
        reopened = Application(reopened_root, preferences_path=self.path)
        self.assertEqual(reopened.theme_name.get(), 'Dark')
        self.assertEqual(reopened.select_game('dw4hyper').theme_name.get(), 'Dark')
        embedded = reopened.select_game('dw3')
        embedded.theme_selector.set('Light')
        embedded.theme_selector.event_generate('<<ComboboxSelected>>')
        reopened_root.update()
        self.assertEqual(reopened.theme_name.get(), 'Light')
        self.assertEqual(reopened.sessions['dw4hyper'][1].theme_name.get(), 'Light')
        self.assertEqual(preferences.load_theme(self.path), 'Light')

    def test_standalone_dw3_loads_same_theme_and_startup_does_not_rewrite_settings(self):
        preferences.save_theme('Dark', self.path)
        with patch.object(preferences, 'save_theme', wraps=preferences.save_theme) as save:
            root = self.new_root()
            editor = gui.Editor(root, preferences_path=self.path)
            self.assertEqual(editor.theme_name.get(), 'Dark')
            save.assert_not_called()
            editor.theme_selector.set('Light')
            editor.theme_selector.event_generate('<<ComboboxSelected>>')
            root.update()
            save.assert_called_once_with('Light', self.path)
        self.assertEqual(preferences.load_theme(self.path), 'Light')

    def test_settings_write_failure_keeps_the_editor_usable_and_pending_edits(self):
        preferences.save_theme('Light', self.path)
        root = self.new_root()
        app = Application(root, preferences_path=self.path)
        editor = app.select_game('pw3')
        editor.changes = {'character_0_attack': 123}
        editor.history = [{}]
        with patch.object(preferences.os, 'replace', side_effect=PermissionError('Settings read-only')):
            app.apply_theme('Dark')
        self.assertEqual(app.theme_name.get(), 'Dark')
        self.assertEqual(editor.theme_name.get(), 'Dark')
        self.assertEqual(editor.changes, {'character_0_attack': 123})
        self.assertEqual(editor.history, [{}])
        self.assertEqual(preferences.load_theme(self.path), 'Light')

    def test_smoke_mode_theme_switches_never_write_preferences(self):
        preferences.save_theme('Dark', self.path)
        original = self.path.read_bytes()
        root = self.new_root()
        app = Application(root, preferences_path=self.path, persist_preferences=False)
        with patch.object(preferences, 'save_theme') as save:
            app.apply_theme('Light')
            editor = app.select_game('dw3')
            editor.apply_theme('Dark')
            app.apply_theme('Light')
            save.assert_not_called()
        self.assertEqual(self.path.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
