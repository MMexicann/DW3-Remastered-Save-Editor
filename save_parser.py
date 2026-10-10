"""Bounded structural parsing, with preserved compatibility-only gameplay data.

Tagged arrays carry their own lengths. A particular player's record count and
growth choices are not the schema: strict edit rules belong to the writer.
"""
from pathlib import Path, PureWindowsPath
import json
import os
import re
from models import SaveDocument, SaveError, fields
import save_codec
import unreal
import bodyguard_growth
from bodyguard_editor import GUARD_WEAPONS, GUARD_ITEMS, validate_saved_skills, validate_skills

MAX_SIZE=16*1024*1024
ENUMS={name:set(values) for name,values in json.loads((Path(__file__).resolve().parent/'native_enums.json').read_text()).items()}
ORDINARY_ITEMS={row['id']:row for row in json.loads((Path(__file__).resolve().parent/'game_metadata.json').read_text(encoding='utf-8'))['items']}
ORDINARY_CAPS={int(key):value for key,value in json.loads((Path(__file__).resolve().parent/'item_limits.json').read_text())['maxima'].items()}
ARRAY_LAYOUTS = {
    'PCSaveDataArray': 'PCSaveData',
    'EquipItemDataArray': 'EquipItemSaveData',
    'GuardEquipItemDataArray': 'EquipItemSaveData',
    'WeaponDataArray': 'WeaponSaveData',
    'UniqueWeaponDataArray': 'WeaponSaveData',
    'CollectedWeaponDataArray': 'WeaponSaveData',
    'GuardWeaponDataArray': 'WeaponSaveData',
    'GuardDataArray': 'GuardSaveData',
    'CanUseCharaArray': None,
    'CanUseScenarioArray': None,
}
# Documentation only: these are initial inventory capacities, not save validity.
INITIAL_COUNTS = {'PCSaveDataArray': 50, 'EquipItemDataArray': 100,
                  'WeaponDataArray': 500, 'UniqueWeaponDataArray': 84,
                  'CollectedWeaponDataArray': 255, 'GuardWeaponDataArray': 100,
                  'GuardEquipItemDataArray': 10, 'CanUseCharaArray': 50,
                  'CanUseScenarioArray': 156}


def _array(prop, expected_type, label):
    if prop is None or prop['type'] != expected_type or not isinstance(prop['value'], dict):
        raise SaveError(f'Unsupported {label} layout.')
    value = prop['value']
    key = 'records' if 'StructProperty(' in expected_type else 'values'
    if (type(value.get('count')) is not int or not isinstance(value.get(key), list)
            or value['count'] != len(value[key])):
        raise SaveError(f'Incomplete {label} array.')
    if expected_type == 'ArrayProperty(IntProperty)':
        if prop['data_size'] != 4 + 4 * value['count'] or any(type(v) is not int for v in value[key]):
            raise SaveError(f'Unsupported {label} integer array.')
    elif expected_type == 'ArrayProperty(BoolProperty)':
        if prop['data_size'] != 4 + value['count'] or any(type(v) is not int or v not in (0, 1) for v in value[key]):
            raise SaveError(f'Unsupported {label} boolean array.')
    return value[key]


def _number(prop, expected_type, size, label):
    if prop is None or prop['type'] != expected_type or prop['data_size'] != size:
        raise SaveError(f'Unsupported {label} field layout.')


def _enum(prop, enum_name, label, warn):
    if (prop is None or not prop['type'].startswith(f'EnumProperty({enum_name}(')
            or not isinstance(prop['value'], str)
            or not re.fullmatch(re.escape(enum_name) + r'::[A-Za-z_][A-Za-z0-9_]*', prop['value'])):
        raise SaveError(f'Unsupported {label} identity representation.')
    if prop['value'] not in ENUMS[enum_name]:
        warn(f'{label} uses an unrecognized {enum_name} value; it will be preserved.')


def _equipment(record, label, warn):
    f = fields(record)
    _number(f.get('Value'), 'IntProperty', 4, label + ' value')
    _enum(f.get('EquipItemID'), 'EEquipItemID', label, warn)
    _enum(f.get('GuardEquipItemID'), 'EGuardEquipItemID', label, warn)
    return f


def _validate_document(doc):
    warnings = []
    def warn(message):
        if message not in warnings:
            warnings.append(message)
    def check_primitive_arrays(properties):
        for prop in properties:
            value = prop['value']
            if prop['type'] in ('ArrayProperty(BoolProperty)', 'ArrayProperty(IntProperty)'):
                _array(prop, prop['type'], prop['name'])
            if isinstance(value, list) and value and isinstance(value[0], dict):
                check_primitive_arrays(value)
            elif isinstance(value, dict) and isinstance(value.get('records'), list):
                for record in value['records']:
                    check_primitive_arrays(record)
    check_primitive_arrays(doc.parsed['properties'])
    for name, struct_name in ARRAY_LAYOUTS.items():
        expected = ('ArrayProperty(BoolProperty)' if struct_name is None else
                    f'ArrayProperty(StructProperty({struct_name}(/Script/Refine)))')
        _array(doc.properties.get(name), expected, name)
    for index, record in enumerate(doc.records('PCSaveDataArray')):
        f = fields(record)
        for name in ('MaxHealth', 'MaxMusou', 'Attack', 'Defence', 'WeaponDataID', 'SPoint', 'Progress', 'BGTeamID', 'MemCnt'):
            _number(f.get(name), 'IntProperty', 4, f'officer {index} {name}')
        _enum(f.get('BGMusouEquipItem'), 'EGuardEquipItemID', f'officer {index} companion item', warn)
    for name in ('EquipItemDataArray', 'GuardEquipItemDataArray'):
        for index, record in enumerate(doc.records(name)):
            f = _equipment(record, f'{name} slot {index}', warn)
            row = (ORDINARY_ITEMS if name == 'EquipItemDataArray' else GUARD_ITEMS).get(index)
            if row is None:
                continue  # Untouched reserved/future item records are opaque to editing.
            ordinary = name == 'EquipItemDataArray'
            enum_name = 'EquipItemID' if ordinary else 'GuardEquipItemID'
            other = 'GuardEquipItemID' if ordinary else 'EquipItemID'
            expected = 'EEquipItemID::' + row['enum'] if ordinary else row['enum']
            sentinel = 'EEquipItemID::NUM' if ordinary else 'EGuardEquipItemID::NUM'
            other_sentinel = 'EGuardEquipItemID::NUM' if ordinary else 'EEquipItemID::NUM'
            if f[other]['value'] != other_sentinel or f[enum_name]['value'] not in (sentinel, expected):
                warn(f'{name} slot {index} has an unrecognized item placement; preserve it without editing.')
            owned, value = f[enum_name]['value'] == expected, f['Value']['value']
            maximum = ORDINARY_CAPS.get(index, 0) if ordinary else row['max_value']
            if ((not owned or row['kind'] == 'rare') and value != 0 or
                    owned and row['kind'] == 'normal' and not 1 <= value <= maximum):
                if owned and row['kind']=='normal' and value>maximum:
                    warn(f'{row["name"]} has saved value {value}, above the normal drop maximum {maximum}. Max actions preserve this value.')
                else:
                    warn(f'{row["name"]} has an unfamiliar saved value {value}; it is preserved unless explicitly edited.')
    for index, record in enumerate(doc.records('GuardDataArray')):
        f = fields(record)
        _number(f.get('SPoint'), 'IntProperty', 4, f'bodyguard team {index} Merit')
        levels = _array(f.get('BGLevels'), 'ArrayProperty(IntProperty)', f'bodyguard team {index} growth')
        weapons = _array(f.get('MemberWeapon'), 'ArrayProperty(IntProperty)', f'bodyguard team {index} weapon choices')
        _enum(f.get('MemberItem'), 'EGuardEquipItemID', f'bodyguard team {index} item', warn)
        if len(weapons) != 10:
            warn(f'Bodyguard team {index} has an unfamiliar weapon-choice array; preserve its layout.')
        try:
            bodyguard_growth.validate_saved_growth(f['SPoint']['value'], levels)
        except ValueError as error:
            warn(f'Bodyguard team {index} has growth outside the supported profile: {error}')
        else:
            try:
                bodyguard_growth.validate_growth(f['SPoint']['value'], levels)
            except ValueError:
                warn(f'Bodyguard team {index} has saved growth that differs from automatic allocation gates. Existing levels are preserved.')
    for name in ('WeaponDataArray', 'UniqueWeaponDataArray', 'CollectedWeaponDataArray', 'GuardWeaponDataArray'):
        for index, record in enumerate(doc.records(name)):
            label = f'{name} slot {index}'
            f = fields(record)
            _number(f.get('DataID'), 'IntProperty', 4, label + ' DataID')
            _number(f.get('Attr'), 'Int64Property', 8, label + ' attributes')
            _number(f.get('GetTime'), 'DoubleProperty', 8, label + ' acquired time')
            for field in ('ID', 'WeaponID'):
                _enum(f.get(field), 'EWeaponID', label, warn)
            skills = _array(f.get('Skill'), 'ArrayProperty(StructProperty(EquipItemSaveData(/Script/Refine)))', label + ' skills')
            if len(skills) != 9:
                warn(f'{label} has an unfamiliar skill-slot count; its full record is preserved.')
            for slot in skills:
                _equipment(slot, label + ' bonus', warn)
            if name == 'GuardWeaponDataArray':
                allowed = {row['enum'] for row in GUARD_WEAPONS.values()} | {'EWeaponID::NUM'}
                if (f['WeaponID']['value'] not in allowed or f['ID']['value'] != f['WeaponID']['value']
                        or f['WeaponID']['value'] != 'EWeaponID::NUM' and f['DataID']['value'] != index
                        or f['Attr']['value'] != 0
                        or any(fields(slot)['EquipItemID']['value'] != 'EEquipItemID::NUM' for slot in skills)):
                    warn(f'{label} uses an unsupported bodyguard weapon profile; keep this copy view-only.')
                item_ids = {row['enum']: item_id for item_id, row in GUARD_ITEMS.items()}
                weapon_ids = {row['enum']: weapon_id for weapon_id, row in GUARD_WEAPONS.items()}
                bonuses = []
                try:
                    for slot in skills:
                        saved = fields(slot)
                        item_enum = saved['GuardEquipItemID']['value']
                        if item_enum == 'EGuardEquipItemID::NUM':
                            if saved['Value']['value'] != 0:
                                raise SaveError('Nonzero empty bonus.')
                        elif item_enum not in item_ids:
                            raise SaveError('Unknown bonus identity.')
                        else:
                            bonuses.append({'id': item_ids[item_enum], 'value': saved['Value']['value']})
                    if f['WeaponID']['value'] == 'EWeaponID::NUM':
                        if bonuses:
                            raise SaveError('Bonuses in an unused inventory slot.')
                    elif f['WeaponID']['value'] in weapon_ids:
                        validate_saved_skills(bonuses)
                        validate_skills(weapon_ids[f['WeaponID']['value']], bonuses)
                except SaveError:
                    warn(f'{label} has bonuses outside the supported authoring profile; this copy is view-only and preserved.')
    item_ids = {row['enum']: item_id for item_id, row in GUARD_ITEMS.items()}
    weapons = doc.records('GuardWeaponDataArray')
    items = doc.records('GuardEquipItemDataArray')
    weapon_rows = {row['enum']: row for row in GUARD_WEAPONS.values()}
    for index, record in enumerate(doc.records('GuardDataArray')):
        team = fields(record)
        item_enum = team['MemberItem']['value']
        if item_enum in item_ids:
            item_id = item_ids[item_enum]
            if item_id >= len(items) or fields(items[item_id])['GuardEquipItemID']['value'] != item_enum:
                warn(f'Bodyguard team {index} has an unavailable item reference; preserve it unless explicitly changing equipment.')
        for family, slot in enumerate(team['MemberWeapon']['value']['values'][:5]):
            if slot == -1:
                continue
            valid = 0 <= slot < len(weapons)
            if valid:
                weapon = fields(weapons[slot])
                row = weapon_rows.get(weapon['WeaponID']['value'])
                valid = row is not None and row['family_index'] == family
            if not valid:
                warn(f'Bodyguard team {index} has an unknown weapon reference; preserve it unless explicitly changing equipment.')
    doc.compatibility_warnings = warnings


# Keep the public DW3 path API; all games share the same copy-only policy.
from save_safety import safe_path, reserved_windows_path as _reserved_windows_path


def parse_bytes(raw: bytes, source: Path | None=None) -> SaveDocument:
    try:
        plain=save_codec.decrypt(raw)
        parsed=unreal.parse(plain)
        h=parsed['header']
        # Engine build/patch numbers are descriptive. Serialization versions,
        # complete property tags and the save class determine our contract.
        if ((h['save_version'],h['ue4_version'],h['ue5_version'],h['custom_version_format'],h['save_class']) != (
                3,522,1017,3,'/Script/Refine.GameStatusSaveGame') or h['engine'][0] != 5):
            raise SaveError('This save version is not supported yet.')
        if parsed['trailer_hex']!='00000000':
            raise SaveError('Unsupported UObject trailer.')
        doc=SaveDocument(source,raw,plain,parsed)
        if len(doc.properties)!=len(parsed['properties']):
            raise SaveError('Duplicate top-level properties.')
        _validate_document(doc)
        if h['engine'] != [5,6,1]:
            doc.compatibility_warnings.append('The engine build differs from the verified release; compatible property layouts are preserved.')
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
