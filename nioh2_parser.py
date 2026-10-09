"""Source-only Nioh 2 PC inspection; native gameplay edits are unsupported.

Published scalar offsets come from alfizari/Nioh-2-Save-Editor, Apache-2.0,
commit 7de1e3d5b20b7f94b055eb228a5e3b0746ea1452, main.py. That program
disables runtime integrity flags instead of validating/updating the checksums.
This implementation never disables those flags and exposes no writable fields.
One public NIOHUSR sample establishes the observed layout, not checksum or
in-game edit validation. The shared library must not register an editor card.
"""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from types import MappingProxyType

from copy_storage import atomic_new, restore_snapshot, snapshot_backup
import katana_codec
from models import SaveError
from save_safety import safe_path


GAME_ID = 'nioh2'
SAVE_SIZE = 2715432
REVISION = 0x21030200
HEADER_SIZE = 0x148
INTEGRITY_FLAG_OFFSETS = (0x7B93C, 0x7B9DA, 0x7B9DC, 0xED0A2)
READ_ONLY_REASON = (
    'Nioh 2 PC inspection is read only: native body checksums have not been '
    'validated or mapped. Runtime integrity flags are preserved.'
)


@dataclass(frozen=True)
class InspectionField:
    id: str
    label: str
    offset: int
    size: int
    group: str

    @property
    def storage_maximum(self):
        """Integer encoding bound only; no gameplay maximum is established."""
        return (1 << (8 * self.size)) - 1

    def value(self, payload):
        return int.from_bytes(payload[self.offset:self.offset + self.size], 'little')


# Widths and absolute offsets mirror the published PC stats list. These are
# observations, not writable mappings; level/stat/proficiency dependencies and
# the current/lifetime currency distinction remain unverified.
INSPECTION_FIELDS = tuple(InspectionField(*entry) for entry in (
    ('amrita', 'Amrita (published offset)', 0x7B8D0, 8, 'Currency'),
    ('gold', 'Gold (published offset)', 0x7B8D8, 8, 'Currency'),
    ('level', 'Level', 0x1C4904, 2, 'Character'),
    ('constitution', 'Constitution', 0x1C490C, 2, 'Attributes'),
    ('heart', 'Heart', 0x1C4910, 2, 'Attributes'),
    ('courage', 'Courage', 0x1C4928, 2, 'Attributes'),
    ('stamina', 'Stamina', 0x1C4914, 2, 'Attributes'),
    ('strength', 'Strength', 0x1C4918, 2, 'Attributes'),
    ('skill', 'Skill', 0x1C491C, 2, 'Attributes'),
    ('dexterity', 'Dexterity', 0x1C4920, 2, 'Attributes'),
    ('magic', 'Magic', 0x1C4924, 2, 'Attributes'),
    ('ninjutsu', 'Ninjutsu proficiency', 0x1C4B58, 4, 'Proficiency'),
    ('onmyo', 'Onmyo proficiency', 0x1C4B64, 4, 'Proficiency'),
    ('sword', 'Sword proficiency', 0x1C4A8C, 4, 'Proficiency'),
    ('dual_sword', 'Dual sword proficiency', 0x1C4A98, 4, 'Proficiency'),
    ('axe', 'Axe proficiency', 0x1C4AB0, 4, 'Proficiency'),
    ('kusarigama', 'Kusarigama proficiency', 0x1C4ABC, 4, 'Proficiency'),
    ('odachi', 'Odachi proficiency', 0x1C4AC8, 4, 'Proficiency'),
    ('tonfa', 'Tonfa proficiency', 0x1C4AD4, 4, 'Proficiency'),
    ('hatchet', 'Hatchet proficiency', 0x1C4AE0, 4, 'Proficiency'),
))
INSPECTION_MAP = MappingProxyType({field.id: field for field in INSPECTION_FIELDS})
FIELD_MAP = MappingProxyType({})


@dataclass(frozen=True)
class Format:
    id: str = GAME_ID
    title: str = 'Nioh 2 (PC) — source-only inspection'
    size: int = SAVE_SIZE
    fields: tuple = ()
    note: str = READ_ONLY_REASON
    sample_verified: bool = False


FORMAT = Format()


@dataclass(frozen=True)
class Document:
    format: Format
    source: Path
    raw: bytes
    payload: bytes
    encrypted: bool

    @property
    def sha256(self):
        return hashlib.sha256(self.raw).hexdigest()


def get_format(game_id=GAME_ID):
    if game_id != GAME_ID:
        raise SaveError('This inspection parser handles the observed PC Nioh 2 user layout only.')
    return FORMAT


def decode(raw, game_id=GAME_ID, source=Path('copy.bin')):
    get_format(game_id)
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != SAVE_SIZE:
        raise SaveError(f'The observed Nioh 2 PC user layout requires exactly {SAVE_SIZE:,} bytes.')
    try:
        native = katana_codec.decode(bytes(raw), GAME_ID)
    except (ValueError, TypeError) as error:
        raise SaveError(str(error)) from error
    payload = native.payload
    # Nioh 1 shares the native magic/crypto. An explicit observed revision and
    # matching body marker are required in addition to the user file size.
    if (payload[:8] != b'NIOHUSR\0' or
            int.from_bytes(payload[8:12], 'little') != REVISION or
            int.from_bytes(payload[0x150:0x154], 'little') != REVISION):
        raise SaveError('Nioh 2 PC user title/revision markers do not match the observed layout.')
    if any(payload[offset] not in (0, 1) for offset in INTEGRITY_FLAG_OFFSETS):
        raise SaveError('Nioh 2 runtime integrity flags do not match the observed layout.')
    return Document(FORMAT, Path(source), bytes(raw), payload, native.encrypted)


def _copy_path(path):
    """Extend the shared copy policy locally without changing other formats."""
    candidate = Path(path)
    resolved = safe_path(candidate)
    for checked in (candidate, candidate.absolute(), resolved):
        text = str(checked).replace('\\', '/').lower()
        if re.search(r'/koeitecmo/nioh\s*2(?:/|$)', text):
            raise SaveError('Use a separate copy outside the live Nioh 2 save folder.')
    return resolved


def read_save(path, game_id=GAME_ID):
    get_format(game_id)
    path = _copy_path(path)
    if path.suffix.lower() != '.bin':
        raise SaveError('Inspect a separate native PC Nioh 2 .bin user save copy.')
    with path.open('rb') as stream:
        raw = stream.read(SAVE_SIZE + 1)
    return decode(raw, game_id, path)


def validate_document(document):
    if not isinstance(document, Document) or document.format != FORMAT:
        raise SaveError('Unregistered Nioh 2 inspection document.')
    original = decode(document.raw, GAME_ID, document.source)
    if original.payload != document.payload or original.encrypted != document.encrypted:
        raise SaveError('The opened Nioh 2 snapshot was changed outside the copy workflow.')


def fields_for(document):
    validate_document(document)
    return ()


def field_map(document):
    validate_document(document)
    return FIELD_MAP


def _unchanged(document, changes):
    validate_document(document)
    if not isinstance(changes, dict) or changes:
        raise SaveError(READ_ONLY_REASON)


def changed_payload(document, changes):
    _unchanged(document, changes)
    return document.payload


def serialize(document, changes):
    _unchanged(document, changes)
    return document.raw


def stage(document, changes, key, value):
    validate_document(document)
    raise SaveError(READ_ONLY_REASON)


def limit_values(document, changes, keys):
    _unchanged(document, changes)
    if tuple(keys):
        raise SaveError(READ_ONLY_REASON)
    return {}


def maximums(document, changes, group=None):
    _unchanged(document, changes)
    return {}


def review(document, changes):
    _unchanged(document, changes)
    return []


def inspection_rows(document):
    validate_document(document)
    rows = [
        {'group': 'Format', 'label': 'Native integrity', 'value': READ_ONLY_REASON},
        {'group': 'Format', 'label': 'Observed revision', 'value': f'{REVISION:08X}'},
        {'group': 'Format', 'label': 'Storage representation',
         'value': 'Native encrypted' if document.encrypted else 'Native decrypted'},
    ]
    rows.extend({'group': field.group, 'label': field.label,
                 'value': f'{field.value(document.payload):,} (read only)'}
                for field in INSPECTION_FIELDS)
    rows.extend({'group': 'Integrity flags', 'label': f'Flag at 0x{offset:X}',
                 'value': f'{document.payload[offset]} (preserved)'}
                for offset in INTEGRITY_FLAG_OFFSETS)
    return tuple(rows)


def backup(document):
    validate_document(document)
    source = _copy_path(document.source)
    folder = _copy_path(source.parent / 'WarriorsEditorBackups')
    return snapshot_backup(document.raw, source, GAME_ID, folder)


def save_as(document, changes, destination):
    """Copy the original bytes only; this never produces a gameplay edit."""
    _unchanged(document, changes)
    destination = _copy_path(destination)
    if destination.suffix.lower() != '.bin':
        raise SaveError('Choose a new .bin destination for the unchanged copy.')
    if destination.exists():
        raise FileExistsError('Choose a new file; existing files are never replaced.')
    with _copy_path(document.source).open('rb') as stream:
        current = stream.read(SAVE_SIZE + 1)
    if current != document.raw:
        raise SaveError('The opened copy changed on disk. Reopen it before copying.')
    backup(document)
    atomic_new(document.raw, destination)
    return decode(document.raw, GAME_ID, destination)


def restore(backup_path, destination, game_id=GAME_ID):
    get_format(game_id)
    backup_path, destination = _copy_path(backup_path), _copy_path(destination)
    _copy_path(backup_path.with_suffix('.json'))
    read_save(backup_path, game_id)
    return restore_snapshot(backup_path, destination, GAME_ID, '.bin', SAVE_SIZE)
