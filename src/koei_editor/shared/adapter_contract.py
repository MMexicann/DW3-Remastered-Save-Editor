"""Shared adapter contracts; format logic remains in explicit game backends.

Scalar backends retain the existing module API. BoundScalarAdapter checks the
selected identity before delegating, without probing another parser. DW3 uses
only EditorSession and keeps its tagged document and patch workflow.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol, Sequence

from koei_editor.games.dw3.models import SaveError


class ScalarField(Protocol):
    id: str
    label: str
    offset: int
    size: int
    minimum: int
    maximum: int
    group: str
    slot: int

    def value(self, payload: bytes) -> int | str: ...
    def validate(self, value: int | str) -> None: ...


class ScalarFormat(Protocol):
    id: str
    title: str
    size: int
    fields: Sequence[ScalarField]


class ScalarDocument(Protocol):
    format: ScalarFormat
    source: Path
    raw: bytes
    payload: bytes
    sha256: str


class ScalarBackend(Protocol):
    def get_format(self, game_id: str) -> ScalarFormat: ...
    def read_save(self, path, game_id: str) -> ScalarDocument: ...
    def decode(self, raw: bytes, game_id: str, source: Path) -> ScalarDocument: ...
    def validate_document(self, document: ScalarDocument) -> None: ...
    def fields_for(self, document: ScalarDocument) -> Sequence[ScalarField]: ...
    def field_map(self, document: ScalarDocument) -> Mapping[str, ScalarField]: ...
    def stage(self, document, changes, key: str, value: int | str) -> dict: ...
    def limit_values(self, document, changes, keys) -> dict: ...
    def maximums(self, document, changes, group=None) -> dict: ...
    def review(self, document, changes) -> Sequence[tuple]: ...
    def changed_payload(self, document, changes) -> bytes: ...
    def serialize(self, document, changes) -> bytes: ...
    def backup(self, document) -> Path: ...
    def save_as(self, document, changes, destination) -> ScalarDocument: ...
    def restore(self, backup_path, destination, game_id: str) -> Path: ...


SESSION_ACTIONS = ('open', 'save_changes', 'save_as', 'undo', 'review', 'dirty_ok')
SCALAR_OPERATIONS = ('get_format', 'read_save', 'decode', 'validate_document',
                     'fields_for', 'field_map', 'stage', 'limit_values',
                     'maximums', 'review', 'changed_payload', 'serialize',
                     'backup', 'save_as', 'restore')


class EditorSession(Protocol):
    """The launcher contract, shared by scalar, research and bespoke editors."""
    document: object
    changes: object
    theme_name: object  # Tk variable with set(), owned by the editor.

    def open(self) -> None: ...
    def save_changes(self) -> None: ...
    def save_as(self) -> None: ...
    def undo(self) -> None: ...
    def review(self) -> None: ...
    def dirty_ok(self) -> bool: ...


def validate_session(editor, game_id):
    missing = [name for name in SESSION_ACTIONS if not callable(getattr(editor, name, None))]
    missing += [name for name in ('document', 'changes', 'theme_name') if not hasattr(editor, name)]
    if not callable(getattr(getattr(editor, 'theme_name', None), 'set', None)):
        missing.append('theme_name.set')
    if missing:
        raise SaveError(f'{game_id}: editor does not implement the session contract ({", ".join(missing)}).')
    identity = getattr(editor, 'game_id', game_id)
    if identity != game_id:
        raise SaveError(f'{game_id}: editor belongs to a different game.')
    return editor


@dataclass(frozen=True)
class BoundScalarAdapter:
    """Bind one backend to one game/platform before reading or writing data."""
    game_id: str
    extension: str
    backend: ScalarBackend

    def __post_init__(self):
        missing = [name for name in SCALAR_OPERATIONS if not callable(getattr(self.backend, name, None))]
        if missing:
            raise SaveError(f'{self.game_id}: incomplete scalar backend ({", ".join(missing)}).')
        self.get_format()

    def _identity(self, game_id):
        if game_id is not None and game_id != self.game_id:
            raise SaveError('The selected adapter belongs to a different game/platform.')

    def _path(self, path):
        if Path(path).suffix.lower() != self.extension:
            raise SaveError(f'{self.game_id} requires an explicit {self.extension} copy.')

    def get_format(self, game_id=None):
        self._identity(game_id)
        layout = self.backend.get_format(self.game_id)
        if getattr(layout, 'id', None) != self.game_id:
            raise SaveError('The registered backend returned a different game/platform format.')
        return layout

    def _document_identity(self, document):
        layout = getattr(document, 'format', None)
        if getattr(layout, 'id', None) != self.game_id or layout != self.get_format():
            raise SaveError('This document belongs to a different game/platform adapter.')

    def validate_document(self, document):
        self._document_identity(document)
        self.backend.validate_document(document)

    def read_save(self, path, game_id=None):
        self._identity(game_id)
        self._path(path)
        document = self.backend.read_save(path, self.game_id)
        self.validate_document(document)
        return document

    def decode(self, raw, game_id=None, source=None):
        self._identity(game_id)
        source = Path('copy' + self.extension) if source is None else Path(source)
        self._path(source)
        document = self.backend.decode(raw, self.game_id, source)
        self.validate_document(document)
        return document

    def _call(self, operation, document, *args):
        # Frozen snapshots were validated on read/decode. Writers keep their
        # own full integrity checks; decoding every staged field would make a
        # bulk GUI operation repeat the entire native cipher hundreds of times.
        self._document_identity(document)
        return getattr(self.backend, operation)(document, *args)

    def fields_for(self, document):
        return self._call('fields_for', document)

    def field_map(self, document):
        return self._call('field_map', document)

    def stage(self, document, changes, key, value):
        return self._call('stage', document, changes, key, value)

    def limit_values(self, document, changes, keys):
        return self._call('limit_values', document, changes, keys)

    def maximums(self, document, changes, group=None):
        return self._call('maximums', document, changes, group)

    def review(self, document, changes):
        return self._call('review', document, changes)

    def changed_payload(self, document, changes):
        return self._call('changed_payload', document, changes)

    def serialize(self, document, changes):
        return self._call('serialize', document, changes)

    def backup(self, document):
        return self._call('backup', document)

    def save_as(self, document, changes, destination):
        self._path(destination)
        result = self._call('save_as', document, changes, destination)
        self.validate_document(result)
        return result

    def restore(self, backup_path, destination, game_id=None):
        self._identity(game_id)
        self._path(backup_path)
        self._path(destination)
        return self.backend.restore(backup_path, destination, self.game_id)
