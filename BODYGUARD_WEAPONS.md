# Bodyguard weapons: verified save mapping and safe edits

The supplied workspace save, shipped cooked tables/native reflection and
shipping executable were inspected without launching the game or accessing
live saves/Steam Cloud. These are conservative **native-drop** templates;
bodyguard weapon fusion and runtime acceptance remain unvalidated. Exact
definitions and per-weapon bonus limits are in
[bodyguard_weapons.json](bodyguard_weapons.json).

The executable used for all RVAs below has SHA-256
`3691d3fd41eb744c99fee8fc0a342159a0155d4aea90f910fe8985b46c5dc2e2`.
RVA means executable relative virtual address; native object strides are not
save-file strides. Save changes must use parsed variable-length tagged fields.

## Inventory, IDs and acquisition

GuardWeaponDataArray is a 100-record WeaponSaveData inventory. Each record has
WeaponID/ID enum FStrings, nine EquipItemSaveData skill records, Int64 Attr,
Int32 DataID and Double GetTime. An empty slot has both weapon enums `NUM`,
nine `EEquipItemID::NUM`/`EGuardEquipItemID::NUM`/zero skills, Attr zero,
DataID −1 and GetTime zero. Constructor `0x1356C30..0x1356CED` creates this
layout, including exactly nine skills.

The insertion routine `0x150AC10` classifies bodyguard IDs by
`byte(WeaponID + 0x53) <= 14` at `0x150AC62..0x150AC6C`: exactly **173–187**.
At `0x150AC72..0x150AD49` it scans GuardWeaponDataArray for the first WeaponID
`NUM` slot, copies the incoming weapon and sets DataID to that inventory
index. It can expand at runtime, but editor v0.2 should refuse acquisition
when the existing 100 slots are full; array expansion is not proved here.

There are five families with three definition tiers each. Generator
`0x1515575..0x1515621` computes `173 + 3*family + min(dropRank,2)`.
EBGTypeNameID's shipped English localization labels the five families.

| Family | Tier 1 | Tier 2 | Tier 3 |
|---|---|---|---|
| Sword (0) | 173 Iron Sword, power 8 | 174 Long Sword, power 15 | 175 Elder Sword, power 20 |
| Spear (1) | 176 Spear, power 7 | 177 Dragon Spear, power 15 | 178 Crescent Blade, power 20 |
| Pike (2) | 179 Long Pike, power 7 | 180 Heavenly Spear, power 15 | 181 Tiger's Chin, power 20 |
| Bow (3) | 182 Iron Bow, power 7 | 183 Steel Bow, power 15 | 184 Gale Bow, power 20 |
| Crossbow (4) | 185 Iron Crossbow, power 8 | 186 Steel Crossbow, power 15 | 187 Wind Crossbow, power 20 |

Base power is the shipped WeaponBaseData `Power` field selected by ID, not an
independent editable stat in WeaponSaveData. Changing tier changes the weapon
definition, model and related properties. It should be an explicit selection,
not a rewrite of arbitrary numeric base attack.

**Saved Attr is zero for generated bodyguard weapons.** The guard branch
clears it at `0x1515624`; it does not copy WeaponBaseData's Attribute bitmask.
The sample includes Long/Elder Swords with Attr zero even though their
definition bitmasks are 1/3. Those definition bits must not be blindly copied
into bodyguard save records.

## Collection cache and equipped references

Before inventory insertion, `0x150AC33..0x150AC5E` initializes
CollectedWeaponDataArray[WeaponID] only when that cache entry's WeaponID is
`NUM`, then sets its DataID to the weapon ID. Thus inventory DataID is a slot
index, while collection DataID is a definition ID. An already owned cache is
preserved for later copies and stronger bonuses.

Equipped loading at `0x13BFE82..0x13BFE9C` reads
GuardData.MemberWeapon[PCSaveData.BGType], then directly indexes
GuardWeaponDataArray at that value. It does **not** equip from the collection
cache. The MemberWeapon array has ten Int32 entries in this sample; the first
five correspond to Sword/Spear/Pike/Bow/Crossbow. Remaining positions are
reserved and preserved. Equipped values are inventory indices, not weapon IDs.

Consequently acquisition must preserve all existing inventory rows and team
references. A separate equip action can set a first-five family entry only
when the referenced slot is owned, DataID equals that slot and its weapon
belongs to the matching family. `−1` is an existing unassigned sentinel; a
normal acquisition does not alter it. Maximizing inventory bonuses does not
require replacing an already owned collection cache.

## Bonus generation and limits

Guard bonuses use **GuardEquipItemID**, with ordinary EquipItemID left `NUM`.
The guard definition getter is `0x14648A0`. The generated pool at
`0x15159F0..0x1515A39` examines IDs 0–9 and keeps Type zero: normal IDs **0–8**.
Rare ID 9 (BG Healing Scroll) has Type 1 and is excluded. No guard rare-skill
insertion was found in this generation branch.

| Guard item ID | Bonus | Highest verified weapon value |
|---:|---|---:|
| 0 | HP | 30 |
| 1 | Musou | 30 |
| 2 | Attack | 20 |
| 3 | Defense | 20 |
| 4 | Bow Attack | 10 |
| 5 | Bow Defense | 10 |
| 6 | Speed | 10 |
| 7 | Reach | 10 |
| 8 | Musou Charge | 10 |

These are weapon bonuses, not ordinary equipped bodyguard item caps.
Weapon generation uses each row's **RandomSeed** array, rather than the
ordinary item generator's ValueRand. The shipped seeds are `[2,4,4,5]` for
HP/Musou, `[2,2,4,4]` for Attack/Defense and `[1,1,2,3]` for other bonuses.

At `0x1515B2B..0x1515C50`, a tier comes from the first **four**
DT_DropRandomTable.SkillItemRandRank thresholds (stage rank capped at 13).
The raw random integer is `0..RandomSeed[tier]−1`. HP/Musou add 1 at tier 2
or 2 at tier 3; Attack/Defense add 1 at tier 3; others add nothing. The final
value is five times that raw result, with zero replaced by **1**. Therefore
native-drop bonus values are 1 or positive multiples of 5.

The maximum count is **three distinct eligible normal bonuses**, even though
nine saved skill slots exist. `0x1515991..0x15159E1` uses shipped
SkillRandomType_GuardWeapon thresholds `[2,12,32,38,0]`, scanning four entries,
then computes `min(3,3−selectedIndex)`. Selector 0 or 1 selects index zero and
three bonuses. A zero-count result uses a single eligible value-1 fallback.
The candidate list is shuffled, so eligible triples and independent highest
random rolls are possible. Invalid family candidates are skipped, and this
can leave gaps among the saved skills; slots need not be consecutive.

Family restrictions at `0x1515AF0..0x1515B2B` are:

- Sword/Spear/Pike: IDs 0,1,2,3,5,6,7,8; Bow Attack (4) is excluded.
- Bow/Crossbow: IDs 0,1,3,4,5,6,8; Attack (2) and Reach (7) are excluded.

There is also a **weapon-tier dependency**. Shipped WeaponRandRank and
SkillItemRandRank tables show that tier-1 weapons drop only at stage ranks
0–4, where bonus tiers are 0/1. Tier-2/3 variants can drop at ranks 7–10 with
bonus tier 3. Rank 7 is reachable in ordinary battles; high-stage reachability
was independently established by ScenarioSettingData plus difficulty
corrections. Exhaustive selector enumeration yields:

| Weapon tier | HP/Musou values | Attack/Defense values | Other bonus values |
|---|---|---|---|
| 1 | 1,5,10,15 | 1,5 | 1 |
| 2 or 3 | 1,5,10,15,20,25,30 | 1,5,10,15,20 | 1,5,10 |

The highest-tier item table row is not sufficient by itself: stage-13 weapon
bonuses scan only four zero thresholds and fall back to tier zero. The maxima
above are proved from reachable rank-7–12 rows, which have nonzero tier-3
thresholds. Lower-tier caps remain conservative until bodyguard fusion is
understood; no transfer-based higher limits are assumed.

## Proposed writer behavior

`Unlock All Bodyguard Weapons` can ensure all 15 definitions exist by adding
only missing IDs to first available NUM slots, preserving existing duplicates,
DataIDs, Attr, GetTime and equipped references. Each new record can receive
a verified three-bonus profile: HP/Attack/Defense for melee, or HP/Defense/Bow
Attack for ranged, at that definition's documented tier caps. Unused slots
retain NUM/NUM/zero. If collection ownership is missing, initialize its record
from this same acquired template with DataID = weapon ID; preserve owned cache.

An explicit `Max Weapon Bonuses` action may replace an owned row's skills with
that legal profile while preserving ID/WeaponID, Attr, DataID and timestamp.
It should be clearly separate from acquisition. Custom bonus edits should
enforce at most three unique IDs, family eligibility and the exact allowed
value set from bodyguard_weapons.json. Existing unsupported/fused combinations
can remain readable/preserved rather than being silently normalized.

The sample has 21 owned inventory rows and 79 blank rows; all 21 owned DataIDs
equal their slot indices, and collection records follow the described mapping.
This observation supports the native dataflow but is not used as a fixed
allocation assumption. Tests must cover full-pool refusal, sequential batch
allocation, unchanged owned rows/equipped references, legal profile round trips,
collection first-copy preservation and family mismatch refusal.

No in-game load or bodyguard fusion test has been performed. Editing array
lengths, overwriting owned rows during acquisition, equipping a definition ID
as an inventory index, copying definition Attr bits and allowing rare item 9
as a weapon bonus are outside the confirmed design.
