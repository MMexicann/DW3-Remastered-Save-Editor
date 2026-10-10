"""Native Wo Long PC balances and conservative existing-stack reductions.

Full header/body integrity is required. Integer tokens alone change; unknown
JSON, owner context, identity keys and mission/reward history are preserved.
"""
from dataclasses import dataclass
from functools import lru_cache
import hashlib
from pathlib import Path
from types import MappingProxyType

from koei_editor.games.dw3.models import SaveError
from koei_editor.games.wolong import wolong_json
from koei_editor.research.katana import katana_codec
from koei_editor.shared.copy_storage import atomic_new, restore_snapshot, snapshot_backup
from koei_editor.shared.save_safety import safe_path
from koei_editor.shared.verified_editor import Field

GAME_ID, SAVE_SIZE, JSON_OFFSET = 'wolong', 5_120_272, 0x108
INTEGRITY_KIND = 'checksum'
MANUAL_CURRENCY_LIMIT = 2_147_483_647
CURRENCY_NAMES = {'senki': 'Available Genuine Qi', 'sen': 'Copper', 'bukun': 'Accolades'}


@dataclass(frozen=True)
class JsonField(Field):
    def value(self, payload):
        return int(payload[self.offset:self.offset + self.size])


@dataclass(frozen=True)
class Format:
    id: str
    title: str
    size: int
    fields: tuple
    note: str
    sample_verified: bool = True
    game_load_verified: bool = False


FORMAT = Format(GAME_ID, 'Wo Long: Fallen Dynasty (PC)', SAVE_SIZE, (),
                'Current native Windows PC USER revision 0x23121200. Both native '
                'checksums are verified. Available currencies use a conservative '
                'manual range, not a claimed natural cap; Max is disabled. Existing '
                'ordinary stacks can only be reduced while retaining at least one. '
                'Equipment, skills, level, stored Qi and story are inspected without '
                'changing their identities, dependencies or history. Genuine parsing '
                'and no-op reconstruction are verified; edited game-load testing '
                'has not been performed by this project.')


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
        raise SaveError('Select the Wo Long Windows PC USER adapter.')
    return FORMAT


def _integer(obj, key, minimum=0, maximum=(1 << 64) - 1):
    value = obj.get(key)
    if type(value) is not int or not minimum <= value <= maximum:
        raise SaveError(f'Unsupported Wo Long {key} type or structural range.')
    return value


def _json(payload):
    encoded = payload[JSON_OFFSET:]
    zero = encoded.find(b'\0')
    if zero < 0 or any(encoded[zero:]):
        raise SaveError('Wo Long JSON must retain its bounded zero padding.')
    root, spans = wolong_json.parse(encoded[:zero])
    if type(root) is not dict:
        raise SaveError('Unsupported Wo Long JSON root.')
    for key in ('PlayerData', 'TempRecordData', 'UIData', 'PossessionItemData', 'MissionData'):
        if type(root.get(key)) is not dict:
            raise SaveError('Unsupported Wo Long USER serializer structure.')
    player = root['PlayerData']
    for key in (*CURRENCY_NAMES, 'senki_storage', 'new_senki_storage', 'level', 'skill_max_level'):
        _integer(player, key)
    if not 1 <= player['level'] <= 65535:
        raise SaveError('Unsupported Wo Long existing character level.')
    if (type(player.get('xing')) is not list or len(player['xing']) != 5
            or any(type(value) is not int or not 0 <= value <= 65535 for value in player['xing'])):
        raise SaveError('Unsupported Wo Long five-Virtue structure.')
    for key, count in (('possession_items', 600), ('storage_items', 2000)):
        records = root['PossessionItemData'].get(key)
        if type(records) is not list or len(records) != count:
            raise SaveError('Unqualified Wo Long inventory layout/count.')
        for wrapped in records:
            if type(wrapped) is not dict or type(wrapped.get('ItemObjectData')) is not dict:
                raise SaveError('Unsupported Wo Long item record wrapper.')
            record = wrapped['ItemObjectData']
            for name in ('key', 'key_num', 'num', 'flag', 'rarity', 'entry_number',
                         'item_level', 'weapon_skill_level', 'equipment_part'):
                _integer(record, name, maximum=0xffffffff)
            _integer(record, 'equipment_slot', -1, 65535)
    return root, spans, zero


@lru_cache(maxsize=4)
def _qualify(raw):
    if len(raw) != SAVE_SIZE or raw[:8] not in (b'WLNUSR\0\0',):
        raise SaveError('Open the qualified 5,120,272-byte Wo Long PC USER copy, not SYSTEM data.')
    try:
        native = katana_codec.decode(raw, GAME_ID)
    except (ValueError, TypeError) as error:
        raise SaveError(str(error)) from error
    if not native.integrity_verified:
        raise SaveError('Wo Long native header/body integrity must both be verified.')
    root, spans, length = _json(native.payload)
    return native.payload, root, spans, length


def decode(raw, game_id=GAME_ID, source=None):
    get_format(game_id)
    if not isinstance(raw, (bytes, bytearray, memoryview)) or len(raw) != SAVE_SIZE:
        raise SaveError('Unsupported Wo Long native USER size/type.')
    raw = bytes(raw)
    payload = _qualify(raw)[0]
    return Document(FORMAT, Path(source) if source is not None else Path('wolong-copy.bin'), raw, payload)


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
            or type(document.raw) is not bytes or type(document.payload) is not bytes
            or _qualify(document.raw)[0] != document.payload):
        raise SaveError('An unchanged immutable Wo Long USER snapshot is required.')


def _ordinary_stack(record):
    # No item creation/deletion or gear quantities. Native num is retained above
    # zero; reductions need no invented per-item capacity or acquisition flags.
    return (record['key'] != 0 and record['key_num'] != 0xffffffff
            and 1 < record['num'] <= 0x7fffffff and record['flag'] == 8
            and record['equipment_part'] == 0 and record['equipment_slot'] == -1
            and record['item_level'] == 1 and record['weapon_skill_level'] == 0)


@lru_cache(maxsize=4)
def _fields(raw):
    _, root, spans, _ = _qualify(raw)
    fields = []
    for key, label in CURRENCY_NAMES.items():
        start, end = spans[('PlayerData', key)]
        fields.append(JsonField(key, label, JSON_OFFSET + start, end - start,
                                MANUAL_CURRENCY_LIMIT, 'Available currencies', maxable=False))
    for group, label, slot_base in (('possession_items', 'Carried stacks', 0),
                                     ('storage_items', 'Stored stacks', 600)):
        for index, wrapped in enumerate(root['PossessionItemData'][group]):
            record = wrapped['ItemObjectData']
            if not _ordinary_stack(record):
                continue
            start, end = spans[('PossessionItemData', group, index, 'ItemObjectData', 'num')]
            fields.append(JsonField(f'{group}_{index}_num',
                                    f'Item key 0x{record["key"]:08X}: Reduce quantity',
                                    JSON_OFFSET + start, end - start, record['num'], label,
                                    slot_base + index + 1, minimum=1, maxable=False))
    return tuple(fields)


def fields_for(document):
    validate_document(document)
    return _fields(document.raw)


def field_map(document):
    return MappingProxyType({field.id: field for field in fields_for(document)})


def changed_payload(document, changes):
    mapping = field_map(document)
    if type(changes) is not dict:
        raise SaveError('Wo Long changes must be a field/value mapping.')
    replacements = []
    for key, value in changes.items():
        field = mapping.get(key)
        if field is None or type(value) is not int:
            raise SaveError('Only qualified integer currencies and existing-stack reductions are writable.')
        original = field.value(document.payload)
        if value != original:
            field.validate(value)
            replacements.append((field.offset, field.offset + field.size, str(value).encode('ascii')))
    if not replacements:
        return document.payload
    length = _qualify(document.raw)[3]
    body = document.payload[JSON_OFFSET:JSON_OFFSET + length]
    for start, end, token in sorted(replacements, reverse=True):
        body = body[:start - JSON_OFFSET] + token + body[end - JSON_OFFSET:]
    if len(body) >= SAVE_SIZE - JSON_OFFSET:
        raise SaveError('Wo Long JSON edits exceed the existing native body capacity.')
    result = document.payload[:JSON_OFFSET] + body + bytes(SAVE_SIZE - JSON_OFFSET - len(body))
    _json(result)
    return result


def stage(document, changes, key, value):
    changed_payload(document, changes)
    proposed = dict(changes)
    proposed[key] = value
    changed_payload(document, proposed)
    field = field_map(document)[key]
    if value == field.value(document.payload):
        proposed.pop(key)
    return proposed


def serialize(document, changes):
    try:
        raw = katana_codec.encode(changed_payload(document, changes), document.raw, GAME_ID)
    except (ValueError, TypeError) as error:
        raise SaveError(str(error)) from error
    decode(raw)
    return raw


def limit_values(document, changes, keys):
    changed_payload(document, changes)
    mapping = field_map(document)
    if any(key not in mapping for key in keys):
        raise SaveError('Unknown Wo Long field selection.')
    return {}


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


def record_label(slot, group='Available currencies'):
    if group == 'Carried stacks':
        return f'Carried slot {slot}'
    if group == 'Stored stacks':
        return f'Storage slot {slot - 600}'
    return group


def field_hint(document, key):
    field = field_map(document)[key if isinstance(key, str) else key.id]
    if field.group == 'Available currencies':
        return ('Manual balance range 0..2,147,483,647 is a conservative editor limit, '
                'not a proven natural cap. Max is disabled. Stored Qi, lifetime/history '
                'records, level and rewards are preserved; unusual opened values can be restored unchanged.')
    return ('Reduce this existing ordinary stack to 1..the opened quantity. '
            'Increasing, deleting or creating items is unavailable until per-item '
            'capacity/ownership dependencies are proved. Identity, flags, equipped '
            'references and acquisition history are preserved. Max is disabled.')


def inspection_rows(document):
    validate_document(document)
    root = _qualify(document.raw)[1]
    player = root['PlayerData']
    rows = [{'group': 'Profile', 'label': 'Native profile',
             'value': 'Windows PC USER 0x23121200; header and body checksums verified'},
            {'group': 'Profile', 'label': 'Stored Qi fields',
             'value': f'senki_storage {player["senki_storage"]:,}; new_senki_storage '
                      f'{player["new_senki_storage"]:,} (read only; semantics/history not fully mapped)'},
            {'group': 'Progression', 'label': 'Level / stored skill maximum',
             'value': f'{player["level"]} / {player["skill_max_level"]} (read only)'},
            {'group': 'Progression', 'label': 'Five Virtues (stored order)',
             'value': ', '.join(str(value) for value in player['xing']) + ' (read only)'}]
    for group in ('possession_items', 'storage_items'):
        for index, wrapped in enumerate(root['PossessionItemData'][group]):
            item = wrapped['ItemObjectData']
            if not item['key']:
                continue
            rows.append({'group': 'Inventory',
                         'label': f'{"Carried" if group == "possession_items" else "Storage"} slot {index + 1} '
                                  f'/ key 0x{item["key"]:08X}',
                         'value': f'Instance {item["key_num"]}; quantity {item["num"]:,}; '
                                  f'rarity {item["rarity"]}; stored item_level {item["item_level"]}; '
                                  f'martial-art field {item["weapon_skill_level"]}; '
                                  f'part {item["equipment_part"]}; equipment slot {item["equipment_slot"]}; '
                                  f'flags 0x{item["flag"]:X}'})
    for index, wrapped in enumerate(player.get('fellow_character_info', ())):
        if type(wrapped) is dict and type(wrapped.get('FellowCharacterInfoData')) is dict:
            info = wrapped['FellowCharacterInfoData']
            if all(type(info.get(key)) is int for key in ('fellow_character_id', 'bond_level', 'bond_point', 'flag')):
                rows.append({'group': 'Companions', 'label': f'Companion slot {index + 1} / ID {info["fellow_character_id"]}',
                             'value': f'Bond level {info["bond_level"]}; points {info["bond_point"]}; '
                                      f'flags 0x{info["flag"]:X} (read only)'})
    return tuple(rows)
