"""Verified bodyguard equipment and final-state edit planning, separate from UI."""
from pathlib import Path
import json
import struct
from models import SaveError, fields
import bodyguard_growth as growth

ROOT=Path(__file__).resolve().parent
GUARD_ITEMS={r['id']:r for r in json.loads((ROOT/'bodyguard_items.json').read_text(encoding='utf-8'))['items']}
GUARD_WEAPONS={r['id']:r for r in json.loads((ROOT/'bodyguard_weapons.json').read_text(encoding='utf-8'))['weapons']}
FAMILY_NAMES=('Sword','Spear','Pike','Bow','Crossbow')
ITEM_IDS={r['enum']:i for i,r in GUARD_ITEMS.items()}
WEAPON_IDS={r['enum']:i for i,r in GUARD_WEAPONS.items()}
CATEGORIES={'bodyguard','guard_item','guard_weapon','guard_weapon_slot'}


def _requests(changes):
    result={category:{} for category in CATEGORIES};seen=set()
    for change in changes:
        if not isinstance(change.category,str) or not isinstance(change.field,str) or type(change.index) is not int:
            raise SaveError('Edit category/field must be text and indexes must be integers.')
        if change.category not in CATEGORIES:continue
        ident=(change.category,change.index,change.field)
        if ident in seen:raise SaveError('Duplicate bodyguard changes.')
        seen.add(ident)
        if type(change.index) is not int:raise SaveError('Bodyguard indexes must be integers.')
        allowed={'bodyguard':{'SPoint','BGLevels','MemberItem','MemberWeapon'},
                 'guard_item':{'Owned','Value'},'guard_weapon':{'Owned','MaxBonuses'},
                 'guard_weapon_slot':{'Skills'}}[change.category]
        valid=(0<=change.index<4 if change.category=='bodyguard' else
               change.index in GUARD_ITEMS if change.category=='guard_item' else
               change.index in GUARD_WEAPONS if change.category=='guard_weapon' else 0<=change.index<100)
        if not valid or change.field not in allowed:raise SaveError('Unsupported bodyguard edit index or field.')
        result[change.category].setdefault(change.index,{})[change.field]=change.value
    return result


def max_skills(weapon_id):
    if type(weapon_id) is not int or weapon_id not in GUARD_WEAPONS:raise SaveError('Unsupported bodyguard weapon.')
    return [dict(skill) for skill in GUARD_WEAPONS[weapon_id]['max_bonus_profile']]


def validate_skills(weapon_id,skills):
    if type(weapon_id) is not int or weapon_id not in GUARD_WEAPONS:raise SaveError('Unlock a supported bodyguard weapon first.')
    row=GUARD_WEAPONS[weapon_id]
    if not isinstance(skills,(list,tuple)) or len(skills)>row['max_skills']:
        raise SaveError('Bodyguard weapons support at most three bonuses.')
    if not skills and row['tier']!=1:
        raise SaveError('Dropped upgraded bodyguard weapons require at least one bonus.')
    result=[];seen=set()
    for skill in skills:
        if not isinstance(skill,dict) or set(skill)!={'id','value'}:raise SaveError('Each weapon bonus needs an item ID and value.')
        item,value=skill['id'],skill['value']
        if type(item) is not int or item not in row['allowed_skill_ids'] or item in seen:
            raise SaveError('Duplicate or ineligible bodyguard weapon bonus.')
        if type(value) is not int or value not in row['allowed_values_by_guard_item_id'][str(item)]:
            raise SaveError('This bonus value cannot be generated for this weapon tier.')
        seen.add(item);result.append({'id':item,'value':value})
    return result


def item_state(document,changes=()):
    requests=_requests(changes)['guard_item'];result={}
    for i,row in enumerate(document.records('GuardEquipItemDataArray')):
        item=GUARD_ITEMS[i];record=fields(row);wanted=requests.get(i,{})
        enum=record['GuardEquipItemID']['value']
        if enum not in ('EGuardEquipItemID::NUM',item['enum']):raise SaveError('Bodyguard item does not match its inventory slot.')
        owned=wanted.get('Owned',enum==item['enum']);value=wanted.get('Value',record['Value']['value'])
        if type(owned) is not bool:raise SaveError('Item ownership requires a boolean.')
        if 'Value' in wanted:
            if item['kind']!='normal' or type(value) is not int or not 1<=value<=item['max_value']:
                raise SaveError(f'{item["name"]} requires a verified normal-item value from 1 to {item["max_value"]}.')
            if 'Owned' not in wanted:owned=True
        if not owned or item['kind']=='rare':value=0
        elif value==0:value=1
        result[i]={'owned':owned,'value':value}
    return result


def weapon_state(document,changes=()):
    requests=_requests(changes);result=[]
    for index,row in enumerate(document.records('GuardWeaponDataArray')):
        record=fields(row);enum=record['WeaponID']['value']
        weapon_id=None if enum=='EWeaponID::NUM' else WEAPON_IDS.get(enum)
        if weapon_id is None and enum!='EWeaponID::NUM':raise SaveError('Unknown bodyguard weapon inventory identity.')
        skills=[]
        for slot in record['Skill']['value']['records']:
            skill=fields(slot);item=skill['GuardEquipItemID']['value']
            if item!='EGuardEquipItemID::NUM':
                if item not in ITEM_IDS:raise SaveError('Unknown bodyguard weapon bonus.')
                skills.append({'id':ITEM_IDS[item],'value':skill['Value']['value']})
        result.append({'slot':index,'weapon_id':weapon_id,'data_id':record['DataID']['value'],'skills':skills})
    for weapon_id,wanted in requests['guard_weapon'].items():
        for value in wanted.values():
            if value is not True:raise SaveError('Bodyguard weapon actions require True; removal is unsupported.')
        owned=[row for row in result if row['weapon_id']==weapon_id]
        if wanted.get('Owned') and not owned:
            blank=next((row for row in result if row['weapon_id'] is None),None)
            if blank is None:raise SaveError('Bodyguard weapon inventory is full. No existing weapon will be replaced.')
            blank.update(weapon_id=weapon_id,data_id=blank['slot'],skills=max_skills(weapon_id));owned=[blank]
        if wanted.get('MaxBonuses'):
            if not owned:raise SaveError('Unlock the bodyguard weapon before maximizing it.')
            for row in owned:row['skills']=max_skills(weapon_id)
    for index,wanted in requests['guard_weapon_slot'].items():
        result[index]['skills']=validate_skills(result[index]['weapon_id'],wanted['Skills'])
    return result


def team_state(document,index,changes=()):
    if type(index) is not int or not 0<=index<4:raise SaveError('Unsupported bodyguard team.')
    wanted=_requests(changes)['bodyguard'].get(index,{})
    original=fields(document.records('GuardDataArray')[index])
    merit=wanted.get('SPoint',original['SPoint']['value'])
    levels=wanted.get('BGLevels',original['BGLevels']['value']['values'])
    try:
        # Match the game's independently earned Count and AI progression.
        if 'SPoint' in wanted or 'BGLevels' in wanted:levels=growth.automatic_levels(merit,levels)
        else:levels=list(growth.validate_growth(merit,levels))
    except ValueError as error:raise SaveError(str(error)) from error
    enum=original['MemberItem']['value']
    item=wanted.get('MemberItem',None if enum=='EGuardEquipItemID::NUM' else ITEM_IDS.get(enum))
    if item is not None and (type(item) is not int or item not in GUARD_ITEMS):raise SaveError('Unsupported equipped bodyguard item.')
    weapons=wanted.get('MemberWeapon',original['MemberWeapon']['value']['values'])
    if not isinstance(weapons,(list,tuple)) or len(weapons)!=10 or any(type(i) is not int for i in weapons):
        raise SaveError('Bodyguard weapon choices must contain the ten saved integer references.')
    if list(weapons)[5:]!=original['MemberWeapon']['value']['values'][5:]:
        raise SaveError('Unmapped extra bodyguard weapon references must be preserved.')
    return {'SPoint':merit,'BGLevels':list(levels),'MemberItem':item,'MemberWeapon':list(weapons)}


def best_weapon_refs(document,changes=()):
    pool=weapon_state(document,changes);result=[]
    for family in range(5):
        options=[row for row in pool if row['weapon_id'] is not None and GUARD_WEAPONS[row['weapon_id']]['family_index']==family]
        if not options:raise SaveError(f'No owned {FAMILY_NAMES[family]} bodyguard weapon.')
        best=max(options,key=lambda row:(GUARD_WEAPONS[row['weapon_id']]['tier'],sum(s['value'] for s in row['skills']),-row['slot']))
        result.append(best['slot'])
    return result


def plan_bodyguard_changes(document,changes,add_property):
    requests=_requests(changes)
    if not any(requests.values()):return
    items=item_state(document,changes);pool=weapon_state(document,changes)
    teams=[team_state(document,i,changes) for i in range(4)]
    # Check final references after acquisitions and equipment choices together.
    for team in teams:
        if team['MemberItem'] is not None and not items[team['MemberItem']]['owned']:
            raise SaveError('An equipped bodyguard item must be owned. Unequip it before removing it.')
        for family,index in enumerate(team['MemberWeapon'][:5]):
            if index==-1:continue
            if not 0<=index<len(pool) or pool[index]['weapon_id'] is None or GUARD_WEAPONS[pool[index]['weapon_id']]['family_index']!=family:
                raise SaveError('Equipped bodyguard weapon references must point to an owned weapon of the correct family.')
    for i,wanted in requests['guard_item'].items():
        if items[i]['owned']:continue
        for row in document.records('PCSaveDataArray'):
            if fields(row)['BGMusouEquipItem']['value']==GUARD_ITEMS[i]['enum']:
                raise SaveError('This bodyguard item is referenced by an officer bodyguard-Musou setup and cannot be removed safely.')
    def integer(prop,value,reason):add_property(prop,struct.pack('<i',value),reason)
    def enum(prop,value,reason):
        data=value.encode('utf-8')+b'\0';add_property(prop,struct.pack('<i',len(data))+data,reason)
    def array(prop,values,reason):add_property(prop,struct.pack('<i',len(values))+struct.pack('<'+'i'*len(values),*values),reason)
    for i in requests['guard_item']:
        original=fields(document.records('GuardEquipItemDataArray')[i]);state=items[i]
        enum(original['GuardEquipItemID'],GUARD_ITEMS[i]['enum'] if state['owned'] else 'EGuardEquipItemID::NUM',f'{GUARD_ITEMS[i]["name"]}: ownership')
        integer(original['Value'],state['value'],f'{GUARD_ITEMS[i]["name"]}: verified item roll')
    for i in requests['bodyguard']:
        original=fields(document.records('GuardDataArray')[i]);state=teams[i]
        integer(original['SPoint'],state['SPoint'],f'Bodyguard team {i+1}: Merit')
        array(original['BGLevels'],state['BGLevels'],f'Bodyguard team {i+1}: legal growth and earned Count/AI')
        item=state['MemberItem']
        enum(original['MemberItem'],'EGuardEquipItemID::NUM' if item is None else GUARD_ITEMS[item]['enum'],f'Bodyguard team {i+1}: equipped item')
        array(original['MemberWeapon'],state['MemberWeapon'],f'Bodyguard team {i+1}: equipped weapon references')
        old_count=growth.derive_stats(original['BGLevels']['value']['values'])['member_count']
        new_count=growth.derive_stats(state['BGLevels'])['member_count']
        if old_count!=new_count:
            for officer,row in enumerate(document.records('PCSaveDataArray')[:42]):
                record=fields(row);count=record['MemCnt']['value']
                if record['BGTeamID']['value']==i and (count==old_count or count>new_count):
                    integer(record['MemCnt'],new_count,f'Officer {officer}: synchronize chosen bodyguard count after team growth')
    def write_weapon(record,state,reason,new=False,data_id=None):
        if new:
            for name in ('ID','WeaponID'):enum(record[name],GUARD_WEAPONS[state['weapon_id']]['enum'],reason+' identity')
            add_property(record['Attr'],struct.pack('<q',0),reason+' guard attribute flags')
            integer(record['DataID'],state['data_id'] if data_id is None else data_id,reason+' inventory/collection reference')
        for index,slot in enumerate(record['Skill']['value']['records']):
            target=fields(slot);skill=state['skills'][index] if index<len(state['skills']) else None
            enum(target['EquipItemID'],'EEquipItemID::NUM',reason+' ordinary item sentinel')
            enum(target['GuardEquipItemID'],'EGuardEquipItemID::NUM' if skill is None else GUARD_ITEMS[skill['id']]['enum'],reason+' bodyguard bonus ID')
            integer(target['Value'],0 if skill is None else skill['value'],reason+' legitimate bonus value')
    for state,row in zip(pool,document.records('GuardWeaponDataArray')):
        if state['weapon_id'] is None:continue
        original=fields(row);new=original['WeaponID']['value']=='EWeaponID::NUM'
        requested=requests['guard_weapon'].get(state['weapon_id'],{})
        if new or requested.get('MaxBonuses') or state['slot'] in requests['guard_weapon_slot']:
            write_weapon(original,state,f'Bodyguard {GUARD_WEAPONS[state["weapon_id"]]["name"]} copy {state["slot"]+1}',new)
    for weapon_id,wanted in requests['guard_weapon'].items():
        if not wanted.get('Owned'):continue
        record=fields(document.records('CollectedWeaponDataArray')[weapon_id])
        if record['WeaponID']['value']=='EWeaponID::NUM':
            first=next(state for state in pool if state['weapon_id']==weapon_id)
            write_weapon(record,first,f'Bodyguard {GUARD_WEAPONS[weapon_id]["name"]}: first acquisition collection cache',True,weapon_id)
        elif record['WeaponID']['value']!=GUARD_WEAPONS[weapon_id]['enum']:
            raise SaveError('Bodyguard weapon collection cache has an unexpected identity.')
