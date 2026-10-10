"""Regression checks for nondecreasing Max actions on supplied save copies."""
from pathlib import Path
import hashlib
import struct
import sys
import unittest

PROJECT=Path(__file__).resolve().parents[1]
WORKSPACE=PROJECT
sys.path.insert(0,str(PROJECT))
from koei_editor.games.dw3.models import Change, SaveError, fields
from koei_editor.games.dw3.save_parser import read_save, parse_bytes
from koei_editor.games.dw3.save_writer import serialize
from test_weapon_rolls import edited_fixture_bytes,enum_bytes,tag_bytes,record_bytes
import koei_editor.games.dw3.officer_weapon_editor as officer
import koei_editor.games.dw3.bodyguard_editor as guard

FIXTURE=WORKSPACE/'work/original-upload/GameStatusData.sav'
REPORTED=WORKSPACE/'work/received-v034/report-2-dd54eb37ba5d.sav'


@unittest.skipUnless(FIXTURE.exists(),'The explicitly supplied workspace copy is required.')
class MaximumPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document=read_save(FIXTURE)
        cls.source_hash=hashlib.sha256(FIXTURE.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()==cls.source_hash

    def synthetic(self,replacements):
        return parse_bytes(edited_fixture_bytes(self.document,replacements))

    def write(self,document,changes):
        raw,audit=serialize(document,changes)
        return parse_bytes(raw),audit

    def high_officer(self,value=150):
        skill=fields(fields(self.document.records('WeaponDataArray')[36])['Skill']['value']['records'][0])
        return self.synthetic([(skill['Value'],struct.pack('<i',value))])

    def high_guard(self,value=50):
        skill=fields(fields(self.document.records('GuardWeaponDataArray')[1])['Skill']['value']['records'][0])
        return self.synthetic([(skill['Value'],struct.pack('<i',value))])

    def test_owned_normal_max_preserves_original_high_after_pending_lower(self):
        row=fields(self.document.records('EquipItemDataArray')[0])
        source=self.synthetic([(row['EquipItemID'],enum_bytes('EEquipItemID::'+officer.ITEMS[0]['enum'])),(row['Value'],struct.pack('<i',50))])
        self.assertEqual(officer.max_item_value(source,0),50)
        self.assertEqual(officer.max_item_value(source,0,[Change('item',0,'Value',1)]),50)
        saved,audit=self.write(source,[Change('item',0,'Value',50)])
        self.assertEqual(saved.encrypted,source.encrypted)
        self.assertEqual(audit['plaintext_changes'],[])
        with self.assertRaises(SaveError):serialize(source,[Change('item',0,'Value',51)])

    def test_unowned_stale_normal_value_does_not_define_a_new_maximum(self):
        row=fields(self.document.records('EquipItemDataArray')[0])
        source=self.synthetic([(row['EquipItemID'],enum_bytes('EEquipItemID::NUM')),(row['Value'],struct.pack('<i',999))])
        self.assertEqual(officer.max_item_value(source,0),officer.ITEM_CAPS[0])
        with self.assertRaises(SaveError):serialize(source,[Change('item',0,'Value',999)])

    def test_value_only_normal_pending_change_implies_owned(self):
        row=fields(self.document.records('EquipItemDataArray')[2])
        source=self.synthetic([(row['EquipItemID'],enum_bytes('EEquipItemID::NUM'))])
        self.assertEqual(officer.max_item_value(source,2,[Change('item',2,'Value',70)]),75)
        for invalid in (True,1.0,'1'):
            with self.subTest(value=invalid),self.assertRaises(SaveError):
                officer.max_item_value(source,2,[Change('item',2,'Value',invalid)])

    def test_guard_item_max_preserves_high_after_pending_lower(self):
        row=fields(self.document.records('GuardEquipItemDataArray')[1])
        source=self.synthetic([(row['Value'],struct.pack('<i',50))])
        self.assertEqual(guard.max_item_value(source,1,[Change('guard_item',1,'Value',1)]),50)
        saved,audit=self.write(source,[Change('guard_item',1,'Value',50)])
        self.assertEqual(saved.encrypted,source.encrypted)
        self.assertEqual(audit['plaintext_changes'],[])
        with self.assertRaises(SaveError):serialize(source,[Change('guard_item',1,'Value',51)])

    def test_guard_unowned_stale_value_is_not_reused(self):
        row=fields(self.document.records('GuardEquipItemDataArray')[0])
        source=self.synthetic([(row['Value'],struct.pack('<i',999))])
        self.assertEqual(guard.max_item_value(source,0),40)
        with self.assertRaises(SaveError):serialize(source,[Change('guard_item',0,'Value',999)])

    def test_officer_max_preserves_high_roll_identity_and_position(self):
        source=self.high_officer();before=officer.state(source,36)
        self.assertTrue(before['editable'],before['reason'])
        skills=officer.max_existing_skills(source,36)
        self.assertEqual(skills[0],before['skills'][0])
        self.assertEqual([s['id'] for s in skills],[s['id'] for s in before['skills']])
        self.assertTrue(all(new['value']>=old['value'] for old,new in zip(before['skills'],skills)))
        saved,_=self.write(source,[Change('weapon_roll',36,'Skills',skills)])
        self.assertEqual(officer.state(saved,36)['skills'],skills)
        for name,prop in source.properties.items():
            if name!='WeaponDataArray':self.assertEqual(tag_bytes(saved,saved.properties[name]),tag_bytes(source,prop),name)

    def test_officer_max_restores_original_high_after_pending_lower(self):
        source=self.high_officer();skills=[dict(s) for s in officer.state(source,36)['skills']];skills[0]['value']=1
        pending=[Change('weapon_roll',36,'Skills',skills)]
        maximum=officer.max_existing_skills(source,36,pending)
        self.assertEqual(maximum[0],{'id':2,'value':150})
        self.write(source,[Change('weapon_roll',36,'Skills',maximum)])

    def test_officer_high_roll_cannot_be_increased_copied_or_transferred(self):
        source=self.high_officer();original=officer.state(source,36)['skills']
        for mode in ('increase','transfer','new-id'):
            skills=[dict(s) for s in original]
            if mode=='increase':skills[0]['value']=151
            elif mode=='transfer':skills[0],skills[1]=skills[1],skills[0]
            else:skills[0]={'id':3,'value':150}
            with self.subTest(mode=mode),self.assertRaises(SaveError):serialize(source,[Change('weapon_roll',36,'Skills',skills)])

    def test_rare_normalization_cannot_move_a_high_officer_roll(self):
        slots=fields(self.document.records('WeaponDataArray')[36])['Skill']['value']['records'];first=fields(slots[0]);last=fields(slots[7])
        source=self.synthetic([(first['EquipItemID'],enum_bytes('EEquipItemID::NUM')),(first['Value'],struct.pack('<i',0)),
                               (last['EquipItemID'],enum_bytes('EEquipItemID::'+officer.ITEMS[2]['enum'])),(last['Value'],struct.pack('<i',150))])
        info=officer.state(source,36);self.assertTrue(info['editable'],info['reason'])
        skills=[dict(s) for s in info['skills']];skills[6]={'id':15,'value':0}
        with self.assertRaises(SaveError):serialize(source,[Change('weapon_roll',36,'Skills',skills)])

    def test_guard_max_keeps_existing_types_and_high_value(self):
        source=self.high_guard();before=guard.weapon_state(source)[1]
        self.assertTrue(before['editable'],before['reason'])
        saved,_=self.write(source,[Change('guard_weapon',174,'MaxBonuses',True)])
        after=guard.weapon_state(saved)[1]
        self.assertEqual(after['skills'][0],before['skills'][0])
        self.assertEqual([s['id'] for s in after['skills']],[s['id'] for s in before['skills']])
        self.assertTrue(all(new['value']>=old['value'] for old,new in zip(before['skills'],after['skills'])))
        self.assertEqual(tag_bytes(saved,saved.properties['CollectedWeaponDataArray']),tag_bytes(source,source.properties['CollectedWeaponDataArray']))
        original=fields(source.records('GuardWeaponDataArray')[1]);result=fields(saved.records('GuardWeaponDataArray')[1])
        for name in ('ID','WeaponID','DataID','Attr','GetTime'):
            self.assertEqual(tag_bytes(saved,result[name]),tag_bytes(source,original[name]),name)

    def test_guard_profile_max_restores_original_high_after_pending_lower(self):
        source=self.high_guard();original=guard.weapon_state(source)[1]['skills'];pending=[dict(s) for s in original];pending[0]['value']=1
        skills=guard.max_skills(174,pending,original)
        self.assertEqual(skills[0],original[0])
        self.write(source,[Change('guard_weapon_slot',1,'Skills',skills)])

    def test_guard_high_roll_cannot_be_created_or_transferred(self):
        source=self.high_guard();original=guard.weapon_state(source)[1]['skills']
        for mode in ('increase','transfer','new-id'):
            skills=[dict(s) for s in original]
            if mode=='increase':skills[0]['value']=51
            elif mode=='transfer':skills[0],skills[1]=skills[1],skills[0]
            else:skills[0]={'id':5,'value':50}
            with self.subTest(mode=mode),self.assertRaises(SaveError):serialize(source,[Change('guard_weapon_slot',1,'Skills',skills)])

    def test_sparse_guard_high_roll_stays_in_its_physical_slot(self):
        slots=fields(self.document.records('GuardWeaponDataArray')[1])['Skill']['value']['records'];first=fields(slots[0]);last=fields(slots[5])
        source=self.synthetic([(first['GuardEquipItemID'],enum_bytes('EGuardEquipItemID::NUM')),(first['Value'],struct.pack('<i',0)),
                               (last['GuardEquipItemID'],enum_bytes(guard.GUARD_ITEMS[8]['enum'])),(last['Value'],struct.pack('<i',50))])
        preview=guard.max_skills(174,guard.weapon_state(source)[1]['skills'],guard.weapon_state(source)[1]['preservation_baseline'])
        saved,_=self.write(source,[Change('guard_weapon',174,'MaxBonuses',True)])
        self.assertEqual(guard.weapon_state(saved)[1]['skills'],preview)
        after=fields(fields(saved.records('GuardWeaponDataArray')[1])['Skill']['value']['records'][5])
        before=fields(fields(source.records('GuardWeaponDataArray')[1])['Skill']['value']['records'][5])
        self.assertEqual(after['GuardEquipItemID']['value'],guard.GUARD_ITEMS[8]['enum'])
        self.assertEqual(after['Value']['value'],50)
        self.assertEqual(tag_bytes(saved,after['GuardEquipItemID']),tag_bytes(source,before['GuardEquipItemID']))

    def test_guard_max_preserves_ineligible_and_unknown_profile_bytes(self):
        first=fields(fields(self.document.records('GuardWeaponDataArray')[1])['Skill']['value']['records'][0])
        for enum in (guard.GUARD_ITEMS[4]['enum'],'EGuardEquipItemID::FutureItem'):
            source=self.synthetic([(first['GuardEquipItemID'],enum_bytes(enum)),(first['Value'],struct.pack('<i',50))])
            self.assertFalse(guard.weapon_state(source)[1]['editable'])
            saved,_=self.write(source,[Change('guard_weapon',174,'MaxBonuses',True)])
            self.assertEqual(record_bytes(saved,'GuardWeaponDataArray',1),record_bytes(source,'GuardWeaponDataArray',1))

    def test_existing_guard_max_adds_only_missing_stock_types(self):
        before=guard.weapon_state(self.document)[2]
        skills=guard.max_skills(174,before['skills'])
        self.assertEqual([s['id'] for s in skills[:len(before['skills'])]],[s['id'] for s in before['skills']])
        self.assertEqual(len(skills),3)
        self.assertEqual(len({s['id'] for s in skills}),3)
        guard.validate_skills(174,skills)

    @unittest.skipUnless(REPORTED.exists(),'The reported workspace copy is required.')
    def test_reported_high_items_never_decrease_and_source_is_untouched(self):
        before_hash=hashlib.sha256(REPORTED.read_bytes()).hexdigest();source=read_save(REPORTED);changes=[]
        for item_id,cap in officer.ITEM_CAPS.items():
            changes.extend([Change('item',item_id,'Owned',True),Change('item',item_id,'Value',officer.max_item_value(source,item_id))])
        for item_id,item in guard.GUARD_ITEMS.items():
            if item['kind']=='normal':changes.extend([Change('guard_item',item_id,'Owned',True),Change('guard_item',item_id,'Value',guard.max_item_value(source,item_id))])
        saved,_=self.write(source,changes)
        for item_id in officer.ITEM_CAPS:
            old=fields(source.records('EquipItemDataArray')[item_id]);new=fields(saved.records('EquipItemDataArray')[item_id])
            if old['EquipItemID']['value']!='EEquipItemID::NUM':self.assertGreaterEqual(new['Value']['value'],old['Value']['value'])
        for item_id,item in guard.GUARD_ITEMS.items():
            if item['kind']=='normal':self.assertGreaterEqual(guard.item_state(saved)[item_id]['value'],guard.item_state(source)[item_id]['value'])
        for name,prop in source.properties.items():
            if name not in ('EquipItemDataArray','GuardEquipItemDataArray'):
                self.assertEqual(tag_bytes(saved,saved.properties[name]),tag_bytes(source,prop),name)
        self.assertEqual(hashlib.sha256(REPORTED.read_bytes()).hexdigest(),before_hash)


if __name__=='__main__':unittest.main()
