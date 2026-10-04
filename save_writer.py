"""Verified byte patches, round-trip validation, backups and atomic output."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import struct
import uuid
from models import Change, Patch, SaveDocument, SaveError, fields
from save_parser import parse_bytes, safe_path, read_save, MAX_SIZE
import save_codec
import bodyguard_editor
import officer_weapon_editor

CAPS={'SPoint':99999}  # Only limits proved from game code are enabled.
OFFICER_FIELDS=('SPoint','MaxHealth','MaxMusou','Attack','Defence')
ROOT=Path(__file__).resolve().parent
METADATA=json.loads((ROOT/'game_metadata.json').read_text(encoding='utf-8'))
ITEMS={item['id']:item for item in METADATA['items']}
UNIQUE_WEAPONS={item['weapon_id']:item for item in json.loads((ROOT/'unique_weapons.json').read_text())['weapons']}
ITEM_CAPS={}
if (ROOT/'item_limits.json').exists():
    ITEM_CAPS={int(k):int(v) for k,v in json.loads((ROOT/'item_limits.json').read_text())['maxima'].items()}

def load_verified_limits():
    path=ROOT/'verified_limits.json'
    if path.exists():
        data=json.loads(path.read_text())
        for name,entry in data.get('officers',{}).items():
            if name in OFFICER_FIELDS and entry.get('confirmed') is True:
                CAPS[name]=int(entry['max'])

load_verified_limits()

def plan_changes(document: SaveDocument, changes: list[Change]) -> list[Patch]:
    patches=[]; seen=set(); item_changes={}; unique_changes={}; size_deltas={}
    all_properties=[]
    def walk(properties):
        for prop in properties:
            all_properties.append(prop)
            value=prop['value']
            if isinstance(value,list) and value and isinstance(value[0],dict):walk(value)
            elif isinstance(value,dict) and 'records' in value:
                for record in value['records']:walk(record)
    walk(document.parsed['properties'])
    def add_property(prop,after,reason):
        offset=prop['data_offset'];before=document.plaintext[offset:offset+prop['data_size']]
        if before==after:return
        patches.append(Patch(offset,before,after,reason))
        delta=len(after)-len(before)
        if delta:
            for parent in all_properties:
                if parent['data_offset']<=offset and offset+len(before)<=parent['data_offset']+parent['data_size']:
                    size_deltas[parent['size_offset']]=size_deltas.get(parent['size_offset'],0)+delta
    for change in changes:
        if not isinstance(change,Change) or not isinstance(change.category,str) or not isinstance(change.field,str) or type(change.index) is not int:
            raise SaveError('Edits need a supported category, field and integer index.')
        ident=(change.category,change.index,change.field)
        if ident in seen: raise SaveError('Duplicate changes.')
        seen.add(ident)
        if change.category in bodyguard_editor.CATEGORIES or change.category in officer_weapon_editor.CATEGORIES:
            continue
        if change.category=='unique_weapon':
            if (type(change.index) is not int or change.index not in UNIQUE_WEAPONS or
                change.field!='Owned' or change.value is not True):
                raise SaveError('Only supported unique weapon acquisition can be edited.')
            weapon=UNIQUE_WEAPONS[change.index]
            if weapon['unique_save_index']>=len(document.records('UniqueWeaponDataArray')):
                raise SaveError('This officer\'s unique weapon slot is absent from this save. Array expansion is not enabled.')
            unique_changes[change.index]=weapon
            continue
        if change.category=='item':
            if type(change.index) is not int or change.index not in ITEMS or change.field not in ('Owned','Value'):
                raise SaveError('Unsupported equipment item index or field.')
            item_changes.setdefault(change.index,{})[change.field]=change.value
            continue
        if change.category=='officer':
            records='PCSaveDataArray'
            if change.category=='officer' and (type(change.index) is not int or not 0<=change.index<42):
                raise SaveError('Only the42 playable officer records can be edited.')
            if change.field not in CAPS:
                raise SaveError('This permanent stat limit has not been verified; editing is disabled.')
            low=1 if change.field in ('MaxHealth','MaxMusou') else 0
            if type(change.value) is not int or not low<=change.value<=CAPS[change.field]:
                raise SaveError(f'{change.field} must be between {low} and {CAPS[change.field]}.')
            prop=fields(document.records(records)[change.index])[change.field]
            offset=prop['data_offset']; after=struct.pack('<i',change.value)
            reason=f'{change.category.title()} {change.index}: {change.field} {prop["value"]} -> {change.value}'
        elif change.category=='unlock':
            counts={'CanUseCharaArray':42,'CanUseScenarioArray':108}
            if change.field not in counts or type(change.index) is not int or not 0<=change.index<counts[change.field]:
                raise SaveError('This unlock index is not supported.')
            if type(change.value) is not bool: raise SaveError('Unlocks require a boolean.')
            prop=document.properties[change.field]
            if prop['type']!='ArrayProperty(BoolProperty)': raise SaveError('Unsupported unlock type.')
            offset=prop['data_offset']+4+change.index; after=bytes([change.value])
            reason=f'{change.field}[{change.index}] -> {change.value}'
        else: raise SaveError('This edit category is not yet supported.')
        before=document.plaintext[offset:offset+len(after)]
        if before!=after: patches.append(Patch(offset,before,after,reason))
    for index,requested in item_changes.items():
        item=ITEMS[index];record=fields(document.records('EquipItemDataArray')[index])
        expected='EEquipItemID::'+item['enum']
        old_enum=record['EquipItemID']['value']
        if old_enum not in ('EEquipItemID::NUM',expected):raise SaveError('Equipment ownership does not match its indexed slot.')
        owned=requested.get('Owned',old_enum==expected)
        if type(owned) is not bool:raise SaveError('Item ownership requires a boolean.')
        value=requested.get('Value',record['Value']['value'])
        if 'Value' in requested:
            if item['kind']!='normal' or index not in ITEM_CAPS:raise SaveError('The maximum for this item has not been verified.')
            if type(value) is not int or not 1<=value<=ITEM_CAPS[index]:raise SaveError(f'{item["name"]} must be1–{ITEM_CAPS[index]}.')
            if 'Owned' not in requested:owned=True
        if not owned:value=0
        elif item['kind']=='rare':value=0
        elif value==0:value=1  # Actual generator minimum: random1..ValueRand in tier0.
        new_enum=expected if owned else 'EEquipItemID::NUM'
        encoded=new_enum.encode('utf-8')+b'\0'
        add_property(record['EquipItemID'],struct.pack('<i',len(encoded))+encoded,f'{item["name"]}: owned -> {owned}')
        add_property(record['Value'],struct.pack('<i',value),f'{item["name"]}: value -> {value}')
    for weapon_id,weapon in unique_changes.items():
        for array,index,data_id in [('UniqueWeaponDataArray',weapon['unique_save_index'],weapon['data_id']),
                                    ('CollectedWeaponDataArray',weapon_id,weapon_id)]:
            record=fields(document.records(array)[index])
            if record['WeaponID']['value']!='EWeaponID::NUM':
                if record['WeaponID']['value']!=weapon['weapon_enum']:raise SaveError('Unique weapon slot has an unexpected owner.')
                continue  # Preserve owned/fused attributes and acquisition timestamps.
            for name in ('ID','WeaponID'):
                value=weapon['weapon_enum'].encode()+b'\0'
                add_property(record[name],struct.pack('<i',len(value))+value,f'{weapon["weapon_name"]}: acquire in {array}')
            if record['Attr']['type']!='Int64Property':raise SaveError('Unsupported weapon attribute representation.')
            if not (array=='UniqueWeaponDataArray' and any(c.category=='weapon_element' and c.index==10000+index for c in changes)):
                add_property(record['Attr'],struct.pack('<q',weapon['attribute_bitmask']),f'{weapon["weapon_name"]}: shipped attribute bitmask')
            add_property(record['DataID'],struct.pack('<i',data_id),f'{weapon["weapon_name"]}: indexed DataID')
            skills=record['Skill']['value']['records']
            if len(skills)!=9 or len(weapon['skill_slots'])!=9:raise SaveError('Unsupported unique weapon skill slots.')
            for slot,template in zip(skills,weapon['skill_slots']):
                f=fields(slot);item_id=template['item_id']
                enum='EEquipItemID::NUM' if item_id==100 else 'EEquipItemID::'+ITEMS[item_id]['enum']
                for name,value in [('EquipItemID',enum),('GuardEquipItemID','EGuardEquipItemID::NUM')]:
                    if name=='EquipItemID' and array=='UniqueWeaponDataArray' and any(c.category=='weapon_roll' and c.index==10000+index for c in changes):continue
                    encoded=value.encode()+b'\0'
                    add_property(f[name],struct.pack('<i',len(encoded))+encoded,f'{weapon["weapon_name"]}: stock skill ID')
                if not (array=='UniqueWeaponDataArray' and any(c.category=='weapon_roll' and c.index==10000+index for c in changes)):
                    add_property(f['Value'],struct.pack('<i',template['value']),f'{weapon["weapon_name"]}: stock skill value')
    bodyguard_editor.plan_bodyguard_changes(document,changes,add_property)
    officer_weapon_editor.plan_weapon_roll_changes(document,changes,add_property)
    for offset,delta in size_deltas.items():
        before=document.plaintext[offset:offset+4]
        value=struct.unpack('<i',before)[0]+delta
        patches.append(Patch(offset,before,struct.pack('<i',value),'Regenerate enclosing tagged-property byte size'))
    patches.sort(key=lambda p:p.offset)
    for a,b in zip(patches,patches[1:]):
        if a.offset+len(a.before)>b.offset: raise SaveError('Overlapping patches.')
    return patches

def serialize(document: SaveDocument, changes: list[Change]=()) -> tuple[bytes,dict]:
    fresh=parse_bytes(document.encrypted,document.source)
    if fresh.plaintext!=document.plaintext or fresh.parsed!=document.parsed:
        raise SaveError('Document bytes or offsets changed outside verified edit operations.')
    patches=plan_changes(document,list(changes))
    original_payload_size=struct.unpack_from('>I',document.plaintext)[0]
    plain=bytearray(document.plaintext[:4+original_payload_size])
    for p in reversed(patches):
        if plain[p.offset:p.offset+len(p.before)]!=p.before: raise SaveError('Stale patch data.')
        plain[p.offset:p.offset+len(p.before)]=p.after
    payload_size=len(plain)-4
    struct.pack_into('>I',plain,0,payload_size)
    plain.extend(bytes((-len(plain))%16))
    raw=save_codec.encrypt(bytes(plain))
    reread=parse_bytes(raw)
    if reread.plaintext!=bytes(plain): raise SaveError('Edited save failed decode validation.')
    changed_blocks=[i//16 for i in range(0,max(len(raw),len(document.encrypted)),16) if raw[i:i+16]!=document.encrypted[i:i+16]]
    resized=payload_size!=original_payload_size
    if not resized:
        # Enum replacements can relocate fields but cancel in total length.
        # Compare the complete plaintext, rather than assuming old offsets
        # still describe every changed byte in that equal-size result.
        expected_blocks=sorted({i//16 for i,(before,after) in enumerate(zip(document.plaintext,plain)) if before!=after})
        if changed_blocks!=expected_blocks: raise SaveError('Unexpected encrypted blocks changed.')
    elif patches:
        first_block=min(p.offset for p in patches)//16
        if raw[16:first_block*16]!=document.encrypted[16:first_block*16]:
            raise SaveError('Unrelated encrypted prefix changed during resizing.')
    audit={'source_sha256':hashlib.sha256(document.encrypted).hexdigest(),
           'output_sha256':hashlib.sha256(raw).hexdigest(),'plaintext_changes':[
               {'offset':p.offset,'old_length':len(p.before),'length':len(p.after),'before_hex':p.before.hex(),
                'after_hex':p.after.hex(),'reason':p.reason} for p in patches],
           'changed_aes_blocks':changed_blocks,'source_payload_size':original_payload_size,'output_payload_size':payload_size,
           'resized':resized,'fields_relocated':any(len(p.before)!=len(p.after) for p in patches),'unchanged_bytes_preserved':True,
           'game_load_validation':'not performed'}
    return raw,audit

def _atomic_write(data: bytes,path: Path,overwrite=False,expected_bytes=None):
    path=safe_path(path)
    if path.exists() and not overwrite: raise FileExistsError('Destination exists.')
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with temp.open('xb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        if temp.read_bytes()!=data: raise SaveError('Temporary output verification failed.')
        if overwrite:
            if expected_bytes is None:
                raise SaveError('Replacing a copy requires the bytes that were backed up.')
            # Recheck immediately before commit: serialization/report creation
            # can take time, during which another editor may change the copy.
            with path.open('rb') as stream:
                current=stream.read(MAX_SIZE+1)
            if current!=expected_bytes:
                raise SaveError('The destination changed while saving. Reopen it before replacing it.')
            os.replace(temp,path)
        else:
            # On Windows os.rename fails if destination exists, including races.
            # It also works on FAT/exFAT, which lack hard links.
            if os.name!='nt':raise SaveError('Safe publishing is supported on Windows only.')
            os.rename(temp,path)
    finally:
        if temp.exists(): temp.unlink()
    return path

def backup_save(document: SaveDocument,folder: Path | None=None) -> Path:
    if document.source is None and folder is None: raise SaveError('Select a backup folder.')
    folder=Path(folder) if folder else document.source.parent/'DW3EditorBackups'
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path=folder/f'GameStatusData.{stamp}.{uuid.uuid4().hex[:8]}.sav'
    path=_atomic_write(document.encrypted,path)
    metadata={'size_bytes':len(document.encrypted),'sha256':hashlib.sha256(document.encrypted).hexdigest()}
    try:
        _atomic_write(json.dumps(metadata,indent=2).encode(),path.with_suffix('.json'))
    except Exception:
        # Only this newly created, uniquely named incomplete backup is removed.
        try:path.unlink()
        except OSError:pass
        raise
    return path

def write_save(document: SaveDocument,path: Path,changes: list[Change]=(),overwrite=False) -> tuple[Path,dict]:
    path=safe_path(path)
    if path.suffix.lower()!='.sav':raise SaveError('Edited saves must use the .sav extension.')
    expected_bytes=None
    if document.source and path==document.source:
        if not overwrite: raise SaveError('Replacing the opened copy requires confirmation.')
        if not path.exists() or read_save(path).encrypted!=document.encrypted:
            raise SaveError('The opened copy changed on disk. Reopen it before replacing it.')
        backup_save(document)
        expected_bytes=document.encrypted
    elif path.exists() and overwrite:
        previous=read_save(path)
        backup_save(previous)
        expected_bytes=previous.encrypted
    else:
        # A destination that did not exist at selection time may appear later.
        # Never replace such a file; it was neither reviewed nor backed up.
        overwrite=False
    raw,audit=serialize(document,changes)
    # Prepare the change report before the save's final commit. If report
    # creation fails, the destination is still untouched. Never raise an
    # "unsaved" error after a successful save commit.
    audit_path=path.with_name(path.name+'.'+uuid.uuid4().hex[:8]+'.changes.json')
    _atomic_write(json.dumps(audit,indent=2).encode(),audit_path)
    try:
        _atomic_write(raw,path,overwrite,expected_bytes=expected_bytes)
    except Exception:
        try:
            audit_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return path,audit

def restore_backup(backup: Path,destination: Path) -> Path:
    backup=safe_path(backup)
    destination=safe_path(destination)
    if Path(destination).suffix.lower()!='.sav':raise SaveError('Restore to a new .sav copy.')
    raw=read_save(backup).encrypted
    manifest=safe_path(backup.with_suffix('.json'))
    with manifest.open('rb') as stream:
        data=stream.read(4097)
    if len(data)>4096:raise SaveError('Backup manifest exceeds the supported size.')
    try:metadata=json.loads(data)
    except (ValueError,UnicodeError) as error:raise SaveError('Backup manifest is damaged.') from error
    if not isinstance(metadata,dict):raise SaveError('Backup manifest must contain an object.')
    if metadata.get('sha256')!=hashlib.sha256(raw).hexdigest() or metadata.get('size_bytes')!=len(raw):
        raise SaveError('Backup hash or size does not match its manifest.')
    return _atomic_write(raw,destination)
