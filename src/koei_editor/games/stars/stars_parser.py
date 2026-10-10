"""Narrow source-backed All-Stars PC available-gold editor.

Native serializers establish packed offsets, grant/spend paths distinguish
available gold from lifetime earnings, and a private genuine save corroborates
the current profile. Story, rewards, cards and hero progression are preserved.
"""
from dataclasses import dataclass
from functools import lru_cache
import hashlib
from pathlib import Path
import struct
from types import MappingProxyType

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.stars import stars_codec as codec
from koei_editor.shared.copy_storage import atomic_new, restore_snapshot, snapshot_backup
from koei_editor.shared.save_safety import safe_path
from koei_editor.shared.verified_editor import Field

GAME_ID, SAVE_SIZE = 'stars', codec.SAVE_SIZE
GOLD_OFFSET, LIFETIME_GOLD_OFFSET, GOLD_MAXIMUM = 0x2F6A, 0x1CE, 9_999_999
ACTIVE_HERO_OFFSET = 0xA3C
MATERIAL_OFFSET, MATERIAL_COUNT, MATERIAL_MAXIMUM = 0x2F10, 45, 9_999
FIELDS = tuple(Field(f'slot_{index}_gold', 'Available gold',
                     codec.SYSTEM_PAYLOAD_SIZE + index * codec.SLOT_PAYLOAD_SIZE + GOLD_OFFSET,
                     4, GOLD_MAXIMUM, 'Campaign gold', index + 1)
               for index in range(codec.SLOT_COUNT))
MATERIAL_FIELDS = tuple(Field(f'slot_{slot}_material_{identity}',
                             f'Material ID {identity}: Quantity',
                             codec.SYSTEM_PAYLOAD_SIZE + slot * codec.SLOT_PAYLOAD_SIZE
                             + MATERIAL_OFFSET + 2 * identity,
                             2, MATERIAL_MAXIMUM, 'Materials', slot + 1,
                             minimum=1, maxable=False)
                        for slot in range(codec.SLOT_COUNT) for identity in range(MATERIAL_COUNT))


@dataclass(frozen=True)
class Format:
    id: str
    title: str
    size: int
    fields: tuple
    note: str
    sample_verified: bool = True
    game_load_verified: bool = False


FORMAT = Format(GAME_ID, 'Warriors All-Stars (PC)', SAVE_SIZE, FIELDS + MATERIAL_FIELDS,
                'Current native PC revision: available gold and existing ordinary '
                'material quantities by numeric ID in nine campaign slots; '
                'lifetime earned gold is inspected separately. Hero progression, '
                'cards, material acquisition, regard, requests, routes and reward history remain '
                'read only. Genuine parsing and unchanged reconstruction are verified; '
                'edited game-load validation has not been performed by this project.')


@dataclass(frozen=True)
class Document:
    format: Format
    source: Path
    raw: bytes
    payload: bytes

    @property
    def sha256(self):
        return hashlib.sha256(self.raw).hexdigest()


def get_format(game_id=GAME_ID):
    if game_id != GAME_ID:
        raise SaveError('Select the Warriors All-Stars native Windows PC adapter.')
    return FORMAT


def decode(raw, game_id=GAME_ID, source=None):
    get_format(game_id)
    payload, _ = codec.decode(raw)
    return Document(FORMAT, Path(source) if source is not None else Path('all-stars-copy.bin'),
                    bytes(raw), payload)


def read_save(path, game_id=GAME_ID):
    get_format(game_id)
    path = safe_path(path)
    if path.suffix.lower() != '.bin':
        raise SaveError('Open a separate SAVEDATA.BIN copy.')
    with path.open('rb') as stream:
        raw = stream.read(SAVE_SIZE + 1)
    return decode(raw, game_id, path)


def validate_document(document):
    if (type(document) is not Document or document.format is not FORMAT
            or type(document.raw) is not bytes or type(document.payload) is not bytes):
        raise SaveError('An immutable native All-Stars snapshot is required.')
    if codec.decode(document.raw)[0] != document.payload:
        raise SaveError('The opened All-Stars snapshot was changed outside the edit workflow.')


@lru_cache(maxsize=4)
def _fields(payload):
    # Save-preview routine44A2B0 accepts a selected hero in the fixed100-record
    # array. Empty -1 and unknown IDs do not authorize creating a campaign.
    qualified = {field.slot for field in FIELDS
                 if 0 <= struct.unpack_from('<h', payload,
                         codec.SYSTEM_PAYLOAD_SIZE + (field.slot - 1) * codec.SLOT_PAYLOAD_SIZE
                         + ACTIVE_HERO_OFFSET)[0] < 100}
    return (tuple(field for field in FIELDS if field.slot in qualified)
            + tuple(field for field in MATERIAL_FIELDS if field.slot in qualified
                    and field.minimum <= field.value(payload) <= field.maximum))


def fields_for(document):
    validate_document(document)
    return _fields(document.payload)


def field_map(document):
    return MappingProxyType({field.id: field for field in fields_for(document)})


def _validate_edit(field, value, original):
    if type(value) is not int:
        raise SaveError('A whole-number resource value is required.')
    if value != original:
        field.validate(value)


def changed_payload(document, changes):
    mapping = field_map(document)
    result = bytearray(document.payload)
    for key, value in changes.items():
        field = mapping.get(key)
        if field is None:
            raise SaveError('Only qualified campaign gold and existing ordinary materials are writable.')
        _validate_edit(field, value, field.value(document.payload))
        result[field.offset:field.offset + field.size] = value.to_bytes(field.size, 'little')
    return bytes(result)


def stage(document, changes, key, value):
    changed_payload(document, changes)
    field = field_map(document).get(key)
    if field is None:
        raise SaveError('Only qualified campaign gold and existing ordinary materials are writable.')
    original = field.value(document.payload)
    _validate_edit(field, value, original)
    result = dict(changes)
    if value == original:
        result.pop(key, None)
    else:
        result[key] = value
    return result


def serialize(document, changes):
    return codec.encode(document.raw, changed_payload(document, changes))


def limit_values(document, changes, keys):
    changed_payload(document, changes)
    mapping = field_map(document)
    result = {}
    for key in keys:
        if key not in mapping:
            raise SaveError('Only qualified campaign gold and existing ordinary materials are writable.')
        field = mapping[key]
        current = changes.get(key, field.value(document.payload))
        if field.maxable and field.minimum <= current <= field.maximum:
            result[key] = field.maximum
    return result


def maximums(document, changes, group=None):
    changed_payload(document, changes)
    result = dict(changes)
    keys = [field.id for field in fields_for(document) if group is None or field.group == group]
    for key, value in limit_values(document, changes, keys).items():
        result = stage(document, result, key, value)
    return result


def review(document, changes):
    changed_payload(document, changes)
    return [(field, field.value(document.payload), changes[field.id])
            for field in fields_for(document) if field.id in changes]


def backup(document):
    validate_document(document)
    return snapshot_backup(document.raw, document.source, GAME_ID,
                           document.source.parent / 'WarriorsEditorBackups')


def save_as(document, changes, destination):
    destination = safe_path(destination)
    if destination.suffix.lower() != '.bin':
        raise SaveError('Choose a new .bin destination.')
    if destination.exists():
        raise FileExistsError('Choose a new file; existing files are never replaced.')
    validate_document(document)
    with safe_path(document.source).open('rb') as stream:
        if stream.read(SAVE_SIZE + 1) != document.raw:
            raise SaveError('The opened copy changed on disk. Reopen it before saving.')
    raw = serialize(document, changes)
    backup(document)
    atomic_new(raw, destination)
    return decode(raw, GAME_ID, destination)


def restore(backup_path, destination, game_id=GAME_ID):
    get_format(game_id)
    return restore_snapshot(backup_path, destination, GAME_ID, '.bin', SAVE_SIZE,
                            validate_raw=lambda raw: decode(raw, game_id))


def record_label(slot, group='Campaign gold'):
    return f'Campaign slot {slot}' if group in ('Campaign gold', 'Materials') else group


def field_hint(document, field):
    key = field.id if isinstance(field, Field) else field
    mapped = field_map(document)[key]
    if mapped.group == 'Materials':
        return ('Existing material quantity only, 1..9,999. Zero, unknown higher '
                'values and empty campaigns remain read only. Numeric material '
                'IDs are shown because names are not yet mapped. Quantity edits '
                'preserve acquisition, request and reward history. Bulk Max leaves materials unchanged.')
    return ('Available gold balance, 0..9,999,999. Max preserves higher opened '
            'values. Editing the balance does not grant lifetime earnings, '
            'request rewards or achievement progress. Story and equipment stay unchanged.')


def inspection_rows(document):
    validate_document(document)
    revision, selected, secondary = struct.unpack_from('<3I', document.payload)
    rows = [{'group': 'System history', 'label': 'Native profile',
             'value': f'Revision 0x{revision:08X}; current campaign slot {selected + 1}; '
                      f'secondary campaign selection {secondary + 1}'},
            {'group': 'System history', 'label': 'Lifetime earned gold',
             'value': f'{struct.unpack_from("<I", document.payload, LIFETIME_GOLD_OFFSET)[0]:,} '
                      '(read only; distinct from spendable campaign balances)'}]
    qualified = {field.id for field in fields_for(document)}
    for field in FIELDS:
        hero = struct.unpack_from('<h', document.payload, codec.SYSTEM_PAYLOAD_SIZE
                                  + (field.slot - 1) * codec.SLOT_PAYLOAD_SIZE + ACTIVE_HERO_OFFSET)[0]
        rows.append({'group': 'Campaign gold', 'label': record_label(field.slot),
                     'value': f'Available gold {field.value(document.payload):,}; selected hero ID {hero}; '
                              f'qualified campaign: {field.id in qualified}'})
    for field in MATERIAL_FIELDS:
        value = field.value(document.payload)
        if value:
            identity = (field.offset - codec.SYSTEM_PAYLOAD_SIZE
                        - (field.slot - 1) * codec.SLOT_PAYLOAD_SIZE - MATERIAL_OFFSET) // 2
            rows.append({'group': 'Materials', 'label': f'{record_label(field.slot, "Materials")} / Material ID {identity}',
                         'value': f'Quantity {value:,}; editable existing stack: {field.id in qualified}'})
    return tuple(rows)


# No checksum covers serialized gameplay bytes. The codec still verifies all
# native encrypted fingerprints; these do not provide payload integrity.
INTEGRITY_KIND = 'none'
