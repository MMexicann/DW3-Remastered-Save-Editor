# Hyrule Warriors Definitive Edition: Switch native export

The independent adapter opens an extracted `zmha.bin` copy from Nintendo Switch.
It does not decrypt console storage or manage console accounts, keys or import.
The qualified observed profile is exactly **252,132 bytes (`0x3D8E4`)**, starts
with `00261015`, and stores its own complete size as little-endian u32 at `0xC`.
Other sizes, markers, editions and stored-size mismatches are rejected.

## Evidence and provenance

- [EdiZon factual definitions](https://github.com/WerWolv/EdiZon_CheatsConfigsAndScripts/blob/d16d36c7509c01dca770f402babd83ff2e9ae6e7/Configs/0100AE00096EA000.json)
  identify Switch title `0100AE00096EA000`, native filename `zmha.bin`, direct
  little-endian rupees/material quantities, character fields and fairy food.
  Their `bin.lua` performs direct scalar reads/writes without integrity repair.
- [iAroc's dedicated web editor](https://github.com/iAroc/iAroc.github.io/tree/15e4a928bdffb202a7893e14fde432f2dcbc10b3/hyruleWarriors)
  independently corroborates rupees at `0x2B8`, materials at `0x1AFE`, the
  character record group at `0x3307A`, and raw save export without a computed
  checksum. The project supplies no qualified save size or native fixture.
- [Public save-sharing thread](https://gbatemp.net/threads/request-hyrule-warriors-de-editor.506421/)
  contains attachment `hyrule-warriors-zip.130517`, one complete native file.
  The uploader explicitly describes edited progression. It contains nontrivial
  inventories and progression, but its existing hacked values are **not** proof
  of natural limits. The file remains private and is not distributed.
- [EdiZon issue 17](https://github.com/WerWolv/EdiZon_CheatsConfigsAndScripts/pull/17)
  documents successful progress persistence after a save-management bug was
  fixed in EdiZon 1.3.2. Earlier save-lock speculation is not treated as a native
  checksum or antipiracy algorithm.
- [EdiZon issue 8](https://github.com/WerWolv/EdiZon_CheatsConfigsAndScripts/pull/8)
  explicitly distinguishes changing a stored level from updating character
  stats and warns that its EXP action has additional irreversible consequences.
  No such progression action is reproduced here.

No project licence was located for the EdiZon definition repository or iAroc's
editor implementation. This project independently implements the storage,
parser, validation and UI contracts. Only factual byte positions, widths,
record ordering and English item/character identities inform the adapter; no
upstream script, UI, translated catalog, dependency or game asset is included.

The profile checks observed identity/size and preserves unknown bytes. Public
successful direct-file editing supports the current scalar write categories;
no aggregate native checksum is identified or fabricated. The adapter cannot
detect arbitrary corruption in unknown bytes. This is structural qualification,
not cryptographic authentication, and does not qualify other revisions.

## Coverage and precise blockers

| System | Implemented scope / remaining evidence |
| --- | --- |
| Rupees | Manual u32 edits at `0x2B8`, 0..9,999,999. Higher opened originals are preserved and can be restored to unstage. Published edit bounds do not establish a natural gameplay clamp; excluded from automatic Max. |
| Named materials | 102 known bronze/silver/gold factual identities in the u16 inventory beginning at `0x1AFE`; only opened ordinary quantities 1..999 qualify manual edits 1..999. Zero, higher, unidentified and reserved slots remain unchanged. Natural clamps and discovery-bit identities require further proof before Max, exhausted-item refill or acquisition actions. |
| Fairy food | 129 named u8 quantities inspected read-only. The source's 255 target is a storage ceiling; legitimate quantity limits, discovery/ownership and fairy-feed consumption dependencies are unresolved. |
| Character progression | 31 named records, stride `0x30` from `0x3307A`: existing unlock byte+`0xA`, EXP u32+`0x12` and stored level index byte+`0x1A`, all read-only. Need synchronized growth/stat/heart rewards, exact level encoding and acquisition dependencies. Reserved Ganon/Cucco rows are inspected without granting ownership. |
| Character health/attack/badges/combos | No writes. The public source calls one health field uncertain and permits values beyond its u16 width. Native caps, derived growth and badge nodes/costs/prerequisites need controlled growth/allocation pairs or native routines. |
| Weapons, stars, attributes, fusion and seals | Searchable read-only weapon/skill records: the observed profile fits exactly 1,030 physical `0x28`-byte entries from `0x337F4` to EOF. The native sample has 345 occupied entries with matching ID/power/stars/eight skill-ID/eight KO-counter fields. 213 factual weapon names include Yuga's ID 212, which the upstream UI incorrectly excludes. Empty 0xFFFF records are omitted; unknown IDs remain numeric. No writes: state/equip ownership, Master Sword/Legendary/Evil's Bane prerequisites, ordinary seals, skill exclusions, fusion/costs and legitimate power bounds remain unresolved. Other profiles need independent array/layout proof; Wii U's different layout is not reused. |
| Adventure map cards/stages/exploration | No writes. Candidate Adventure offsets do not qualify all nine maps, reward/medal/rank/objective bits, fog, item cards, searches or prerequisite state. Need exact map record identities and controlled use/clear/reward pairs. |
| My Fairy / companions | Food inspection does not edit fairy ownership, element, personality, skills, trust, refresh levels, clothing or companion skills. Need native fairy records and feed/refresh/equip pairs, with growth thresholds and dependencies. |
| Story/character/weapon/costume unlocks | No writes. Unlock flags alone cannot create starter equipment or rewards. Need explicit ownership/entitlement and reward dependencies; story remains separate from resource controls. |
| Collections/gallery/music/movies/medals | No writes; named flag records and legitimate unlock/reward prerequisites are missing. |
| Other revisions/platforms | Need separate complete native samples, their exact identity/size/integrity and independent field maps. Wii U, 3DS Legends, Age of Calamity and Switch 2 are different formats. |

## Validation

Eight format tests and one real Tk workflow pass with `HYRULE_DE_COPY` enabled.
The private shared native file passes byte-exact unchanged roundtrip and a
surgical known-material edit; all bytes outside that u16 remain identical.
Procedural tests separately cover endian encoding, malformed sizes/markers,
stored-size mismatch, immutable snapshots, bounds, unknown/empty/higher-record
exclusions, original-value unstage, disabled Max, read-only character/food/weapon inspection, Yuga/unknown IDs, backups,
exact-byte restore, changed-source rejection and destination protection.
The GUI test covers named search, Apply, Review, Undo, inspection, themes,
backup and Save As. Without a native input, one native test skips explicitly.

**No edited Switch save was imported, loaded or re-saved in the game.** The
shared downloaded file is edited native data, not an untouched gameplay control.
Controlled unmodified before/after saves remain useful for deeper qualification.
