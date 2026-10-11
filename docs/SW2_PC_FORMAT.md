# Original Samurai Warriors 2 — Windows PC

This is the original 2008 Windows PC game, native disk save revision 2. It is
not SW2 HD, Xtreme Legends, Empires, a console export or a later Samurai Warriors
game. The `sw2` adapter uses the existing scalar GUI, staged Undo, Review Changes,
automatic original backups and guarded atomic Save As to a new copied-save path.
The latest own-pool equipment expansion and checks are documented in
[Samurai / classic Dynasty editor depth](SAMURAI_DYNASTY_DEPTH.md).

## Evidence and licence boundary

The period [Van SW2Editor 1.00 Build 706 description](https://dl.3dmgame.com/patch/14394.html)
explicitly identifies original PC traditional-Chinese 1.0 disk-save support.
The archive contains a July 2008 Windows editor with native disk reader/writer
and per-record getters/setters. Static NRV decompression and UPX call-filter
reversal were performed privately; packed/unpacked Adler checks agreed. No
downloaded executable was run. The author restricts redistribution: no binary,
source, UI resources, extracted catalog or implementation from that editor is
included here. The adapter independently implements the observed format facts.

Two independently shared complete PC saves were obtained from
[Speedrun's original SW2 PC resource](https://www.speedrun.com/sw2/resources/u6qw3)
and [SaveGame.Pro's original 2008 PC save](https://savegame.pro/pc-samurai-warriors-2-savegame/).
Both qualify the exact native size, revision, checksum, officer/weapon layout
and unchanged byte roundtrip. These are genuine shared gameplay files, not
controlled clean-game action pairs; advanced/modded values are preserved. Save
contents, player context and input hashes remain private and are not fixtures.

The official UK 1.1 patch was also statically unpacked from its distribution.
Its protected executable did not supply a readable serializer in this review.
Neither a game executable nor a DRM runtime was executed. The format evidence
comes from the period disk editor and the independent complete PC copies.

## Serialization and integrity

| Native fact | Mapping |
| --- | --- |
| File size | Exactly `0x22EB4` / 143,028 bytes |
| Disk revision | Little-endian unsigned 16-bit `2` at offset `4` |
| Encoding | Plain fixed-size bytes; little-endian integer fields |
| Integrity | Sum of unsigned bytes `[0, 0x22E94)`, modulo `2^32` |
| Stored checksum | Little-endian unsigned 32-bit at `0x22E94` |
| Remaining trailer | 28 bytes after the checksum; untouched, outside coverage |

The static reader checks exact file size, revision and checksum before exposing
records; the writer stores the same additive sum and writes the exact native
length. Its file buffer is based at `0x4ABFB0`; reader/writer routines begin at
`0x407AF0` / `0x407C50` in this specific period editor. The native reader does
not check the first DWORD, the upper revision word or trailer contents. The
adapter preserves these instead of inventing zero-padding requirements.

There is no intrinsic title string or cryptographic title authentication.
Original-PC provenance, independently corroborated native serialization and
the static original-game record accessors establish this supported profile.
Selected adapters never fall back to another game's parser. Known foreign
sizes/revisions, truncation and corruption reject; an adversary could construct
a same-sized revision-2 file with a valid additive sum. That limitation is not
hidden behind invented fingerprint markers.

## Records and writable scope

| Record or field | Layout and behavior |
| --- | --- |
| Money | Unsigned 32-bit balance at `0x2150`; adjacent history remains untouched |
| Officers | 26 records, base `0xC`, stride `0xEC`, original roster order |
| Stored growth | Eight unsigned 32-bit values at officer `+0`: Life, Musou, Attack, Defense, Riding, Speed, Dexterity / Jump, Luck |
| EXP and level | Unsigned 32-bit EXP `+0x20`, zero-index level byte `+0x24`; read only |
| Weapons | Eight 19-byte existing records at officer `+0x28`; byte identity, element, eight attribute IDs, eight amounts and occupied-slot count |
| Equipment | Equipped weapon byte index `+0xC0`; existing qualified own-pool selection on already owned officers |
| Skills | 40 rank bytes at `+0xC1`; low seven bits are rank, high bit is preserved separately |
| Unique ability | Byte `+0xE9`; read only, as are adjoining unqualified bytes |
| Officer ownership | Bitset at `0x214C`; never changed by money/growth/skill/weapon edits |
| Guards | 54 catalog growth records, base `0x1804`, stride `0x2C`, eight stored stats, EXP `+0x20`, level byte `+0x24`; inspected only |

The period accessors independently establish the officer/guard strides, stat
widths, EXP, byte-level level encoding, skill mask and weapon fields. Weapon ID
`0x7F` is empty; IDs below 104 follow four weapon tiers for each of 26 officers.
Bonus IDs 0–7 refer to the eight stats, 8 to Musou charge and 9 to range; 10
is no attribute. Unknown identities and unqualified slot/type/count combinations
stay opaque. Within weapon records, only an occupied attribute on a known weapon belonging to its
original officer record is writable. Identity, element, attribute IDs, slot
count, inventory and equipped reference are not changed by bonus edits.

Equipped weapon selection is a separate control. It accepts only existing
known own-family weapons from that owned officer's eight-slot pool with
occupied bonus counts 1–8. Empty ID 127, unknown/foreign families and unusual
count-zero records stay unavailable as targets. Selection writes only `+0xC0`;
identity, element, bonuses, count, inventory and ownership remain unchanged.
It is excluded from Max, and an unusual original reference can be restored
through unstaging.

The seventh stat is labeled `跳跃` (Jump) in the period PC editor. The
[original English game guide](https://gamefaqs.gamespot.com/ps2/930941-samurai-warriors-2/faqs/44990)
uses `Dex` for Dexterity. The adapter labels this stored growth value
`Dexterity / Jump` to make both terms recognizable; this mechanics reference
does not establish PC offsets or replace verification of derived display totals.

Growth edits are selected only from already owned officers. Ordinary acquired
skills may be set to ranks 1–3; unacquired and each category's rare final skill
are excluded. The skill high bit survives writes, and assigning an unusual
opened rank unstages an edit without normalizing it. Ordinary categories are
numbered honestly: an English per-slot skill-name enum is not yet independently
qualified. Numeric money/growth/weapon edits use their documented integer
storage widths; those ceilings are explicitly not natural gameplay maxima.
Bulk Max leaves all these fields unchanged.

## Mechanics and remaining inputs

The [original game's publisher manual](https://manualzz.com/doc/70494033/games-microsoft-xbox-samurai-warriors-2-owner-s-manual)
is used for mechanics only, not PC offsets. Gold purchases skills, weapon
improvements, guards and mounts. Character level grows with EXP; Might skills
increase stats and Growth skills affect future growth. Weapon bonuses contribute
to displayed totals. Story/Free/Survival progress and reward unlocks are separate
from a money balance or stored growth value. The game supports eight weapon
slots per officer, eight hired guards and three owned horses.

Guard catalog growth is not hired ownership. To expose guard or mount editing,
need original-PC controlled hire/release/equip and horse purchase/replace pairs,
including displayed stats and an unchanged control. Rare skills require a
controlled shop/Survival unlock and acquisition pair establishing prerequisites.
Progression needs controlled original-PC Story/Free/Survival clear and interim
save pairs mapping history, completion, unlocks and rewards separately. Level
and EXP need controlled level-up pairs proving threshold/derived dependencies.
Own-pool weapon references are implemented without acquisition or new records.
Other equipment references, including guards and mounts, still require
owned-record/equip pairs. These precise inputs are missing; those bytes remain
untouched by the functioning resource/growth/equipment editor.

## Validation distinctions

`tests/test_sw2_pc_format.py` supplies procedural contract, corruption, wrong
revision/platform, unusual values, high-bit preservation, existing-record
dependencies and surgical byte-preservation checks. Its optional
`SW2_PC_SAVE_COPY` test separately exercises a complete genuine file's unchanged
roundtrip and surgical money edit. Shared contract tests cover backups, restore,
source mutation, immutable staging and new destinations. Independent review
tests add malformed pending batches, spoofed/mutable snapshots and unchecked
header/trailer preservation.

`tests/test_sw2_pc_gui.py` runs actual Tk callbacks through the registered
Windows PC library card: copied open, search, stage, Review Changes, Undo,
retained session, theme changes, inspectors, Save As, original backup and restore.
An optional genuine-file GUI workflow uses a temporary copy of `SW2_PC_SAVE_COPY`.

Both independent genuine files were parsed and round-tripped unchanged; their
money edits were reserialized with native checksum and reparsed, without
changing input files. A separate private surgical matrix exercised every
discovered writable field: 2,329 individual edits in the first copy and 2,314 in
the second. Each reparsed successfully and changed only that scalar's bytes
and the required checksum. Those matrix checks are genuine-file serialization
evidence, separate from the public procedural suite.

**Actual edited Windows game load/re-save has not been
performed.** Procedural and genuine-file checks do not imply that validation.
