"""Origins copy inspection and preservation, deliberately without guessed edits.

An encrypted blob's size or file name is not game identity. Only exact public
reference fingerprints can currently be recognized; all other copies remain
unverified artifacts. No gameplay serializer is enabled for either kind.
"""
from koei_editor.resources import read_json
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.copy_storage import atomic_new, snapshot_backup, restore_snapshot
from koei_editor.shared.save_safety import safe_path

GAME_ID = 'origins'
MAX_SIZE = 16 * 1024 * 1024
EVIDENCE = read_json('origins_evidence.json')


@dataclass(frozen=True)
class OriginsCopy:
    source: Path | None
    raw: bytes

    @property
    def sha256(self):
        return hashlib.sha256(self.raw).hexdigest()

    @property
    def reference(self):
        return next((row for row in EVIDENCE['references']
                     if row['bytes'] == len(self.raw) and row['sha256'] == self.sha256), None)

    @property
    def editable(self):
        return False


def inspect_bytes(raw, source=None):
    if type(raw) is not bytes or not 16 <= len(raw) <= MAX_SIZE:
        raise SaveError('Choose a nonempty bounded Origins .dat copy (16 bytes to 16 MiB).')
    if raw.startswith(b'GVAS') or raw[4:8] == b'GVAS' or len(set(raw)) < 2:
        raise SaveError('This is not a supported encrypted Origins copy.')
    # This is artifact inspection, not validation or game-format recognition.
    return OriginsCopy(source, raw)


def inspect_copy(path):
    path = safe_path(path)
    if path.suffix.lower() != '.dat':
        raise SaveError('Origins uses .dat copies. DW3 .sav files belong in the DW3 editor.')
    with path.open('rb') as stream:
        raw = stream.read(MAX_SIZE + 1)
    return inspect_bytes(raw, path)


def parse_bytes(raw, source=None):
    copy = inspect_bytes(raw, source)
    if copy.reference is None:
        raise SaveError('Origins format is unverified. Use copy inspection; gameplay parsing is unavailable.')
    return copy


def read_save(path):
    copy = inspect_copy(path)
    return parse_bytes(copy.raw, copy.source)


def serialize(document, changes=()):
    if changes:
        raise SaveError('Origins gameplay edits require a verified schema; editing is unavailable.')
    # Even a known fingerprint supplies no editable schema or integrity rules.
    raise SaveError('Origins gameplay serialization is unavailable. Use Save Copy As for an unchanged copy.')


def backup_copy(document, folder=None):
    if document.source is None:
        raise SaveError('Open an explicit file copy first.')
    return snapshot_backup(document.raw, document.source, GAME_ID, folder)


def duplicate_copy(document, destination):
    destination = safe_path(destination)
    if destination.suffix.lower() != '.dat':
        raise SaveError('Save an unchanged copy with the .dat extension.')
    if document.source is not None:
        current = inspect_copy(document.source)
        if current.raw != document.raw:
            raise SaveError('The opened copy changed on disk. Reopen it before copying.')
    return atomic_new(document.raw, destination)


def restore_backup(backup, destination):
    return restore_snapshot(backup, destination, GAME_ID, '.dat', MAX_SIZE)


def compare_copies(before, after, limit=128):
    if type(limit) is not int or not 1 <= limit <= 1024:
        raise ValueError('Comparison range limit must be 1–1024.')
    ranges, total_ranges, changed_bytes, start = [], 0, 0, None
    for offset in range(max(len(before.raw), len(after.raw))):
        changed = before.raw[offset:offset + 1] != after.raw[offset:offset + 1]
        if changed:
            changed_bytes += 1
            if start is None:
                start = offset
        elif start is not None:
            total_ranges += 1
            if len(ranges) < limit:
                ranges.append({'offset': start, 'length': offset - start})
            start = None
    if start is not None:
        total_ranges += 1
        if len(ranges) < limit:
            ranges.append({'offset': start, 'length': max(len(before.raw), len(after.raw)) - start})
    return {'game_id': GAME_ID, 'kind': 'opaque-byte-comparison',
            'before_sha256': before.sha256, 'after_sha256': after.sha256,
            'before_bytes': len(before.raw), 'after_bytes': len(after.raw),
            'changed_bytes': changed_bytes, 'changed_range_count': total_ranges,
            'ranges': ranges, 'ranges_truncated': total_ranges > len(ranges),
            'interpretation': 'Encrypted file offsets only; no gameplay fields or edit offsets inferred.'}


def export_comparison(report, destination):
    destination = safe_path(destination)
    if not destination.name.endswith('.changes.json'):
        raise SaveError('Use a .changes.json report name; reports can contain private save fingerprints.')
    return atomic_new(json.dumps(report, indent=2).encode('utf-8'), destination)
