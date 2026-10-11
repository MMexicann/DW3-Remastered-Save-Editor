# Samurai Warriors 4-II Windows PC native adapter

`sw4ii` is a separate adapter from Samurai Warriors 4 DX. It accepts native
`SAVEDATA0000.dat`–`SAVEDATA0004.dat` gameplay copies, exactly `0xC8210` bytes,
whose decoded payload revision is `0x31A4`. Image/import files, other revisions,
console exports and SW4 DX are rejected. Filenames are descriptive; native
integrity, revision and 76 serialized officer identities qualify the contents.

The source-backed editor reference targets English PC v1.0. The two independently
shared genuine files have the same native revision and layout; their exact game
executable build, region and DLC purchase entitlement are not supplied. Support
therefore names the serialized revision, not an unverified Steam build or all
language/DLC variants. The adapter does not grant DLC ownership or create files.

The latest equipment expansion and native/GUI checks are recorded in
[Samurai / classic Dynasty editor depth](SAMURAI_DYNASTY_DEPTH.md).

## Implemented mechanics

- Manual current gold and five held strategy-tome counters: red, green, blue,
  yellow and purple. Adjacent history is preserved; resource edits do not
  purchase skills or reproduce transactions.
- Five stored base stats on initialized standard officer records 0–55: health,
  attack, defense, riding and speed. Level, EXP, move/Musou unlocks, personal
  skill trees, growth rewards and effective battle modifiers remain unchanged.
- Equipped weapon selection within an officer's own pool, restricted to an
  already occupied known normal/rare weapon and the first 15 positions. The
  full physical pool has 20 records; selectable positions beyond the source's
  documented ordinary capacity need stronger selection evidence. An unusual
  opened reference can be preserved or restored with Undo; no empty record,
  foreign family or new weapon becomes an equipment target.
- Manual magnitudes of existing attached attributes on known occupied primary
  weapons. The independently corroborated 17 IDs are Health, Attack, Defense,
  Speed, Riding, Musou+, Spirit+, Range, Attack speed, Indirect, Fire, Lightning,
  Ice, Wind, Earth, Death and Luck. Weapon identity, attribute identity/order,
  rank, level, EXP, ceiling, attack and other unknown bytes stay unchanged.
- Manual positive power, stamina and speed on existing occupied known mount
  records with native type IDs 0–12 and valid stored level/ceiling. Empty type
  26, unknown types and unusual progression remain preserved and read only.
  Mount ownership, growth, abilities and story rewards are separate.
- Equipped mount selection on initialized standard officers, restricted to
  qualified existing occupied mount slots in the opened inventory. This changes
  the officer reference only, preserving mount identity, ownership, growth,
  abilities and combat stats. Unknown/empty targets are unavailable; assigning
  an unusual opened reference restores it through Undo.
- Read-only progression, own-pool weapons/attributes, equipment references,
  mount levels/stats and adjacent unqualified gold history inspection.
- Shared themes, staged Undo, Review Changes, named equipment choices,
  automatic/manual backups, protected source copies, atomic new-destination
  Save As and exact-byte backup restoration.

Every writable field has `maxable=False`. Unsigned 32/16/8-bit editing limits
are representational bounds, not claimed natural gameplay maxima. Mount combat
stats additionally require positive values to retain the supported occupied
record qualification. This project has not independently established natural
caps or verified edited gameplay loading. Bulk Max leaves all these fields
unchanged, including unusually high originals.

## Independently implemented framing and integrity

The retained clear slot/menu header occupies `0x20C` bytes. At file `0x20C`,
little-endian `<HH` stores the native word checksum and original stream seed.
The `0xC8000`-byte payload starts at file `0x210`.

For each little-endian DWORD, advance the state **three** times, then XOR:

```text
state = (state * 0x5B1A7851 + 0xCE4E) modulo 2^32
word ^= state_after_three_advances
```

The envelope checksum is the sum of all decoded little-endian 16-bit words,
modulo `2^16`. It includes the opaque tail; nothing is discarded or zeroed.
This is distinct from the current SW4 DX one-advance stream and revision
`0x39EA`. Shared cipher primitives are reused; layouts and checksums are not.

Static inspection of the freely available Van English-PC editor Build1010
establishes exact native checksum sections. Reference PE writer
`0x4088B8`–`0x408999` and byte-sum helper `0x40A3F0` use an envelope buffer whose
payload starts four bytes after its pointer. These reference addresses belong
to that editor, not a game executable or save offsets. The helper's end is
exclusive. The editor splits section e at `0xD8EE`; summing its contiguous
parts is equivalent to the single span below.

| Sum | Payload start | Payload end, exclusive |
| --- | ---: | ---: |
| a | `0x8` | `0xA8` |
| b | `0xAC` | `0xA0C` |
| c | `0xA0C` | `0x104E` |
| d | `0x1052` | `0xCC36` |
| e | `0xCC36` | `0xD92E` |
| f | `0xD92E` | `0x5D86E` |

The four stored little-endian DWORDs at payload `0x4`, `0xA8`, `0x104E` and
`0x5D86E` are, respectively:

```text
((d+a)*b+e) & 0x7FFFFFFF
((d+f+b)*a) & 0x7FFFFFFF
(a+b+c+d) & 0x7FFFFFFF
(checksum1+checksum2+checksum3) & 0x7FFFFFFF
```

All four independently match both genuine native copies. Both copies happen
to have zero-filled section f, but the implementation uses the exact native
span and accepts/preserves populated opaque data. Generated tests deliberately
populate all six sections and the tail; this is procedural preservation proof,
not evidence that a genuine interim-save state was loaded in the game.
Incoming integrity is always checked before fields appear. Qualified edits
recompute the four section values and the envelope sum, retain the original
header/seed and opaque bytes, and reparse output. No-edit output is byte exact.

## Field and ownership evidence

| System | Native payload mapping | Qualification / separate state |
| --- | --- | --- |
| Officer records | `0x1052`, stride `0x8C`, 76 consecutive u32 IDs | First 56 standard officers; last 20 custom records stay untouched. Stored level at `+0xC` must be 1–50 for base-stat fields |
| Officer progression | EXP u32 `+8`, level u32 `+0xC` | Inspected, never changed independently of growth/rewards |
| Five base stats | u16 `+0x20`, `+0x22`, `+0x24`, `+0x26`, `+0x28` | Exact ordering corroborated by PC memory schema and both serialized native files; not effective battle stats |
| Primary weapon pools | `0x4702`, 60 physical families × 20 × `0x1C` | Static registry has 61 families including a leading 20-record group at `0x44D2`, which is excluded. Only first 56 standard families are edited |
| Known primary identity | u16 weapon `+0` | Both native files establish normal/rare IDs `2+2*officer` and `3+2*officer`; sentinel 351 is statically validated. Other/DLC/template identities stay read only |
| Equipped primary weapon | officer byte `+0x3B` | Existing known own-pool targets only; four genuine unusual empty references are preserved instead of rejecting or repairing their file |
| Attached attributes | IDs `+0xC`–`+0x13`; magnitudes `+0x14`–`+0x1B` | Known IDs 0–16 only; empty ID 255 and unknown IDs remain untouched. All 20 physical positions can have their existing known attributes edited in place |
| Mount records | `0xCA42`, 20 × `0x10`, ending at gold | Known occupied native types 0–12; native empty sentinel 26 is statically validated; manual stats are bytes `+0xA`/`+0xB`/`+0xC` |
| Equipped mount | Officer byte `+0x3D` | Existing qualified occupied mount slots only; a reference selects inventory position rather than replacing its type. Initialized standard officers only; unusual opened references are preserved |
| Current gold | u32 `0xCB82` | Separate adjacent history retained without asserting its unknown meaning |
| Five current tomes | u16 `0xCC16` + two bytes per color | Native saved gold-to-tome gap `0x94` exactly matches independent PC memory schema; current held resources, not lifetime purchases |

The PC record stride is `0x8C`; the PS4 tutorial's `0x89` stride is not used.
SW4 DX's offsets, weapons, gem system, record sizes and maxima are not reused.
The native-editor player's 15-weapon capacity is kept separate from the exact
20-record serialized family. No acquisition/equipment ambiguity creates new
records or changes IDs.

## Sources and licence handling

- [Public PC full-save page](https://savegame.pro/pc-samurai-warriors-4-ii-savegame/): freely shared native `SAVEDATA0000.dat`, independently downloaded and retained privately.
- [Steam PC save discussion](https://steamcommunity.com/app/348470/discussions/0/481115363862745012/): a second independently shared native copy, downloaded through the ordinary public link. Fixture URLs, bytes and player context are not distributed.
- [Van native save-editor announcement](https://down.gamersky.com/pc/201510/671462.shtml) and [usage instructions](https://www.gamersky.com/handbook/201510/675670.shtml): Build1010, English PC v1.0, save and memory support. An accessible public mirror provided the editor for static study. The author limits it to personal research and requires permission for redistribution; the binary, readme, unpacked reference and analysis stay private and are not packaged. No downloaded binary was executed and no project/code was copied into this adapter.
- [PC memory research](https://github.com/Hexorg/CheatEngineTables/blob/0e7092b235f62ee5af4d3942c4323eb6c414f9c6/tables/shinkansen_samurai_warriors_4-ii_v1003_583.ct): independent stat ordering, held tome colors, equipment offsets, weapon attribute IDs/values and mount fields. Consulted as factual research; never executed or imported into runtime code. Trainer write targets are not gameplay caps.
- [Native-editor player research](https://game.ali213.net/forum.php?mod=viewthread&tid=5953892): 56 standard officers, custom IDs 56–75, ordinary inventory capacity and separate weapon/mount systems. Some enum indices conflict with the actual memory schema; the conflicting lists are not imported.
- [PC player dependency report](https://www.tapatalk.com/groups/koeiwarriors/modding-costumes-appearances-in-pc-version-t24602.html): direct level edits bypass move/Musou unlocks; skill grids and DLC acquisition stay separate.
- [Official PC manual](https://cdn.steamstatic.com/steam/apps/348470/manuals/steam-sw4-2-mnl%28EN%29.pdf): powering-up, tomes/skill grid, weapon/mount development and Survival/Interim Save mechanics.
- [PS4 format tutorial](https://nextgenupdate.com/forums/ps4-game-save-modding/1015243-samurai-warriors-4-ii-advanced-mode.html) and [older SW4 console checksum research](https://github.com/bucanero/save-decrypters/tree/master/sw4-checksum-fixer): leads only; console offsets/caps are not treated as PC evidence.
- [Nexus PC clear-save listing](https://www.nexusmods.com/samuraiwarriors4ii/mods/1): inspected as an additional native-save lead. Its file was not downloaded or counted as qualification; the two genuine fixtures above supply the tests.

## Tests and precise remaining inputs

`test_sw4ii_format.py` covers surgical edits across every eligible field,
round trips, seeds/clear headers/custom records/opaque bytes, complete native
integrity, malformed inputs, foreign revisions, manual bounds, field ownership,
immutable staging, standard scalar contract and safe save/backup/restore.
`test_sw4ii_review.py` independently covers native six-section arithmetic,
populated former ambiguous spans, outer-repaired corruption, same-size foreign
SW4 DX rejection, original unusual values/references, record stability, forged
snapshots and exact bounded restore under changed-backup races.
`test_sw4ii_gui.py` exercises actual Tk open, named equipment choices, officer,
weapon and mount edits, Review, Undo, manual-only Max, inspectors/themes,
Save As, backup and Restore Backup dialogs on private native bytes when supplied.

Run with `SW4II_SAVE_COPY` and optionally `SW4II_SECOND_SAVE_COPY` pointing to
separate native copies outside game/Steam Cloud directories. Missing genuine
inputs skip only the genuine-file case; Tk requires a display. The final focused suite passes 20 tests with both private genuine copies and a
Tk display: nine format/common-contract cases, ten independent review cases and
one GUI workflow. The registered copied-save CLI self-test also passes native
integrity, unchanged output, source preservation and backup/restore; its Max
action stages no fields because these controls are manual. Neither genuine
serialization nor GUI saving claims that an edited file was loaded in-game.

| Mechanic | Coverage / exact remaining input |
| --- | --- |
| Current gold / five strategy tomes | Implemented manual resource edits. Native gameplay add/spend routines or controlled cap pairs still needed for natural Max values |
| Stored base stats | Implemented for initialized standard records. Growth/skill modifier tables and controlled level-up pairs needed for natural stat ceilings/effective-stat calculations |
| Character EXP / level / proficiency | Read-only level/EXP. Need threshold/growth/move/Musou unlock tables and one-action level-up controls; no distinct saved proficiency system is assumed from SW4 DX |
| Personal skill grid / equipped skill tiers | Preserved. Need owned-skill bit dictionary, tier/prerequisite rules and one purchase/equip pair per tier; resources do not unlock skills |
| Weapons / attributes | Existing primary normal/rare magnitudes implemented. Need native generation/fusion rules, attribute exclusions and dictionary for other/DLC identities before replacement, ceiling edits or creation |
| Equipped weapons | Existing own-pool known targets implemented in positions 0–14. Need native selection limit/translation or displayed equip pairs for positions 15–19 before offering those targets |
| Weapon rank / level / EXP / attack | Inspected, preserved. Need forging thresholds and attack growth tables/pairs before independent writes or simulated upgrades |
| Mount stats / inventory / equipment | Known occupied types 0–12 manual combat stats and existing mount-slot selection implemented. Ownership, growth and abilities stay separate. Need qualified identities/entitlement for unknown/DLC types, rank/EXP/growth tables and acquisition/ability pairs for other controls |
| Equipment, consumables, abilities | Attached weapon magnitudes are separate from the personal grid. Need native item/ability dictionary, existing ownership and equip prerequisites for remaining records |
| Customization / custom characters | Custom records/cosmetics/names retained. Need full identity/occupancy mapping, enum/name encoding and controlled appearance pairs; no private names are emitted in test reports |
| Relationships / exploration / collections | No separate relationship or exploration system inferred from other games. Need game-specific mechanics plus serialized one-action pairs for any collection flags |
| Story / Survival / rewards / prerequisites | Preserved. Need clear/reward/interim pairs and native prerequisite transitions; populated opaque section f is preserved, not edited |
| Edited gameplay load/re-save | Still required on the exact PC build/language/DLC, including edited resources, stats, attributes, equipment and mount controls; neither procedural nor genuine-file tests substitutes for this |
