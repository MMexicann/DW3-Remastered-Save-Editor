# Dynasty Warriors 4: PC and PS2 formats

DW4 Hyper and DW4 Xtreme Legends use separate editors and platform selections.
Both implementations follow published format research. **Independent validation
against genuine saves and edited game load/re-save checks remains pending.**
“Published format” does not mean “independently verified editing.”

## Provenance

The supplied references were inspected at these commits:

- [DW4 Hyper PC editor](https://github.com/talkative-platano/dw4hyper-save-editor/tree/3638c8dc23d2607b862a1105bfc9806e69d9e871),
  `3638c8dc23d2607b862a1105bfc9806e69d9e871`: its README and HTML document
  native PC structures, lossless round trips and author-reported game acceptance.
- [DW4 XL PS2 editor](https://github.com/talkative-platano/dw4xl-save-editor/tree/b3ea895c6e854accd6860fd51ce69aeb024f53e9),
  `b3ea895c6e854accd6860fd51ce69aeb024f53e9`: documents USA `SLUS-20812`,
  memory-card exports and author-reported controlled difficulty/stat/item edits.

These are source-backed observations, not official format specifications. Neither
repository supplied a complete genuine fixture for independent local validation.
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

The Hyper adapter exposes 331 bounded integer fields: standard officer playable
flags, Life/Musou/Attack/Defense, character EXP, weapon EXP, 32 semantic items,
four bodyguard point values and difficulty. Equipped item references, bodyguard
names and custom character presence are inspected; custom records, equipment,
challenge rankings and suspended battle data are preserved.

The XL adapter's scope is 298 bounded integer fields: 42 officers' four stats,
character points and weapon EXP, 41 semantic items, four bodyguard point values
and difficulty. It preserves equipment references and bodyguard names for
inspection. The officer record's first byte is published as a constant marker;
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
equipment references. These relationships still require independent game checks.

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

Provide original, unchanged copies privately and identify edition, region and
game build:

- Hyper: native 69,568-byte `save.dat`; displayed officer/item/weapon values;
  normal-save and suspended-save examples if both are to be qualified.
- XL: a complete USA `SLUS-20812` `.psu` export retaining directory entries,
  metadata, icon files and padding. Include the exact 34,064-byte game entry.
- For each platform: an unchanged control pair and separate before/after pairs
  changing one stat, one character EXP/point value, one weapon EXP/special weapon,
  one item, one bodyguard point value or difficulty through the game.
- Finally: controlled edited-copy import/load/re-save checks with the displayed
  results. Procedural tests and correct checksums do not replace this evidence.

Other PS2 regions, original DW4, Xbox editions and modified formats are separate
verification targets. No save sample, console key or account data belongs in a
source or release package.
