# Game mechanics, evidence and safe editing

This research is for **native Windows PC editions**. Understanding a game system
is a prerequisite for choosing fields and limits; it does not establish a save
offset, encryption algorithm or safe serialization by itself. See
[KOEI_FORMATS.md](KOEI_FORMATS.md) for the implemented binary layouts.

Evidence is classified as:

- **Native project evidence:** previously decoded game tables and native rules in
  the existing DW3 editor, preserved with their evidence addresses.
- **PC save observation:** a field/value relationship corroborated in genuine PC
  saves. Observational formulas are labelled inferred, not treated as code proofs.
- **Published PC runtime evidence:** author-labelled structures and original
  instruction signatures. Runtime addresses are not disk-save offsets.
- **Published patch bounds:** values used by a save patch, which can exceed normal
  progression. They are not automatically natural game maxima.
- **Tutorial semantics:** descriptions of how a game system works, useful for
  identifying dependencies but insufficient to implement a serializer.

No downloaded trainer or Cheat Engine script was executed. No downloaded save,
account data, tutorial text, copyrighted asset or third-party implementation is
distributed. Notes and in-app explanations are independently authored.

## DW3 Complete Edition Remastered

The original project already contains substantial game-specific evidence. It is
retained as the strongest model for further games:

| System | Established relationship | Editor consequence |
| --- | --- | --- |
| Permanent officer stats | Merit 99,999; Life/Musou 250; Attack/Defense 150, from native clamp paths | Equipment bonuses are not mistaken for permanent stats |
| Normal items | Individual shipped item rules, rank/random-value generation and scenario modifiers | Use per-item reachable limits rather than one numeric maximum |
| Weapon bonuses | Native drop and direct-copy fusion rules differ from item limits | Validate reachable bonus combinations; preserve unusual existing values |
| Bodyguards | Allocated growth points are separate from automatic Count and AI | Count thresholds 25k/50k/75k Merit; AI thresholds 30k/60k/90k; retain dependency rules |
| Musou completion | Officer-specific routes; three officers have no route | Route completion does not invent battle records, scores, clear times or achievement events |
| Huanglong Elixirs | Native limit 999; first-clear award three; zero counter can be absent | Preserve the v1.1 fresh-save handling |

Sources are the existing `src/koei_editor/data/verified_limits.json`, `src/koei_editor/data/item_limits.json`,
`src/koei_editor/data/weapon_bonus_rules.json`, `src/koei_editor/data/bodyguard_growth.json`, `src/koei_editor/data/progression_routes.json`,
`src/koei_editor/data/collection_unlocks.json` and the retained editor regression tests. Runtime
addresses in their evidence are not save offsets.

## DW8 Xtreme Legends Complete Edition

Published PC source:
[Hexorg PC v1.0.0.7 table](https://github.com/Hexorg/CheatEngineTables/blob/0e7092b235f62ee5af4d3942c4323eb6c414f9c6/tables/shinkansen_dynasty_warriors_8_v1007_158.ct).
Inspected repository commit `0e7092b235f62ee5af4d3942c4323eb6c414f9c6`.

### Processing ceilings versus natural progression

Original instruction signatures, as published in the table, corroborate:

| Value | Referenced PC routine | Interpretation |
| --- | --- | --- |
| Attack/Defense 1,500 | Lines 740/792 compare against `0x5DC` | Combat calculation processing ceiling in that build |
| Gold 9,999,999 | Line 3299 compares against `0x98967F` | Selection/display path ceiling for the consumed value |
| Facility materials 9,999 | Line 4559 compares a uint16 against `0x270F` | Inspected Ambition display-path ceiling |
| Weapon attribute rank 10 | Lines 1842–1866 compare a rank byte against `0x0A` | Attribute effect processing ceiling in that routine |
| Gems 9,999 | Two independent Steam guides cited below | Community-corroborated normal inventory limit; higher existing values preserved |
| Health 1,000 | Apollo save patch only | Published patch bound; normal progression maximum not independently proven here |

Processing ceilings do not prove that every officer can naturally reach them,
or that the game rewrites excess saved values. The Max controls therefore say
they use **published editing limits**. Higher existing values are preserved.

### Progression and equipment dependencies

The PC runtime table separates permanent officer records, selected-officer
structures and battle structures. Officer level/EXP are distinct from
leadership/leadership EXP. Stored integer stats are distinct from battle floats,
current/max gauges and temporary bonuses. It does not establish the recalculation
equations or when level-up, equipment changes, battle entry or later saving
replace edited permanent stats. These triggers need in-game controls.

Weapons distinguish identity, affinity, six attribute IDs, six attribute ranks,
price and acquired order. Equipped skills distinguish rankable/enabled/rank.
Bodyguards distinguish current/max skill levels, skill EXP, support skills and
male/female bonds. Ambition facilities and allies distinguish material balances,
invested materials, facility rank/unlock, supervisors, roster/count, fame and
capacity. Filling all bytes with a maximum would damage these relationships.

Before those editors can be enabled, obtain PC save pairs for one weapon
acquisition/fusion, one skill unlock/rank increase, one bodyguard strengthening,
one facility upgrade and one ally acquisition. For stat behavior, re-save an
edited copy after load, equipment change, battle entry and level-up, keeping
untouched controls. The implemented field layout is separately corroborated by
the [PC converter](https://github.com/koko-tsuu/dw8xl_save_converter/tree/8ca795108a4f4f0bee91c55d3efce0c6da78515f)
and genuine PC sample.

## Pirate Warriors 3

Two genuine native PC saves were examined:

| Source | Inspected commit | SHA-256 |
| --- | --- | --- |
| [Ceraph1216/pirateWarriors3Save](https://github.com/Ceraph1216/pirateWarriors3Save) | `a4addb6b4483c9e51afa8aabb3fa5cea86d60483` | `1905c7e95c46d3fa6c2a593d849626c6e6a88b81db2450eed238c5e63ef06913` |
| [gamesaves/OPPW3](https://github.com/gamesaves/OPPW3) | `39a79e77483b2683656abca0ee981f060ee01a7f` | `6a16ac7557980adb1db138c2c96966349e9a5d7b4ba1a26b09388e6b23c58832` |

Both repositories identify Windows Documents save locations; both files have the
native PC size/title/layout and pass the implemented integrity checks. These
are the editing evidence. Console references only corroborate shared structure.

### Observed progression

Each record begins at PC plaintext `0x650 + slot * 0x1F0`: XP at `+0`, HP at
`+4`, Attack/Defense at `+6/+8`, bars at `+10`, stored level at `+11`, slots at
`+12`. A progression-related bitmask at `+16` remains unresolved. The published
level-100 patch writes 99, corroborating zero-based level storage. Level and XP
are available for **read-only inspection**, not editing.

| Displayed-level candidate | XP observed | HP observed |
| --- | --- | --- |
| 1 | 0 | 2,000 |
| 17 | 54,500 | 2,979 |
| 30 | 220,500 | 3,775 |
| 34 | 325,500 | 4,020 |
| 37 | 450,617 | 4,204 |
| 50 | 1,000,000 | 5,000 |
| 100 | 3,000,000 | 6,000 |

All observed health values follow this **inferred sample model**, where `s` is
the stored level index:

```text
s <= 49: HP = 2000 + floor(3000 * s / 49)
s > 49:  HP = 5000 + 20 * (s - 49)
```

This is not a proven native clamp or complete stat-growth equation. Published
10,000 HP and 1,000 Attack/Defense are boost bounds above the observed progression
values. The [published patch](https://github.com/bucanero/apollo-patches/blob/99f4e10e415e1a1590c301b105667530710854fa/PS3/NPEB02211.savepatch)
explicitly warns that stat/bar boosts reset on level-up. The level/health
correlation supports recalculation as an explanation; the exact code path and
other triggers remain unverified.

### Relationships that must be preserved

- Record pairs `0↔37` through `8↔45` share level, XP, bars and slot values in both
  saves, while some stats differ. They appear related, possibly variants; do not
  assume independent characters or assign guessed identities.
- Bars and skill slots are not functions of level alone. Observed ranges are
  1–4 bars and 1–6 slots, including different capacities at level one. New writes
  reject zero for these capacities; existing data is preserved when untouched.
- The [published PC v1.0 runtime table](https://github.com/Hexorg/CheatEngineTables/blob/0e7092b235f62ee5af4d3942c4323eb6c414f9c6/tables/shinkansen_one_piece_pirate_warriors_3_v1000_621.ct#L142)
  labels adjacent fields Current Beli and Earned Beli. This supports an
  interpretation of the saved pair, but the memory-to-disk mapping and safe
  update relationship have not been demonstrated; it does not enable writes.
- Currency pairs are `999,999,999 / 1,000,000,000` and
  `19,585,649 / 26,304,000`. The published money patch changes both values, so
  the update relationship needs earning/spending pairs. Currency remains read only.
- Medal rows contain two independent bytes: examples `44 63`, `23 48`, `20 2A`.
  Treating them as one uint16 quantity would be an unsupported interpretation.
- Required controls include one level-up, one bar upgrade, one skill-slot
  upgrade, one standard-coin purchase and one limit-break purchase. Record the
  displayed values and keep equipment unchanged where possible.

## Pirate Warriors 4

Public PC research:
[Glubus/oppw4-sdk](https://github.com/Glubus/oppw4-sdk/tree/ed00f9fa0dae4ac561106c9e0d93cd2bcc44be88),
commit `ed00f9fa0dae4ac561106c9e0d93cd2bcc44be88`, and
[Glubus/oppw4-data](https://github.com/Glubus/oppw4-data/tree/9b544c4c961db6985f5a5079c9b97aef24a1cb10),
commit `9b544c4c961db6985f5a5079c9b97aef24a1cb10`.

[PC reward probes](https://github.com/Glubus/oppw4-sdk/blob/ed00f9fa0dae4ac561106c9e0d93cd2bcc44be88/docs/reverse-notes/difficulty-reward-ghidra-2026-05-20.md)
distinguish Beli reward components and committed/displayed totals (lines 229–264),
medal/item IDs/counts/new flags (266–288), and crew points whose displayed total
differs from raw deltas (289–333). Soul reward fields are explicitly unresolved
(335–446). The source warns about outdated Cheat Engine addresses.

These provide a resource/dependency model, not a disk-save schema. Do not equate
reward deltas with persistent totals or reuse old memory addresses. Build/DLC-
specific growth and Soul Map caps still need independent verification. PW4 remains
outside the editor selector until a genuine PC save decoder/writer is validated.

## Berserk and the Band of the Hawk

The official [Steam PC manual](https://store.steampowered.com/manual/502280)
states a natural character Level 99 limit (printed p27), three equipped
accessories (p29), and four inherited accessory skills with consumed amalgamation
inputs (p26). These mechanic limits do not establish storage offsets or bounds.

Additional public PC tutorial translation:
[ayozetr/berserk-band-of-the-hawk-es](https://github.com/ayozetr/berserk-band-of-the-hawk-es/tree/a10d3affa706dc9d4650f5f54e82bb90c251986c),
commit `a10d3affa706dc9d4650f5f54e82bb90c251986c`,
[tutorial entries](https://github.com/ayozetr/berserk-band-of-the-hawk-es/blob/a10d3affa706dc9d4650f5f54e82bb90c251986c/translation/es.json#L2784).
These are translated tutorial semantics, not native save mappings:

- Vitality, Attack, Defense and Technique grow with character level (2784–2786).
- Accessories support up to four inherited abilities; repeated equipped
  abilities increase effects (2789).
- Ability upgrades use matching-color materials; accessory reinforcement reaches
  +9. Promotion and fusion involve item class, rare materials, consumed items and
  choosing inherited abilities when more than four would result (2792–2796).
- Endless Eclipse floor rewards are per character; desire completion is shared
  (2802–2803). Ongoing health/items/progress have distinct persistence rules (2806).
- Some character levels also increase action level and unlock attacks (2804).

A future equipment editor therefore needs valid item identity/class, reinforcement,
ability IDs/levels, equipped-item references and material compatibility. Eclipse
progress needs separate per-character, shared and ongoing-run state. A genuine
PC file now qualifies its three-advance outer cipher/checksum and unchanged
roundtrip, while body records, revision and additional integrity remain
unqualified. No gameplay adapter is registered. See the
[Windows research checklist](BERSERK_PC_RESEARCH.md) for official manual evidence,
the PS Vita editor distinction and controlled-save prerequisites.

## DW8 Empires and Samurai Warriors 4-II

PC runtime references from the same Hexorg commit:

- [DW8 Empires v1.0.0.4](https://github.com/Hexorg/CheatEngineTables/blob/0e7092b235f62ee5af4d3942c4323eb6c414f9c6/tables/shinkansen_dynasty_warriors_8_empires_v1004_124.ct)
  separates Merit/Level, kingdom/location/rank, virtue/friendship/fatigue/leadership,
  ownership bitfields/equipped indices, six equipped stratagems/cooldowns and
  bonus points/lifetime earned points. It needs an independent campaign model.
- [Samurai Warriors 4-II v1.0.0.3](https://github.com/Hexorg/CheatEngineTables/blob/0e7092b235f62ee5af4d3942c4323eb6c414f9c6/tables/shinkansen_samurai_warriors_4-ii_v1003_583.ct)
  separates EXP/level and stored/battle stats. Weapons have rank/current/max level,
  eight ability IDs and eight ability levels. Mounts have their own rank/levels/
  flags; five colored strategy-tome balances are separate resources. Original 4,
  4-II and 4 DX require independent verification.

No applicable PC serialized layout or normal-cap proof was established. Also,
Apollo's DW8 Empires console patches titled “999999” actually encode 90,000
materials and 99,999 money. Patch titles must not be used as numeric evidence.

## Origins, DW9 and Orochi

The [Origins asset tools](https://github.com/Kelebek1/dwo/tree/5de9b3e615691f2280ceeb6100416275adfbe75c)
operate on LINKDATA and stage scripts. Their `unit_set_courage` signed `level`
argument controls a stage unit, not player rank/proficiency. Demo/full-game and
patch differences reinforce version-specific research. No player cap, skill-tree
dependency or save-progress equation was established. Needed samples are listed
in [ORIGINS_FORMAT.md](ORIGINS_FORMAT.md), starting with a verified save decoder.

DW9's available console patches are explicitly untested and distinguish
version-dependent accessory IDs/modifiers. Orochi 3 console references distinguish
level/EXP/proficiency/transmigration, growth-jade allocation, equipped slots and
attribute display/effect values. These are research leads only, not PC support.
The other PC candidates in `src/koei_editor/data/support_catalog.json` likewise remain unavailable
until their own native PC files and rules are established.

## Research access and remaining work

Direct official KT manuals, Steam guides/store pages and Fandom requests returned
network-policy 403 errors in this environment. They were not represented as read
or verified. Public-domain additions were saved only to the environment configuration
draft; they have not been activated or published. Accessible GitHub material and
native save evidence were used in the meantime.

Continue corroborating tutorial/community claims against current PC manuals,
version-labelled saves and native routines. For every new feature, establish
identity and ownership, progression prerequisites, derived values, the relevant
game-build/DLC limits, output integrity and behavior after a game load/re-save.
Keep observed values, native processing caps and deliberate cheat boosts separate.


## Additional PC mappings implemented

Steam guides were successfully fetched during the final mapping pass. Manual
redirects and Wikipedia/PCGamingWiki requests remained blocked; Fandom returned
HTTP 402. Earlier access failures do not describe the later Steam guide access.

DW8 guides [happynaru](https://steamcommunity.com/sharedfiles/filedetails/?id=259699645)
and [MasterMario4](https://steamcommunity.com/sharedfiles/filedetails/?id=268825547)
independently describe 9,999 gems, Blacksmith level 30 for fusion, additive ranked
attributes capped at 10, and attributes without ranks. Weapon attack ceilings
vary by type/rank, so attack and identity are inspected without new writes.

DW8 PC officer records start at 0x7FC9, stride 0x48. Read-only fields are stored
level-minus-one byte +0x17, leadership-minus-one uint32 +0x18, EXP uint32 +0x1C,
leadership EXP uint32 +0x20 and two uint16 equipped zero-based weapon references
at +0x30/+0x32. These positions are corroborated by the native PC table described
above and the actual PC sample. A published EXP patch begins one byte earlier;
it must not be interpreted as one aligned four-byte XP value.

DW8 physical weapons start at 0xE715, stride 0x18, count 1,830 (not a claim about
user inventory capacity). ID is uint16 +2; affinity +4; stored attack +5; six IDs
+6 and six ranks +12. The shared published patch layout and PC sample corroborate
these positions. Observed populated flags 1/3 are the editing subset: flag-zero
records contain stale nonempty data and must be preserved. Only observed variable
rank IDs receive 1–10 writes. Empty ID255, consistently-one attributes and unknown
IDs remain untouched. Native PC instructions independently name ID7 Velocity and
ID41 Comet. In-game loading remains untested.

PW3 [PC asset guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2306008901)
and [DLC guide](https://steamcommunity.com/sharedfiles/filedetails/?id=518357813)
corroborate 16 curated native character labels in game_content.py. All 28 literal
costume associations match the progressed PC save at character base +0x2F plus
local costume slot; the low-progress sample has 255 at all 28 positions. These
associations are read only and do not establish entitlement, equipped state or
unlock writes. Native ID41 stays unnamed because the guide has a contradictory
name. The [skill guide](https://steamcommunity.com/sharedfiles/filedetails/?id=729079419)
reports skill-tier assignment can vary with acquisition order; skill arrays are
therefore not assigned guessed fixed names. Coins, Beli and progression writes
remain unavailable. No downloaded assets or full guide text are shipped.

## Renewed native PC mechanics and candidate implementation

The [renewed PC research report](PC_RESEARCH_RETRY.md) records retrieved PC
guides, runtime references, blocked save links and exact copied-file needs for
DW4 Hyper, DW6, DW7 Definitive, DW8 Empires, DW9/DW9 Empires, SW4-II, WO3
Definitive, PW4, Berserk and Persona 5 Strikers. The in-app guide now separates
DW9 from Empires and explains their gem, artifact, reputation, proficiency and
CAW dependencies. These are sourced mechanics observations; no runtime address
is used as a disk offset.

DW4 Hyper has 42 published standard officer identities and 32 published item
identities. Candidate item semantics distinguish lock byte 255 from stored
level-plus-one, normal levels 1–20, orbs 1–4 and rare-item ownership. Weapon EXP
36,001 selects its special level-10 weapon; Hyper has no level-11 weapon.
Character EXP, permanent stats and bodyguard points are independently bounded
by storage width, with natural maxima/growth thresholds unresolved. Bulk Max
therefore excludes those fields and difficulty. Equipped-item references, names,
custom characters, rankings and suspended battle data remain read only.
Published author game tests are recorded as external evidence; this project's
procedural fixtures are never described as genuine PC saves.

DW9 gems have a type plus four bonus-type/value pairs in the inspected PC runtime
guide; duplicate records, multi-byte values and patch changes require validation.
DW9 Empires has six reputation tracks gating titles; campaign titles differ
from CAW template Way of Life. Artifact rarity controls gem slots and weapon
rarity, while gem bonuses differ from element increases. Four Secret Plans,
card ownership/acquisition stars, campaign proficiency, preferred weapons and
child inheritance must be mapped separately. Public CAW export/hex tools work
on process memory and can be followed by game recalculation; they are not
serialized save editors.

The DW6 plaintext-reader lead provides substantive native disk observations but
no complete fixture, accepted size or integrity model. P5S's reproduced PC
stream vector and DW8 Empires' procedural cipher tests similarly do not prove
gameplay serialization or native platform identity. Their source-only research
primitives expose no gameplay adapter.

Both supplied DW4 formats are now available in separate platform libraries.
The PC and USA PS2 implementations use distinct item/equipment identifiers,
weapon maxima, difficulties and checksums; see DW4_PLATFORM_FORMATS.md.
Availability follows their published editors, while independent genuine-file
and in-game validation remain pending.
