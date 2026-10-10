"""Verified unique acquisition, collection gallery and two Tactics costumes.

The gallery records acquisition snapshots, independently of the owned inventory.
Ordinary gallery entries never manufacture equipped/inventory copies. The native
unique acquisition path expands its indexed array through WeaponID - 89.
"""
import struct
from koei_editor.games.dw3.models import Change, SaveError, fields
from koei_editor.games.dw3.unreal import Reader, tags
import koei_editor.games.dw3.officer_weapon_editor as weapons

CATEGORIES={'koei_editor.games.dw3.weapon_collection'}
COLLECTION_IDS=tuple(range(130))+tuple(range(132,173))+tuple(range(188,193))
TACTICS_OFFICERS=(12,13)  # Native setter 0x1512EF0; costume slot 2 belongs to DLC.


def all_collection_changes():
    return [Change('koei_editor.games.dw3.weapon_collection',0,'CollectAll',True)]


def tactics_costume_changes():
    return [Change('koei_editor.games.dw3.weapon_collection',0,'TacticsCostumes',True)]


def has_all_collection(document,changes=()):
    if any(c.category=='koei_editor.games.dw3.weapon_collection' and c.field=='CollectAll' and c.value is True for c in changes):return True
    rows=document.records('CollectedWeaponDataArray')
    return all(i<len(rows) and fields(rows[i])['WeaponID']['value']==weapons.WEAPONS[i]['enum'] and
               fields(rows[i])['ID']['value']==weapons.WEAPONS[i]['enum'] for i in COLLECTION_IDS)


def has_tactics_costumes(document,changes=()):
    if any(c.category=='koei_editor.games.dw3.weapon_collection' and c.field=='TacticsCostumes' and c.value is True for c in changes):return True
    rows=document.records('PCSaveDataArray')
    return all(i<len(rows) and len(fields(rows[i])['CanUseCostume']['value']['values'])>3 and
               bool(fields(rows[i])['CanUseCostume']['value']['values'][3]) for i in TACTICS_OFFICERS)


def original_value(document,change):
    if change.field=='CollectAll':return has_all_collection(document)
    if change.field=='TacticsCostumes':return has_tactics_costumes(document)
    raise SaveError('Unsupported weapon collection action.')


def _string(value):
    encoded=value.encode('utf-8')+b'\0'
    return struct.pack('<i',len(encoded))+encoded


def _record_bytes(document,record,array):
    start=record[0]['tag_offset']
    reader=Reader(document.plaintext,start,array['data_offset']+array['data_size'])
    tags(reader)
    return document.plaintext[start:reader.pos]


def _render_record(document,record,array,updates):
    """Replace leaves and regenerate only their enclosing tagged sizes."""
    start=record[0]['tag_offset']; raw=bytearray(_record_bytes(document,record,array))
    properties=[]
    def walk(rows):
        for prop in rows:
            properties.append(prop)
            value=prop['value']
            if isinstance(value,list) and value and isinstance(value[0],dict):walk(value)
            elif isinstance(value,dict) and 'records' in value:
                for row in value['records']:walk(row)
    walk(record)
    patches=[];deltas={}
    for prop,after in updates:
        offset=prop['data_offset'];before=document.plaintext[offset:offset+prop['data_size']]
        if before==after:continue
        patches.append((offset-start,len(before),after))
        delta=len(after)-len(before)
        if delta:
            for parent in properties:
                if parent['data_offset']<=offset and offset+len(before)<=parent['data_offset']+parent['data_size']:
                    deltas[parent['size_offset']]=deltas.get(parent['size_offset'],0)+delta
    for offset,delta in deltas.items():
        old=struct.unpack_from('<i',document.plaintext,offset)[0]
        patches.append((offset-start,4,struct.pack('<i',old+delta)))
    for offset,size,after in sorted(patches,reverse=True):raw[offset:offset+size]=after
    return bytes(raw)


def _identity_updates(record,weapon_id,data_id,attr,skills,get_time=0.0):
    f=fields(record)
    if len(f['Skill']['value']['records'])!=9:raise SaveError('A new weapon needs the verified nine-slot record schema.')
    enum='EWeaponID::NUM' if weapon_id is None else weapons.WEAPONS[weapon_id]['enum']
    result=[(f['ID'],_string(enum)),(f['WeaponID'],_string(enum)),
            (f['Attr'],struct.pack('<q',attr)),(f['DataID'],struct.pack('<i',data_id)),
            (f['GetTime'],struct.pack('<d',get_time))]
    for row,skill in zip(f['Skill']['value']['records'],skills):
        s=fields(row);item=skill['id']
        enum='EEquipItemID::NUM' if item is None else 'EEquipItemID::'+weapons.ITEMS[item]['enum']
        result.extend([(s['EquipItemID'],_string(enum)),(s['GuardEquipItemID'],_string('EGuardEquipItemID::NUM')),
                       (s['Value'],struct.pack('<i',skill['value']))])
    return result


def _credible_blank(record,data_id):
    f=fields(record)
    return (f['ID']['value']=='EWeaponID::NUM' and f['WeaponID']['value']=='EWeaponID::NUM' and
            f['Attr']['value']==0 and f['DataID']['value'] in (-1,data_id) and f['GetTime']['value']==0.0 and
            len(f['Skill']['value']['records'])==9 and all(
                fields(s)['EquipItemID']['value']=='EEquipItemID::NUM' and
                fields(s)['GuardEquipItemID']['value']=='EGuardEquipItemID::NUM' and
                fields(s)['Value']['value']==0 for s in f['Skill']['value']['records']))


def _snapshot_skills(record):
    f=fields(record);rows=f['Skill']['value']['records']
    if f['ID']['value']!=f['WeaponID']['value'] or len(rows)!=9:return None
    result=[]
    for row in rows:
        s=fields(row);enum=s['EquipItemID']['value'];item=weapons.ITEM_IDS.get(enum)
        if (item is None and enum!='EEquipItemID::NUM') or s['GuardEquipItemID']['value']!='EGuardEquipItemID::NUM':return None
        result.append({'id':item,'value':s['Value']['value']})
    return result


def _blank_source(document):
    # These are all native WeaponSaveData constructor fields. Extra fields in
    # existing copies are preserved, but cannot be cloned into a new record.
    required={'ID','WeaponID','Attr','DataID','GetTime','Skill'}
    for name in ('UniqueWeaponDataArray','CollectedWeaponDataArray','WeaponDataArray'):
        array=document.properties[name]
        for row in document.records(name):
            f=fields(row)
            if set(f)==required and len(f['Skill']['value']['records'])==9 and all(
                set(fields(s))=={'EquipItemID','GuardEquipItemID','Value'} for s in f['Skill']['value']['records']):
                return row,array
    raise SaveError('No verified native weapon record schema is available for acquisition.')


def _stock_skills(weapon_id):
    if weapon_id in weapons.UNIQUES:
        return [{'id':s['item_id'] if s['item_id'] in weapons.ITEMS else None,'value':s['value']}
                for s in weapons.UNIQUES[weapon_id]['skill_slots']]
    skills=[{'id':None,'value':0} for _ in range(9)]
    if not weapons.WEAPONS[weapon_id]['initial_possession']:
        skills[0]={'id':0,'value':1}  # Speed Scroll: native rank generator tier-0 minimum.
    return skills


def plan_weapon_collection_changes(document,changes,add_property):
    """Plan the unique payload and independent gallery records without overlap."""
    actions=set(); acquisitions={};requests=weapons._requests(changes)
    for change in changes:
        if change.category in CATEGORIES:
            if change.index!=0 or type(change.index) is not int or change.field not in ('CollectAll','TacticsCostumes') or change.value is not True:
                raise SaveError('Choose a supported collection action; existing collections cannot be removed.')
            actions.add(change.field)
        elif change.category=='unique_weapon':
            if change.index not in weapons.UNIQUES or change.field!='Owned' or change.value is not True:
                raise SaveError('Only verified unique weapon acquisition is supported.')
            acquisitions[change.index]=weapons.UNIQUES[change.index]

    if 'TacticsCostumes' in actions:
        officers=document.records('PCSaveDataArray')
        for index in TACTICS_OFFICERS:
            if index>=len(officers):raise SaveError('The Tactics costume officer record is absent from this save.')
            prop=fields(officers[index])['CanUseCostume'];values=prop['value']['values']
            if (prop['type']!='ArrayProperty(BoolProperty)' or len(values)<=3 or
                prop['data_size']!=4+len(values) or any(type(v) is not int or v not in (0,1) for v in values)):
                raise SaveError('This save has no supported Tactics costume flag.')
            payload=bytearray(document.plaintext[prop['data_offset']:prop['data_offset']+prop['data_size']])
            payload[7]=1
            add_property(prop,bytes(payload),f'Officer {index}: unlock Tactics costume; preserve DLC and story flags')

    unique_prop=document.properties['UniqueWeaponDataArray'];unique_rows=document.records('UniqueWeaponDataArray')
    unique_edits={data_id:requested for data_id,requested in requests.items() if weapons._location(document,data_id)[0]=='UniqueWeaponDataArray'}
    if acquisitions or unique_edits:
        blank_row,blank_array=_blank_source(document)
        end=max([len(unique_rows)]+[w['unique_save_index']+1 for w in acquisitions.values()])
        rendered=[_record_bytes(document,row,unique_prop) for row in unique_rows]
        for index in range(len(unique_rows),end):
            rendered.append(_render_record(document,blank_row,blank_array,
                _identity_updates(blank_row,None,10000+index,0,[{'id':None,'value':0} for _ in range(9)])))
        targets={w['unique_save_index']:w for w in acquisitions.values()}
        for data_id in unique_edits:targets.setdefault(data_id-10000,None)
        for index,template in targets.items():
            data_id=10000+index
            row=unique_rows[index] if index<len(unique_rows) else blank_row
            array=unique_prop if index<len(unique_rows) else blank_array
            f=fields(row);owned=index<len(unique_rows) and f['WeaponID']['value']!='EWeaponID::NUM'
            if template and owned and f['WeaponID']['value']!=template['weapon_enum']:
                raise SaveError('Unique acquisition would replace a different saved weapon identity.')
            if template and not owned and index<len(unique_rows) and not _credible_blank(row,data_id):
                raise SaveError('The unique slot has nonempty or unknown data; preserve it without replacing it.')
            info=weapons.state(document,data_id,changes)
            updates=[]
            if template and not owned:
                updates=_identity_updates(row,template['weapon_id'],data_id,info['attr'],info['skills'])
            elif data_id in unique_edits:
                requested=unique_edits[data_id]
                if 'Elements' in requested:updates.append((f['Attr'],struct.pack('<q',info['attr'])))
                if 'Skills' in requested:
                    for skill_row,skill in zip(f['Skill']['value']['records'],info['skills']):
                        s=fields(skill_row);enum='EEquipItemID::NUM' if skill['id'] is None else 'EEquipItemID::'+weapons.ITEMS[skill['id']]['enum']
                        updates.extend([(s['EquipItemID'],_string(enum)),(s['Value'],struct.pack('<i',skill['value']))])
            rendered[index]=_render_record(document,row,array,updates)
        payload=struct.pack('<i',len(rendered))+b''.join(rendered)
        add_property(unique_prop,payload,'Acquire indexed unique weapons, pad native blank slots, and apply requested unique bonuses')

    wanted=set(COLLECTION_IDS) if 'CollectAll' in actions else set(acquisitions)
    if wanted:
        gallery_prop=document.properties['CollectedWeaponDataArray'];gallery=document.records('CollectedWeaponDataArray')
        if max(wanted)>=len(gallery):raise SaveError('This save lacks the required weapon collection slots; preserve it without guessing a migration.')
        for weapon_id in sorted(wanted):
            row=gallery[weapon_id];f=fields(row);enum=weapons.WEAPONS[weapon_id]['enum']
            if f['WeaponID']['value']==enum:
                if f['ID']['value']!=enum:raise SaveError('A collection snapshot has inconsistent identities; preserve it without replacing it.')
                continue  # Preserve an existing acquisition snapshot exactly.
            if f['WeaponID']['value']!='EWeaponID::NUM':raise SaveError('A collection slot contains a different identity; preserve it without replacing it.')
            if not _credible_blank(row,weapon_id):raise SaveError('A collection slot has nonempty or unknown data; preserve it without replacing it.')
            source=next((r for name in ('WeaponDataArray','UniqueWeaponDataArray') for r in document.records(name)
                         if fields(r)['WeaponID']['value']==enum and _snapshot_skills(r) is not None),None)
            attr=fields(source)['Attr']['value'] if source else (
                weapons.UNIQUES[weapon_id]['attribute_bitmask'] if weapon_id in weapons.UNIQUES else weapons.WEAPONS[weapon_id]['attribute_bitmask'])
            skills=_snapshot_skills(source) if source else _stock_skills(weapon_id)
            before=_record_bytes(document,row,gallery_prop)
            get_time=fields(source)['GetTime']['value'] if source else 0.0
            after=_render_record(document,row,gallery_prop,_identity_updates(row,weapon_id,weapon_id,attr,skills,get_time))
            # Replacing one complete tagged record leaves other gallery records
            # independent, so bodyguard acquisition can safely edit its own IDs.
            span={'type':'StructProperty','data_offset':row[0]['tag_offset'],'data_size':len(before)}
            add_property(span,after,f'Collect weapon {weapon_id}; preserve other acquisition snapshots and owned inventory')
