"""Candidate native PC DW4 Hyper layout, independently implemented from facts.

Reference: talkative-platano/dw4hyper-save-editor, commit
3638c8dc23d2607b862a1105bfc9806e69d9e871 (README.md). No third-party code or
save is included. The reference author reports game testing; a genuine PC
sample has not yet been independently validated in this project. The format
is unencrypted, with a byte-sum checksum, and is distinct from PS2 DW4 XL.
"""
from dataclasses import dataclass
import hashlib
from pathlib import Path
from types import MappingProxyType

from copy_storage import atomic_new, restore_snapshot, snapshot_backup
from models import SaveError
from save_safety import safe_path


GAME_ID = 'dw4hyper'
SAVE_SIZE = 0x10FC0
CHECKSUM_OFFSET = 0x10FA8
OFFICER_BASE, OFFICER_STRIDE, OFFICER_COUNT = 0xB8, 24, 42
WEAPON_EXP_BASE = 0x798
ITEM_BASE = 0x7F6
TEAM_BASE, TEAM_STRIDE = 0x508, 96
CUSTOM_BASE, CUSTOM_STRIDE = 0x688, 0x40

OFFICER_NAMES = (
    'Zhao Yun', 'Guan Yu', 'Zhang Fei', 'Xiahou Dun', 'Dian Wei',
    'Xu Zhu', 'Zhou Yu', 'Lu Xun', 'Taishi Ci', 'Diao Chan',
    'Zhuge Liang', 'Cao Cao', 'Lu Bu', 'Sun Shang Xiang', 'Liu Bei',
    'Sun Jian', 'Sun Quan', 'Dong Zhuo', 'Yuan Shao', 'Ma Chao',
    'Huang Zhong', 'Xiahou Yuan', 'Zhang Liao', 'Sima Yi', 'Lu Meng',
    'Gan Ning', 'Jiang Wei', 'Zhang Jiao', 'Xu Huang', 'Zhang He',
    'Zhen Ji', 'Huang Gai', 'Sun Ce', 'Wei Yan', 'Pang Tong',
    'Meng Huo', 'Zhu Rong', 'Da Qiao', 'Xiao Qiao', 'Cao Ren',
    'Zhou Tai', 'Yue Ying',
)
ITEM_NAMES = (
    'Peacock Urn', 'Dragon Amulet', 'Tiger Amulet', 'Tortoise Amulet',
    'Speed Scroll', 'Wing Boots', "Huang's Bow", 'Nanman Armor',
    'Horned Helm', 'Cavalry Armor', 'Seven Star Sash', 'Elixir',
    'Herbal Remedy', 'Fire Orb', 'Lightning Orb', 'Vorpal Orb',
    'Ice Orb', 'Blast Orb', 'Poison Orb', 'Red Hare Harness',
    'Hex Mark Harness', 'Storm Harness', 'Shadow Harness', 'Elephant Harness',
    'Art of War', 'Survival Guide', 'Bodyguard Manual', 'Way of Musou',
    'Power Scroll', 'Wind Scroll', 'Fire Arrows', 'Charge Bracer',
)


@dataclass(frozen=True)
class Field:
    id: str
    label: str
    offset: int
    size: int
    maximum: int
    group: str = 'Options'
    slot: int = 0
    minimum: int = 0
    storage: str = 'unsigned'
    maxable: bool = True
    kind: str = 'int'

    def value(self, payload):
        value = int.from_bytes(payload[self.offset:self.offset + self.size], 'little')
        if self.storage == 'item-level':
            return 0 if value == 0xFF else value + 1
        return value

    def validate(self, value):
        if type(value) is not int or not self.minimum <= value <= self.maximum:
            raise SaveError(f'{self.label} requires a whole number from '
                            f'{self.minimum:,} to {self.maximum:,}.')

    def encoded(self, value):
        self.validate(value)
        stored = (0xFF if value == 0 else value - 1) if self.storage == 'item-level' else value
        return stored.to_bytes(self.size, 'little')


@dataclass(frozen=True)
class Format:
    id: str
    title: str
    size: int
    fields: tuple
    note: str
    sample_verified: bool = False


_fields = [Field('difficulty', 'Difficulty (0 Easy / 1 Normal / 2 Hard)',
                 0x9A, 1, 2, maxable=False)]
for _index, _name in enumerate(OFFICER_NAMES):
    for _key, _label, _relative, _size, _maximum in (
            ('unlocked', 'Playable (0 locked / 1 unlocked)', 0, 1, 1),
            ('life', 'Life', 1, 1, 255), ('musou', 'Musou', 2, 1, 255),
            ('attack', 'Attack', 3, 1, 255), ('defense', 'Defense', 4, 1, 255),
            ('experience', 'Character EXP', 16, 2, 65535)):
        _fields.append(Field(f'officer_{_index}_{_key}', f'{_name}: {_label}',
                             OFFICER_BASE + OFFICER_STRIDE * _index + _relative,
                             _size, _maximum, 'Officers', _index + 1,
                             maxable=_key == 'unlocked'))
    _fields.append(Field(f'officer_{_index}_weapon_experience', f'{_name}: Weapon EXP',
                         WEAPON_EXP_BASE + 2 * _index, 2, 36001, 'Weapons', _index + 1))
for _index, _name in enumerate(ITEM_NAMES):
    _maximum = 20 if _index < 13 else 4 if _index < 19 else 1
    _label = _name + (' ownership (0 locked / 1 owned)' if _index >= 19 else ' level (0 locked)')
    _fields.append(Field(f'item_{_index}', _label, ITEM_BASE + _index, 1,
                         _maximum, 'Items', storage='item-level'))
for _index in range(4):
    _fields.append(Field(f'team_{_index}_points', f'Bodyguard team {_index + 1}: Points',
                         TEAM_BASE + TEAM_STRIDE * _index + 94, 2, 65535,
                         'Bodyguards', _index + 1, maxable=False))

FORMAT = Format(
    GAME_ID, 'Dynasty Warriors 4 Hyper (PC)', SAVE_SIZE, tuple(_fields),
    'Candidate; genuine PC save sample validation pending. '
    'Standard officers, character/weapon EXP, playable flags, items, bodyguard '
    'points and difficulty. Item level 0 means locked; rare items use ownership 0/1. '
    'Equipped items, custom characters, suspended battles and rankings remain read only.'
)
FIELD_MAP = MappingProxyType({field.id: field for field in FORMAT.fields})


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
        raise SaveError('This candidate parser handles native PC DW4 Hyper only.')
    return FORMAT


def decode(raw, game_id=GAME_ID, source=Path('copy.dat')):
    layout = get_format(game_id)
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != SAVE_SIZE:
        raise SaveError(f'DW4 Hyper PC requires exactly {SAVE_SIZE:,} bytes.')
    raw = bytes(raw)
    if raw[CHECKSUM_OFFSET + 4:] != bytes(20):
        raise SaveError('DW4 Hyper PC trailer does not match the required format.')
    payload = raw[:CHECKSUM_OFFSET]
    if int.from_bytes(raw[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 4], 'little') != sum(payload):
        raise SaveError('DW4 Hyper PC byte-sum checksum failed.')
    if payload[0x9A] not in (0, 1, 2):
        raise SaveError('DW4 Hyper PC difficulty must be between 0 and 2.')
    for index in range(OFFICER_COUNT):
        if payload[OFFICER_BASE + OFFICER_STRIDE * index + 5] != index:
            raise SaveError('DW4 Hyper PC officer identities do not match this save layout.')
    return Document(layout, Path(source), raw, payload)


def read_save(path, game_id=GAME_ID):
    get_format(game_id)
    path = safe_path(path)
    if path.suffix.lower() != '.dat':
        raise SaveError('Open a separate native PC .dat save copy.')
    with path.open('rb') as stream:
        raw = stream.read(SAVE_SIZE + 1)
    return decode(raw, game_id, path)


def validate_document(document):
    if not isinstance(document, Document) or document.format != FORMAT:
        raise SaveError('Unregistered DW4 Hyper candidate document.')
    original = decode(document.raw, GAME_ID, document.source)
    if original.payload != document.payload or document.seed != 0:
        raise SaveError('The opened DW4 Hyper snapshot was changed outside the edit workflow.')


def field_map(document):
    validate_document(document)
    return FIELD_MAP


def fields_for(document):
    validate_document(document)
    return FORMAT.fields


def record_label(slot, group='Officers'):
    """Published names for UI labels, without guessing custom or scenario IDs."""
    if group in ('Officers', 'Weapons') and type(slot) is int and 1 <= slot <= OFFICER_COUNT:
        return OFFICER_NAMES[slot - 1]
    if group == 'Bodyguards' and type(slot) is int and 1 <= slot <= 4:
        return f'Bodyguard team {slot}'
    return group if not slot else f'{group} record {slot}'


def changed_payload(document, changes):
    validate_document(document)
    result = bytearray(document.payload)
    for key, value in changes.items():
        if key not in FIELD_MAP:
            raise SaveError('The requested field is not mapped for this PC candidate.')
        field = FIELD_MAP[key]
        result[field.offset:field.offset + field.size] = field.encoded(value)
    return bytes(result)


def serialize(document, changes):
    payload = changed_payload(document, changes)
    if payload == document.payload:
        return document.raw
    raw = payload + sum(payload).to_bytes(4, 'little') + document.raw[CHECKSUM_OFFSET + 4:]
    if decode(raw, GAME_ID, document.source).payload != payload:
        raise SaveError('DW4 Hyper edited copy verification failed.')
    return raw


def stage(document, changes, key, value):
    validate_document(document)
    if key not in FIELD_MAP:
        raise SaveError('The requested field is not mapped for this PC candidate.')
    field = FIELD_MAP[key]
    result = dict(changes)
    if type(value) is int and value == field.value(document.payload):
        result.pop(key, None)
    else:
        field.validate(value)
        result[key] = value
    return result


def limit_values(document, changes, keys):
    validate_document(document)
    result = {}
    for key in keys:
        if key not in FIELD_MAP:
            raise SaveError('The requested field is not mapped for this PC candidate.')
        field = FIELD_MAP[key]
        current = changes.get(key, field.value(document.payload))
        if field.maxable and type(current) is int and current <= field.maximum:
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
            for field in FORMAT.fields if field.id in changes]


def backup(document):
    validate_document(document)
    return snapshot_backup(document.raw, document.source, GAME_ID,
                           document.source.parent / 'WarriorsEditorBackups')


def save_as(document, changes, destination):
    destination = safe_path(destination)
    if destination.suffix.lower() != '.dat':
        raise SaveError('Choose a new .dat destination.')
    if destination.exists():
        raise FileExistsError('Choose a new file; existing files are never replaced.')
    validate_document(document)
    with safe_path(document.source).open('rb') as stream:
        current = stream.read(SAVE_SIZE + 1)
    if current != document.raw:
        raise SaveError('The opened copy changed on disk. Reopen it before saving.')
    raw = serialize(document, changes)
    backup(document)
    atomic_new(raw, destination)
    return decode(raw, GAME_ID, destination)


def restore(backup_path, destination, game_id=GAME_ID):
    get_format(game_id)
    read_save(backup_path, game_id)
    return restore_snapshot(backup_path, destination, GAME_ID, '.dat', SAVE_SIZE)


def _name(payload, offset):
    # Read-only decoding never changes undecodable or noncanonical name bytes.
    return payload[offset:offset + 9].split(b'\0', 1)[0].decode('ascii', errors='replace')


def progression(document, slot):
    validate_document(document)
    if type(slot) is not int or not 1 <= slot <= OFFICER_COUNT:
        raise SaveError('Choose one of the 42 standard PC DW4 Hyper officers.')
    index = slot - 1
    return {'level': None, 'observed_health': None, 'name': OFFICER_NAMES[index],
            'experience': FIELD_MAP[f'officer_{index}_experience'].value(document.payload),
            'weapon_experience': FIELD_MAP[f'officer_{index}_weapon_experience'].value(document.payload)}


def progressions(document):
    return tuple(progression(document, slot) for slot in range(1, OFFICER_COUNT + 1))


def inspection_rows(document):
    """Read-only named equipment, bodyguard names and custom character presence."""
    validate_document(document)
    rows = [{'group': 'Options', 'label': 'Difficulty',
             'value': ('Easy', 'Normal', 'Hard')[document.payload[0x9A]]}]
    for index, name in enumerate(OFFICER_NAMES):
        offset = OFFICER_BASE + OFFICER_STRIDE * index
        equipment = []
        for identity in document.payload[offset + 8:offset + 16]:
            equipment.append('Empty' if identity == 32 else ITEM_NAMES[identity]
                             if identity < 32 else f'Unknown item ID {identity}')
        character_exp = int.from_bytes(document.payload[offset + 16:offset + 18], 'little')
        weapon_exp = int.from_bytes(document.payload[WEAPON_EXP_BASE + 2 * index:
                                                    WEAPON_EXP_BASE + 2 * index + 2], 'little')
        rows.append({'group': 'Officers', 'label': name,
                     'value': f'Character EXP {character_exp:,}; weapon EXP {weapon_exp:,}; '
                              'equipped item IDs: ' + ', '.join(equipment)})
    for team in range(4):
        offset = TEAM_BASE + TEAM_STRIDE * team
        rows.append({'group': 'Bodyguard names', 'label': f'Team {team + 1}',
                     'value': _name(document.payload, offset)})
        rows.extend({'group': 'Bodyguard names', 'label': f'Team {team + 1}, guard {guard + 1}',
                     'value': _name(document.payload, offset + 9 + 9 * guard)}
                    for guard in range(8))
    for slot in range(4):
        offset = CUSTOM_BASE + CUSTOM_STRIDE * slot
        rows.append({'group': 'Custom characters', 'label': f'Custom slot {slot + 1}',
                     'value': f'Created byte {document.payload[offset]}; '
                              f'name {_name(document.payload, offset + 0x34)} (read only)'})
    return tuple(rows)


def field_hint(document, field):
    validate_document(document)
    key = field.id if isinstance(field, Field) else field
    if key not in FIELD_MAP:
        raise SaveError('The requested field is not mapped for this PC candidate.')
    mapped = FIELD_MAP[key]
    if key == 'difficulty':
        return 'Easy=0, Normal=1, Hard=2. Difficulty is excluded from bulk Max.'
    if mapped.group == 'Weapons':
        return ('Weapon level is EXP-derived: normal play 0..36000; 36001 is the special '
                'Lv.10 weapon. Hyper has no Lv.11 weapon. Higher existing EXP is preserved by Max.')
    if mapped.group == 'Items':
        return ('0 means locked. Leveled items use 1..20, orbs 1..4, ownership items 1 means owned. '
                'Equipped item references are inspected separately and remain unchanged.')
    if mapped.group == 'Bodyguards':
        return ('Bodyguard team stats and unlocked guard count derive from points. '
                '65535 is the storage bound. '
                'Points are excluded from bulk Max. Names and other team bytes remain unchanged.')
    return ('Standard officer stats, EXP and playable flags only. Stat 255 and character EXP '
            '65535 are storage bounds; those fields are excluded from bulk Max. '
            'Equipped items, identity and unknown bytes are preserved.')
