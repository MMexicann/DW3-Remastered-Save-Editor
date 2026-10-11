"""Conservative Three Houses slot editor using the shared scalar contract.

No foreign implementation or extracted game catalog is included. Public source
facts and independently examined exports establish the native layouts described
in docs/THREE_HOUSES_FORMAT.md. Unknown identities, values and bytes are retained.
"""
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
import hashlib
from pathlib import Path
from types import MappingProxyType

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.three_houses import codec
from koei_editor.games.three_houses.equipment import ORDINARY_EQUIPMENT
from koei_editor.shared.copy_storage import atomic_new, restore_snapshot, snapshot_backup
from koei_editor.shared.save_safety import safe_path

GAME_ID = 'three_houses'
TITLE = 'Fire Emblem: Three Houses'
EXTENSION = ''
SAVE_SIZE = codec.SAVE_SIZE
HEADER_SIZE = codec.HEADER_SIZE
PROFILES = codec.PROFILES
BYTEORDER = codec.BYTEORDER
INTEGRITY_KIND = 'checksum'
# Original public source Database.cs CHARACTER_USEABLE_COUNT and InitLists use
# these actual native unit IDs. Additional/DLC unit IDs need independent owner
# mapping and entitlement evidence; they are inspected but never edited here.
BASE_OWNER_IDS = frozenset(range(35))


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
    kind: str = 'integer'
    forbidden: tuple = ()

    def value(self, payload):
        return codec.uint(payload, self.offset, self.size)

    def validate(self, value):
        if type(value) is not int or not self.minimum <= value <= self.maximum:
            raise SaveError(f'{self.label} requires a whole number from {self.minimum:,} to {self.maximum:,}.')
        if value in self.forbidden:
            raise SaveError('The native unlimited-durability sentinel cannot be granted by a numeric edit.')


@dataclass(frozen=True)
class Format:
    id: str = GAME_ID
    title: str = TITLE
    size: int = SAVE_SIZE
    fields: tuple = ()
    sample_verified: bool = True
    game_load_verified: bool = False
    note: str = ('Nintendo Switch known main-campaign extracted slot/auto; native revisions 13 and 23 only. '
                 'Exact update and DLC entitlement cannot be inferred from these revision numbers. '
                 'Cindered Shadows side-story and additional/DLC character ownership are unqualified. '
                 'Open an extensionless copy with known Three Houses extraction provenance.')


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

    @property
    def profile(self):
        return PROFILES[codec.uint(self.raw, 4, 4)]


def get_format(game_id=GAME_ID):
    if game_id != GAME_ID:
        raise SaveError(f'Choose the explicit {TITLE} Nintendo Switch adapter.')
    return FORMAT


def decode(raw, game_id=GAME_ID, source=Path('slot-copy')):
    get_format(game_id)
    codec.qualify(raw)
    raw = bytes(raw)
    return Document(FORMAT, Path(source), raw, raw)


def _extension(path):
    if Path(path).suffix:
        raise SaveError('Use a separate extensionless Three Houses slot/auto export copy.')


def read_save(path, game_id=GAME_ID):
    get_format(game_id)
    path = safe_path(path)
    _extension(path)
    with path.open('rb') as stream:
        raw = stream.read(SAVE_SIZE + 1)
    return decode(raw, game_id, path)


def validate_document(document):
    if (type(document) is not Document or document.format is not FORMAT
            or type(document.raw) is not bytes or type(document.payload) is not bytes):
        raise SaveError(f'Invalid immutable {TITLE} snapshot.')
    codec.qualify(document.raw)
    if document.payload != document.raw:
        raise SaveError('The opened snapshot changed outside the edit workflow.')


def _character_rows(raw):
    profile = PROFILES[codec.uint(raw, 4, 4)]
    rows = []
    for index in range(codec.CHARACTER_COUNT):
        base = HEADER_SIZE + codec.CHARACTER_BASE + index * profile.character_stride
        rows.append({'slot': index + 1, 'index': index, 'offset': base,
            'id': codec.item_id(raw, base + 0x24), 'level': raw[base + 0x4A],
            'class': raw[base + 0x4B], 'hp': raw[base + 0x4C],
            'exp': codec.uint(raw, base + 0x2C, 2),
            'flags': codec.uint(raw, base + 0xAC, 4), 'item_count': raw[base + 0x87]})
    counts = Counter(row['id'] for row in rows if row['id'] >= 0)
    for row in rows:
        row['qualified_owner'] = (row['id'] in BASE_OWNER_IDS and counts[row['id']] == 1
            and row['level'] > 0 and row['flags'] & 3 == 3 and not row['flags'] & 8)
    return tuple(rows)


def characters(document):
    validate_document(document)
    return _character_rows(document.payload)


def items(document):
    validate_document(document)
    raw = document.payload
    rows = []
    for index in range(codec.CONVOY_COUNT):
        base = HEADER_SIZE + index * codec.ITEM_STRIDE
        identity = codec.item_id(raw, base)
        if identity != -1:
            rows.append({'owner': 'Convoy', 'slot': index + 1, 'id': identity,
                'durability': raw[base + 2], 'quantity': raw[base + 3]})
    for owner in _character_rows(raw):
        for index in range(6):
            base = owner['offset'] + index * codec.ITEM_STRIDE
            identity = codec.item_id(raw, base)
            if identity != -1:
                rows.append({'owner': f"Character slot {owner['slot']} / native ID {owner['id']}",
                    'slot': index + 1, 'id': identity, 'durability': raw[base + 2],
                    'quantity': 'Not a held quantity'})
    return tuple(rows)


@lru_cache(maxsize=4)
def _field_index(raw):
    profile = PROFILES[codec.uint(raw, 4, 4)]
    gold = HEADER_SIZE + profile.player_offset + 0x1074
    fields = [Field('gold', 'Gold (decrease only)', gold, 4, codec.uint(raw, gold, 4))]
    for index in range(codec.CONVOY_COUNT):
        base = HEADER_SIZE + index * codec.ITEM_STRIDE
        if codec.item_id(raw, base) not in ORDINARY_EQUIPMENT or raw[base + 3] == 0:
            continue
        identity = codec.item_id(raw, base)
        label = f'Convoy slot {index + 1} / {ORDINARY_EQUIPMENT[identity]} / ID {identity}'
        if raw[base + 2] != 100:
            fields.append(Field(f'convoy:{index}:durability', label + ' durability (decrease only)',
                base + 2, 1, raw[base + 2], 'Convoy', index + 1, forbidden=(100,)))
        fields.append(Field(f'convoy:{index}:quantity', label + ' quantity (decrease only)',
            base + 3, 1, raw[base + 3], 'Convoy', index + 1, minimum=1))
    for owner in _character_rows(raw):
        if not owner['qualified_owner']:
            continue
        for index in range(6):
            base = owner['offset'] + index * codec.ITEM_STRIDE
            identity = codec.item_id(raw, base)
            if identity not in ORDINARY_EQUIPMENT or raw[base + 2] == 100:
                continue
            fields.append(Field(f"character:{owner['index']}:item:{index}:durability",
                f"Character slot {owner['slot']} / ID {owner['id']}, item slot {index + 1} / {ORDINARY_EQUIPMENT[identity]} / ID {identity} durability (decrease only)",
                base + 2, 1, raw[base + 2], 'Held equipment', owner['slot'], forbidden=(100,)))
    return MappingProxyType({field.id: field for field in fields})


def field_map(document):
    validate_document(document)
    return _field_index(document.payload)


def fields_for(document):
    return tuple(field_map(document).values())


def changed_payload(document, changes):
    if type(changes) is not dict:
        raise SaveError('Pending changes must be a dictionary.')
    fields = field_map(document)
    output = bytearray(document.payload)
    for key, value in changes.items():
        if type(key) is not str or key not in fields:
            raise SaveError('This field or existing owner is not qualified for edits.')
        field = fields[key]
        # Assigning unusual opened values always preserves/unstages the original.
        field.validate(value)
        if value != field.value(document.payload):
            output[field.offset:field.offset + field.size] = value.to_bytes(field.size, BYTEORDER)
    return codec.encode(bytes(output), document.raw)


def serialize(document, changes):
    result = changed_payload(document, changes)
    if decode(result, GAME_ID, document.source).payload != result:
        raise SaveError('Edited Three Houses export failed read-back validation.')
    return result


def stage(document, changes, key, value):
    changed_payload(document, changes)
    fields = field_map(document)
    if type(key) is not str or key not in fields:
        raise SaveError('This field or existing owner is not qualified for edits.')
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
    if type(keys) not in (list, tuple, set, frozenset):
        raise SaveError('Select a collection of qualified field identifiers.')
    for key in keys:
        if type(key) is not str or key not in fields:
            raise SaveError('This field is not qualified for edits.')
    return {}  # No source-backed natural gameplay caps are asserted.


def maximums(document, changes, group=None):
    changed_payload(document, changes)
    return dict(changes)


def review(document, changes):
    changed_payload(document, changes)
    return [(field, field.value(document.payload), changes[field.id])
            for field in fields_for(document) if field.id in changes]


def backup(document):
    validate_document(document)
    source = safe_path(document.source)
    return snapshot_backup(document.raw, source, GAME_ID, source.parent / 'WarriorsEditorBackups')


def save_as(document, changes, destination):
    destination = safe_path(destination)
    _extension(destination)
    if destination.exists():
        raise FileExistsError('Choose a new destination; existing files are never replaced.')
    validate_document(document)
    with safe_path(document.source).open('rb') as stream:
        current = stream.read(SAVE_SIZE + 1)
    if current != document.raw:
        raise SaveError('The opened copy changed on disk. Reopen it before saving.')
    result = serialize(document, changes)
    backup(document)
    atomic_new(result, destination)
    return decode(result, GAME_ID, destination)


def restore(backup_path, destination, game_id=GAME_ID):
    get_format(game_id)
    return restore_snapshot(safe_path(backup_path), safe_path(destination), GAME_ID,
        EXTENSION, SAVE_SIZE, validate_raw=lambda raw: decode(raw, game_id))


def record_label(slot, group='Resources'):
    return f'{group} record {slot}' if slot else group


def field_hint(document, key):
    field = field_map(document).get(key)
    if field is None:
        raise SaveError('This original record is not qualified for edits.')
    return ('Decrease this opened balance/value only; no natural Max is asserted. '
            'Existing identity, record count, ownership and equipped references are preserved. '
            'Equipment writes require a reviewed ordinary weapon ID; held writes additionally '
            'require a unique living available/joined base-unit owner ID 0–34. '
            'Durability 100 is the native unlimited sentinel and remains read only. '
            'Held-item amount bytes are not quantities. Recruitment, progression, rewards and DLC entitlement are separate.')


def inspection_rows(document):
    validate_document(document)
    profile = document.profile
    raw = document.payload
    return ({'group': 'Native profile', 'label': 'Save-format revision', 'value': profile.revision},
        {'group': 'Native profile', 'label': 'Game update / DLC entitlement', 'value': 'Not encoded by this revision marker'},
        {'group': 'Native profile', 'label': 'Qualified context', 'value': 'Known main-campaign exports; side story and DLC/additional owners unqualified'},
        {'group': 'Resources', 'label': 'Gold', 'value': codec.uint(raw, HEADER_SIZE + profile.player_offset + 0x1074, 4)},
        {'group': 'Resources', 'label': 'Renown (read only)', 'value': codec.uint(raw, HEADER_SIZE + profile.activities_offset + 0xC, 4)},
        {'group': 'Progression', 'label': 'Professor experience (read only)', 'value': codec.uint(raw, HEADER_SIZE + profile.activities_offset + 0x12, 2)})
