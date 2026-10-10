# Bodyguards in editor v0.2

The Bodyguards tab edits four saved teams, their growth, ten bodyguard items
and a shared inventory of 100 bodyguard weapon copies. It uses shipped game
tables and verified native save/generation paths. **Edited saves have not yet
been loaded in the game.** Use a separate save copy, retain its automatic
backup and keep the game closed when eventually installing an edited copy.
The editor refuses live game-save and Steam Cloud paths.

## Using the controls

1. Open a copied `GameStatusData.sav`, then choose a team on Bodyguards.
2. On Team Growth, enter Merit and allocate Life, Attack, Defense and
   Bow/Moveset points. Count and AI follow the entered Merit. The preview
   shows the legal point budget and growth base stats.
3. A selected-team preset sets 99,999 Merit and a legal allocation. Max All
   Teams applies Balanced growth to all saved teams.
4. BG Items can unlock individual items, edit verified normal rolls, unlock
   all items or maximize them. The Healing Scroll has ownership only.
5. BG Weapons displays the 15 definitions and owned copies. Unlock adds a
   missing copy; Max Selected Bonuses updates every owned copy of that
   selected definition. Max All Bonuses ensures all definitions are owned
   and applies the verified bonus profiles to every copy. Select an owned
   copy beneath a definition to choose up to three eligible bonuses from
   the verified values, then apply that copy's bonuses.
6. On Team Equipment, choose an owned item and a weapon copy for each of the
   five families, then apply the equipment choices. Equip Best Owned Weapons
   selects the highest owned tier in each family, breaking ties by the sum
   of saved bonuses. It is a convenience rule, not a combat optimization.
7. Review the pending changes and use Save As or Save Changes to write them.
   Applying a form changes the editor's pending state until then.

Unlocking preserves existing weapon copies and equipped choices. Maximizing
weapon bonuses deliberately replaces their current bonuses with the legal
profiles described below. Growth/item/weapon presets preserve team names,
member appearance/type and story completion. Remove The Grind includes
balanced team growth, all bodyguard items at verified caps and all bodyguard
weapons with legal bonuses; equipment choices remain separate.

## Merit and legal growth

`GuardDataArray` contains four variable-length `GuardSaveData` tagged records.
`SPoint` is Int32 Merit, capped at **99,999** by native result accumulation
`0x1518977..0x1518986` and normalization `0x1508EA7`/`0x1508EB1`.
`BGLevels` is an Int32 array of six levels:

| Index | Growth | Maximum | Consumes the shared budget? |
|---:|---|---:|---|
| 0 | Life | 11 | Yes |
| 1 | Attack | 11 | Yes |
| 2 | Defense | 11 | Yes |
| 3 | Count | 3 | No; automatically earned |
| 4 | Bow / Moveset | 3 | Yes; also Merit gated |
| 5 | AI | 3 | No; automatically earned |

The shared spend is `BGLevels[0]+[1]+[2]+[4]`. Shipped
`DT_BGTotalLevelPoint` gives **25 points at 99,999 Merit**, rather than a
25,000-Merit cap. Its 26 thresholds, levels 0–25, are:

```text
0, 1000, 2000, 4000, 6000, 8000, 10000, 13000, 16000, 19000,
23000, 27000, 31000, 35000, 39000, 44000, 49000, 54000, 59000,
64000, 69000, 75000, 81000, 87000, 93000, 99999
```

Count and Bow/Moveset ranks 1/2/3 require 25,000/50,000/75,000 Merit.
AI ranks 1/2/3 require 30,000/60,000/90,000. Growth application synchronizes
Count and AI to earned ranks and checks the four allocations against their
final Merit. Reducing Merit is accepted only with a legal final allocation;
the editor rejects over-budget or Merit-ineligible combinations.

At 99,999 Merit, each preset spends exactly 25 points:

| Preset | Life / Attack / Defense / Count / Bow / AI | Base Life and Musou | Base Attack | Base Defense |
|---|---|---:|---:|---:|
| Balanced | 8 / 7 / 7 / 3 / 3 / 3 | 260 | 110 | 110 |
| Favor Life | 11 / 6 / 5 / 3 / 3 / 3 | 290 | 100 | 90 |
| Favor Attack | 6 / 11 / 5 / 3 / 3 / 3 | 240 | 130 | 90 |
| Favor Defense | 6 / 5 / 11 / 3 / 3 / 3 | 240 | 90 | 130 |

These are legal editor allocation choices. All four allocated growth fields
cannot simultaneously reach their individual maxima within the 25-point
budget. The preview is **growth base data**: equipment, bodyguard type,
formation/order, battle modifiers and converted Unreal movement units are
excluded. Base Life/Musou use `DT_BGLevelData[Life].HP_Special` plus
`DT_BGMemLevelData[Bow].HP_Add`; the runtime clamp is 400. Base Attack/Defense
come from their growth rows, whose maximum is 130 before equipment/context.
Bow is a percentage multiplier; moveset and AI are progression selections,
not flat Attack/Defense values.

The Count rank selects 3/5/7/9 members. Associated playable officers' `MemCnt`
is updated when it equalled the team's previous maximum; smaller selected
counts are preserved. A reduction clamps selected counts above the new
maximum. Officer placeholders remain unchanged.

Native evidence and all table rows are recorded in
[bodyguard_growth.json](../src/koei_editor/data/bodyguard_growth.json). Budget/spend paths are
`0x150622F`, `0x1506262..0x1506275` and getter `0x145E6B0`; Count/AI progression
is `0x15061BB`/`0x15061F5`; Bow's Merit gate is `0x1506434`.

## Bodyguard items

`GuardEquipItemDataArray` has ten indexed `EquipItemSaveData` records. Its
ordinary `EquipItemID` stays `EEquipItemID::NUM`; bodyguard ownership uses
`GuardEquipItemID`, whose enum must match the inventory index. Unowned is
`EGuardEquipItemID::NUM` with Value zero. Normal Value is Int32, 1 through
the following native-generation cap:

| ID | Item | Effect | Ordinary item cap | Highest tier-2/3 weapon bonus |
|---:|---|---|---:|---:|
| 0 | BG Peacock Urn | Life | 40 | 30 |
| 1 | BG Dragon Amulet | Musou | 40 | 30 |
| 2 | BG Tiger Amulet | Attack | 25 | 20 |
| 3 | BG Tortoise Amulet | Defense | 25 | 20 |
| 4 | BG Huang's Bow | Bow Attack | 15 | 10 |
| 5 | BG Shell Armor | Bow Defense | 15 | 10 |
| 6 | BG Speed Scroll | Speed | 15 | 10 |
| 7 | BG Wind Scroll | Reach | 15 | 10 |
| 8 | BG Elixir | Musou Charge | 15 | 10 |
| 9 | BG Healing Scroll | Heals the bodyguard once | Ownership only; Value 0 | Excluded |

Ordinary generation `0x15175D0..0x15176F0` uses five drop thresholds and
`tier*ValueRand+randomInteger(1,ValueRand)`. The shipped rows use ValueRand
8/8/5/5/3/3/3/3/3; reachable stage rank 13 selects tier 4. Ordinary pickup
`0x13761FD` passes the battle rank. Rare acquisition
`0x1677FC0..0x1678022` calls the guard-item writer with Value zero. Full enums,
names, effects, asset hashes and evidence are in
[bodyguard_items.json](../src/koei_editor/data/bodyguard_items.json).

Each team's `MemberItem` is an owned bodyguard item enum or NUM. The editor
refuses removing a team-equipped item until it is unequipped. It also refuses
removing an item referenced by playable officers' `BGMusouEquipItem`, whose
full inventory dependency is not established. Those officer settings are
preserved.

## Weapons, tiers and bonuses

The 100-slot `GuardWeaponDataArray` inventory stores ordinary
`WeaponSaveData` tagged records. There are **15 bodyguard definitions**:

| Family | Tier 1: ID, name, base power | Tier 2 | Tier 3 |
|---|---|---|---|
| Sword (0) | 173 Iron Sword, 8 | 174 Long Sword, 15 | 175 Elder Sword, 20 |
| Spear (1) | 176 Spear, 7 | 177 Dragon Spear, 15 | 178 Crescent Blade, 20 |
| Pike (2) | 179 Long Pike, 7 | 180 Heavenly Spear, 15 | 181 Tiger's Chin, 20 |
| Bow (3) | 182 Iron Bow, 7 | 183 Steel Bow, 15 | 184 Gale Bow, 20 |
| Crossbow (4) | 185 Iron Crossbow, 8 | 186 Steel Crossbow, 15 | 187 Wind Crossbow, 20 |

Base power is resolved from shipped WeaponBaseData by weapon ID; it is not
an independent save scalar. Saved bodyguard Attr is zero, even where the
definition has Attribute bits. The inventory's `ID` and `WeaponID` match;
`DataID` equals the inventory slot. Each record has nine saved skills, but
native drops allow at most **three distinct eligible normal bonuses**.
Bonuses use GuardEquipItemID with ordinary EquipItemID NUM.

Sword/Spear/Pike permit skill IDs 0,1,2,3,5,6,7,8. Bow/Crossbow permit
0,1,3,4,5,6,8. The Healing Scroll is never a generated weapon bonus. Exact
generated values depend on the weapon's tier:

| Bonus type | Tier 1 allowed values | Tier 2/3 allowed values |
|---|---|---|
| Life/Musou | 1, 5, 10, 15 | 1, 5, 10, 15, 20, 25, 30 |
| Attack/Defense | 1, 5 | 1, 5, 10, 15, 20 |
| Other eligible bonuses | 1 | 1, 5, 10 |

The maxima are conservative native-drop limits, established from both weapon
and skill tier reachability. They do not assume fusion can transfer higher
bonuses onto tier-1 weapons. Max actions use Life/Attack/Defense on melee and
Life/Defense/Bow Attack on ranged, at that definition's respective caps.
Per-definition metadata and full native proof are in
[bodyguard_weapons.json](../src/koei_editor/data/bodyguard_weapons.json) and
[BODYGUARD_WEAPONS.md](BODYGUARD_WEAPONS.md). Per-copy bonus controls use
family-eligible IDs, forbid duplicate IDs and offer only the exact discrete
values for that tier. Max actions replace any previous custom choices with
the documented maximum profiles.

Acquisition adds only missing IDs to first available NUM inventory slots,
preserving existing duplicates, times and equipped references. A full pool
causes an error; the editor does not expand it or replace existing weapons.
Native acquisition `0x150AC10` populates
`CollectedWeaponDataArray[weaponID]` only for first ownership, with DataID set
to the definition ID. Existing collection caches stay unchanged when bonuses
are maximized, matching native first-copy behavior.

`GuardData.MemberWeapon` has ten Int32 references in this layout; only the
first five families are editable, and remaining entries are preserved.
They reference **inventory slot indices**, not definition IDs or collection
indices. Native equipped loading `0x13BFE82..0x13BFE9C` selects
`MemberWeapon[PCSaveData.BGType]` then loads that GuardWeaponDataArray slot.
The editor checks owned state, matching family and slot identity. NUM weapons
cannot be equipped; `−1` is the existing unequipped sentinel.

## Write validation and remaining boundaries

The shared writer locates tagged fields, updates variable-length enum strings
and every enclosing payload size, updates the big-endian envelope length,
regenerates zero AES padding and reencrypts. It reparses the result and
preserves other parsed regions. Unchanged output remains byte-identical;
enum resizing shifts later offsets and may change many ECB blocks. There is
no invented checksum or guessed fixed bodyguard disk stride.

The evidence executable has SHA-256
`3691d3fd41eb744c99fee8fc0a342159a0155d4aea90f910fe8985b46c5dc2e2`.
Native strides (`GuardSaveData` 0x58, `WeaponSaveData` 0x30) describe runtime
objects, not serialized records. Bodyguard fusion, unknown extra equipment
slots, model/type changes, other game builds and in-game acceptance remain
unverified. Supported controls enforce the discovered bounds; unsupported
fields are preserved or refused.

## v0.3.2 compatibility

The editor uses the teams actually stored in the save. Two- and four-team
samples are verified; team count, order and names are preserved. Existing
weapon bonuses outside the conservative native-drop profiles are view-only
and preserved by bulk maximum actions. See [COMPATIBILITY_FIX.md](COMPATIBILITY_FIX.md).
