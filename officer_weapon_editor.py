"""Officer weapon bonus editing using parsed records and verified fusion rules.

Only ordinary numeric bonuses are editable. Identity, power definition,
attribute/hit flags, rare slots, time, equipment and collection caches stay
unchanged. No material-consuming fusion workflow is performed here.
"""
from pathlib import Path
import json
import struct
from models import Change, SaveError, fields

ROOT=Path(__file__).resolve().parent
METADATA=json.loads((ROOT/'game_metadata.json').read_text(encoding='utf-8'))
ITEMS={r['id']:r for r in METADATA['items']}
ITEM_IDS={'EEquipItemID::'+r['enum']:r['id'] for r in METADATA['items']}
WEAPONS={r['id']:r for r in METADATA['weapons']}
WEAPON_IDS={r['enum']:r['id'] for r in METADATA['weapons']}
UNIQUES={r['weapon_id']:r for r in json.loads((ROOT/'unique_weapons.json').read_text())['weapons']}
UNIQUE_SLOTS={r['unique_save_index']:r for r in UNIQUES.values()}
_rule_file=ROOT/'weapon_bonus_rules.json'
RULES=json.loads(_rule_file.read_text(encoding='utf-8')) if _rule_file.exists() else {}
NORMAL_ITEMS={int(r['id']):r for r in RULES.get('normal_items',[])}
CATEGORIES={'weapon_roll'}


def _requests(changes):
    result={}
    for change in changes:
        if not isinstance(change,Change):raise SaveError('Weapon edits must be supported Change records.')
        if not isinstance(change.category,str) or not isinstance(change.field,str):raise SaveError('Weapon edit category and field must be text.')
        if change.category not in CATEGORIES:continue
        if type(change.index) is not int or change.field!='Skills' or change.index in result:
            raise SaveError('Weapon rolls need an integer inventory reference, Skills field and no duplicates.')
        result[change.index]=change.value
    return result


def _location(document,data_id):
    if type(data_id) is not int:raise SaveError('Weapon inventory references must be integers.')
    if 0<=data_id<500:return 'WeaponDataArray',data_id
    if 10000<=data_id<10000+len(document.records('UniqueWeaponDataArray')):
        return 'UniqueWeaponDataArray',data_id-10000
    raise SaveError('Choose an existing officer weapon inventory slot.')


def original_skills(document,data_id):
    array,index=_location(document,data_id)
    result=[]
    for row in fields(document.records(array)[index])['Skill']['value']['records']:
        slot=fields(row);enum=slot['EquipItemID']['value']
        item=None if enum=='EEquipItemID::NUM' else ITEM_IDS.get(enum)
        if item is None and enum!='EEquipItemID::NUM':
            # Native reserved IDs are readable, but have no verified edit rules.
            if not enum.startswith('EEquipItemID::EquipItemID_') or not enum.rsplit('_',1)[-1].isdigit():
                raise SaveError('Unknown ordinary weapon bonus identity.')
            item=int(enum.rsplit('_',1)[-1])
        result.append({'id':item,'value':slot['Value']['value']})
    return result


def allowed_values(info,item_id):
    if type(item_id) is not int or item_id not in NORMAL_ITEMS:raise SaveError('Only verified normal weapon bonuses can be edited.')
    values=set(NORMAL_ITEMS[item_id]['allowed_values'])
    if info['array']=='UniqueWeaponDataArray' and info['weapon_id'] in UNIQUES:
        for slot in UNIQUES[info['weapon_id']]['skill_slots']:
            if slot['item_id']==item_id:values.add(slot['value'])
    return sorted(v for v in values if v>0)


def _base_state(document,data_id,changes):
    array,index=_location(document,data_id);record=fields(document.records(array)[index])
    weapon_id=WEAPON_IDS.get(record['WeaponID']['value']);owned=record['WeaponID']['value']!='EWeaponID::NUM'
    skills=original_skills(document,data_id);attr=record['Attr']['value']
    template=UNIQUE_SLOTS.get(index) if array=='UniqueWeaponDataArray' else None
    pending=template is not None and any(c.category=='unique_weapon' and c.index==template['weapon_id'] and c.field=='Owned' and c.value is True for c in changes)
    newly_acquired=not owned and pending
    if newly_acquired:
        weapon_id=template['weapon_id'];owned=True;attr=template['attribute_bitmask']
        skills=[{'id':s['item_id'] if s['item_id'] in ITEMS else None,'value':s['value']} for s in template['skill_slots']]
    metadata=WEAPONS.get(weapon_id,{})
    minimum=sum(s['item_id'] in NORMAL_ITEMS for s in template['skill_slots']) if template else (0 if metadata.get('initial_possession') else 1)
    info={'data_id':data_id,'array':array,'index':index,'weapon_id':weapon_id,'owned':owned,
          'skills':skills,'metadata':metadata,'attr':attr,'blue_limit':None,'blue_minimum':minimum,'editable':False,'reason':''}
    if not owned:info['reason']='Unlock this unique weapon before editing its rolls.'
    elif not NORMAL_ITEMS:info['reason']='Weapon bonus limits have not been verified.'
    elif array=='WeaponDataArray' and weapon_id not in set(range(89))|{188,189,190}:
        info['reason']='This ordinary inventory identity is not a supported playable weapon.'
    elif array=='UniqueWeaponDataArray' and (template is None or weapon_id!=template['weapon_id']):
        info['reason']='This unique weapon identity does not match its inventory slot.'
    elif not newly_acquired and (record['ID']['value']!=record['WeaponID']['value'] or record['DataID']['value']!=data_id):
        info['reason']='Weapon identity or inventory reference is inconsistent.'
    elif any(s['id'] is not None and s['id'] not in ITEMS for s in skills):
        info['reason']='This copy contains a reserved bonus identity with no verified edit rules.'
    elif any(fields(s)['GuardEquipItemID']['value']!='EGuardEquipItemID::NUM' for s in record['Skill']['value']['records']):
        info['reason']='Bodyguard bonuses cannot be changed in an officer weapon.'
    else:
        rank_row=RULES.get('weapon_rules',{}).get(str(weapon_id))
        if not rank_row:info['reason']='Weapon rank limits are unsupported.'
        else:
            info['rank']=rank_row['rank'];info['blue_limit']=rank_row['max_blue'];info['editable']=True
            try:validate_skills(info,skills)
            except SaveError as error:info['editable']=False;info['reason']=str(error)
    return info


def validate_skills(info,skills):
    if not info['owned'] or info['blue_limit'] is None:raise SaveError(info.get('reason') or 'Choose a supported owned weapon.')
    if not isinstance(skills,(list,tuple)) or len(skills)!=9:raise SaveError('Officer weapons have exactly nine saved bonus slots.')
    result=[];seen=set();blue=0
    for index,skill in enumerate(skills):
        if not isinstance(skill,dict) or set(skill)!={'id','value'}:raise SaveError('Each weapon slot needs an item ID and value.')
        item,value=skill['id'],skill['value'];original=info['skills'][index]
        if item is not None and type(item) is not int:raise SaveError('Weapon bonus IDs must be integers or None.')
        if type(value) is not int:raise SaveError('Weapon bonus values must be integers.')
        if original['id'] is not None and original['id'] not in NORMAL_ITEMS:
            if skill!=original:raise SaveError('Existing rare weapon skills must be preserved in their saved slots.')
        elif item is None:
            if value!=0:raise SaveError('Empty weapon bonus slots require zero value.')
        elif item not in NORMAL_ITEMS:
            raise SaveError('Only verified normal bonus identities can be added or changed.')
        if item is not None:
            if item in seen:raise SaveError('A weapon cannot have duplicate bonus identities.')
            seen.add(item)
            if item in NORMAL_ITEMS:
                blue+=1
                if value not in allowed_values(info,item):raise SaveError(f'{ITEMS[item]["name"]} has an unsupported weapon roll.')
        result.append({'id':item,'value':value})
    if blue>info['blue_limit']:raise SaveError(f'This weapon supports at most {info["blue_limit"]} normal bonuses.')
    if blue<info['blue_minimum']:raise SaveError(f'Keep at least {info["blue_minimum"]} normal bonuses for this weapon. Replace their types instead of removing them.')
    return result


def state(document,data_id,changes=()):
    changes=list(changes);info=_base_state(document,data_id,changes);requests=_requests(changes)
    if data_id in requests:
        if not info['editable']:raise SaveError(info['reason'])
        info['skills']=validate_skills(info,requests[data_id])
    return info


def states(document,changes=()):
    changes=list(changes)
    for array,base in [('WeaponDataArray',0),('UniqueWeaponDataArray',10000)]:
        for index in range(len(document.records(array))):
            info=state(document,base+index,changes)
            if info['owned']:yield info


def max_existing_skills(document,data_id,changes=()):
    info=state(document,data_id,changes)
    if not info['editable']:raise SaveError(info['reason'])
    return [{'id':s['id'],'value':max(allowed_values(info,s['id'])) if s['id'] in NORMAL_ITEMS else s['value']} for s in info['skills']]


def plan_weapon_roll_changes(document,changes,add_property):
    for data_id in _requests(changes):
        info=state(document,data_id,changes)
        record=fields(document.records(info['array'])[info['index']])
        for index,skill in enumerate(info['skills']):
            slot=fields(record['Skill']['value']['records'][index])
            enum='EEquipItemID::NUM' if skill['id'] is None else 'EEquipItemID::'+ITEMS[skill['id']]['enum']
            encoded=enum.encode('utf-8')+b'\0'
            reason=f'{info["metadata"].get("name") or "Weapon"} copy {data_id}: bonus slot {index+1}'
            add_property(slot['EquipItemID'],struct.pack('<i',len(encoded))+encoded,reason+' identity')
            add_property(slot['Value'],struct.pack('<i',skill['value']),reason+' verified numeric roll')
