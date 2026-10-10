"""Copied-save validation for explicitly registered scalar adapters."""
import hashlib
import json
from koei_editor.shared.copy_storage import atomic_new
from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.save_safety import safe_path


def run(game_id, source, output):
    from koei_editor.game_registry import get_game
    return _run(get_game(game_id).get_scalar_adapter(), game_id, source, output)


def _run(backend, game_id, source, output):
    integrity_kind = getattr(backend.backend, 'INTEGRITY_KIND', 'unspecified')
    if integrity_kind not in {'checksum', 'none', 'external', 'unspecified'}:
        raise SaveError('The backend declares an unknown integrity profile.')
    original = backend.read_save(source, game_id)
    output = safe_path(output)
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise SaveError('Self-test output must be a new or empty directory.')
    extension = original.source.suffix
    working_path = atomic_new(original.raw, output / ('input-copy' + extension))
    working = backend.read_save(working_path, game_id)
    snapshot = backend.backup(working)
    changes = backend.maximums(working, {})
    edited = backend.save_as(working, changes, output / ('edited' + extension))
    reopened = backend.read_save(edited.source, game_id)
    expected = backend.changed_payload(working, changes)
    if reopened.payload != expected:
        raise SaveError('Self-test plaintext preservation check failed.')
    for field in backend.fields_for(working):
        if field.value(reopened.payload) != changes.get(field.id, field.value(working.payload)):
            raise SaveError('Self-test field verification failed.')
    if backend.serialize(working, {}) != original.raw:
        raise SaveError('Self-test unchanged round trip failed.')
    restored = backend.restore(snapshot, output / ('restored' + extension), game_id)
    if restored.read_bytes() != original.raw or working_path.read_bytes() != original.raw:
        raise SaveError('Self-test backup or input-copy preservation failed.')
    with safe_path(original.source).open('rb') as stream:
        current = stream.read(original.format.size + 1)
    if current != original.raw:
        raise SaveError('Self-test input preservation failed.')
    checksum_verified = integrity_kind == 'checksum'
    sample_verified = getattr(original.format, 'sample_verified', True)
    report = {'success':True, 'game_id':game_id, 'input_sha256':original.sha256,
              'edited_sha256':hashlib.sha256(edited.raw).hexdigest(),
              'fields_checked':len(backend.fields_for(working)), 'fields_changed':len(changes),
              'input_preserved':True, 'unchanged_roundtrip':True, 'backup_restored':True,
              'integrity_kind':integrity_kind, 'checksum_verified':checksum_verified,
              'format_sample_verified':sample_verified,
              'native_integrity_verified':checksum_verified and sample_verified,
              'in_game_load_tested':False}
    atomic_new(json.dumps(report, indent=2).encode('utf-8'), output / 'self-test-report.json')
    return report
