# Nioh 3 native PC integrity qualification

This pass independently qualifies two publicly shared native PC user files and
one matching encrypted/decrypted USER pair. It implements strict source-only
inspection in `nioh3_native.py`, including native body integrity validation.
**No Nioh 3 gameplay editor or library card is enabled.** The acquired native
files do not qualify the published fixed inventory maps.

## Qualified native envelope

| Native property | Qualified value |
| --- | --- |
| User file size | `0x9001B0` |
| Clear user identity | `RNNUSR` followed by two zero bytes |
| Header size | `0x158` |
| Body size | `0x900058` |
| Header length/body length fields | u32 little endian at `0x18`/`0x1C` |
| Observed user revisions | u32 `0x01030001` and `0x01040000` at `0x08` |
| Matching body revision | u32 at `0x15C` |
| Integrity-covered body | `[0x190, 0x900190)` |
| Integrity seed/result | u32 little endian at `0x900190`/`0x900194` |
| Cipher exclusion | Final eight bytes, retained exactly |

The per-save checksum starts with an unsigned 64-bit zero accumulator. For each
`0x400`-byte block in the covered body, sum 128 signed little-endian 64-bit
values, add that sum to the accumulator, XOR with the stored 32-bit seed and
reduce to 64 bits. The resulting checksum is
`(accumulator // 0xFFFFFFFF + (accumulator & 0xFFFFFFFF)) & 0xFFFFFFFF`.
The division is not a normal upper-word shift. This is the native game's weak
integrity checksum, not a cryptographic authentication claim. No flags are
cleared, damaged input is not repaired, and the original seed is retained.

The existing MIT-attributed Katana primitives reproduce the encrypted
USER sample's entire decoded gameplay body. The published plaintext fixture has zeroes in the 64-byte body-key span
`[0x49, 0x89)`, while its encrypted partner retains wrapped key material there.
The inspection decoder preserves the original decrypted header with wrapped
key material and retains the unencrypted final eight bytes. The entire body,
all header bytes outside that key span and the tail match the acquired reference
exactly. The full decoded files are not asserted to be byte-identical across
their different key representations. No account rebinding is exposed.

## Coverage and precise blockers

| Discovered system | Result or required evidence |
| --- | --- |
| Native identity/revision/size and body checksum | Implemented source-only validation; genuine files and malformed-input tests |
| Native encryption/decryption | Genuine encrypted USER pair qualifies decoded representation; exact no-op return preserves original ciphertext |
| Currency and seven character attributes | Published offsets fail to independently qualify these acquired revisions; needs displayed-value/controlled-change correspondence |
| Existing equipment level and pre-forge level | Published equipment record fields differ from claims of universally mirrored levels. A genuine record has level 16 and pre-forge 8; never rewrite both on a presumed mirror |
| Existing equipment reinforcement | Published per-record `+0x0A` map has controlled observations in another project, but exact native array base/count/version remains unqualified here |
| Affix IDs/values and fixed/inherited/star metadata | Source descriptions exist; effect limits depend on category and game build, and external catalogs/asset-derived data are not incorporated. Needs qualified native pool plus factual independent category limits |
| Existing scroll fields, attempts and seeds | Published fixed pool `0x176CCE`, 400 x `0xE8`, contains no populated scrolls in either acquired file. Need a native USER save with an owned scroll and a controlled attempt/reward change |
| Equipment/consumable/storage pool boundaries | Published fixed addresses `0x270066`, `0x302832`, `0x35779E` do not qualify these files. Mirrored candidate equipment headers cluster elsewhere, but heuristic matches do not prove an owned inventory, pool boundary or revision-independent array |
| Appearance, equipped flags/references and ownership | Separate from numeric equipment stats. Need controlled appearance/equip/acquisition pairs and validation of cross references |
| Level, EXP, skills/proficiency, story, missions and collections | No independently qualified native disk maps or reward transitions established; level/stat changes alone would not model these dependencies |

The unregistered module therefore accepts qualified USER copies for inspection,
returns an unchanged copy byte for byte and rejects every gameplay edit. It
rejects SYS data, unobserved revisions, inconsistent inner revision/lengths,
truncation, oversized input, corrupted covered bodies and forged snapshots.

## Source and licence provenance

Only independently authored factual implementations are contributed. No GPL or
PolyForm implementation, catalog, extracted game data, player save or account
identifier is included in this project's public source/runtime packages.

- [alfizari/Nioh-3-Save-Editor](https://github.com/alfizari/Nioh-3-Save-Editor/tree/b5d0789791fe31d06ad325d4012aa0333c60cd8f),
  commit `b5d0789791fe31d06ad325d4012aa0333c60cd8f`, Apache-2.0: two native user
  copies, matching encrypted/decrypted pair, envelope/body-checksum observations
  and inventory/stat mapping leads. Third-party executables were not executed.
- [Master-Bayesian/Nioh3-Scroll-Generator](https://github.com/Master-Bayesian/Nioh3-Scroll-Generator/tree/4e2ec6d3e9640ba11e821adc7b037d793a112448),
  commit `4e2ec6d3e9640ba11e821adc7b037d793a112448`, GPL-3.0: independently
  corroborating native USER checksum, scroll semantics and version-scoped maps.
- [lylarcher/Nioh3EquipmentAffixEditor](https://github.com/lylarcher/Nioh3EquipmentAffixEditor/tree/2409a4fdb9fbf948f65d3958ec94c2b31d5b5404),
  commit `2409a4fdb9fbf948f65d3958ec94c2b31d5b5404`, PolyForm Noncommercial:
  documented moved/variable inventory layouts, reinforcement observations and
  fixed-affix dependencies. No code or datasets are reused.
- [mi5hmash/KatanaSaveDataResigner](https://github.com/mi5hmash/KatanaSaveDataResigner),
  MIT: custom-cipher family comparison. Its Nioh 3 reference pair is SYS data,
  not a player USER fixture. Ronin and Fatal Frame II fixtures are labelled
  dummies, so those do not establish another gameplay editor.

`tests/test_nioh3_native.py` supplies independent signed-boundary vectors and
procedural malformed-input checks. Optional locally held native copies are
selected using `NIOH3_NATIVE_DIR`; the pair uses `NIOH3_ENCRYPTED_COPY` and
`NIOH3_DECRYPTED_COPY`. Native qualification and unchanged roundtrips do not
constitute actual Windows game-load validation.
