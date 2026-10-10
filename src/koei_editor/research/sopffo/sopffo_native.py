"""Strict, unchanged-only Stranger of Paradise native PC envelope inspection.

Framing is independently verified against freely shared launch-era Epic and
later Steam USER/SYSTEM copies. The later SYSTEM also matches an attributed
Katana source fixture. See docs/SOPFFO_RESEARCH.md for the exact evidence boundary.

AES-CBC decoding reuses this project's attributed Katana primitives. Cipher and
framing qualification do not establish gameplay integrity: every write remains
disabled, including account reassignment, checksum repair and settings changes.
"""
from dataclasses import dataclass
import struct

from koei_editor.games.dw3.models import SaveError
from koei_editor.research.katana import katana_codec


HEADER_SIZE = 0x100
USER_SIZE = 6_216_976
SYSTEM_SIZE = 17_568
LAUNCH_REVISION = 0x22020200
LATER_REVISION = 0x23013100
MAGIC = {'user': b'RNNUSR\0\0', 'system': b'RNNSYS\0\0'}
# Each kind/revision combination has its own complete external fixture evidence.
PROFILE_SIZES = {
    ('user', LAUNCH_REVISION): USER_SIZE,
    ('system', LAUNCH_REVISION): SYSTEM_SIZE,
    ('user', LATER_REVISION): USER_SIZE,
    ('system', LATER_REVISION): SYSTEM_SIZE,
}


@dataclass(frozen=True)
class Document:
    raw: bytes
    payload: bytes
    file_kind: str
    revision: int
    encrypted: bool

    @property
    def integrity_verified(self) -> bool:
        return False

    @property
    def writable(self) -> bool:
        return False


def _kind(file_kind: str) -> bytes:
    if type(file_kind) is not str or file_kind not in MAGIC:
        raise SaveError('Select Stranger of Paradise PC USER or SYSTEM inspection explicitly.')
    return MAGIC[file_kind]


def _validate_plaintext(payload: bytes, file_kind: str) -> int:
    expected_magic = _kind(file_kind)
    if payload[:8] != expected_magic:
        raise SaveError('Wrong Stranger of Paradise PC title or selected USER/SYSTEM kind.')
    revision = struct.unpack_from('<I', payload, 8)[0]
    if PROFILE_SIZES.get((file_kind, revision)) != len(payload):
        raise SaveError('Unreviewed Stranger of Paradise PC revision/size combination.')
    if struct.unpack_from('<II', payload, 0x14) != (HEADER_SIZE, len(payload) - HEADER_SIZE):
        raise SaveError('Stranger of Paradise PC header/body lengths do not match the file.')
    if payload[0x108:0x110] != payload[8:16]:
        raise SaveError('Stranger of Paradise PC inner revision/context does not match its header.')
    return revision


def decode(raw: bytes, file_kind: str = 'user') -> Document:
    """Decode only observed complete PC profiles, with an explicit file kind.

The size, identity and repeated framing are checked. Unknown gameplay corruption
cannot be detected because native integrity is unqualified. No field, flag,
owner identifier, tail or unknown byte is normalized by this inspection.
"""
    expected_magic = _kind(file_kind)
    allowed_sizes = {size for (kind, _), size in PROFILE_SIZES.items() if kind == file_kind}
    if not isinstance(raw, (bytes, bytearray)) or len(raw) not in allowed_sizes:
        raise SaveError('Select a complete observed-size Stranger of Paradise PC copy.')
    raw = bytes(raw)
    # Wrong selected kinds fail before cipher work; never retry another parser.
    if raw[:8] in MAGIC.values() and raw[:8] != expected_magic:
        raise SaveError('Wrong selected Stranger of Paradise PC USER/SYSTEM kind.')
    encrypted = raw[:8] != expected_magic
    if encrypted:
        # Check the small CBC header before decrypting a multi-megabyte USER.
        header = katana_codec._cbc(raw[:HEADER_SIZE], katana_codec._SOP_KEY,
                                   katana_codec._SOP_IV, 'decrypt')
        if header[:8] != expected_magic:
            raise SaveError('Wrong encrypted Stranger of Paradise PC identity.')
        revision = struct.unpack_from('<I', header, 8)[0]
        if (PROFILE_SIZES.get((file_kind, revision)) != len(raw) or
                struct.unpack_from('<II', header, 0x14) != (HEADER_SIZE, len(raw) - HEADER_SIZE)):
            raise SaveError('Unreviewed encrypted Stranger of Paradise PC framing.')
        payload = katana_codec._cbc(raw, katana_codec._SOP_KEY,
                                    katana_codec._SOP_IV, 'decrypt')
    else:
        payload = raw
    revision = _validate_plaintext(payload, file_kind)
    return Document(raw, payload, file_kind, revision, encrypted)


def _original(document: Document) -> Document:
    if (type(document) is not Document or type(document.raw) is not bytes or
            type(document.payload) is not bytes or type(document.file_kind) is not str or
            type(document.revision) is not int or type(document.encrypted) is not bool):
        raise SaveError('Foreign or mutable Stranger of Paradise inspection snapshot.')
    original = decode(document.raw, document.file_kind)
    if original != document:
        raise SaveError('The Stranger of Paradise inspection snapshot was changed.')
    return original


def serialize(document: Document, changes) -> bytes:
    """Return the immutable original only; no integrity bypass or gameplay write."""
    original = _original(document)
    if changes:
        raise SaveError('Stranger of Paradise gameplay writes are unavailable: native integrity is unqualified.')
    return original.raw


def inspection_rows(document: Document) -> tuple[tuple[str, str], ...]:
    """Public-safe framing summary, excluding owner/header contents and tails."""
    original = _original(document)
    provenance = ('independent launch-era Epic PC USER/SYSTEM corpus'
                  if original.revision == LAUNCH_REVISION else
                  'independent Steam PC USER/SYSTEM corpus; matching Katana SYSTEM source pair')
    return (
        ('File kind', original.file_kind.upper()),
        ('Revision', f'0x{original.revision:08X}'),
        ('Total bytes', str(len(original.raw))),
        ('Header bytes', str(HEADER_SIZE)),
        ('Body bytes', str(len(original.payload) - HEADER_SIZE)),
        ('Representation', 'AES-CBC encrypted' if original.encrypted else 'decoded'),
        ('Evidence', provenance),
        ('Native gameplay integrity', 'Unqualified; body corruption may be undetected'),
        ('Gameplay writes', 'Disabled'),
    )
