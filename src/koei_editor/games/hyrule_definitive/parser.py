"""Conservative source-backed decrypted export adapter; no console crypto.

Mappings and exclusions are documented in docs/SWITCH_WARRIORS_RESEARCH.md. The native
export remains immutable; serialization only touches staged, qualified scalars.
"""
from dataclasses import dataclass
from functools import lru_cache
import hashlib
from pathlib import Path
from types import MappingProxyType

from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.copy_storage import atomic_new, restore_snapshot, snapshot_backup
from koei_editor.shared.save_safety import safe_path
from koei_editor.games.hyrule_definitive.catalog import MATERIALS, FOOD, CHARACTERS, WEAPONS

GAME_ID = 'hyrule_definitive'
TITLE = 'Hyrule Warriors Definitive Edition'
SAVE_SIZE = 0x3D8E4
EXTENSION = '.bin'
BYTEORDER = 'little'
LAYOUT_MARKER = bytes.fromhex('00261015')
RUPEES_OFFSET = 0x2B8


@dataclass(frozen=True)
class Field:
    id: str
    label: str
    offset: int
    size: int
    maximum: int
    group: str = 'Resources'
    slot: int = 0
    minimum: int = 0
    maxable: bool = False

    def value(self, payload):
        return int.from_bytes(payload[self.offset:self.offset + self.size], BYTEORDER)

    def validate(self, value):
        if type(value) is not int or not self.minimum <= value <= self.maximum:
            raise SaveError(f'{self.label} requires a whole number from {self.minimum:,} to {self.maximum:,}.')


@dataclass(frozen=True)
class Format:
    id: str = GAME_ID
    title: str = TITLE
    size: int = SAVE_SIZE
    fields: tuple = (Field('rupees', 'Rupees', RUPEES_OFFSET, 4, 9_999_999),)
    sample_verified: bool = True
    note: str = ('Switch zmha.bin, observed layout marker 00261015. '
                 'Edit rupees and existing named material quantities manually; '
                 'inspect characters and fairy food. Story and ownership are preserved.')

FORMAT = Format()


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
        raise SaveError(f'Choose the explicit {TITLE} platform adapter.')
    return FORMAT


def decode(raw, game_id=GAME_ID, source=Path('zmha.bin')):
    get_format(game_id)
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != SAVE_SIZE:
        raise SaveError(f'{TITLE} requires a complete {SAVE_SIZE:,}-byte decrypted native export.')
    raw = bytes(raw)
    if raw[:4] != LAYOUT_MARKER:
        raise SaveError(f'{TITLE} export does not match the observed Switch layout marker.')
    if int.from_bytes(raw[12:16], 'little') != SAVE_SIZE:
        raise SaveError('The native stored size does not match this export profile.')
    return Document(FORMAT, Path(source), raw, raw)


def _copy_path(path):
    return safe_path(path)


def _extension(path):
    if Path(path).suffix.casefold() != EXTENSION:
        raise SaveError('Use a separate Switch zmha.bin copy outside console-managed folders.')


def read_save(path, game_id=GAME_ID):
    get_format(game_id)
    path = _copy_path(path)
    _extension(path)
    with path.open('rb') as stream:
        raw = stream.read(SAVE_SIZE + 1)
    return decode(raw, game_id, path)


def validate_document(document):
    if (type(document) is not Document or document.format != FORMAT
            or type(document.raw) is not bytes or type(document.payload) is not bytes):
        raise SaveError(f'Invalid immutable {TITLE} snapshot.')
    original = decode(document.raw, GAME_ID, document.source)
    if original.payload != document.payload:
        raise SaveError('The opened snapshot changed outside the edit workflow.')


def _uint(payload, offset, size):
    return int.from_bytes(payload[offset:offset + size], BYTEORDER)


WEAPON_BASE, WEAPON_STRIDE, WEAPON_COUNT = 0x337F4, 0x28, 1030


def weapons(document):
    validate_document(document)
    rows = []
    for index in range(WEAPON_COUNT):
        offset = WEAPON_BASE + index * WEAPON_STRIDE
        identity = _uint(document.payload, offset + 0x10, 2)
        if identity == 0xFFFF:
            continue
        rows.append({'slot': index + 1, 'id': identity,
                     'name': WEAPONS.get(identity, f'Unknown weapon ID {identity}'),
                     'power': _uint(document.payload, offset + 0x12, 2),
                     'stars': _uint(document.payload, offset + 0x14, 2),
                     'state': document.payload[offset + 0x1E],
                     'skills': tuple((document.payload[offset + 0x16 + i],
                                      _uint(document.payload, offset + i * 2, 2))
                                     for i in range(8))})
    return tuple(rows)


def _inspection(payload):
    rows = []
    for relative, name in CHARACTERS:
        offset = 0x3307A + relative
        rows.extend((
            {'group': 'Characters', 'label': name + ': stored level index (read only)',
             'value': payload[offset + 0x1A]},
            {'group': 'Characters', 'label': name + ': EXP (read only)',
             'value': _uint(payload, offset + 0x12, 4)},
            {'group': 'Characters', 'label': name + ': unlock flag (read only)',
             'value': payload[offset + 0x0A]},
        ))
    for offset, name in MATERIALS:
        rows.append({'group': 'Material inventory', 'label': name,
                     'value': _uint(payload, offset, 2)})
    for offset, name in FOOD:
        rows.append({'group': 'Fairy food', 'label': name + ' (read only)',
                     'value': payload[offset]})
    return tuple(rows)


@lru_cache(maxsize=4)
def _field_index(payload):
    fields = list(FORMAT.fields)
    for index, (offset, name) in enumerate(MATERIALS):
        # Discovery bits are not independently mapped. Preserve empty, higher
        # and unidentified slots; do not manufacture ownership or rewards.
        if 1 <= _uint(payload, offset, 2) <= 999:
            fields.append(Field(f'material_{offset:x}', name, offset, 2, 999,
                                'Material inventory', index + 1, minimum=1))
    return MappingProxyType({field.id: field for field in fields})


def field_map(document):
    validate_document(document)
    return _field_index(document.payload)


def fields_for(document):
    return tuple(field_map(document).values())


def changed_payload(document, changes):
    fields = field_map(document)
    output = bytearray(document.payload)
    for key, value in changes.items():
        if key not in fields:
            raise SaveError('This field or existing record is not qualified for edits.')
        field = fields[key]
        field.validate(value)
        output[field.offset:field.offset + field.size] = value.to_bytes(field.size, BYTEORDER)
    return bytes(output)


def serialize(document, changes):
    raw = changed_payload(document, changes)
    if decode(raw, GAME_ID, document.source).payload != raw:
        raise SaveError('Edited export failed read-back verification.')
    return raw


def stage(document, changes, key, value):
    fields = field_map(document)
    if key not in fields:
        raise SaveError('This field or existing record is not qualified for edits.')
    result = dict(changes)
    if type(value) is int and value == fields[key].value(document.payload):
        result.pop(key, None)
    else:
        fields[key].validate(value)
        result[key] = value
    return result


def limit_values(document, changes, keys):
    changed_payload(document, changes)
    fields = field_map(document)
    result = {}
    for key in keys:
        if key not in fields:
            raise SaveError('This field is not qualified for edits.')
        field = fields[key]
        current = changes.get(key, field.value(document.payload))
        if field.maxable and type(current) is int and field.minimum <= current <= field.maximum:
            result[key] = field.maximum
    return result


def maximums(document, changes, group=None):
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
    source = _copy_path(document.source)
    return snapshot_backup(document.raw, source, GAME_ID, source.parent / 'WarriorsEditorBackups')


def save_as(document, changes, destination):
    destination = _copy_path(destination)
    _extension(destination)
    if destination.exists():
        raise FileExistsError('Choose a new destination; existing files are never replaced.')
    validate_document(document)
    with _copy_path(document.source).open('rb') as stream:
        current = stream.read(SAVE_SIZE + 1)
    if current != document.raw:
        raise SaveError('The opened copy changed on disk. Reopen it before saving.')
    raw = serialize(document, changes)
    backup(document)
    atomic_new(raw, destination)
    return decode(raw, GAME_ID, destination)


def restore(backup_path, destination, game_id=GAME_ID):
    get_format(game_id)
    return restore_snapshot(_copy_path(backup_path), _copy_path(destination), GAME_ID,
                            EXTENSION, SAVE_SIZE, validate_raw=lambda raw: decode(raw, game_id))


def record_label(slot, group='Resources'):
    return f'{group} record {slot}' if slot else group


def field_hint(document, key):
    if key not in field_map(document):
        raise SaveError('This field is not qualified for edits.')
    return ('Manual resource edit in the observed Switch zmha.bin profile. '
            'Only existing ordinary named materials qualify; discovery, fairy food, '
            'levels, EXP, equipment, rewards and story remain unchanged. '
            'These controls are excluded from automatic Max; original values unstage.')


def inspection_rows(document):
    validate_document(document)
    return _inspection(document.payload)


# Direct plaintext scalar editing; no native payload checksum was identified.
INTEGRITY_KIND = 'none'
