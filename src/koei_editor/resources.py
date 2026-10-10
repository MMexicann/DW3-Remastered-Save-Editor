"""Read bundled metadata from the installed application package.

Package resources resolve beside ``koei_editor`` both in source installations
and in PyInstaller's extracted package. Build inputs must retain the
``koei_editor/data`` destination so these lookups do not depend on the working
directory or the location of an individual game module.
"""
from importlib.resources import files
import json


def data_file(name):
    """Return a metadata resource without requiring a filesystem installation."""
    if (not isinstance(name, str) or not name or name in {'.', '..'}
            or any(character in name for character in ('/', '\\', ':', '\0'))):
        raise ValueError('Metadata names must be individual package filenames.')
    return files('koei_editor').joinpath('data', name)


def read_json(name):
    """Decode UTF-8 JSON metadata from the installed package."""
    return json.loads(data_file(name).read_text(encoding='utf-8'))
