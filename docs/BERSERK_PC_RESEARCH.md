# Berserk and the Band of the Hawk: Windows qualification

The Windows game remains **research-only**. A complete public native file
qualifies its observed outer cipher and checksum, but the native gameplay
records, save revision and any further integrity have not been established.
No writable fields or library card are registered. The identified existing
save editor targets PS Vita and cannot supply Windows field mappings.

## Native file evidence

The [SaveGame.Pro contribution](https://savegame.pro/pc-berserk-and-the-band-of-the-hawk-savegame/)
contains `BKSAVEDATA0000.dat`, 1,268,512 bytes (`0x135B20`). It was reacquired
privately for this investigation. The contributor's “100% completed” label
does not establish ordinary field values, the installed DLC, region, executable
build, save revision or a successful edited game load. The archive's shortcuts
and link files were not run; only the native data file was extracted.

Observed complete-file facts:

- The first four bytes store a little-endian u16 checksum and u16 seed.
- Starting at the stored seed, each complete payload u32 is XORed with the
  state after **three** advances of
  `state = (state * 0x5B1A7851 + 0xCE4E) mod 2^32`.
- The checksum equals the sum of all decrypted little-endian u16 words modulo
  65,536. The decoded payload is `0x135B1C` bytes.
- Payload offset `0` starts the exact ASCII title
  `BERSERK and the Band of the Hawk`, followed by NUL padding. Offset `0x80`
  starts the ASCII display label `Saved Data: 1`. Neither the display label
  nor the opaque decimal text in the following header establishes a native
  format revision. The player's remaining header/body contents stay private.
- The original seed and entire ciphertext are preserved by an unchanged
  decrypt/encrypt roundtrip. Independently tested one- and four-advance
  candidates fail this native checksum. Single-bit changes at the first and
  last ciphertext payload bytes fail the matching outer checksum.

These facts qualify one observed envelope. They do not prove a semantic record
layout or the absence of internal integrity. A recomputed outer sum alone
cannot authorize a gameplay write. Complete-byte identity, payload identity
and native checksum validation are file tests; no edited output was imported,
loaded or re-saved in the game.

## Existing editor and source survey

| Reference | Scope and licence finding | Consequence for a Windows editor |
| --- | --- | --- |
| [EvilGoku's GBAtemp release](https://gbatemp.net/threads/release-berserk-and-band-of-the-hawk-save-editor.503586/), May 11, 2018 | The thread is in Sony PS Vita. Its attachment contains one .NET GUI executable and no source or licence. Static metadata explicitly titles it “Berserk and Band of the Hawk (U) Save Editor Psvita”. Its controls cover character status, gold and materials. | Static inspection found direct byte reads/writes without the Windows cipher, native checksum, title/revision or complete-layout qualification. No Windows field equivalence was proved. The executable was never run, and its implementation and private analysis are not distributed. |
| [iccugs/BERSERK_trainer](https://github.com/iccugs/BERSERK_trainer/tree/afec9a6c7685b3b6c9bb7092762a686af9b99937), `afec9a6c7685b3b6c9bb7092762a686af9b99937` | Live process trainer; no implementation licence located. Its gold control is commented out. | Live gauges, pointers and large cheat targets do not qualify disk offsets, persistent growth or natural limits. No code was copied or run. |
| [Lyall/BerserkFix](https://github.com/Lyall/BerserkFix/tree/c64747519f6967df6264a1efbd7bf369f7b3aea5), `c64747519f6967df6264a1efbd7bf369f7b3aea5` | MIT display, frame-rate and runtime fixes. | The reviewed source contains no native save serializer or inventory/progression schema. No source was incorporated. |
| [ayozetr's PC tutorial translation](https://github.com/ayozetr/berserk-band-of-the-hawk-es/tree/a10d3affa706dc9d4650f5f54e82bb90c251986c), `a10d3affa706dc9d4650f5f54e82bb90c251986c` | The licence grants MIT terms to the original software/docs and explicitly excludes `translation/`, which derives from Koei's game text. | Mechanic facts are summarized with attribution; translated text, catalogs and game assets are not bundled. LINKDATA/text layouts are asset layouts, not player-save records. |

Repository and code searches for the exact native basename, the PC title with
save/checksum terms, and Berserk save-editor projects found no qualifying public
Windows save serializer. PS Vita save exports and PS4 cheats remain separate
platform evidence. The source survey supplies leads and mechanics, not a licence
to transplant unverified console or runtime offsets.

## Persistent mechanics and dependencies

The official [Steam PC manual](https://store.steampowered.com/manual/502280)
is the primary mechanical reference. Page numbers below are its printed pages.
It is read privately, with no manual pages/assets included in this repository.
The tutorial reference supplies additional rules absent from the short manual.

| Mechanic | Established gameplay facts | Required native mapping before editing |
| --- | --- | --- |
| Money and materials | The briefing shop buys and sells accessories/materials (manual p24); the tutorial also distinguishes purchasable equipped items and shop stock refreshed after victories (`e2575.u11.s76`). Enhancement consumes materials of the skill's corresponding color (p25, tutorial `s78`). | Current quantities versus earned/spent history; native IDs, widths, arrays, unusual values and item/reward ownership; monetary/material limits and costs. Do not adopt a trainer target, storage ceiling or the progressed sample's values as Max. |
| Existing accessories and reinforcement | Three accessories can be equipped (p29). An accessory can carry four skills; amalgamation combines skill levels and consumes the other accessory (p26). Tutorial `e2575.u11.s75` and `s78`–`s81` distinguish duplicate equipped effects, reinforcement to +9, class promotion using rare materials and choosing inherited skills when more than four result. | Occupied-record identity, item/class/rarity IDs, reinforcement versus promoted class, four skill IDs/ranks, native base stats, equipped references and material compatibility. The +9 mechanic does not prove its storage encoding or permit creating accessories. |
| Character growth and skills | Character level naturally reaches 99; EXP increases level, stats and sometimes available actions (p27). Tutorial `e2575.u11.s89` distinguishes action-level unlocks and vitality restoration on level-up. | Per-character ownership and record identity, EXP curve, stored level versus derived stats, action prerequisites and reward transitions. A manual cap is not an offset map; level or EXP writes cannot bypass unresolved dependent fields. |
| Frenzy, death blow and sub-weapons | The manual describes battle gauges and character-specific battle effects; accessories affect their operation (pp9–14, p28). | Determine which quantities persist. Runtime gauge pointers do not establish stored growth, transformation, skill ownership or cooldown fields. |
| Warhorses | Scenario completion or special battle conditions unlock horses (p30). Charge power, endurance and speed are distinct. | Existing ownership, horse identity and equipped references; do not create a reinforcement system or edit unlocks as resource quantities. |
| Endless Eclipse and behelits | Desires span five layers; depth affects rewards, checkpoints open after reaching layers, and stray war demons can award behelits (pp31–32). Tutorial `e2575.u11.s86`–`s90` separates story-gated depth, per-character layer rewards, shared first-time desire progress/rewards, and an active run whose vitality/items and abandonment rules differ from permanent records. | Character-specific cleared layers/checkpoints and reward claims; shared desire identity/first-clear/claim flags; active-run state and behelit/gallery prerequisites. A numeric floor/desire edit must not silently grant, reset or duplicate rewards. |
| Story, gallery and unlocks | Story clears add battles/events (pp23–24); tutorial `e2575.u11.s82`, `s85` connects behelits to gallery panels and scenarios to events. | Separate completion/ranks, reward claims, ownership, entitlement and resource edits. No blanket story-completion or unlock operation is qualified. |

## Exact enabling inputs

The shortest path to an editor is a matched Windows serializer/getter or
controlled native action pairs with the corresponding displayed values and
build context. Further unrelated progressed saves cannot qualify arbitrary
integer search/replacement. Needed inputs are:

1. The matching original `BERSERK.exe` for static serializer/getter analysis,
   with executable version/build, region and installed DLC context. It will
   not be executed or distributed. A source-backed Windows save editor is
   another route if its revision/record/integrity evidence is independently
   verified and its licence is respected.
2. Complete copied native save folders: an unchanged control plus before/after
   pairs for one purchase/sale, one material use, one existing accessory
   enhancement/amalgamation and one equipment change, with visible identities
   and quantities. Accessory promotion needs its own pair.
3. Per-character EXP/level/action-growth pairs and separate Eclipse checkpoint,
   first-desire completion and reward-claim pairs. Record story gates and
   active-run state without conflating them with resource edits.
4. Proof of all internal integrity and a native title/revision gate, followed
   by surgical payload comparisons and actual edited game-load/re-save
   validation on the identified Windows build.

The qualified outer envelope can be reused when those facts are available.
Until then, gameplay edits, GUI save/Undo/review workflows for this title and
edited game-load claims remain blocked; existing registered editors are
unaffected.
