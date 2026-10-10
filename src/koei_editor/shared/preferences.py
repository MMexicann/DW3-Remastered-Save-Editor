"""Small optional application preferences, separate from game save storage."""
import json
import os
from pathlib import Path
import sys
import tempfile


THEMES = frozenset({'Light', 'Dark'})
MAX_BYTES = 4096


def preference_path():
    if os.name == 'nt':
        base = Path(os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA') or
                    Path.home() / 'AppData' / 'Roaming')
    elif sys.platform == 'darwin':
        base = Path.home() / 'Library' / 'Application Support'
    else:
        base = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config')
    return base / 'UniversalKoeiTecmoSaveEditor' / 'preferences.json'


def load_theme(path=None):
    """Missing, inaccessible or unsupported settings fall back to Light."""
    try:
        with Path(path if path is not None else preference_path()).open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return 'Light'
        value = json.loads(raw)
        if (isinstance(value, dict) and set(value) == {'schema', 'theme'} and
                type(value['schema']) is int and value['schema'] == 1 and
                type(value['theme']) is str and value['theme'] in THEMES):
            return value['theme']
    except (OSError, ValueError, TypeError, RecursionError):
        pass
    return 'Light'


def save_theme(name, path=None):
    """Atomically remember a theme; settings failures never prevent editing."""
    if type(name) is not str or name not in THEMES:
        return False
    temporary = None
    try:
        destination = Path(path if path is not None else preference_path())
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = (json.dumps({'schema': 1, 'theme': name}) + '\n').encode('utf-8')
        with tempfile.NamedTemporaryFile(mode='wb', dir=destination.parent,
                                         prefix='.preferences.', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        return True
    except (OSError, ValueError, TypeError):
        return False
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
