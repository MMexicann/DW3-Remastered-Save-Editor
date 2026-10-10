"""Native Steam WO3 Ultimate Definitive layout, independently mapped.

See OROCHI_RESEARCH.md for executable, public patch and copied-native evidence.
The file is packed little endian plaintext. Serialized vtable fragments are
layout markers, not checksums; preserve their original ASLR-dependent values.
"""
from dataclasses import dataclass
import hashlib
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType

from copy_storage import atomic_new, restore_snapshot, snapshot_backup
from models import SaveError
from save_safety import safe_path

GAME_ID = 'wo3u'
SAVE_SIZE = 0x2119CA
SIGNATURE = bytes.fromhex('f1180314')
OFFICER_BASE, OFFICER_STRIDE = 0xECF2, 0x2B0
OFFICER_COUNT, SERIALIZED_OFFICER_COUNT = 145, 150
WEAPON_BASE, WEAPON_STRIDE, WEAPON_COUNT = 0xC8010, 0x1C, 145 * 16
# Factual IDs from the public element patch; Verity is corroborated by the
# annotated native sample. Unmapped IDs remain read only.
ATTRIBUTE_NAMES = {5: 'Agility', 6: 'Reach', 7: 'Multi', 8: 'Brawn',
                   9: 'Air', 10: 'Frenzy', 11: 'Cavalier', 31: 'Verity'}
MATERIAL_SPANS = ((0xE9A8, 16), (0xE9C8, 16), (0xE9E8, 16),
                  (0xEA08, 34), (0xEA3A, 34), (0xEA6C, 34), (0xEAA8, 145))


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
    storage: str = 'unsigned'
    maxable: bool = True
    kind: str = 'int'

    def value(self, payload):
        return int.from_bytes(payload[self.offset:self.offset + self.size], 'little')

    def validate(self, value):
        if type(value) is not int or not self.minimum <= value <= self.maximum:
            raise SaveError(f'{self.label} requires a whole number from '
                            f'{self.minimum:,} to {self.maximum:,}.')

    def encoded(self, value):
        self.validate(value)
        return value.to_bytes(self.size, 'little')


@dataclass(frozen=True)
class Format:
    id: str
    title: str
    size: int
    fields: tuple
    note: str
    sample_verified: bool = True


_static = [Field('growth_points', 'Unallocated growth points', 0x1378, 4, 9999999, maxable=False),
           Field('gems', 'Precious stones (gems)', 0x137C, 4, 999999, maxable=False)]
for index in range(OFFICER_COUNT):
    for key, name, relative, cap in (
            ('health', 'Health', 0, 999), ('musou', 'Musou', 2, 999),
            ('attack', 'Attack', 4, 999), ('defense', 'Defense', 6, 999),
            ('speed', 'Speed', 8, 180)):
        _static.append(Field(f'officer_{index}_{key}',
                             f'Officer {index + 1}: {name}',
                             OFFICER_BASE + index * OFFICER_STRIDE + relative,
                             2, cap, 'Officers', index + 1))
for index in range(58):
    _static.append(Field(f'orb_{index}', f'Weapon attribute orb {index + 1}',
                         0xE944 + index, 1, 99, 'Attribute orbs', maxable=False))
for family, (base, count) in enumerate(MATERIAL_SPANS):
    for index in range(count):
        _static.append(Field(f'material_{family}_{index}',
                             f'Crafting material family {family + 1}, record {index + 1}',
                             base + index, 1, 99, 'Crafting materials', maxable=False))
FORMAT = Format(GAME_ID, 'Warriors Orochi 3 Ultimate Definitive Edition (Steam PC)',
                SAVE_SIZE, tuple(_static),
                'Native copied-file validation; edited game loading remains untested. '
                'Stats, growth points, gems, attribute orbs, crafting materials and '
                'existing weapon slots/ranked attributes. Story, unlocks and promotions '
                'remain unchanged. Five internal officer records are read only.')


@dataclass(frozen=True)
class Document:
    format: Format
    source: Path
    raw: bytes
    payload: bytes
    seed: int = 0

    @property
    def sha256(self):
        return hashlib.sha256(self.raw).hexdigest()


def get_format(game_id=GAME_ID):
    if game_id != GAME_ID:
        raise SaveError('This parser handles native Steam WO3 Ultimate Definitive only.')
    return FORMAT


def decode(raw, game_id=GAME_ID, source=Path('copy.bin')):
    get_format(game_id)
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != SAVE_SIZE:
        raise SaveError(f'WO3 Ultimate Definitive requires exactly {SAVE_SIZE:,} bytes.')
    raw = bytes(raw)
    if raw[:4] != SIGNATURE:
        raise SaveError('WO3 Ultimate Definitive PC title/revision marker failed.')
    _validate_native(raw)
    return Document(FORMAT, Path(source), raw, raw)


@lru_cache(maxsize=8)
def _validate_native(raw):
    officer_marker = raw[OFFICER_BASE - 10:OFFICER_BASE - 6]
    weapon_marker = raw[WEAPON_BASE - 4:WEAPON_BASE]
    # ASLR changes the upper word. The supported build's vtable offsets and
    # difference qualify the packed revision without normalizing those bytes.
    if (officer_marker[:2] != b'\xa8\x6d' or weapon_marker[:2] != b'\x28\x62'
            or officer_marker[2:] != weapon_marker[2:]):
        raise SaveError('Unsupported WO3 Ultimate Definitive serialized record revision.')
    if any(raw[OFFICER_BASE - 10 + index * OFFICER_STRIDE:
               OFFICER_BASE - 6 + index * OFFICER_STRIDE] != officer_marker
           for index in range(SERIALIZED_OFFICER_COUNT)):
        raise SaveError('WO3 Ultimate Definitive officer layout markers are inconsistent.')
    if any(raw[WEAPON_BASE - 4 + index * WEAPON_STRIDE:
               WEAPON_BASE + index * WEAPON_STRIDE] != weapon_marker
           for index in range(WEAPON_COUNT)):
        raise SaveError('WO3 Ultimate Definitive weapon layout markers are inconsistent.')


def read_save(path, game_id=GAME_ID):
    get_format(game_id)
    path = safe_path(path)
    if path.suffix.lower() != '.bin':
        raise SaveError('Open a separate native Steam SAVEDATA.BIN copy.')
    with path.open('rb') as stream:
        return decode(stream.read(SAVE_SIZE + 1), game_id, path)


def validate_document(document):
    if (type(document) is not Document or document.format != FORMAT
            or type(document.raw) is not bytes or type(document.payload) is not bytes
            or type(document.seed) is not int):
        raise SaveError('Foreign WO3 Ultimate Definitive document.')
    original = decode(document.raw, GAME_ID, document.source)
    if original.payload != document.payload or document.seed != 0:
        raise SaveError('The opened WO3 Ultimate Definitive snapshot was modified externally.')


@lru_cache(maxsize=4)
def _fields(payload):
    result = list(FORMAT.fields)
    for index in range(WEAPON_COUNT):
        offset = WEAPON_BASE + index * WEAPON_STRIDE
        identity = int.from_bytes(payload[offset:offset + 2], 'little')
        if not 0 <= identity <= 1394:  # Empty/unknown IDs stay untouched.
            continue
        slots = payload[offset + 2]
        if slots > 8:
            continue
        if slots <= 8:
            result.append(Field(f'weapon_{index}_slots',
                                f'Weapon {index + 1} (ID {identity}): Attribute slots',
                                offset + 2, 1, 8, 'Weapons', index + 1,
                                maxable=not any(identity != 255 for identity in
                                                payload[offset + 4 + slots:offset + 12])))
        for attribute_slot in range(8):
            identity = payload[offset + 4 + attribute_slot]
            if (identity not in ATTRIBUTE_NAMES or attribute_slot >= slots
                    or payload[offset + 12 + attribute_slot] == 0):
                continue
            cap = 1 if identity == 31 else 10
            result.append(Field(f'weapon_{index}_rank_{attribute_slot}',
                                f'Weapon {index + 1}: {ATTRIBUTE_NAMES[identity]} rank',
                                offset + 12 + attribute_slot, 1, cap,
                                'Weapons', index + 1, minimum=1))
    return tuple(result)


def fields_for(document):
    validate_document(document)
    return _fields(document.payload)


@lru_cache(maxsize=4)
def _field_index(payload):
    return MappingProxyType({field.id: field for field in _fields(payload)})


def field_map(document):
    validate_document(document)
    return _field_index(document.payload)


def record_label(slot, group='Officers'):
    if group == 'Weapons' and slot:
        return f'Officer {(slot - 1) // 16 + 1}, weapon {(slot - 1) % 16 + 1}'
    return f'Officer {slot}' if group == 'Officers' and slot else group


def changed_payload(document, changes):
    mapped = field_map(document)
    result = bytearray(document.payload)
    for key, value in changes.items():
        if key not in mapped:
            raise SaveError('The requested WO3 Ultimate Definitive field is not mapped.')
        field = mapped[key]
        # Slots must neither hide existing nor activate dormant attributes,
        # including unknown IDs whose relationship to the count is unproved.
        field.validate(value)
        if key.startswith('weapon_') and key.endswith('_slots'):
            index = field.slot - 1
            base = WEAPON_BASE + index * WEAPON_STRIDE
            original = document.payload[base + 2]
            if value < original and any(identity != 255 for identity in
                                        document.payload[base + 4 + value:base + 12]):
                raise SaveError('Attribute slots cannot hide existing weapon attributes.')
            if value > original and any(identity != 255 for identity in
                                        document.payload[base + 4 + original:base + 4 + value]):
                raise SaveError('Attribute slots cannot activate dormant weapon attributes.')
        result[field.offset:field.offset + field.size] = field.encoded(value)
    return bytes(result)


def serialize(document, changes):
    payload = changed_payload(document, changes)
    if payload == document.payload:
        return document.raw
    reopened = decode(payload, GAME_ID, document.source)
    if reopened.payload != payload:
        raise SaveError('WO3 Ultimate Definitive edited-copy validation failed.')
    return payload


def stage(document, changes, key, value):
    mapped = field_map(document)
    if key not in mapped:
        raise SaveError('The requested WO3 Ultimate Definitive field is not mapped.')
    result = dict(changes)
    if type(value) is int and value == mapped[key].value(document.payload):
        result.pop(key, None)
    else:
        mapped[key].validate(value)
        result[key] = value
        changed_payload(document, result)
    return result


def limit_values(document, changes, keys):
    mapped = field_map(document)
    result = {}
    for key in keys:
        if key not in mapped:
            raise SaveError('The requested WO3 Ultimate Definitive field is not mapped.')
        field = mapped[key]
        current = changes.get(key, field.value(document.payload))
        if field.maxable and type(current) is int and current <= field.maximum:
            result[key] = field.maximum
    return result


def maximums(document, changes, group=None):
    mapped = field_map(document)
    result = dict(changes)
    for key, field in mapped.items():
        if group is not None and field.group != group:
            continue
        current = result.get(key, field.value(document.payload))
        if field.maxable and type(current) is int and current <= field.maximum:
            if field.value(document.payload) == field.maximum:
                result.pop(key, None)
            else:
                result[key] = field.maximum
    changed_payload(document, result)
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


def inspection_rows(document):
    validate_document(document)
    rows = []
    for index in range(SERIALIZED_OFFICER_COUNT):
        offset = OFFICER_BASE + index * OFFICER_STRIDE
        rows.append({'group': 'Progression', 'label': f'Officer {index + 1}' if index <145
                     else f'Internal record {index + 1}',
                     'value': f'Stored level {document.payload[offset + 17] + 1}; '
                              f'EXP {int.from_bytes(document.payload[offset + 26:offset + 30], "little"):,}; '
                              f'promotions {document.payload[offset + 62]}; '
                              f'item slots {document.payload[offset + 44]} (read only)'})
    for index in range(WEAPON_COUNT):
        offset = WEAPON_BASE + index * WEAPON_STRIDE
        identity = int.from_bytes(document.payload[offset:offset + 2], 'little')
        if identity == 65535:
            continue
        attrs = ', '.join(f'{ATTRIBUTE_NAMES.get(identity, "Unmapped ID " + str(identity))} '
                          f'[{document.payload[offset + 12 + slot]}]'
                          for slot, identity in enumerate(document.payload[offset + 4:offset + 12])
                          if identity != 255)
        rows.append({'group': 'Weapons', 'label': record_label(index + 1, 'Weapons'),
                     'value': f'Weapon ID {identity}; slots {document.payload[offset + 2]}; '
                              f'attributes: {attrs or "none"}; compatibility/reinforcement read only'})
    return tuple(rows)


def field_hint(document, field):
    validate_document(document)
    key = field.id if isinstance(field, Field) else field
    mapped = field_map(document)
    if key not in mapped:
        raise SaveError('The requested WO3 Ultimate Definitive field is not mapped.')
    if mapped[key].group == 'Officers':
        return ('Stored stat only. Level, EXP, promotion, upgrade-stone allocation, unlocks '
                'and story are preserved. Stat growth may later change this value. '
                'Max preserves higher existing values.')
    if mapped[key].group == 'Weapons':
        return ('Existing records only. Attribute identities, unknown attributes, weapon ID '
                'and equipped references are preserved. Verity is binary (rank 1); '
                'mapped standard attributes use ranks 1..10. Slots cannot hide or activate dormant attributes.')
    return ('This resource uses a published edit limit, not a proven natural cap, and is excluded from bulk Max. Only this balance changes. Names for numbered crafting/orb records '
            'are not yet mapped. Max preserves higher existing values; it grants no '
            'character, story, recipe or collection unlocks.')
