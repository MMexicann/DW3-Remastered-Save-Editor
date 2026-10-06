"""Private-copy regression tests for native indexed acquisition and gallery."""
from pathlib import Path
import hashlib
import struct
import sys
import unittest

PROJECT=Path(__file__).resolve().parents[1]
WORKSPACE=PROJECT.parent.parent
sys.path.insert(0,str(PROJECT))
from models import Change, SaveError, fields
from save_parser import read_save, parse_bytes
from save_writer import serialize
import officer_weapon_editor as weapon
import weapon_collection as collection
from test_weapon_rolls import edited_fixture_bytes, enum_bytes, record_bytes, tag_bytes

FIXTURE=WORKSPACE/'work/original-upload/GameStatusData.sav'
REPORT=WORKSPACE/'work/received-v034/report-2-dd54eb37ba5d.sav'


@unittest.skipUnless(FIXTURE.exists(),'The supplied private fixture is required.')
class WeaponCollectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document=read_save(FIXTURE)
        cls.original_hash=hashlib.sha256(FIXTURE.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()==cls.original_hash

    def edit(self,changes,document=None):
        raw,audit=serialize(document or self.document,changes)
        return parse_bytes(raw),audit

    def assert_other_tags(self,new,allowed,old=None):
        old=old or self.document
        for name,prop in old.properties.items():
            if name not in allowed:self.assertEqual(tag_bytes(old,prop),tag_bytes(new,new.properties[name]),name)

    def test_ziluan_fourth_expands_only_native_constructor_blanks(self):
        changes=[Change('unique_weapon',191,'Owned',True)]
        pending=weapon.state(self.document,10102,changes)
        self.assertTrue(pending['editable'],pending['reason'])
        self.assertIn(10102,{row['data_id'] for row in weapon.states(self.document,changes)})
        new,audit=self.edit(changes)
        self.assertEqual(len(new.records('UniqueWeaponDataArray')),103)
        for i in range(84):self.assertEqual(record_bytes(new,'UniqueWeaponDataArray',i),record_bytes(self.document,'UniqueWeaponDataArray',i))
        for i in range(84,102):
            f=fields(new.records('UniqueWeaponDataArray')[i])
            self.assertEqual(f['WeaponID']['value'],'EWeaponID::NUM')
            self.assertEqual(f['ID']['value'],'EWeaponID::NUM')
            self.assertEqual(f['DataID']['value'],10000+i)
            self.assertEqual(f['Attr']['value'],0)
            self.assertEqual(f['GetTime']['value'],0.0)
            self.assertEqual(weapon.original_skills(new,10000+i),[{'id':None,'value':0}]*9)
        self.assertEqual(weapon.state(new,10102)['weapon_id'],191)
        self.assertEqual(weapon.state(new,10102)['attr'],131)
        self.assertTrue(audit['resized'])
        self.assert_other_tags(new,{'UniqueWeaponDataArray','CollectedWeaponDataArray'})
        self.assertEqual(serialize(new,changes)[0],new.encrypted)

    def test_ziluan_fifth_and_combined_roll_element_acquisition(self):
        acquire=Change('unique_weapon',192,'Owned',True)
        info=weapon.state(self.document,10103,[acquire])
        skills=weapon.max_existing_skills(self.document,10103,[acquire])
        element=next(mask for mask in weapon.allowed_elements(info).values() if mask and mask!=info['elements'])
        changes=[acquire,Change('weapon_roll',10103,'Skills',skills),Change('weapon_element',10103,'Elements',element)]
        new,_=self.edit(changes)
        self.assertEqual(len(new.records('UniqueWeaponDataArray')),104)
        self.assertEqual(weapon.state(new,10103)['skills'],skills)
        self.assertEqual(weapon.state(new,10103)['elements'],element)
        self.assertEqual(fields(new.records('UniqueWeaponDataArray')[102])['WeaponID']['value'],'EWeaponID::NUM')
        # The first collection snapshot remains stock, independently of fusion.
        self.assertEqual(fields(new.records('CollectedWeaponDataArray')[192])['Attr']['value'],67)

    @unittest.skipUnless(REPORT.exists(),'The supplied Ziluan report is required.')
    def test_report104_preserves_owned_fifth_while_acquiring_fourth(self):
        old=read_save(REPORT);source=record_bytes(old,'UniqueWeaponDataArray',103)
        self.assertEqual(fields(old.records('UniqueWeaponDataArray')[103])['WeaponID']['value'],'EWeaponID::WeaponID_192')
        new,_=self.edit([Change('unique_weapon',191,'Owned',True)],old)
        self.assertEqual(len(new.records('UniqueWeaponDataArray')),104)
        self.assertEqual(record_bytes(new,'UniqueWeaponDataArray',103),source)
        self.assert_other_tags(new,{'UniqueWeaponDataArray','CollectedWeaponDataArray'},old)

    def test_unique_roll_alone_changes_no_other_unique_record(self):
        info=weapon.state(self.document,10004);skills=weapon.max_existing_skills(self.document,10004)
        new,_=self.edit([Change('weapon_roll',10004,'Skills',skills)])
        self.assertEqual(weapon.state(new,10004)['skills'],skills)
        for i in range(84):
            if i!=4:self.assertEqual(record_bytes(new,'UniqueWeaponDataArray',i),record_bytes(self.document,'UniqueWeaponDataArray',i))
        self.assert_other_tags(new,{'UniqueWeaponDataArray'})
        for name in ('ID','WeaponID','Attr','DataID','GetTime'):
            self.assertEqual(tag_bytes(new,fields(new.records('UniqueWeaponDataArray')[4])[name]),
                             tag_bytes(self.document,fields(self.document.records('UniqueWeaponDataArray')[4])[name]))

    def test_collect_all176_is_gallery_only_preserves_snapshots_and_merit(self):
        new,_=self.edit(collection.all_collection_changes())
        self.assertEqual(len(collection.COLLECTION_IDS),176)
        self.assertTrue(collection.has_all_collection(new))
        self.assertTrue(collection.has_all_collection(self.document,collection.all_collection_changes()))
        self.assert_other_tags(new,{'CollectedWeaponDataArray'})
        for i,row in enumerate(self.document.records('CollectedWeaponDataArray')):
            if i not in collection.COLLECTION_IDS or fields(row)['WeaponID']['value']!='EWeaponID::NUM':
                self.assertEqual(record_bytes(new,'CollectedWeaponDataArray',i),record_bytes(self.document,'CollectedWeaponDataArray',i))
        self.assertEqual(serialize(new,collection.all_collection_changes())[0],new.encrypted)
        self.assertFalse(collection.has_tactics_costumes(new))

    def test_tactics_only_two_flags_preserves_dlc_and_story(self):
        new,audit=self.edit(collection.tactics_costume_changes())
        self.assertTrue(collection.has_tactics_costumes(new))
        self.assert_other_tags(new,{'PCSaveDataArray'})
        for i,row in enumerate(self.document.records('PCSaveDataArray')):
            old=fields(row);edited=fields(new.records('PCSaveDataArray')[i])
            for name,prop in old.items():
                if i in collection.TACTICS_OFFICERS and name=='CanUseCostume':
                    expected=list(prop['value']['values']);expected[3]=1
                    self.assertEqual(edited[name]['value']['values'],expected)
                else:self.assertEqual(tag_bytes(self.document,prop),tag_bytes(new,edited[name]),(i,name))
        self.assertFalse(audit['resized'])
        changes=[i for i,(a,b) in enumerate(zip(self.document.plaintext,new.plaintext)) if a!=b]
        self.assertEqual(changes,[fields(self.document.records('PCSaveDataArray')[i])['CanUseCostume']['data_offset']+7 for i in (12,13)])
        self.assertEqual(serialize(new,collection.tactics_costume_changes())[0],new.encrypted)

    def test_collection_and_bodyguard_acquisition_have_disjoint_gallery_edits(self):
        new,_=self.edit(collection.all_collection_changes()+[Change('guard_weapon',173,'Owned',True)])
        self.assertTrue(collection.has_all_collection(new))
        self.assertEqual(fields(new.records('CollectedWeaponDataArray')[173])['WeaponID']['value'],'EWeaponID::WeaponID_173')
        self.assert_other_tags(new,{'CollectedWeaponDataArray','GuardWeaponDataArray'})

    def test_invalid_collection_actions_and_wrong_identity_refuse(self):
        for change in [Change('weapon_collection',0,'CollectAll',False),Change('weapon_collection',1,'CollectAll',True),
                       Change('weapon_collection',0,'Unknown',True),Change('unique_weapon',193,'Owned',True)]:
            with self.subTest(change=change),self.assertRaises(SaveError):serialize(self.document,[change])
        f=fields(self.document.records('UniqueWeaponDataArray')[0])
        old=parse_bytes(edited_fixture_bytes(self.document,[(f['WeaponID'],enum_bytes('EWeaponID::WeaponID_132'))]))
        with self.assertRaises(SaveError):serialize(old,[Change('unique_weapon',89,'Owned',True)])
        self.assertEqual(serialize(old)[0],old.encrypted)

    def test_empty_looking_records_with_unknown_data_are_not_overwritten(self):
        for array,index,change in [('UniqueWeaponDataArray',0,Change('unique_weapon',89,'Owned',True)),
                                   ('CollectedWeaponDataArray',89,collection.all_collection_changes()[0])]:
            f=fields(self.document.records(array)[index])
            for prop,data in [(f['ID'],enum_bytes('EWeaponID::FutureSword')),(f['Attr'],struct.pack('<q',64)),
                              (fields(f['Skill']['value']['records'][0])['Value'],struct.pack('<i',1))]:
                old=parse_bytes(edited_fixture_bytes(self.document,[(prop,data)]))
                with self.subTest(array=array,field=prop['name']),self.assertRaises(SaveError):serialize(old,[change])
                self.assertEqual(serialize(old)[0],old.encrypted)

    def test_unknown_owned_bonus_preserved_while_collecting_stock_history(self):
        f=fields(self.document.records('WeaponDataArray')[36])
        slot=fields(f['Skill']['value']['records'][0])
        old=parse_bytes(edited_fixture_bytes(self.document,[(slot['EquipItemID'],enum_bytes('EEquipItemID::FutureBonus'))]))
        new,_=self.edit(collection.all_collection_changes(),old)
        self.assertTrue(collection.has_all_collection(new))
        self.assertEqual(tag_bytes(new,new.properties['WeaponDataArray']),tag_bytes(old,old.properties['WeaponDataArray']))

    def test_nonstandard_complete_skill_count_is_view_only(self):
        f=fields(self.document.records('WeaponDataArray')[36]);prop=f['Skill']
        rows=prop['value']['records'];start=rows[0][0]['tag_offset'];end=rows[1][0]['tag_offset']
        # Construct a structurally complete ten-slot array; malformed counts are
        # covered elsewhere and must still be refused.
        raw=self.document.plaintext[prop['data_offset']:prop['data_offset']+prop['data_size']]
        payload=struct.pack('<i',10)+raw[4:]+self.document.plaintext[start:end]
        old=parse_bytes(edited_fixture_bytes(self.document,[(prop,payload)]))
        info=weapon.state(old,36)
        self.assertFalse(info['editable']);self.assertFalse(info['element_editable'])
        self.assertEqual(len(info['skills']),10)
        self.assertEqual(serialize(old)[0],old.encrypted)


if __name__=='__main__':unittest.main(verbosity=2)
