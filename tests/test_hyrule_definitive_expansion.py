"""Qualified Switch weapon edits: procedural constraints + private native tests."""
import os
from pathlib import Path
import unittest
from koei_editor.games.dw3.models import SaveError
from koei_editor.games.hyrule_definitive import parser as p
from koei_editor.games.hyrule_definitive.editor import Editor
from tests.test_hyrule_definitive import procedural_raw
from tests.test_hyrule_gui import GuiWorkflow


class DefinitiveWeaponTests(unittest.TestCase):
    def test_surgical_stars_and_decrease_only_seal_counter(self):
        raw = procedural_raw()
        document = p.decode(raw)
        changes = p.stage(document, {}, 'weapon_1_stars', 5)
        changes = p.stage(document, changes, 'weapon_1_skill_1_kos', 0)
        output = p.serialize(document, changes)
        allowed = {p.WEAPON_BASE, p.WEAPON_BASE + 1, p.WEAPON_BASE + 0x14, p.WEAPON_BASE + 0x15}
        self.assertLessEqual({i for i,(x,y) in enumerate(zip(raw, output)) if x != y}, allowed)
        self.assertEqual(p.weapons(p.decode(output))[0]['power'], 280)
        self.assertEqual(p.weapons(p.decode(output))[0]['state'], 3)
        self.assertNotIn('weapon_1_skill_1_kos', p.maximums(document, {}))
        with self.assertRaises(SaveError): p.stage(document, {}, 'weapon_1_skill_1_kos', 1001)
        with self.assertRaises(SaveError): p.stage(document, {}, 'weapon_1_stars', 6)

    def test_unknown_reserved_master_states_and_special_seals_preserved(self):
        for identity,state,skill in ((60,3,5), (212,11,5), (108,3,5), (109,3,5),
                (0xFFFE,3,5), (212,0,5), (212,2,5), (212,255,5),
                (212,3,41), (212,3,42), (212,3,53), (212,3,55), (212,3,0)):
            raw = bytearray(procedural_raw());o=p.WEAPON_BASE
            raw[o+0x10:o+0x12]=identity.to_bytes(2,'little');raw[o+0x1E]=state;raw[o+0x16]=skill
            doc=p.decode(raw);f=p.field_map(doc)
            if identity in (60,108,109,0xFFFE) or state not in (3,19):
                self.assertNotIn('weapon_1_stars',f)
            self.assertNotIn('weapon_1_skill_1_kos',f)
            self.assertEqual(p.serialize(doc,{})[o:],bytes(raw[o:]))

    def test_higher_stars_unstage_and_invalid_pending_before_max(self):
        raw=bytearray(procedural_raw());o=p.WEAPON_BASE+0x14
        raw[o:o+2]=(8).to_bytes(2,'little');doc=p.decode(raw)
        self.assertNotIn('weapon_1_stars',p.maximums(doc,{}))
        self.assertEqual(p.stage(doc,{'weapon_1_stars':1},'weapon_1_stars',8),{})
        for changes in ({'weapon_1_stars':True},{'weapon_1_stars':6},{'weapon_1_skill_1_kos':1001},{'unknown':1}):
            with self.assertRaises(SaveError):p.maximums(doc,changes)

    @unittest.skipUnless(os.environ.get('HYRULE_DE_COPY'),'Private native Switch export absent')
    def test_genuine_weapon_fields_each_surgical_and_special_master_preserved(self):
        source=Path(os.environ['HYRULE_DE_COPY']);raw=source.read_bytes();doc=p.decode(raw)
        fields=[f for f in p.fields_for(doc) if f.id.startswith('weapon_')]
        self.assertGreater(len(fields),300)
        master=next(r for r in p.weapons(doc) if r['id']==60)
        for field in fields:
            value=field.value(raw);target=max(0,min(field.maximum,value-1))
            edited=p.serialize(doc,p.stage(doc,{},field.id,target))
            self.assertLessEqual({i for i,(a,b) in enumerate(zip(raw,edited)) if a!=b},set(range(field.offset,field.offset+field.size)))
            self.assertEqual(field.value(p.decode(edited).payload),target)
            self.assertEqual(edited[master['offset']:master['offset']+p.WEAPON_STRIDE],raw[master['offset']:master['offset']+p.WEAPON_STRIDE])
        self.assertEqual(source.read_bytes(),raw)


class DefinitiveWeaponGuiTests(GuiWorkflow,unittest.TestCase):
    backend=p
    editor_type=Editor
    fixture=staticmethod(procedural_raw)
    group,search,field,value='Weapon stars','Burning Frame','weapon_1_stars',5

    def test_seal_ko_search_and_excluded_from_visible_max(self):
        e=self.editor;e.group.set('Ordinary skill seals');e.search.set('Strong Attack V');e.refresh()
        self.assertEqual(e.fields.get_children(),('weapon_1_skill_1_kos',))
        e.max_visible();self.assertEqual(e.changes,{})
        e.fields.selection_set('weapon_1_skill_1_kos');e.value.set('0');e.apply_selected()
        self.assertEqual(e.changes,{'weapon_1_skill_1_kos':0})
