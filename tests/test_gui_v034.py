from pathlib import Path
import sys
import struct
import tkinter as tk
import unittest
from unittest.mock import patch

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
sys.path.insert(0,str(PROJECT/'tests'))
import gui
import save_writer
import officer_weapon_editor as weapon
from models import Change, fields
from save_parser import read_save, parse_bytes
from unreal import Reader, tags
from test_review_regressions import edited_fixture_bytes

FIXTURE=PROJECT.parents[1]/'work/original-upload/GameStatusData.sav'

@unittest.skipUnless(FIXTURE.exists(),'Private supplied fixture is required.')
class NewGuiRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source=read_save(FIXTURE)
    def setUp(self):
        self.root=tk.Tk();self.root.withdraw();self.editor=gui.Editor(self.root)
        self.errors=[]
        self.error_patch=patch.object(gui.messagebox,'showerror',side_effect=lambda *a,**k:self.errors.append(str(a)))
        self.confirm_patch=patch.object(gui.messagebox,'askyesno',return_value=True)
        self.error_patch.start();self.confirm_patch.start()
        self.editor.document=self.source;self.editor.set_loaded(True);self.editor.refresh()
    def tearDown(self):
        self.confirm_patch.stop();self.error_patch.stop();self.root.destroy()
    def test_pending_ziluan_element_edit_and_combined_actions(self):
        g=self.editor
        g.weapons.selection_set('unique:191');g.unlock_selected_weapon()
        g.weapon_element.set('Wind');g.apply_weapon_element()
        self.assertFalse(self.errors)
        self.assertEqual(g.current_weapon_data_id,10102)
        self.assertEqual(weapon.state(self.source,10102,list(g.changes.values()))['elements'],32)
        g.collect_all_weapons();g.unlock_tactics_costumes();g.unlock_side_stories();g.complete_all_musou()
        self.assertFalse(self.errors)
        raw,_=save_writer.serialize(self.source,list(g.changes.values()))
        edited=parse_bytes(raw)
        self.assertEqual(fields(edited.records('UniqueWeaponDataArray')[102])['Attr']['value'] & weapon.ELEMENT_MASK,32)
        self.assertEqual(save_writer.serialize(edited)[0],raw)
    def test_short_skill_array_clears_unused_controls(self):
        f=fields(self.source.records('WeaponDataArray')[36]);prop=f['Skill']
        first=prop['value']['records'][0]
        r=Reader(self.source.plaintext,first[0]['tag_offset'],prop['data_offset']+prop['data_size']);tags(r)
        payload=struct.pack('<i',1)+self.source.plaintext[first[0]['tag_offset']:r.pos]
        document=parse_bytes(edited_fixture_bytes(self.source,[(prop,payload)]))
        self.editor.document=document;self.editor.refresh()
        self.editor.weapons.selection_set('WeaponDataArray:36');self.editor.select_weapon()
        for i in range(1,9):
            self.assertEqual(self.editor.weapon_bonus_names[i].get(),'None')
            self.assertEqual(str(self.editor.weapon_bonus_boxes[i].cget('state')),'disabled')
        self.editor.change_weapon_bonus(8)
        self.assertFalse(self.errors)
    def test_saved_growth_with_different_auto_gate_has_stat_preview(self):
        files=list((PROJECT.parents[1]/'work/received-v034').glob('report-1*.sav'))
        if not files:self.skipTest('Private reporter fixture is required.')
        self.editor.document=read_save(files[0]);self.editor.refresh()
        self.editor.bodyguards.selection_set('3');self.editor.select_bodyguard()
        self.assertIn('Growth base:',self.editor.guard_stats.get())
        self.assertFalse(self.errors)
