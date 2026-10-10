"""Bounded optional PS3 export identity metadata; never reads account values."""
import struct
from pathlib import Path

from koei_editor.games.dw3.models import SaveError
from koei_editor.shared.save_safety import safe_path

MAX_SFO_SIZE = 4096


def savedata_directory(raw):
    """Read only SAVEDATA_DIRECTORY from a PSF 1.1 export metadata file."""
    if type(raw) is not bytes or not 20 <= len(raw) <= MAX_SFO_SIZE:
        raise SaveError('PS3 export metadata has an invalid bounded size.')
    magic, version, keys, data, count = struct.unpack_from('<5I', raw)
    if (magic != 0x46535000 or version != 0x101 or count > 128
            or not 20 + count * 16 <= keys <= data <= len(raw)):
        raise SaveError('PS3 export metadata header is invalid.')
    found = None
    for index in range(count):
        key_offset, encoding, length, capacity, relative = struct.unpack_from('<HH3I', raw, 20 + index * 16)
        start = keys + key_offset
        if not keys <= start < data:
            raise SaveError('PS3 export metadata key is outside its table.')
        end = raw.find(b'\0', start, data)
        if end < 0:
            raise SaveError('PS3 export metadata key is unterminated.')
        if raw[start:end] != b'SAVEDATA_DIRECTORY':
            continue
        position = data + relative
        if (found is not None or encoding != 0x204 or not 1 <= length <= capacity <= 128
                or position < data or position + capacity > len(raw)):
            raise SaveError('PS3 export directory identity is invalid.')
        value = raw[position:position + length]
        if value[-1:] != b'\0' or b'\0' in value[:-1]:
            raise SaveError('PS3 export directory identity is malformed.')
        try:
            found = value[:-1].decode('ascii')
        except UnicodeDecodeError as error:
            raise SaveError('PS3 export directory identity must be ASCII.') from error
    if found is None:
        raise SaveError('PS3 export metadata lacks a save-directory identity.')
    return found


def validate_optional_context(source, title_ids, *, exact=False):
    """Reject a conflicting companion, while standalone qualified copies work."""
    companion = Path(source).parent / 'PARAM.SFO'
    if not companion.exists():
        return
    with safe_path(companion).open('rb') as stream:
        directory = savedata_directory(stream.read(MAX_SFO_SIZE + 1))
    if not any(directory == title or (not exact and directory.startswith(title + '-'))
               for title in title_ids):
        raise SaveError('PS3 export metadata belongs to a different game or unsupported region.')
