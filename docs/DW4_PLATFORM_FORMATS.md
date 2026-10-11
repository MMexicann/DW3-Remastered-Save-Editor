# Dynasty Warriors 4: PC and PS2 formats

DW4 Hyper and DW4 Xtreme Legends use separate editors and platform selections.
Both implementations follow independently reimplemented published format facts.
A public native Hyper save and two independently shared USA XL saves qualify
identity, integrity and surgical edits. **Edited game load/re-save checks remain
unperformed.** Native file qualification and game acceptance are separate.

## Provenance

The supplied references were inspected at these commits:

- [DW4 Hyper PC editor](https://github.com/talkative-platano/dw4hyper-save-editor/tree/3638c8dc23d2607b862a1105bfc9806e69d9e871),
  `3638c8dc23d2607b862a1105bfc9806e69d9e871`: its README and HTML document
  native PC structures, lossless round trips and author-reported game acceptance.
- [DW4 XL PS2 editor](https://github.com/talkative-platano/dw4xl-save-editor/tree/b3ea895c6e854accd6860fd51ce69aeb024f53e9),
  `b3ea895c6e854accd6860fd51ce69aeb024f53e9`: documents USA `SLUS-20812`,
  memory-card exports and author-reported controlled difficulty/stat/item edits.

These are source-backed observations, not official format specifications. Neither
repository supplied a complete genuine fixture. Public samples were acquired
separately, rather than treating an editor's procedural example as a player save.
The Python implementations are independently authored; external implementation
code, screenshots, icons and game saves are not shipped with the application.

## File and integrity boundaries

| Property | DW4 Hyper — native Windows PC | DW4 XL — PS2 USA SLUS-20812 |
| --- | --- | --- |
| Selected file | Copied raw `save.dat`, `.dat` | Copied `.psu` memory-card export |
| Game data | Entire file, `0x10FC0` / 69,568 bytes | Exact inner `BASLUS-20812` entry, `0x8510` / 34,064 bytes |
| Container | No memory-card wrapper | 512-byte directory entries; file data padded to 1,024-byte boundaries |
| Checksum | Little-endian u32 at `0x10FA8`, sum of bytes before that offset | Little-endian u16 at offset 0, sum of inner bytes from 4 to the end, modulo 65,536 |
| Additional checks | 20 zero trailer bytes; standard roster indices; difficulty 0–2 | Product/directory and payload identity; inner version u16 at 2 equals 3; difficulty 0–4 |
| Encryption | Published layout is plaintext | Published inner layout is plaintext |
| Difficulty | Easy 0, Normal 1, Hard 2 | Novice 0, Easy 1, Normal 2, Hard 3, Expert 4 |
| Item inventory | 32 entries; equipped empty sentinel 32 | 41 entries; equipped empty sentinel 41 |

The XL source's example puts its payload at `0x1C000`. That is an observed
container position, **not a universal offset**: the parser walks the export's
directory records and padded file lengths. Save metadata, icons, timestamps,
other entries and padding must survive unchanged.

Hyper normal saves and suspended battle saves share the same PC file layout.
The published source identifies a suspended battle by a nonzero total-time value
at `0xB170`; it does not establish a general file-type byte. This application
preserves suspended battle and challenge-ranking blocks. It does not reinterpret
them as ordinary officer progression or claim to edit live battle entities.

An extension alone is insufficient identity. Hyper data must not be sent through
the XL parser even where offsets happen to coincide. The XL editor accepts the
declared USA PSU format; whole `.ps2` memory cards, save states, `.max`/`.cbs`/`.psv`
containers and other regional product IDs need their own format verification.

## Implemented field scope and published limits

Shared published structures include 42 standard officer records at `0xB8` with
24-byte stride, u16 weapon EXP at `0x798 + 2 × officer`, item bytes at `0x7F6`,
and four bodyguard team records at `0x508` with 96-byte stride. Shared locations
do not imply shared validation rules.

The Hyper adapter exposes 415 base bounded integer fields: standard officer playable
flags, Life/Musou/Attack/Defense, character EXP, weapon EXP, 32 semantic items,
four bodyguard point values, difficulty and 84 harness/orb assignments. Existing
identified custom appearances expose up to five cosmetic fields each: color,
head, chest, arms/legs and hip. Named choices distinguish gender-specific clothing.
Creation, gender, moveset, weapon model, names and unknown metadata stay unchanged.
Unknown cosmetic enums remain read only. The genuine sample exposes 435
base/custom fields plus 192 qualified occupied general-item slots, totaling 627.

An existing custom's five manual stat/EXP controls are additionally offered only
when its 24-byte appearance/roster originals already match, its model copies are
known and equal, and its duplicate Attack/Defense values agree. These writes
synchronize only the mapped value across all corresponding copies. The supplied
public Hyper reference has four differing appearance templates and grown roster
records: its stat/EXP controls are therefore excluded, while its cosmetics remain
editable. No edit repairs or reconciles different templates. Up to 455 base/custom
fields can appear on a fully matching layout, plus qualified occupied general
slots; those matching-custom-record tests are procedural.
Custom stat 255 and EXP 65,535 are manual storage bounds, excluded from Max.

Equipment, bodyguard names, custom identities, challenge top-10 tables and the
suspended timer are searchable inspections. Challenge scores distinguish points
from Time Attack's frames at 60 fps. Suspended phase bytes can change within a
battle and are not story-clear flags. Originally occupied known-owned general
slots now allow replacement or unequip; empty/unqualified general slots and
live battle entities remain unchanged.

The XL adapter's base scope is 382 bounded integer fields: 42 officers' four stats,
character points and weapon EXP, 41 semantic items, four bodyguard point values
and difficulty, plus 84 owned harness/orb assignments. Additional originally
occupied known-owned general slots allow replacement or unequip; the tested
native export exposes 189 such slots, totaling 571 fields. Empty/unqualified
general slots and bodyguard names remain read only. The officer record's first byte is published as a constant marker;
it is not treated as Hyper's playable/unlocked flag.

| Value | Published meaning and editing bound |
| --- | --- |
| Weapon EXP | Normal progression 0–36,000; special Lv.10 value 36,001 in both; XL alone adds Lv.11 value 36,002 |
| Leveled items 0–12 | Levels 1–20 |
| Orbs 13–18 | Levels 1–4 |
| Remaining items | Ownership only: locked or owned; Hyper 19–31, XL 19–40 |
| Stored item byte | `0xFF` locked; otherwise displayed level equals stored byte plus 1; editor value 0 means locked |
| Officer stat bytes | 0–255 is the storage bound; a natural maximum has not been independently established |
| Character EXP/points and bodyguard points | 0–65,535 is the u16 storage bound; normal progression thresholds are not independently established |

Weapon levels are reported as EXP-derived by the supplied research. Bodyguard
stats and guard availability are reported as point-derived. Equipment-slot
availability grows with weapon progression; granting items must preserve existing
equipment references. Harness slot 0 permits owned IDs 19–23 and orb slot 1
permits owned IDs 13–18; each platform retains its own empty sentinel. Pending
item grants can precede harness/orb assignments. Locking an owned item is rejected
while an officer still equips it. Granting a rare item does not clear its stage.
General-slot availability thresholds and their weapon-progression dependency
remain unqualified. Slots 2–7 are writable only when the original position
contains a known-owned general item: general IDs 0–12 and 24–31 for Hyper,
0–12 and 24–40 for XL. They can be replaced by an originally owned general item
or cleared with the platform's empty sentinel; empty original slots cannot be
filled, and pending grants cannot qualify a target. Final ownership and unique
general-item assignments are checked, and that officer's weapon EXP must stay
unchanged in the same staged batch. Max excludes these choices. The field proof,
independent native matrices and Tk checks are recorded in
[Samurai / classic Dynasty editor depth](SAMURAI_DYNASTY_DEPTH.md).
These relationships still require independent game-load checks.

Bulk Max uses the published weapon/item limits and preserves higher existing
weapon EXP. Uncertain stat/character-point/bodyguard-point bounds and difficulty
are excluded from Max. Hyper receives no XL-only items or Lv.11 weapon value.
Unknown bytes and unrelated structures remain unchanged.

## Windows application, exported PS2 data

The Windows executable can edit a copied PS2 `.psu` export because the export is
an ordinary file on the computer. It does not access the running game, console,
emulator memory, game installation or live memory-card filesystem. Export and
later import are separate user actions through a suitable memory-card tool.
Opening a copy stages changes; Review, Undo, automatic original backups and
Save As operate on the copied data. Merely opening a file does not modify
the selected export or live save.

## Samples needed for independent qualification

Public qualification sources, kept private and never included in the project:

- [SaveGame.Pro native Hyper save](https://savegame.pro/pc-dynasty-warriors-4-hyper-savegame/),
  described as 100% completed with all items, weapons and characters unlocked.
  The save qualifies exact size, standard identities, trailer and checksum.
- [GameFAQs USA XL archives](https://gamefaqs.gamespot.com/ps2/915429-dynasty-warriors-4-xtreme-legends/saves),
  entries 11988 (CodeBreaker) and 6829 (MAX Drive), independently shared completed
  states. Both contain the exact 34,064-byte `BASLUS-20812` gameplay file.
  Japanese entry 4640 and European entry 5256 were independently extracted and
  correctly rejected by the USA adapter.

Archive conversion was performed privately using Ross Ridge's public-domain
[mymc archive facts](https://github.com/ps2dev/mymc/blob/master/ps2save.py),
its LZARI codec and MIT/public-domain
[mymc-py directory packing](https://github.com/G4brym/mymc-py). CodeBreaker RC4
and zlib and MAX Drive LZARI are archive compression/encryption, distinct from
the plaintext native XL gameplay format. Conversion preserves native file bytes;
MAX archives do not supply original memory-card timestamps, so generated PSU
metadata is not claimed to be an original console-produced PSU export. No
converter, external implementation or sample is shipped. Neither gameplay
reference repository declares a licence; its factual offsets and names informed
independent Python implementations rather than a source-code import.

Focused checks include per-field genuine surgical edits (627 Hyper fields and
571 XL fields in the latest qualified copies), unchanged roundtrips, exact source preservation, integrity,
unknown bytes/container files/padding, copied-file Tk named equipment/custom
controls, Review, Undo, Max exclusion, backup and same-bytes validated restore.
Fixtures are opt-in through `DW4HYPER_SAVE_COPY` and `DW4XL_PSU_COPY`; unavailable
fixtures or displays produce skips. No game binary is executed.

Provide original, unchanged copies privately and identify edition, region and
game build:

- Hyper: additional normal/suspended native copies with displayed values; an
  in-game-created custom and a controlled growth pair to distinguish template
  stats from grown roster stats before editing mismatched records.
- XL: an original USA `SLUS-20812` `.psu` export retaining directory entries,
  metadata, icons and padding, to complement converted genuine archive evidence.
- For each platform: an unchanged control pair and separate before/after pairs
  changing one stat, one character EXP/point value, one weapon EXP/special weapon,
  one item, one bodyguard point value or difficulty through the game.
- Finally: controlled edited-copy import/load/re-save checks with the displayed
  results. Procedural tests and correct checksums do not replace this evidence.

Other PS2 regions, original DW4, Xbox editions and modified formats are separate
verification targets. No save sample, console key or account data belongs in a
source or release package.

## Mechanics coverage and remaining boundaries

| System | Implemented scope / specific remaining blocker |
| --- | --- |
| Standard stats and character EXP/points | Bounded manual edits; natural stat caps and EXP/stat growth thresholds are not qualified for automatic Max. |
| Weapons | Published EXP-derived progression and each platform's special weapon values; general-slot thresholds need controlled progression/equipment pairs. No XL Lv.11 value is offered in Hyper. |
| Items and equipment | Named levels/ownership, category-checked owned harness/orb assignments and replacement/unequip in originally occupied known-owned general slots. Empty general positions remain unwritable pending availability thresholds; no stage/rare-item reward completion is bundled in grants. |
| Bodyguards | Team points edit; names inspected. Natural thresholds, count/type/growth effects and safe name encoding writes need action pairs. |
| Hyper custom characters | Existing identified cosmetics and matching-record manual stat/EXP edits; differing template/grown roster data preserved. Creation, deletion, gender/moveset/model changes need full coupled initialization and stat-generation qualification. |
| Hyper challenge rankings | Sorted record order, officer IDs and points/frame scores inspected. Editing needs legitimate score bounds and safe insertion/sort/reward dependencies. |
| Hyper suspended battle | Timer snapshot inspected. Linked alive/dead state, leader HP, aggregate guard life/count, morale, guard availability and variable squad identities need controlled suspend/resume pairs; isolated trainer targets are insufficient. |
| Campaigns, stages, movies/music and history | Unknown completion and reward flags retained; content dictionaries and prerequisite relationships remain unqualified. |
| Other PS2 regions, base DW4, legacy SW2/XL/Xbox | Distinct product, serialization and platform profiles required; no region substitution or console-to-PC offset fallback. |
