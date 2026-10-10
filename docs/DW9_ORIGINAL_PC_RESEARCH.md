# Dynasty Warriors 9 original: Windows PC evidence and remaining inputs

This is **the original Dynasty Warriors 9**, Steam app 730310, not Dynasty
Warriors 9 Empires. Research was renewed on 2026-10-11. A freely shared native
PC save bundle was acquired; the earlier “download blocked / basename unknown”
status is superseded. No writable adapter has been qualified for this game.
No downloaded game, trainer or editor executable was run. Player files, source
pages, local hashes and detailed byte analysis remain outside the checkout.

## Acquired input and identity limits

The [Steam save-sharing discussion](https://steamcommunity.com/app/730310/discussions/0/691996723218915728/)
links the [SaveGame.Pro PC bundle](https://savegame.pro/pc-dynasty-warriors-9-savegame/).
The page's dated download URL failed with HTTP 403; its ordinary public download
endpoint `https://savegame.pro/?wpdmdl=1416` returned a 382,175-byte 7z archive.
The archive was listed before extraction, and contains these classes:

| File class | Acquired size / count | Observations, not a qualified format |
| --- | --- | --- |
| `PLAYERDATA/SAVEDATA.BIN` | 3,940,247 bytes; one file | First little-endian DWORD is `0x160116F0`. Its role as a native revision discriminator still needs serializer proof. |
| `STORYDATA*/SAVEDATA.BIN` | 1,843,200 bytes each; 13 files | All begin with little-endian u16 `9`, a variable u16 at byte 2, u32 `1` at byte 4 and u32 `9` at byte `0x14`. Those words have no proven gameplay meaning. |
| `PLAYERDATA/sinpmap.dat` | 108 bytes; one file | Separate input-map companion; not presumed save integrity or gameplay data. |

All gameplay files are named `SAVEDATA.BIN`, but their parent folder distinguishes
player data from per-story data. One parser must not infer interchangeable
layouts from the shared basename. These are fourteen gameplay files from **one
public bundle**, not fourteen independent players or controlled action pairs.
The archive's timestamps are in 2019; timestamps are not an exact executable
build, language, region or DLC declaration. Full versus trial/free-officer
edition and installed DLC remain unqualified. The page advertises “100%
Completed”; Steam respondents instead describe unlocked characters and map
exploration without every character story completed. Neither description
qualifies individual acquisition, reward or story bits. Prior editing or
normalization by the sharer has not been excluded.

The bytes contain substantial zero/`0xFF` regions and structured-looking data.
That observation is insufficient to assert complete plaintext serialization,
absence of native integrity, or correct record ownership. Whole-body byte sums,
little-endian u16 sums, CRC-HQX with seeds zero and `0xFFFF`, CRC32 and Adler32
did not establish the variable story-header u16 as a checksum. In particular,
that u16 is **not labelled a checksum or seed**. No checksum from Empires,
DW8 XL, DW7 or a console title was substituted. Untouched archive extraction is
not a native decode/encode roundtrip or a malformed-file validation test.

## Public format and mechanics sources

- The [official Steam PC manual](https://www.koeitecmoamerica.com/manual/dw9/steam/EN/index.html)
  establishes actual game systems. In particular, [Officer Info](https://www.koeitecmoamerica.com/manual/dw9/steam/EN/4500.html),
  [Belongings](https://www.koeitecmoamerica.com/manual/dw9/steam/EN/4600.html),
  [Upgrading Officers](https://www.koeitecmoamerica.com/manual/dw9/steam/EN/5700.html)
  and [Taking a Rest](https://www.koeitecmoamerica.com/manual/dw9/steam/EN/5800.html)
  distinguish EXP, upgrade allocation, crafting, mounts, bonds and hunting rewards.
  They supply gameplay semantics, not native offsets or bounds.
- The [PC custom-gem guide](https://steamcommunity.com/sharedfiles/filedetails/?id=1367429596)
  describes a runtime 18-byte gem representation: a u16 type followed by four
  bonus-type/value pairs, with values wider than one byte and possibly duplicate
  runtime copies. Its later update also includes **Empires-exclusive IDs**;
  those must not be added to the original game's catalog. It provides no disk
  serializer, checksum, existing-record ownership or original-version catalog.
  Runtime addresses and search patterns were not promoted to save offsets.
- The [PC achievement guide](https://steamcommunity.com/sharedfiles/filedetails/?id=1312426274)
  distinguishes discovery locations from fog-of-war area; officer encounters
  from bonds; and legendary-horse availability from purchasing the horse.
  It is secondary mechanics evidence, not a native limits table.
- The [public PS4 patch](https://github.com/bucanero/apollo-patches/blob/0ccc07ed39ea378db83e9901dbfa610b04637d7d/PS4/CUSA10421.savepatch)
  is explicitly labelled untested and has revision-dependent offsets. Some
  later offsets exceed the acquired PC player-file length. Its console codes
  and cheat targets do not qualify the PC layout, native maxima or integrity.
  No patch or project implementation was copied into the editor.

GitHub repository searches for the original game's save editor, `dw9` saves,
`smusou8` and native savegame research supplied no licensed PC disk writer.
GitHub's unauthenticated code search required sign-in. Steam guide and discussion
searches for save editing, hex and checksums were inspected; the useful gem
reference remains a runtime guide. Nexus and Fearless Revolution requests
returned HTTP 403. The save-editor.com PC thread checked independently contains
boilerplate rather than a usable map. These are search/access limits, not proof
that a writer cannot exist. Sources were used as factual references; no external
source code, binary, catalog or attached player content is incorporated.

## Per-system coverage and precise blockers

Every row below remains blocked for writes until the **matching native PC
serializer and full-file integrity behavior** are qualified. Additional inputs
needed for each system are listed separately so one blocked system does not
become a reason to assume another game's offsets or systems.

| System | Mechanic established / exact additional proof needed |
| --- | --- |
| Gold and old coins | Spendable gold and collectible coins are separate; coins can be exchanged for scrolls/weapons. Need displayed purchase/exchange before-after pairs, exact owning file/record, storage width, native limits and any mirrored balances. No lifetime counter is treated as a balance. |
| Items, materials, arrows and bait | Quantities, crafted items and equipped consumable references differ. Need native item/category IDs, occupied-record schema, quantity limits, equip links and a one-item acquire/use/equip pair. A zero or matching numeric pattern does not establish ownership. |
| Officer EXP, level and Upgrade Points | Level gains raise officer-specific abilities and grant freely allocated Upgrade Points. Need named officer identity, EXP thresholds, allocation/level reward routines and one-level/one-point pairs. Unspent points must remain separate from allocated stats and lifetime gains. |
| Officer base abilities and derived combat stats | Strength plus weapon determines Attack; Toughness plus accessories determines Defense. Need stored base fields, officer-specific growth and allocation dependencies; displayed Attack/Defense are not written as presumed base stats. |
| Skills / proficiency | No native persistent skill tree or DW8-style weapon-proficiency field is qualified. Need proof such a system exists in the selected original-game build before adding it; Empires compatibility and secret plans are not imported. |
| Weapons and Reforge | Weapons are purchased/crafted; Favorite Weapons affect Unique Attacks; gems attach to attack categories. Need weapon IDs/ownership, equipped references, gem attachments and acquisition/crafting prerequisites. There is no presumed conventional weapon-level or DW8 attribute-fusion map. |
| Gems and bonus attributes | Runtime type plus four bonus pairs is a lead, including combined duplicate effects. Need native inventory framing/count/occupancy, original-build IDs, bonus legality/ranges, mirrored-record rules and gem craft/equip pairs. Do not use the guide's later Empires-only enumeration. |
| Accessories and other equipment | Four accessory slots affect stats/effects. Need original catalog, acquisition flags, equipped references and valid slot/dependency rules. Owning an accessory does not mean it is equipped. |
| Crafting scrolls | Completed scrolls require their pieces and permit repeated crafting with materials. Need piece counters, completed-recipe flags, crafting costs and reward/state transitions. Raising materials alone must not manufacture completed scrolls. |
| Horses / animal companions | Horse purchase, stable selection and equipped-horse training are distinct; only the selected mount gains development. Need individual occupied records, identity/rarity, EXP-growth rules, stable/equip links and acquire/train/equip pairs. Any companion system added by later updates needs that build's exact acquisition/equipment schema. |
| Hideaways, furniture and customization | Hideaways are purchased; furniture has a placement-point budget and enables actions; costumes can remain customized across story progression. Need ownership versus placement slots, capacity, catalogs, furniture-action prerequisites and costume eligibility. A purchased-item bit is not a placement/equip reference. |
| Relationships / visitors | Acquaintance, invitation eligibility and bond growth differ; furniture and letters can enable presents/actions. Need per-officer/active-story ownership, bond ranges, encounter/invitation flags, time/visit rules and rewards. No marriage/offspring system is invented from Empires. |
| Exploration / fast travel | Discovering locations, obtaining map information and clearing fog are distinct; fast travel also depends on allied influence or ownership. Need location IDs, discovery/map flags and travel gates with a one-location control pair. No blanket exploration edit doubles as story completion. |
| Hunting | Best Hunting score is a record with tiered rewards; it is not spendable currency. Need score owner, recorded-versus-claimed reward state and tier dependencies. No direct score edit or bulk Max bypasses reporting/rewards. |
| Gallery, battle entries, movies, music and collections | Need each original-build catalog, ownership/unlock maps and reward dependencies. DLC/complete-edition initial availability must be distinguished from story-cleared rewards. |
| Chapter K.O. count, cumulative records and achievements | The manual identifies the current-chapter count as affecting EXP/drop rates. Need exact scope/reset behavior and mirrored/history records; no count is relabelled current currency or globally maximized. |
| Story, requests and clear rewards | Missions advance the story and reward EXP/gold; requests have separate acceptance/report/reward states. Need per-story identity, prerequisite/reward transitions and controlled completion/claim pairs. These transitions remain separate from resource edits. |

## Inputs required to finish a native adapter

The concrete first input is the exact Windows original-game executable revision
matching the shared bundle, or public native serializer/integrity research with
that build qualified. Static analysis must establish PLAYERDATA and STORYDATA
framing, saved lengths, revision handling, integrity coverage and any owner or
companion-file dependencies. A current-build, explicitly labelled full/trial,
language/region/DLC save folder and unchanged control would independently
qualify any later profile rather than extending the 2019 observations by guess.

Controlled one-action copies should record the officer, active story, displayed
before/after values and relevant ownership/equipment state privately. Separate
pairs are needed for purchase/use, level/point allocation, gem creation/equip,
horse purchase/train/equip, relationship visits, exploration discovery and
recipe/reward claims. Existing occupied records must be identified before writes.

No registered editor, procedural adapter tests, genuine native roundtrip,
surgical gameplay write, malformed-input guarantee or GUI save/backup/restore
qualification is claimed for original DW9. Actual Windows game load/re-save
validation also remains unperformed. Once native proof is available, integrate
through the shared scalar safety contract, preserve unknown bytes and unusual
values, and run each of those validations before updating support metadata to
claim editing.
