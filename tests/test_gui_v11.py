"""Fresh-save counter regression uses supplied copies and actual GUI callbacks."""
from pathlib import Path
import hashlib
import os
import shutil
import sys
import tempfile
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch
import uuid

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
sys.path.insert(0,str(PROJECT/'tests'))
import koei_editor.games.dw3.gui as gui
import koei_editor.games.dw3.bodyguard_customization as customization
import koei_editor.games.dw3.progression_editor as progression
from koei_editor.games.dw3.save_parser import read_save
from koei_editor.games.dw3.save_parser import parse_bytes
from koei_editor.games.dw3.save_writer import serialize
from test_elixirs_v08 import replace_top_tag

FIXTURE=PROJECT/'work/original-upload/GameStatusData.sav'
AREA=PROJECT/'work/gui-v11-tests'


@unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'),
                     'A graphical display is required.')
class AppearanceGuiTests(unittest.TestCase):
    """Appearance switches must leave forms, selection and disabled actions intact."""
    def setUp(self):
        area = PROJECT / '.test-runs'
        area.mkdir(exist_ok=True)
        self.preference_folder = tempfile.TemporaryDirectory(dir=area)
        self.addCleanup(self.preference_folder.cleanup)
        self.root=tk.Tk();self.root.withdraw()
        self.editor=gui.Editor(self.root, preferences_path=Path(self.preference_folder.name) / 'preferences.json')

    def tearDown(self):
        self.root.destroy()

    def test_theme_selector_preserves_controls_and_uses_readable_colors(self):
        g=self.editor
        g.notebook.select(g.tabs['Items'])
        g.item_filter.set('Peacock')
        g.item_value.set('12')
        original_states=[str(button.cget('state')) for button in g.buttons]
        popup=g.theme_selector.tk.call('ttk::combobox::PopdownWindow',str(g.theme_selector))
        for name in ('Dark','Light'):
            g.theme_selector.set(name)
            g.theme_selector.event_generate('<<ComboboxSelected>>')
            self.root.update_idletasks()
            self.assertEqual(g.theme_name.get(),name)
            self.assertEqual(g.notebook.select(),str(g.tabs['Items']))
            self.assertEqual(g.item_filter.get(),'Peacock')
            self.assertEqual(g.item_value.get(),'12')
            self.assertEqual([str(button.cget('state')) for button in g.buttons],original_states)
            self.assertFalse(g.changes)
            for canvas,_ in g.scroll_areas:
                self.assertEqual(canvas.cget('background'),self.root.cget('background'))
            self.assertEqual(g.theme_selector.tk.call(f'{popup}.f.l','cget','-background'),
                             g.style.lookup('TCombobox','fieldbackground'))
            self.assertEqual(g.theme_selector.tk.call(f'{popup}.f.l','cget','-foreground'),
                             g.style.lookup('TCombobox','foreground'))
            def luminance(color):
                channels=[int(color[i:i+2],16)/255 for i in (1,3,5)]
                linear=[v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4 for v in channels]
                return sum(v*weight for v,weight in zip(linear,(0.2126,0.7152,0.0722)))
            front=luminance(g.style.lookup('TEntry','foreground'))
            back=luminance(g.style.lookup('TEntry','fieldbackground'))
            self.assertGreaterEqual((max(front,back)+0.05)/(min(front,back)+0.05),4.5)
        with self.assertRaises(ValueError):g.apply_theme('Invalid')
        self.assertEqual(g.theme_name.get(),'Light')

    def test_contact_dialog_created_in_dark_theme_has_readable_entry(self):
        g=self.editor;g.apply_theme('Dark');g.show_contact()
        dialog=next(child for child in self.root.winfo_children() if isinstance(child,tk.Toplevel))
        self.assertEqual(dialog.cget('background'),self.root.cget('background'))
        self.assertEqual(g.style.lookup('TEntry','foreground',('readonly',)),g.style.lookup('TEntry','foreground'))
        self.assertEqual(g.style.lookup('TEntry','fieldbackground',('readonly',)),g.style.lookup('TEntry','fieldbackground'))


@unittest.skipUnless(FIXTURE.exists(),'An explicitly supplied private fixture is required.')
class MissingCounterGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=read_save(FIXTURE)
        cls.fixture_hash=hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        cls.missing=replace_top_tag(cls.original,cls.original.properties['BeansNum'],b'')

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()==cls.fixture_hash

    def setUp(self):
        AREA.mkdir(parents=True,exist_ok=True)
        self.folder=AREA/uuid.uuid4().hex
        self.folder.mkdir()
        self.copy=self.folder/'fresh-copy.sav'
        self.copy.write_bytes(self.missing.encrypted)
        self.root=tk.Tk();self.root.withdraw()
        self.editor=gui.Editor(self.root, preferences_path=self.folder / 'preferences.json')
        self.errors=[]
        self.dialogs=[]
        for name,kwargs in [('showerror',{'side_effect':lambda *a,**k:self.errors.append(a)}),
                            ('showinfo',{}),('showwarning',{}),('askyesno',{'return_value':True})]:
            hook=patch.object(gui.messagebox,name,**kwargs);hook.start();self.dialogs.append(hook)
        with patch.object(gui.filedialog,'askopenfilename',return_value=str(self.copy)):
            self.editor.open()
        self.assertFalse(self.errors)

    def tearDown(self):
        try:
            self.assertEqual(self.copy.read_bytes(),self.missing.encrypted)
        finally:
            for hook in reversed(self.dialogs):hook.stop()
            self.root.destroy()
            assert self.folder.resolve().is_relative_to(AREA.resolve())
            shutil.rmtree(self.folder)

    def test_zero_counter_can_be_edited_and_saved_without_a_story_clear(self):
        g=self.editor
        self.assertEqual(g.elixir_input.get(),'0')
        for widget in (g.elixir_entry,g.elixir_apply_button,g.elixir_max_button):
            self.assertEqual(str(widget.cget('state')),'normal')
        self.assertEqual(g.backup.read_bytes(),self.copy.read_bytes())
        g.max_elixirs()
        target=self.folder/'edited.sav'
        g.save_to(target)
        self.assertFalse(self.errors)
        result=read_save(target)
        self.assertEqual(progression.elixir_state(result)['value'],999)
        self.assertEqual(result.properties['EngiClearCharaArray']['value'],self.missing.properties['EngiClearCharaArray']['value'])
        self.assertEqual(g.elixir_input.get(),'999')
        self.assertFalse(g.changes)

    def test_first_clear_award_preview_undo_and_explicit_zero_override(self):
        g=self.editor
        officer=next(row['officer_id'] for row in progression.progression_state(g.document)['officers']
                     if row['can_clear'] and not row['cleared'])
        g.stage_many(progression.musou_clear_changes(g.document,officer))
        self.assertFalse(self.errors)
        self.assertEqual(g.elixir_input.get(),'3')
        g.elixir_input.set('0');g.apply_elixirs()
        self.assertEqual(g.elixir_input.get(),'0')
        g.undo()
        self.assertEqual(g.elixir_input.get(),'3')
        g.elixir_input.set('0');g.apply_elixirs()
        target=self.folder/'story-clear-zero.sav'
        g.save_to(target)
        self.assertFalse(self.errors)
        result=read_save(target)
        self.assertNotIn('BeansNum',result.properties)
        self.assertEqual(progression.elixir_state(result)['value'],0)
        self.assertTrue(result.properties['EngiClearCharaArray']['value']['values'][officer])
        self.assertEqual(g.elixir_input.get(),'0')

    def test_yellow_uniform_shortcut_uses_existing_color_flag(self):
        g=self.editor
        self.assertEqual(g.yellow_uniform_button.cget('text'),'Unlock Yellow Uniform')
        self.assertIn('Yellow uniform',g.guard_customization_note.get())
        g.yellow_uniform_button.invoke()
        self.assertFalse(self.errors)
        self.assertEqual(list(g.changes),[('guard_customization',5,'OutfitUnlocked')])
        result=parse_bytes(serialize(g.document,list(g.changes.values()))[0])
        yellow=next(row for row in customization.customization_state(result)['outfits'] if row['id']==5)
        self.assertTrue(yellow['unlocked'])
        self.assertEqual(result.properties['CanUseSecretGuardColorArray']['value']['values'],[1,0,0,0])
        self.assertEqual(result.properties['NewCanUseSecretGuardColorArray']['value']['values'],[1,0,0,0])
        self.assertNotIn('BeansNum',result.properties)
        self.assertEqual(result.properties['EngiClearCharaArray']['value'],g.document.properties['EngiClearCharaArray']['value'])
        g.undo()
        self.assertFalse(g.changes)

    def test_theme_switch_preserves_pending_edits_undo_and_review(self):
        g=self.editor;g.max_elixirs()
        changes=g.changes.copy();history=g.history.copy()
        saved_before=g.document.encrypted
        bytes_before=serialize(g.document,list(g.changes.values()))[0]
        g.review()
        g.apply_theme('Dark')
        self.assertEqual(g.changes,changes)
        self.assertEqual(g.history,history)
        self.assertEqual(g.document.encrypted,saved_before)
        self.assertEqual(g.elixir_input.get(),'999')
        self.assertEqual(serialize(g.document,list(g.changes.values()))[0],bytes_before)
        self.assertEqual(str(g.elixir_apply_button.cget('state')),'normal')
        g.apply_theme('Light');g.undo()
        self.assertFalse(g.changes)
        self.assertEqual(g.elixir_input.get(),'0')


if __name__=='__main__':unittest.main()
