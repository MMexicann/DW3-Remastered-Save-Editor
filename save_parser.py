"""Strict parsing of the verified DW3 Remastered UE5.6 save format."""
from pathlib import Path, PureWindowsPath
import json
import os
import re
from models import SaveDocument, SaveError, fields
import save_codec
import unreal
import bodyguard_growth
from bodyguard_editor import GUARD_WEAPONS, GUARD_ITEMS, item_state, weapon_state, team_state, validate_skills

MAX_SIZE=16*1024*1024
ENUMS={name:set(values) for name,values in json.loads((Path(__file__).resolve().parent/'native_enums.json').read_text()).items()}
ORDINARY_ITEMS={row['id']:row for row in json.loads((Path(__file__).resolve().parent/'game_metadata.json').read_text(encoding='utf-8'))['items']}
ORDINARY_CAPS={int(key):value for key,value in json.loads((Path(__file__).resolve().parent/'item_limits.json').read_text())['maxima'].items()}
EXPECTED_COUNTS={'PCSaveDataArray':50,'EquipItemDataArray':100,'WeaponDataArray':500,'UniqueWeaponDataArray':84,
                 'CollectedWeaponDataArray':255,'GuardDataArray':4,'GuardWeaponDataArray':100,
                 'GuardEquipItemDataArray':10,'CanUseCharaArray':50,'CanUseScenarioArray':156}

def _reserved_windows_path(path):
    """Keep Python 3.10+ compatibility without os.path.isreserved (3.13+)."""
    windows=PureWindowsPath(str(path))
    devices={'CON','PRN','AUX','NUL','CONIN$','CONOUT$'}
    devices.update(prefix+digit for prefix in ('COM','LPT') for digit in '123456789\u00b9\u00b2\u00b3')
    return any(part.endswith((' ','.')) or any(ord(c)<32 or c in ':<>"|?*' for c in part)
               or part.split('.',1)[0].rstrip(' ').upper() in devices
               for part in windows.parts if part!=windows.anchor)

def safe_path(path: Path) -> Path:
    path=Path(path)
    if os.name=='nt' and _reserved_windows_path(path):
        raise SaveError('Use an ordinary file name, without device names or alternate data streams.')
    # Check lexically before resolving/accessing the named live save directory.
    for text in (str(path).replace('\\','/').lower(), str(path.absolute()).replace('\\','/').lower()):
        if re.search(r'/koeitecmo/dw3ce_re/saved(?:/|$)',text):
            raise SaveError('Use a copied save outside the live game folder.')
        if re.search(r'/steam/userdata(?:/|$)',text) or re.search(r'/userdata/[^/]+/[^/]+/remote(?:/|$)',text):
            raise SaveError('Steam Cloud folders cannot be accessed. Use a separate save copy.')
    if path.name.lower() in ('steam_autocloud.vdf','remotecache.vdf'):
        raise SaveError('Steam Cloud metadata cannot be opened or changed.')
    resolved=path.resolve()
    if resolved.name.lower() in ('steam_autocloud.vdf','remotecache.vdf'):
        raise SaveError('Steam Cloud metadata cannot be opened or changed through an alias.')
    if os.name=='nt' and _reserved_windows_path(resolved):
        raise SaveError('The resolved file name is unsupported.')
    if re.search(r'/koeitecmo/dw3ce_re/saved(?:/|$)',str(resolved).replace('\\','/').lower()):
        raise SaveError('Live save folders cannot be accessed by this editor.')
    text=str(resolved).replace('\\','/').lower()
    if re.search(r'/steam/userdata(?:/|$)',text) or re.search(r'/userdata/[^/]+/[^/]+/remote(?:/|$)',text):
        raise SaveError('Steam Cloud folders cannot be accessed.')
    return resolved

def parse_bytes(raw: bytes, source: Path | None=None) -> SaveDocument:
    try:
        plain=save_codec.decrypt(raw)
        parsed=unreal.parse(plain)
        h=parsed['header']
        if (h['save_version'],h['ue4_version'],h['ue5_version'],h['engine'],h['save_class']) != (
            3,522,1017,[5,6,1],'/Script/Refine.GameStatusSaveGame'):
            raise SaveError('This save version is not supported yet.')
        if parsed['trailer_hex']!='00000000':
            raise SaveError('Unsupported UObject trailer.')
        doc=SaveDocument(source,raw,plain,parsed)
        if len(doc.properties)!=len(parsed['properties']):
            raise SaveError('Duplicate top-level properties.')
        for name,count in EXPECTED_COUNTS.items():
            p=doc.properties.get(name)
            if p is None or not isinstance(p['value'],dict) or p['value'].get('count')!=count:
                raise SaveError(f'Unsupported {name} layout.')
        for record in doc.records('PCSaveDataArray'):
            f=fields(record)
            for name in ('MaxHealth','MaxMusou','Attack','Defence','SPoint','Progress','BGTeamID','MemCnt'):
                if name not in f or f[name]['type']!='IntProperty' or f[name]['data_size']!=4:
                    raise SaveError('Unsupported officer field layout.')
        for record in doc.records('EquipItemDataArray')+doc.records('GuardEquipItemDataArray'):
            f=fields(record)
            if (f['Value']['type']!='IntProperty' or f['Value']['data_size']!=4 or
                not f['EquipItemID']['type'].startswith('EnumProperty(EEquipItemID(') or
                f['EquipItemID']['value'] not in ENUMS['EEquipItemID'] or
                not f['GuardEquipItemID']['type'].startswith('EnumProperty(EGuardEquipItemID(') or
                f['GuardEquipItemID']['value'] not in ENUMS['EGuardEquipItemID']):
                raise SaveError('Unsupported equipment record.')
        for record in doc.records('GuardDataArray'):
            f=fields(record)
            if f['SPoint']['type']!='IntProperty' or f['SPoint']['data_size']!=4:
                raise SaveError('Unsupported bodyguard Merit.')
            for field,count in [('BGLevels',6),('MemberWeapon',10)]:
                if f[field]['type']!='ArrayProperty(IntProperty)' or f[field]['value'].get('count')!=count or f[field]['data_size']!=4+4*count:
                    raise SaveError('Unsupported bodyguard growth or weapon reference array.')
            if (not f['MemberItem']['type'].startswith('EnumProperty(EGuardEquipItemID(') or
                f['MemberItem']['value'] not in ENUMS['EGuardEquipItemID']):
                raise SaveError('Unsupported equipped bodyguard item.')
            bodyguard_growth.validate_growth(f['SPoint']['value'],f['BGLevels']['value']['values'])
        for name in ('CanUseCharaArray','CanUseScenarioArray'):
            if doc.properties[name]['type']!='ArrayProperty(BoolProperty)' or any(v not in (0,1) for v in doc.properties[name]['value']['values']):
                raise SaveError('Unsupported unlock array.')
        for name in ('WeaponDataArray','UniqueWeaponDataArray','CollectedWeaponDataArray','GuardWeaponDataArray'):
            for index,record in enumerate(doc.records(name)):
                f=fields(record)
                if (f['DataID']['type']!='IntProperty' or f['DataID']['data_size']!=4 or
                    f['Attr']['type']!='Int64Property' or f['Attr']['data_size']!=8 or
                    f['GetTime']['type']!='DoubleProperty' or f['GetTime']['data_size']!=8 or
                    f['Skill']['type']!='ArrayProperty(StructProperty(EquipItemSaveData(/Script/Refine)))' or
                    len(f['Skill']['value']['records'])!=9):
                    raise SaveError('Unsupported weapon record layout.')
                for field in ('ID','WeaponID'):
                    if (not f[field]['type'].startswith('EnumProperty(EWeaponID(') or
                        f[field]['value'] not in ENUMS['EWeaponID']):
                        raise SaveError('Unsupported weapon identity.')
                for slot in f['Skill']['value']['records']:
                    s=fields(slot)
                    if (s['Value']['type']!='IntProperty' or s['Value']['data_size']!=4 or
                        not s['EquipItemID']['type'].startswith('EnumProperty(EEquipItemID(') or
                        s['EquipItemID']['value'] not in ENUMS['EEquipItemID'] or
                        not s['GuardEquipItemID']['type'].startswith('EnumProperty(EGuardEquipItemID(') or
                        s['GuardEquipItemID']['value'] not in ENUMS['EGuardEquipItemID']):
                        raise SaveError('Unsupported weapon skill representation.')
                if name=='GuardWeaponDataArray':
                    allowed={w['enum'] for w in GUARD_WEAPONS.values()}|{'EWeaponID::NUM'}
                    if f['WeaponID']['value'] not in allowed or f['ID']['value']!=f['WeaponID']['value']:
                        raise SaveError('Unsupported bodyguard weapon identity.')
                    if f['WeaponID']['value']!='EWeaponID::NUM' and f['DataID']['value']!=index:
                        raise SaveError('Bodyguard weapon DataID must match its inventory slot.')
                    if f['Attr']['value']!=0:
                        raise SaveError('Bodyguard weapon attribute flags are unsupported.')
                    if any(fields(slot)['EquipItemID']['value']!='EEquipItemID::NUM' for slot in f['Skill']['value']['records']):
                        raise SaveError('Bodyguard weapon bonuses must use bodyguard item IDs.')
        for index,item in ORDINARY_ITEMS.items():
            f=fields(doc.records('EquipItemDataArray')[index])
            expected='EEquipItemID::'+item['enum']
            if f['GuardEquipItemID']['value']!='EGuardEquipItemID::NUM' or f['EquipItemID']['value'] not in ('EEquipItemID::NUM',expected):
                raise SaveError('Ordinary item identity must match its inventory slot.')
            owned=f['EquipItemID']['value']==expected;value=f['Value']['value']
            if (not owned or item['kind']=='rare') and value!=0:
                raise SaveError('Unowned and rare ordinary items must have zero numeric value.')
            if owned and item['kind']=='normal' and not 1<=value<=ORDINARY_CAPS[index]:
                raise SaveError('Ordinary item value is outside its verified roll range.')
        for index,record in enumerate(doc.records('GuardEquipItemDataArray')):
            f=fields(record)
            if f['EquipItemID']['value']!='EEquipItemID::NUM' or f['GuardEquipItemID']['value'] not in ('EGuardEquipItemID::NUM',GUARD_ITEMS[index]['enum']):
                raise SaveError('Bodyguard item identity must match its inventory slot.')
            item=GUARD_ITEMS[index];owned=f['GuardEquipItemID']['value']==item['enum'];value=f['Value']['value']
            if (not owned or item['kind']=='rare') and value!=0:
                raise SaveError('Unowned and rare bodyguard items must have zero numeric value.')
            if owned and item['kind']=='normal' and not 1<=value<=item['max_value']:
                raise SaveError('Bodyguard item value is outside its verified roll range.')
        items=item_state(doc);pool=weapon_state(doc)
        for state,record in zip(pool,doc.records('GuardWeaponDataArray')):
            for slot in fields(record)['Skill']['value']['records']:
                skill=fields(slot)
                if skill['GuardEquipItemID']['value']=='EGuardEquipItemID::NUM' and skill['Value']['value']!=0:
                    raise SaveError('Empty bodyguard weapon bonus slots must have zero value.')
            if state['weapon_id'] is None:
                if state['skills']:raise SaveError('Empty bodyguard weapon inventory slots cannot have bonuses.')
            else:validate_skills(state['weapon_id'],state['skills'])
        for index in range(4):
            team=team_state(doc,index)
            if team['MemberItem'] is not None and not items[team['MemberItem']]['owned']:
                raise SaveError('Equipped bodyguard item is not owned.')
            for family,slot in enumerate(team['MemberWeapon'][:5]):
                if slot==-1:continue
                if not 0<=slot<len(pool) or pool[slot]['weapon_id'] is None or GUARD_WEAPONS[pool[slot]['weapon_id']]['family_index']!=family:
                    raise SaveError('Equipped bodyguard weapon must reference an owned copy of the correct family.')
        for record in doc.records('PCSaveDataArray'):
            cached=fields(record)['BGMusouEquipItem']
            if not cached['type'].startswith('EnumProperty(EGuardEquipItemID(') or cached['value'] not in ENUMS['EGuardEquipItemID']:
                raise SaveError('Unsupported officer bodyguard-Musou equipment reference.')
        return doc
    except (ValueError,KeyError,TypeError,IndexError,UnicodeError) as error:
        if isinstance(error,SaveError): raise
        raise SaveError(f'Damaged or unsupported save: {error}') from error

def read_save(path: Path) -> SaveDocument:
    selected=safe_path(path)
    if selected.suffix.lower()!='.sav':raise SaveError('Choose a .sav save copy.')
    with selected.open('rb') as stream:
        raw=stream.read(MAX_SIZE+1)
    if len(raw)>MAX_SIZE: raise SaveError('Save exceeds the supported size.')
    return parse_bytes(raw,selected)
