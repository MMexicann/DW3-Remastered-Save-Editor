"""Remove between-stage Musou saves using the shipped native defaults.

Records stay in their original positions: the game uses their array index as
the save-slot identity. Permanent stats, clear flags and battle records live
outside this array and are never changed by these actions.
"""
from datetime import datetime, timedelta
from pathlib import Path
import json
import struct

from models import Change, SaveError, fields

CATEGORIES = {'musou_slot'}
ARRAY = 'EngiSaveDataArray'
EMPTY_OFFICER = 'EPlayerCharaID::NUM'
ROOT = Path(__file__).resolve().parent
OFFICERS = {'EPlayerCharaID::' + r['enum']: r for r in
            json.loads((ROOT / 'game_metadata.json').read_text(encoding='utf-8'))['officers']}
RECORD_FIELDS = {'CharaID', 'NowStage', 'EventFlag', 'StageSPoint', 'ClearTime',
                 'KOData', 'isClearChara', 'PCColor', 'GuardNum', 'SaveDate', 'isNewMusouMode'}


def _schema(prop, kind, size=None):
    if (not isinstance(prop, dict) or prop.get('type') != kind or
            prop.get('array_index') != 0 or
            (size is not None and prop.get('data_size') != size)):
        raise SaveError('The campaign slot uses an unsupported property layout.')


def _int_array(prop, count):
    _schema(prop, 'ArrayProperty(IntProperty)', 4 + count * 4)
    value = prop.get('value')
    if (not isinstance(value, dict) or value.get('count') != count or
            not isinstance(value.get('values'), list) or len(value['values']) != count or
            any(type(v) is not int for v in value['values'])):
        raise SaveError('The campaign slot uses an unsupported growth/history array.')


def _bool(prop):
    _schema(prop, 'BoolProperty', 0)
    if type(prop.get('value')) is not bool or prop.get('flags') not in (0, 0x10):
        raise SaveError('The campaign slot uses an unsupported boolean layout.')


def _record_schema(record):
    props = fields(record)
    if set(props) != RECORD_FIELDS:
        raise SaveError('This campaign slot has missing or unknown fields and is view-only.')
    _schema(props['CharaID'], 'EnumProperty(EPlayerCharaID(/Script/Refine),ByteProperty)')
    officer = props['CharaID']['value']
    if officer != EMPTY_OFFICER and officer not in OFFICERS:
        raise SaveError('This campaign slot has an unknown officer and is view-only.')
    for name in ('NowStage', 'EventFlag', 'PCColor'):
        _schema(props[name], 'IntProperty', 4)
        if type(props[name]['value']) is not int:
            raise SaveError('Unsupported campaign scalar.')
    for name in ('StageSPoint', 'ClearTime'):
        _int_array(props[name], 10)
    _int_array(props['GuardNum'], 2)
    for name in ('isClearChara', 'isNewMusouMode'):
        _bool(props[name])
    _schema(props['SaveDate'], 'StructProperty(DateTime(/Script/CoreUObject))', 8)
    ko = props['KOData']
    _schema(ko, 'ArrayProperty(StructProperty(KOData(/Script/Refine)))')
    value = ko.get('value')
    if (not isinstance(value, dict) or value.get('count') != 10 or
            not isinstance(value.get('records'), list) or len(value['records']) != 10):
        raise SaveError('Unsupported campaign KO history array.')
    for record in value['records']:
        entry = fields(record)
        if set(entry) != {'KOCnt', 'KOCommanderList', 'isGekiMusou'}:
            raise SaveError('The campaign KO history contains unknown fields.')
        _schema(entry['KOCnt'], 'IntProperty', 4)
        if type(entry['KOCnt']['value']) is not int:
            raise SaveError('Unsupported campaign KO count.')
        _bool(entry['isGekiMusou'])
        commanders = entry['KOCommanderList']
        _schema(commanders, 'ArrayProperty(EnumProperty(EUnitTypeID(/Script/Refine),UInt16Property))')
        array = commanders.get('value')
        if (not isinstance(array, dict) or type(array.get('count')) is not int or
                not isinstance(array.get('values'), list) or len(array['values']) != array['count']):
            raise SaveError('Unsupported campaign commander history.')
    return props


def _slots(document):
    prop = document.properties.get(ARRAY)
    if prop is None:
        return []
    _schema(prop, 'ArrayProperty(StructProperty(EngiSaveData(/Script/Refine)))')
    value = prop.get('value')
    if (not isinstance(value, dict) or type(value.get('count')) is not int or
            not isinstance(value.get('records'), list) or len(value['records']) != value['count']):
        raise SaveError('Unsupported Musou campaign save array.')
    return value['records']


def _requests(changes):
    indices = set()
    for change in changes:
        if change.category not in CATEGORIES:
            continue
        if (type(change.index) is not int or change.index < 0 or
                change.field != 'Remove' or change.value is not True):
            raise SaveError('Campaign slots support only explicit Remove actions.')
        if change.index in indices:
            raise SaveError('Duplicate campaign slot removals.')
        indices.add(change.index)
    return indices


def remove_slot_change(index):
    if type(index) is not int or index < 0:
        raise SaveError('Choose an existing campaign slot.')
    return Change('musou_slot', index, 'Remove', True)


def _date(document, prop):
    if not prop or prop.get('data_size') != 8:
        return ''
    try:
        ticks = struct.unpack_from('<q', document.plaintext, prop['data_offset'])[0]
        return (datetime(1, 1, 1) + timedelta(microseconds=ticks // 10)).isoformat(' ', timespec='seconds') if ticks > 0 else ''
    except (ValueError, OverflowError, struct.error, KeyError):
        return ''


def slot_state(document, changes=()):
    """Keep unknown layouts visible without making the whole save fail open."""
    pending = _requests(changes)
    try:
        records = _slots(document)
    except SaveError as exc:
        return {'editable': False, 'reason': str(exc), 'slots': [], 'active_count': 0}
    if any(i >= len(records) for i in pending):
        raise SaveError('This campaign slot is absent from the save.')
    rows = []
    for index, record in enumerate(records):
        props = fields(record)
        reason = ''
        try:
            _record_schema(record)
            editable = True
        except SaveError as exc:
            reason, editable = str(exc), False
        enum = props.get('CharaID', {}).get('value', EMPTY_OFFICER)
        officer = OFFICERS.get(enum)
        active = enum != EMPTY_OFFICER
        if index in pending:
            if not editable:
                raise SaveError(reason)
            active = False
        stage = props.get('NowStage', {}).get('value')
        rows.append({'index': index, 'active': active, 'editable': editable, 'reason': reason,
                     'officer_id': officer['id'] if officer else None,
                     'officer_name': officer['name'] if officer else ('Empty' if not active else str(enum)),
                     'stage': stage if type(stage) is int else None,
                     'side_story': props.get('isNewMusouMode', {}).get('value') is True,
                     'saved_at': _date(document, props.get('SaveDate'))})
    return {'editable': any(r['editable'] for r in rows), 'reason': '' if rows else 'No saved campaigns.',
            'slots': rows, 'active_count': sum(r['active'] for r in rows)}


def remove_all_changes(document):
    return [remove_slot_change(r['index']) for r in slot_state(document)['slots']
            if r['active'] and r['editable']]


def original_value(document, change):
    if change.category not in CATEGORIES:
        raise SaveError('Unsupported campaign slot edit.')
    rows = slot_state(document)['slots']
    if type(change.index) is not int or not 0 <= change.index < len(rows) or change.field != 'Remove':
        raise SaveError('Choose an existing campaign slot.')
    return not rows[change.index]['active']


def plan_slot_changes(document, changes, add_property):
    indices = _requests(changes)
    if not indices:
        return
    records = _slots(document)
    for index in sorted(indices):
        if index >= len(records):
            raise SaveError('This campaign slot is absent from the save.')
        props = _record_schema(records[index])
        reason = f'Musou save slot {index + 1}: remove saved campaign'
        def boolean(prop):
            proxy = {**prop, 'data_offset': prop['flags_offset'], 'data_size': 1}
            add_property(proxy, bytes([prop['flags'] & ~0x10]), reason)
        raw = EMPTY_OFFICER.encode('utf-8') + b'\0'
        add_property(props['CharaID'], struct.pack('<i', len(raw)) + raw, reason)
        for name in ('NowStage', 'EventFlag', 'PCColor'):
            add_property(props[name], bytes(4), reason)
        for name, count in (('StageSPoint', 10), ('ClearTime', 10), ('GuardNum', 2)):
            add_property(props[name], struct.pack('<i', count) + bytes(count * 4), reason)
        add_property(props['SaveDate'], bytes(8), reason)
        for name in ('isClearChara', 'isNewMusouMode'):
            boolean(props[name])
        for ko in props['KOData']['value']['records']:
            entry = fields(ko)
            add_property(entry['KOCnt'], bytes(4), reason)
            add_property(entry['KOCommanderList'], bytes(4), reason)
            boolean(entry['isGekiMusou'])
