"""Independent, research-only Persona 5 Strikers PC byte-stream tools.

The 32-byte vector below was transcribed from a published PC encrypted/clear
hex-view screenshot. It verifies the stream transform, not a complete native
save or its integrity rules. No gameplay fields, file writer, or editor adapter
are provided. Candidate inspection reports structural evidence only and never
claims checksum validation or a successful game load.

Algorithm and layout observations are attributed to the source URLs below.
This implementation was written independently; it does not import or execute
the referenced utility. Inputs stay in memory; account IDs are neither required
nor returned. Recovered states identify only a low-24-bit stream equivalence
class, not the original account.
"""

from dataclasses import dataclass, field


SOURCE_COMMIT = "2462a2043aba3bc551d2eb6b732a81d2374aa826"
SOURCE_ROOT = "https://github.com/zarroboogs/p5spc.saveutil/blob/" + SOURCE_COMMIT
VECTOR_SOURCE_URL = SOURCE_ROOT + "/img/crypt.png"
CIPHER_SOURCE_URL = SOURCE_ROOT + "/src/p5spc.saveutil/Save/SaveCrypt.cs"
LAYOUT_SOURCE_URL = SOURCE_ROOT + "/src/p5spc.saveutil/Save/SaveConvert.cs"

# Actual screenshot bytes, including the final clear byte 0x10.
PUBLISHED_CIPHERTEXT = bytes.fromhex(
    "e1b9d643f8cd458e0c4ff9fd6f85e4c4"
    "085774954d009ddba1d2ac96d40bcbe9"
)
PUBLISHED_PLAINTEXT = bytes.fromhex(
    "00200120060000000001000000000000"
    "000000002fd9000000000000ffff0010"
)

MULTIPLIER = 0x41C64E6D
INCREMENT = 12345
STATE_MASK = (1 << 24) - 1
MAX_DATA_SIZE = 32 * 1024 * 1024
MAX_KNOWN_PREFIX = 256

PC_SIZE = 0x55DEA0
# The bytes are 00 20 01 20: the little-endian integer is 0x20012000.
PC_VERSION_BYTES = bytes.fromhex("00200120")
PC_VERSION = 0x20012000
PC_HEADER_SIZE = 0x1C
PC_SLOT_COUNT = 10
PC_BASE_SLOT_SIZE = 0x88DF4
PC_NAME_SIZE = 33  # Bytes per name, not a guaranteed character count.
PC_NAME_OFFSET = 0x87842
PC_SLOT_SIZE = PC_BASE_SLOT_SIZE + 2 * PC_NAME_SIZE
PC_SLOTS_END = PC_HEADER_SIZE + PC_SLOT_COUNT * PC_SLOT_SIZE
PC_TRAILER_SIZE = 4
PC_LAYOUT_MARKER_OFFSET = PC_HEADER_SIZE + PC_SLOT_SIZE + 0x938
PC_LAYOUT_MARKER = 0x0036EE7F


def _bytes_input(data, label):
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError(label + " must be bytes, bytearray, or a byte memoryview.")
    if isinstance(data, memoryview):
        if data.ndim != 1 or data.itemsize != 1:
            raise ValueError(label + " must be a one-dimensional byte view.")
        size = data.nbytes
    else:
        size = len(data)
    if size > MAX_DATA_SIZE:
        raise ValueError(label + " exceeds the research byte limit.")
    return bytes(data)


def _state_input(state):
    if type(state) is not int:
        raise TypeError("Stream state must be an integer, excluding bool.")
    if not 0 <= state <= 0xFFFFFFFF:
        raise ValueError("Stream state must fit an unsigned 32-bit integer.")
    return state & STATE_MASK


def transform(data, initial_state):
    """XOR a byte span using an initial LCG state; return immutable bytes.

    This symmetric primitive has no file-format or trailer semantics. The
    first byte uses the state after one LCG advance. Upper eight state bits
    have no effect on the emitted keystream; a recovered low24 class suffices.
    Empty spans are accepted. Neither the input nor the state is modified.
    """
    raw = _bytes_input(data, "Data")
    state = _state_input(initial_state)
    output = bytearray(raw)
    for index, value in enumerate(raw):
        state = (MULTIPLIER * state + INCREMENT) & STATE_MASK
        output[index] = value ^ ((state >> 16) & 0xFF)
    return bytes(output)


def recover_stream_states(ciphertext, known_plaintext):
    """Return all compatible initial low24 classes for a known byte prefix.

    Four to 256 known plaintext bytes are required. Results may contain zero,
    one, or multiple classes: known plaintext must not be assumed correct and
    callers must not select an arbitrary class when recovery is ambiguous.
    Returned integers cannot identify the original account.
    """
    cipher = _bytes_input(ciphertext, "Ciphertext")
    plain = _bytes_input(known_plaintext, "Known plaintext")
    if not 4 <= len(plain) <= MAX_KNOWN_PREFIX:
        raise ValueError("Known plaintext must contain 4 to 256 prefix bytes.")
    if len(cipher) < len(plain):
        raise ValueError("Ciphertext is shorter than the known prefix.")
    masks = bytes(cipher[index] ^ value for index, value in enumerate(plain))
    inverse = pow(MULTIPLIER, -1, 1 << 24)
    candidates = []
    for low16 in range(1 << 16):
        first_state = (masks[0] << 16) | low16
        state = first_state
        for mask in masks[1:]:
            state = (MULTIPLIER * state + INCREMENT) & STATE_MASK
            if ((state >> 16) & 0xFF) != mask:
                break
        else:
            candidates.append(((first_state - INCREMENT) * inverse) & STATE_MASK)
    return tuple(candidates)


def recover_unique_stream_state(ciphertext, known_plaintext):
    """Recover one stream class, rejecting absent or ambiguous evidence."""
    candidates = recover_stream_states(ciphertext, known_plaintext)
    if len(candidates) != 1:
        raise ValueError("Known prefix does not determine one stream class.")
    return candidates[0]


@dataclass(frozen=True)
class PCSlotSpan:
    """Bounded byte spans from the published PC converter layout."""

    index: int
    start: int
    end: int
    first_name: tuple[int, int]
    last_name: tuple[int, int]


@dataclass(frozen=True)
class PCCandidateInspection:
    """Structural observations; none certify integrity or editing support."""

    byte_length: int
    version: int
    selected_slot: int
    slots: tuple[PCSlotSpan, ...]
    layout_marker_offset: int
    layout_marker_value: int
    opaque_tail: tuple[int, int]
    trailer: tuple[int, int]
    checksum_model_verified: bool = field(default=False, init=False)
    integrity_verified: bool = field(default=False, init=False)
    in_game_load_tested: bool = field(default=False, init=False)


def inspect_pc_plaintext_candidate(data):
    """Inspect a full clear PC candidate, without returning editable payloads.

    Exact size, explicit version bytes, selected-slot bounds, ten block/name
    spans, and the published layout marker are required. The marker's actual
    gameplay meaning and the name encoding remain unresolved. The final four
    bytes are opaque: the published utility rewrites a trailer byte during
    transformation without checking the incoming value, so its behavior does
    not establish a validated checksum model.
    """
    raw = _bytes_input(data, "PC candidate")
    if len(raw) != PC_SIZE:
        raise ValueError("Candidate does not have the published native PC size.")
    if raw[:4] != PC_VERSION_BYTES:
        raise ValueError("Candidate does not have the observed PC version bytes.")
    selected = int.from_bytes(raw[4:8], "little", signed=True)
    if not -1 <= selected < PC_SLOT_COUNT:
        raise ValueError("Candidate selected slot is outside the published bounds.")
    marker = int.from_bytes(raw[PC_LAYOUT_MARKER_OFFSET:PC_LAYOUT_MARKER_OFFSET + 4], "little")
    if marker != PC_LAYOUT_MARKER:
        raise ValueError("Candidate does not have the published PC layout marker.")
    payload_end = len(raw) - PC_TRAILER_SIZE
    slots = []
    for index in range(PC_SLOT_COUNT):
        start = PC_HEADER_SIZE + index * PC_SLOT_SIZE
        end = start + PC_SLOT_SIZE
        name_start = start + PC_NAME_OFFSET
        first_name = (name_start, name_start + PC_NAME_SIZE)
        last_name = (first_name[1], first_name[1] + PC_NAME_SIZE)
        if not PC_HEADER_SIZE <= start < name_start < last_name[1] <= end <= payload_end:
            raise ValueError("Candidate PC block or name span is out of bounds.")
        slots.append(PCSlotSpan(index, start, end, first_name, last_name))
    return PCCandidateInspection(
        byte_length=len(raw),
        version=PC_VERSION,
        selected_slot=selected,
        slots=tuple(slots),
        layout_marker_offset=PC_LAYOUT_MARKER_OFFSET,
        layout_marker_value=marker,
        opaque_tail=(PC_SLOTS_END, payload_end),
        trailer=(payload_end, len(raw)),
    )


def inspect_pc_ciphertext_candidate(data, initial_state=None):
    """Read-only structural inspection of an encrypted full PC candidate.

    The initial state is optional: the observed four-byte version can recover
    a unique low24 class. A candidate must still pass every clear-layout check.
    Only the payload before the last four bytes is transformed. The incoming
    trailer is retained untouched and is not treated as verified. No decrypted
    file, mutated save, account ID, or writer is returned.
    """
    raw = _bytes_input(data, "PC candidate")
    if len(raw) != PC_SIZE:
        raise ValueError("Candidate does not have the published native PC size.")
    state = (recover_unique_stream_state(raw[:4], PC_VERSION_BYTES)
             if initial_state is None else _state_input(initial_state))
    clear = transform(raw[:-PC_TRAILER_SIZE], state) + raw[-PC_TRAILER_SIZE:]
    return inspect_pc_plaintext_candidate(clear)
