"""Independent element editing on unique copies; private fixtures are optional."""
from pathlib import Path
import hashlib
import struct
import sys
import unittest

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
from models import Change,SaveDocument,SaveError,fields
from save_parser import parse_bytes,read_save
from save_writer import serialize
from test_weapon_rolls import edited_fixture_bytes,enum_bytes,record_bytes,tag_bytes
import officer_weapon_editor as weapon

FIXTURE=PROJECT/'work/original-upload/GameStatusData.sav'


def prop(name,value,**extra):
    return {'name':name,'value':value,**extra}


def unique_document():
    rows=[]
    for index in range(max(weapon.UNIQUE_SLOTS)+1):
        template=weapon.UNIQUE_SLOTS.get(index)
        enum=weapon.WEAPONS[template['weapon_id']]['enum'] if template else 'EWeaponID::NUM'
        skills=[{'id':None,'value':0} for _ in range(9)]
        if template:
            skills=[{'id':s['item_id'] if s['item_id'] in weapon.ITEMS else None,'value':s['value']}
                    for s in template['skill_slots']]
        skill_rows=[[prop('EquipItemID','EEquipItemID::NUM' if s['id'] is None else
                         'EEquipItemID::'+weapon.ITEMS[s['id']]['enum']),
                     prop('GuardEquipItemID','EGuardEquipItemID::NUM'),prop('Value',s['value'])]
                    for s in skills]
        rows.append([prop('ID',enum),prop('WeaponID',enum),prop('DataID',10000+index),
                     prop('Attr',template['attribute_bitmask'] if template else 0,
                          type='Int64Property',data_size=8),prop('Skill',{'records':skill_rows})])
    return SaveDocument(None,b'',b'',{'properties':[
        prop('WeaponDataArray',{'records':[]}),prop('UniqueWeaponDataArray',{'records':rows})]})


class UniqueElementRules(unittest.TestCase):
    def test_all_84_unique_templates_support_each_native_single_element(self):
        document=unique_document()
        self.assertEqual(len(weapon.UNIQUES),84)
        for row in weapon.states(document):
            with self.subTest(weapon_id=row['weapon_id']):
                self.assertTrue(row['element_editable'],row['element_reason'])
                for mask in (4,8,16,32):
                    after=weapon.state(document,row['data_id'],[Change('weapon_element',row['data_id'],'Elements',mask)])
                    self.assertEqual(after['attr'] & ~weapon.ELEMENT_MASK,row['attr'] & ~weapon.ELEMENT_MASK)
                    self.assertEqual(after['skills'],row['skills'])

    def test_bonus_ineligibility_does_not_disable_known_attribute_leaf(self):
        document=unique_document();data_id=weapon.UNIQUES[116]['data_id']
        record=fields(document.records('UniqueWeaponDataArray')[data_id-10000])
        fields(record['Skill']['value']['records'][0])['EquipItemID']['value']='EEquipItemID::EquipItemID_099'
        row=weapon.state(document,data_id)
        self.assertFalse(row['editable']);self.assertTrue(row['element_editable'])
        self.assertEqual(weapon.element_changes(document,[data_id],32),[Change('weapon_element',data_id,'Elements',32)])
        with self.assertRaises(SaveError):
            weapon.state(document,data_id,[Change('weapon_roll',data_id,'Skills',row['skills'])])

    def test_identity_and_attribute_schema_failures_still_block_elements(self):
        for field,value in [('ID','EWeaponID::NUM'),('DataID',7),('WeaponID','EWeaponID::NUM')]:
            document=unique_document();data_id=weapon.UNIQUES[116]['data_id']
            fields(document.records('UniqueWeaponDataArray')[data_id-10000])[field]['value']=value
            with self.subTest(field=field),self.assertRaises(SaveError):
                weapon.element_changes(document,[data_id],4)
        document=unique_document();data_id=weapon.UNIQUES[116]['data_id']
        fields(document.records('UniqueWeaponDataArray')[data_id-10000])['Attr']['type']='IntProperty'
        with self.assertRaises(SaveError):weapon.element_changes(document,[data_id],4)

    def test_batch_rejects_duplicates_unknown_bits_combinations_and_removal(self):
        document=unique_document();elemental=next(r for r in weapon.states(document) if r['elements'])
        for refs,mask in [([],4),([True],4),([elemental['data_id']]*2,4),
                          ([elemental['data_id']],0),([elemental['data_id']],64),
                          ([elemental['data_id']],12),([elemental['data_id']],True)]:
            with self.subTest(refs=refs,mask=mask),self.assertRaises(SaveError):
                weapon.element_changes(document,refs,mask)
        changes=weapon.owned_unique_element_changes(document,32)
        self.assertEqual(len(changes),sum(r['elements']!=32 for r in weapon.states(document)))
        self.assertEqual(weapon.owned_unique_element_changes(document,32,changes),[])


@unittest.skipUnless(FIXTURE.exists(),'The supplied workspace save copy is required.')
class UniqueElementSerialization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document=read_save(FIXTURE)
        cls.digest=hashlib.sha256(FIXTURE.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()==cls.digest

    def test_all_unique_acquisition_and_each_element_preserve_flags_and_gallery(self):
        acquisitions=[Change('unique_weapon',i,'Owned',True) for i in weapon.UNIQUES]
        source=parse_bytes(serialize(self.document,acquisitions)[0])
        self.assertEqual(sum(r['array']=='UniqueWeaponDataArray' for r in weapon.states(source)),84)
        for mask in (4,8,16,32):
            with self.subTest(mask=mask):
                changes=weapon.owned_unique_element_changes(source,mask)
                edited=parse_bytes(serialize(source,changes)[0])
                for before in weapon.states(source):
                    if before['array']!='UniqueWeaponDataArray':continue
                    after=weapon.state(edited,before['data_id'])
                    self.assertEqual(after['attr'],(before['attr'] & ~weapon.ELEMENT_MASK)|mask)
                    old=fields(source.records(before['array'])[before['index']])
                    new=fields(edited.records(before['array'])[before['index']])
                    for name in old:
                        if name!='Attr':self.assertEqual(tag_bytes(source,old[name]),tag_bytes(edited,new[name]),name)
                for name,old in source.properties.items():
                    if name!='UniqueWeaponDataArray':
                        self.assertEqual(tag_bytes(source,old),tag_bytes(edited,edited.properties[name]),name)
                self.assertEqual(serialize(edited)[0],edited.encrypted)

    def test_reserved_bonus_and_high_attribute_flags_survive_attr_only_edit(self):
        source=parse_bytes(serialize(self.document,[Change('unique_weapon',116,'Owned',True)])[0])
        data_id=weapon.UNIQUES[116]['data_id'];index=data_id-10000
        record=fields(source.records('UniqueWeaponDataArray')[index])
        skill=fields(record['Skill']['value']['records'][0])
        before_attr=-(1<<63)|(1<<45)|record['Attr']['value']
        source=parse_bytes(edited_fixture_bytes(source,[(skill['EquipItemID'],enum_bytes('EEquipItemID::EquipItemID_099')),
                                                        (skill['Value'],struct.pack('<i',1000)),
                                                        (record['Attr'],struct.pack('<q',before_attr))]))
        before=fields(source.records('UniqueWeaponDataArray')[index])
        row=weapon.state(source,data_id);self.assertFalse(row['editable']);self.assertTrue(row['element_editable'])
        edited=parse_bytes(serialize(source,weapon.element_changes(source,[data_id],32))[0])
        after=fields(edited.records('UniqueWeaponDataArray')[index])
        self.assertEqual(after['Attr']['value'],(before_attr & ~weapon.ELEMENT_MASK)|32)
        for name in before:
            if name!='Attr':self.assertEqual(tag_bytes(source,before[name]),tag_bytes(edited,after[name]),name)
        for name,old in source.properties.items():
            if name!='UniqueWeaponDataArray':self.assertEqual(tag_bytes(source,old),tag_bytes(edited,edited.properties[name]),name)
        for other in range(len(source.records('UniqueWeaponDataArray'))):
            if other!=index:
                self.assertEqual(record_bytes(source,'UniqueWeaponDataArray',other),record_bytes(edited,'UniqueWeaponDataArray',other))


if __name__=='__main__':unittest.main()
