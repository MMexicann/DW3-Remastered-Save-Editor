"""Bounded, anonymous inspection of genuine US PS3 Strikeforce exports.

Independent facts only: no external implementation or extracted catalogs.
Native integrity/revision remain unresolved; this is not an editing adapter.
"""
from dataclasses import dataclass, field
import hashlib
from pathlib import Path

from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.ps3_export import MAX_SFO_SIZE, savedata_directory
from koei_editor.shared.save_safety import safe_path
from koei_editor.shared.scalar_presentation import InspectionTable

DIRECTORY = 'BLUS30471-SAVEDATA'
SAVE_SIZE = 0x48064
SLOT_STRIDE = 0x18000
INVENTORY_COUNT = 196
KNOWN_MATERIAL_IDS = frozenset(range(188)) | {197}
SOURCE_URL = 'https://github.com/bucanero/apollo-patches/blob/main/PS3/BLUS30471.savepatch'
CORROBORATING_SOURCE = ('https://github.com/alsharfa/'
                        'Dynasty-Warriors-Strikeforce-ps3-save-editor/tree/'
                        'a92709c2b8aedb6bbd23a36afad4bb0228d376ff')


@dataclass(frozen=True)
class StorehouseRow:
    row: int
    material_id: int
    raw_ownership: int
    quantity: int
    known_material_id: bool
    existing_positive_row: bool


@dataclass(frozen=True)
class OfficerRow:
    ordinal: int
    stored_id: int
    raw_status: int
    stored_level: int
    stored_exp: int
    progression_words: tuple
    main_weapon_id: int
    sub_weapon_id: int


@dataclass(frozen=True)
class Slot:
    number: int
    qualified_existing_record: bool
    candidate_gold: int
    selected_officer_id: int | None
    selected_level: int | None
    selected_exp: int | None
    selected_progression_words: tuple
    officers: tuple
    storehouse: tuple


@dataclass(frozen=True)
class Inspection:
    size: int
    directory: str
    slots: tuple
    raw: bytes = field(repr=False)
    source: Path | None = None
    context_digest: str = field(default='', repr=False)
    editable: bool = False
    qualified_game_profile: bool = False
    native_integrity_qualified: bool = False
    native_revision: None = None


def _word(raw, offset, width=2):
    return int.from_bytes(raw[offset:offset + width], 'big')


def _occupied(raw, slot):
    base = slot * SLOT_STRIDE
    marker = raw[base + 0x64:base + 0x68]
    if marker == bytes(4):
        # Known modified files contain cheat-created resources and progression
        # in these unoccupied records. Never infer occupancy from those values.
        return False
    if marker != b'\0\0\0\xc8':
        raise SaveError('Unqualified Strikeforce player-record structure marker.')
    name = raw[base + 0x74:base + 0x94]
    if (name[0] == 0 or b'\0' not in name
            or name != raw[base + 0xB1:base + 0xD1]
            or raw[base + 0xD8] >= 42
            or any(raw[base + 0x1878 + officer * 0x40] != officer for officer in range(42))):
        raise SaveError('An existing Strikeforce player record has conflicting names or officer identities.')
    # Names are compared as opaque bytes and never returned or displayed.
    return True


def inspect(raw, directory):
    if type(raw) is not bytes or len(raw) != SAVE_SIZE or directory != DIRECTORY:
        raise SaveError('Inspection requires decrypted US PS3 Strikeforce APP.BIN '
                        '(0x48064 bytes) with exact BLUS30471-SAVEDATA identity.')
    slots = []
    for ordinal in range(3):
        base = ordinal * SLOT_STRIDE
        occupied = _occupied(raw, ordinal)
        inventory, officers = [], []
        selected_words = ()
        selected = None
        if occupied:
            selected = raw[base + 0xD8]
            selected_words = tuple(_word(raw, base + 0xE0 + index * 2) for index in range(12))
            for row in range(INVENTORY_COUNT):
                identity = raw[base + 0x9B8 + row]
                ownership = raw[base + 0xA7C + row]
                quantity = raw[base + 0xB44 + row]
                known = identity in KNOWN_MATERIAL_IDS
                inventory.append(StorehouseRow(row + 1, identity, ownership, quantity,
                                                known, known and ownership == 1 and quantity > 0))
            for officer in range(42):
                start = base + 0x1874 + officer * 0x40
                officers.append(OfficerRow(officer, raw[start + 4], raw[start + 5],
                                           _word(raw, start + 6), _word(raw, start + 8, 4),
                                           tuple(_word(raw, start + 12 + index * 2) for index in range(12)),
                                           _word(raw, start + 0x28), _word(raw, start + 0x2A)))
        slots.append(Slot(ordinal + 1, occupied, _word(raw, base + 0x1588, 4),
                          selected, _word(raw, base + 0xDA) if occupied else None,
                          _word(raw, base + 0xDC, 4) if occupied else None,
                          selected_words, tuple(officers), tuple(inventory)))
    if not any(slot.qualified_existing_record for slot in slots):
        raise SaveError('No qualified existing US PS3 Strikeforce player record.')
    return Inspection(len(raw), directory, tuple(slots), raw)


def _context(path):
    companion = safe_path(Path(path).parent / 'PARAM.SFO')
    if not companion.is_file():
        raise SaveError('Keep original US PARAM.SFO beside the copied decrypted APP.BIN.')
    with companion.open('rb') as stream:
        raw = stream.read(MAX_SFO_SIZE + 1)
    directory = savedata_directory(raw)
    if directory != DIRECTORY:
        raise SaveError('Requires exactly BLUS30471-SAVEDATA; other regions/platforms are unqualified.')
    return directory, hashlib.sha256(raw).hexdigest()


def read_copy(path):
    from dataclasses import replace
    path = safe_path(path)
    if path.suffix.lower() != '.bin':
        raise SaveError('Inspect a separate decrypted .bin copy with original PARAM.SFO.')
    directory, digest = _context(path)
    with path.open('rb') as stream:
        snapshot = inspect(stream.read(SAVE_SIZE + 1), directory)
    return replace(snapshot, source=path, context_digest=digest)


def validate_snapshot(snapshot):
    if (type(snapshot) is not Inspection or snapshot.editable
            or snapshot.qualified_game_profile or snapshot.native_integrity_qualified
            or snapshot.native_revision is not None):
        raise SaveError('An immutable unregistered Strikeforce inspection snapshot is required.')
    expected = inspect(snapshot.raw, snapshot.directory)
    if snapshot.size != expected.size or snapshot.slots != expected.slots:
        raise SaveError('Strikeforce inspection does not match its immutable input.')


def unchanged_bytes(snapshot):
    """No-edit byte roundtrip; deliberately no editing/repair/save operation."""
    validate_snapshot(snapshot)
    return snapshot.raw


def source_unchanged(snapshot):
    """Check copied source/context without exposing metadata or account fields."""
    validate_snapshot(snapshot)
    if snapshot.source is None:
        raise SaveError('This inspection has no opened-copy context.')
    _directory, digest = _context(snapshot.source)
    with safe_path(snapshot.source).open('rb') as stream:
        raw = stream.read(SAVE_SIZE + 1)
    return digest == snapshot.context_digest and raw == snapshot.raw


def inspection_tables(snapshot):
    validate_snapshot(snapshot)
    slots = tuple((slot.number, 'Existing record' if slot.qualified_existing_record else 'Unqualified / preserved',
                   slot.candidate_gold, slot.selected_officer_id)
                  for slot in snapshot.slots)
    inventory = tuple((slot.number, row.row, row.material_id, row.raw_ownership, row.quantity,
                       'Existing positive row' if row.existing_positive_row else 'Unqualified / preserved')
                      for slot in snapshot.slots for row in slot.storehouse)
    officers = tuple((slot.number, row.ordinal, row.stored_id, row.raw_status, row.stored_level,
                      row.stored_exp, ', '.join(map(str, row.progression_words)),
                      row.main_weapon_id, row.sub_weapon_id)
                     for slot in snapshot.slots for row in slot.officers)
    selected = tuple((slot.number, slot.selected_officer_id, slot.selected_level, slot.selected_exp,
                      ', '.join(map(str, slot.selected_progression_words)),
                      ', '.join(map(str, slot.officers[slot.selected_officer_id].progression_words)),
                      slot.selected_progression_words == slot.officers[slot.selected_officer_id].progression_words)
                     for slot in snapshot.slots if slot.qualified_existing_record)
    note = 'Read-only research. Native integrity/revision and gameplay dependencies remain unqualified.'
    return (InspectionTable('Strikeforce candidate slots', ('Slot', 'Record qualification', 'Candidate gold', 'Selected officer ID'), slots, note),
            InspectionTable('Strikeforce storehouse', ('Slot', 'Native row', 'Material ID', 'Raw ownership', 'Quantity', 'Row qualification'), inventory, note),
            InspectionTable('Strikeforce officers', ('Slot', 'Ordinal', 'Stored ID', 'Raw status', 'Stored level', 'Stored EXP', '12 progression words', 'Main weapon ID', 'Sub weapon ID'), officers, note),
            InspectionTable('Strikeforce selected officer copies', ('Slot', 'Selected ID', 'Runtime level', 'Runtime EXP', 'Runtime progression words', 'Persistent progression words', 'Words match'), selected,
                            note + ' A mismatch is preserved; synchronization rules are not established.'))
