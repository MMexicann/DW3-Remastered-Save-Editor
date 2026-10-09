"""Refresh the explicit public source list after source edits, without discovering private files."""
import argparse
import hashlib
import json
from pathlib import Path
import os
import uuid
from package_release import public_path, PERSONAL_PATH, verified_sources, version

ROOT = Path(__file__).resolve().parent


def refresh(root=ROOT, additions=()):
    root = root.resolve()
    path = root / 'SOURCE_MANIFEST.json'
    if path.is_symlink():
        raise ValueError('The source manifest cannot be a symlink.')
    existing = json.loads(path.read_text(encoding='utf-8'))
    names = {entry['path'] for entry in existing['files']}
    names.update(additions)
    entries = []
    for name in sorted(names):
        relative = public_path(name)
        source = root / relative
        if (any(root.joinpath(*relative.parts[:i]).is_symlink() for i in range(1, len(relative.parts) + 1)) or
                not source.resolve().is_relative_to(root)):
            raise ValueError(f'Public source escapes the checkout: {name}')
        data = source.read_bytes()
        text = data.decode('utf-8-sig')
        if '\0' in text or PERSONAL_PATH.search(text):
            raise ValueError(f'Private path or binary content in public source: {name}')
        entries.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    encoded = (json.dumps({'version': version(root), 'files': entries}, indent=2) + '\n').encode('utf-8')
    original = path.read_bytes()
    temporary = path.with_name('.SOURCE_MANIFEST.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_bytes(encoded)
        os.replace(temporary, path)
        try:
            verified_sources(root)
        except Exception:
            # Preserve the old manifest on a failed candidate verification.
            path.write_bytes(original)
            raise
    finally:
        temporary.unlink(missing_ok=True)
    return len(entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--add', nargs='*', default=[], help='Explicit reviewed public files to add.')
    args = parser.parse_args()
    print(f'Verified and refreshed {refresh(additions=args.add)} public source entries.')


if __name__ == '__main__':
    main()
