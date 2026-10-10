"""US PS3 DW8 Empires SYSTEM: existing custom-horse Body Type only.

The PS3 table is independently identified in a genuine console export; see
docs/DW8E_PS3.md for console profile, semantic evidence and validation limits.
PARAM.PFD encryption, reimport and resigning remain external.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
import hashlib
from pathlib import Path
from types import MappingProxyType

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.dw8e_ps3 import codec
from koei_editor.shared.copy_storage import atomic_new, restore_snapshot, snapshot_backup
from koei_editor.shared.save_safety import safe_path
from koei_editor.shared.ps3_export import MAX_SFO_SIZE, savedata_directory, validate_optional_context

GAME_ID = 'dw8e_ps3'
TITLE_IDS = ('NPUB31656-SYSTEM',)
SAVE_SIZE = codec.SAVE_SIZE
HORSE_BASE, HORSE_STRIDE, HORSE_COUNT = 0x39B94, 0x4C, 150
QUALIFIED_MENU_TYPES = frozenset(range(8))
QUALIFIED_MODELS = frozenset(range(0x96, 0x9E))
SLIDERS = (('body', 'Body type', 0x10), ('head', 'Head size', 0x11),
           ('neck', 'Neck length', 0x12), ('torso', 'Torso length', 0x13),
           ('legs', 'Leg length', 0x14), ('tail', 'Tail length', 0x15),
           ('muscle', 'Muscle volume', 0x16))
# Published horse schema names Body Type and positions 0..4; official console
# Edit Mode documentation and the independent PS3 table corroborate this subset.
# Other named sliders remain inspection-only pending their own qualification.
EDITABLE_SLIDERS = SLIDERS[:1]


@dataclass(frozen=True)
class Field:
    id: str
    label: str
    offset: int
    size: int = 1
    maximum: int = 4
    group: str = 'Horse appearance'
    slot: int = 0
    minimum: int = 0
    maxable: bool = False
    kind: str = 'int'

    def value(self, payload):
        return payload[self.offset]

    def validate(self, value):
        if type(value) is not int or not 0 <= value <= 4:
            raise SaveError(f'{self.label} requires a slider position from 0 to 4.')

    def encoded(self, value):
        self.validate(value)
        return bytes([value])


@dataclass(frozen=True)
class Format:
    id: str
    title: str
    size: int
    fields: tuple
    note: str
    sample_verified: bool = True
    game_load_verified: bool = False


FORMAT = Format(GAME_ID, 'Dynasty Warriors 8 Empires (PS3, US SYSTEM custom horses)', SAVE_SIZE, (),
                'Open a copied, decrypted US PS3 SYSTEM APP.BIN with PARAM.SFO. '
                'Campaign resources, horse identity, ownership, type, model, abilities '
                'and progression remain unchanged. Reimport/resign with Apollo; Max excludes appearance choices.')


@dataclass(frozen=True)
class Document:
    format: Format
    source: Path
    raw: bytes
    payload: bytes
    seed: int

    @property
    def sha256(self):
        return hashlib.sha256(self.raw).hexdigest()


def get_format(game_id=GAME_ID):
    if game_id != GAME_ID:
        raise SaveError('Select US PS3 DW8 Empires SYSTEM custom horses.')
    return FORMAT


@lru_cache(maxsize=4)
def _qualify_horses(payload):
    if any(int.from_bytes(payload[HORSE_BASE + identity * HORSE_STRIDE + 0x44:
                                   HORSE_BASE + identity * HORSE_STRIDE + 0x48], 'little')
           != identity + 30 for identity in range(HORSE_COUNT)):
        raise SaveError('Unsupported DW8 Empires SYSTEM custom-horse identity/layout.')


def decode(raw, game_id=GAME_ID, source=Path('system-copy.bin')):
    get_format(game_id)
    frozen = raw
    payload = codec.decode(frozen)
    seed = codec.SYSTEM_SEED
    _qualify_horses(payload)
    return Document(FORMAT, Path(source), frozen, payload, seed)


def _context(path, required=False):
    if required and not (Path(path).parent / 'PARAM.SFO').is_file():
        raise SaveError('Keep the matching NPUB31656-SYSTEM PARAM.SFO beside the copied APP.BIN; '
                        'the gameplay payload does not independently identify its region.')
    validate_optional_context(path, TITLE_IDS, exact=True)


def prepare_copy_context(document, output_dir):
    """Copy required identity context opaquely into a private local test folder.

    The entire bounded original is preserved; only directory identity is parsed.
    This is export context, never rebuilt console metadata or signing support.
    """
    validate_document(document)
    companion = safe_path(document.source.parent / 'PARAM.SFO')
    with companion.open('rb') as stream:
        metadata = stream.read(MAX_SFO_SIZE + 1)
    if savedata_directory(metadata) != TITLE_IDS[0]:
        raise SaveError('The copied PS3 context must identify exactly NPUB31656-SYSTEM.')
    destination = safe_path(Path(output_dir) / 'PARAM.SFO')
    if destination.exists():
        raise FileExistsError('Self-test context must have a new PARAM.SFO destination.')
    return atomic_new(metadata, destination)


def read_save(path, game_id=GAME_ID):
    get_format(game_id)
    path = safe_path(path)
    if path.suffix.lower() != '.bin':
        raise SaveError('Open a separate decrypted PS3 APP.BIN copy.')
    _context(path, required=True)
    with path.open('rb') as stream:
        return decode(stream.read(SAVE_SIZE + 1), game_id, path)


def validate_document(document):
    if (type(document) is not Document or document.format is not FORMAT
            or type(document.raw) is not bytes or type(document.payload) is not bytes
            or type(document.seed) is not int):
        raise SaveError('A frozen US PS3 DW8 Empires SYSTEM snapshot is required.')
    if document.seed != codec.SYSTEM_SEED or codec.decode(document.raw) != document.payload:
        raise SaveError('The opened DW8 Empires SYSTEM snapshot was changed externally.')
    _qualify_horses(document.payload)


def _name(payload, start):
    raw = payload[start + 2:start + 15].split(b'\0', 1)[0]
    try:
        decoded = raw.decode('utf-8')
        return ''.join(character if character.isprintable() else f'\\u{ord(character):04X}'
                       for character in decoded) or '(unnamed)'
    except UnicodeDecodeError:
        return repr(raw)[2:-1] or '(unnamed)'


@lru_cache(maxsize=4)
def _mapped_fields(payload):
    fields = []
    for identity in range(HORSE_COUNT):
        start = HORSE_BASE + identity * HORSE_STRIDE
        if (payload[start] != 1 or payload[start + 15] not in QUALIFIED_MENU_TYPES
                or payload[start + 0x1E] not in QUALIFIED_MODELS):
            continue
        name = _name(payload, start)
        for key, label, relative in EDITABLE_SLIDERS:
            if 0 <= payload[start + relative] <= 4:
                fields.append(Field(f'horse_{identity}_{key}', f'{name}: {label}',
                                    start + relative, slot=identity + 1))
    return tuple(fields)


def fields_for(document):
    validate_document(document)
    return _mapped_fields(document.payload)


def field_map(document):
    return MappingProxyType({field.id: field for field in fields_for(document)})


def changed_payload(document, changes):
    if not isinstance(changes, Mapping):
        raise SaveError('Pending SYSTEM edits must be a field/value mapping.')
    mapping = field_map(document)
    result = bytearray(document.payload)
    for key, value in changes.items():
        if key not in mapping:
            raise SaveError('Only qualified existing custom-horse appearance sliders are writable.')
        field = mapping[key]
        if type(value) is int and value == field.value(document.payload):
            continue
        result[field.offset:field.offset + field.size] = field.encoded(value)
    return bytes(result)


def serialize(document, changes):
    payload = changed_payload(document, changes)
    raw = document.raw if payload == document.payload else codec.encode(payload)
    if decode(raw, GAME_ID, document.source).payload != payload:
        raise SaveError('DW8 Empires SYSTEM edited copy verification failed.')
    return raw


def stage(document, changes, key, value):
    changed_payload(document, changes)
    mapping = field_map(document)
    if key not in mapping:
        raise SaveError('The requested custom-horse slider is not editable.')
    field = mapping[key]
    result = dict(changes)
    if type(value) is int and value == field.value(document.payload):
        result.pop(key, None)
    else:
        field.validate(value)
        result[key] = value
    return result


def limit_values(document, changes, keys):
    mapping = field_map(document)
    changed_payload(document, changes)
    for key in keys:
        if key not in mapping:
            raise SaveError('The requested custom-horse slider is not editable.')
    return {}  # Appearance sliders are choices, never ordered resource upgrades.


def maximums(document, changes, group=None):
    changed_payload(document, changes)
    return dict(changes)


def review(document, changes):
    changed_payload(document, changes)
    return [(field, field.value(document.payload), changes[field.id])
            for field in fields_for(document) if field.id in changes]


def backup(document):
    validate_document(document)
    return snapshot_backup(document.raw, document.source, GAME_ID,
                           document.source.parent / 'UniversalEditorBackups')


def save_as(document, changes, destination):
    validate_document(document)
    destination = safe_path(destination)
    if destination.suffix.lower() != '.bin':
        raise SaveError('Choose a new decrypted PS3 .bin copy destination.')
    _context(document.source, required=True)
    _context(destination, required=True)
    if destination.exists():
        raise FileExistsError('Choose a new file; existing files are never replaced.')
    with safe_path(document.source).open('rb') as stream:
        if stream.read(SAVE_SIZE + 1) != document.raw:
            raise SaveError('The opened SYSTEM copy changed on disk. Reopen it before saving.')
    raw = serialize(document, changes)
    backup(document)
    atomic_new(raw, destination)
    return decode(raw, GAME_ID, destination)


def restore(backup_path, destination, game_id=GAME_ID):
    get_format(game_id)
    _context(safe_path(destination), required=True)
    return restore_snapshot(backup_path, destination, GAME_ID, '.bin', SAVE_SIZE,
                            validate_raw=lambda raw: decode(raw, GAME_ID))


def record_label(slot, group='Horse appearance'):
    return f'Custom horse slot {slot}' if type(slot) is int and 1 <= slot <= HORSE_COUNT else group


def horses(document):
    validate_document(document)
    rows = []
    for identity in range(HORSE_COUNT):
        start = HORSE_BASE + identity * HORSE_STRIDE
        rows.append({'slot': identity + 1, 'ordinal': identity + 30, 'name': _name(document.payload, start),
                     'occupied': document.payload[start], 'menu_type': document.payload[start + 15],
                     'sliders': tuple(document.payload[start + offset] for _, _, offset in SLIDERS),
                     'model_byte': document.payload[start + 0x1E],
                     'speed': int.from_bytes(document.payload[start + 0x24:start + 0x26], 'little'),
                     'power': int.from_bytes(document.payload[start + 0x2A:start + 0x2C], 'little'),
                     'abilities': tuple(document.payload[start + 0x2E:start + 0x32])})
    return tuple(rows)


def field_hint(document, field):
    key = field.id if isinstance(field, Field) else field
    if key not in field_map(document):
        raise SaveError('The requested custom-horse slider is not editable.')
    return ('Existing custom-horse appearance slider, position 0..4 from left to right. '
            'Unknown type/model records are inspection-only. Max leaves appearance choices unchanged; '
            'name, type, model, abilities, '
            'combat stats and ownership are preserved. Reimport and resign edited exports '
            'with Apollo; this editor does not rebuild PS3 PARAM.PFD or change accounts.')


INTEGRITY_KIND = 'checksum'
