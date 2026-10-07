# Dynasty Warriors 3: Complete Edition Remastered save format

## v0.85 customization, collections and campaign saves

`bodyguard_customization.py` handles four native lazy Bool arrays. Model
availability and new-option notifications are stored in
`CanUseSecretGuardModelArray` / `NewCanUseSecretGuardModelArray` (two known
entries); colors use `CanUseSecretGuardColorArray` /
`NewCanUseSecretGuardColorArray` (four known entries). Native model setter
RVA `0x1512FF0` maps gender IDs 2/3 to slots 0/1 (Nanman Male/Female).
Native color setter RVA `0x1513120` maps clothing IDs 5/6/7/8 to slots
0/1/2/3 (Yellow/White/Black/Pink). Missing or short arrays are extended with
zero entries like the native setters. Existing extra entries are preserved.
A notification is set only when its corresponding choice becomes available
for the first time. Equipped appearances, story clears and team growth are
independent and remain unchanged. Confidence: confirmed native dataflow,
localized names and supplied serialized records.

`collection_editor.py` uses `OptionData.Edit.bPlayMovie`, a native 100-entry
Bool array. Shipped `DT_MovieData` identifies supported playable movie IDs
0–49. ID 50 and IDs 52–99 are placeholders; ID 51 is the title loop, so none
of those are authored by the gallery action. Missing current flags are
initialized false using the native default count and matching tagged Bool
serialization. Existing sibling acknowledgement flags (`bPlayMovie_Old`)
and other options are preserved; additional future array entries are kept.
Nested insertions regenerate all enclosing property byte sizes. Confidence:
confirmed schema, native defaults, authored table entries and byte round trips.

Music current/acknowledgement arrays are `OptionData.Sound.bPlayBGM` and
`bPlayBGM_Old` (native defaults: 100 false entries). In v1.0,
`collection_editor.py` unlocks the **42 displayed MUSIC gallery entries,
IDs 0–41**. The copied executable's native `BGMGalleryWidget` constructor
RVA `0x12AE520` sets its private list count to 42 at instance offset `0x388`.
NativeConstruct `0x16C7600` builds IDs 0–41 in order, and list population
`0x16C85F0` passes each unchanged ID to item setup `0x16C8C60`.
The item reads `bPlayBGM[id]` directly: reflected OptionData offset `0x1C8`,
Sound offset `0x48`, current-array offset `0x18` (OptionData + `0x60`).
The native count is not a reflected Blueprint property.

`bPlayBGM_Old` is the game's acknowledgement state, at Sound + `0x28`
(OptionData + `0x70`). The item displays NEW when current is true and old
is false; native acknowledge function `0x16C8EE0` sets old[id] to true.
The editor preserves that array and every current slot from 42 onward,
including pre-existing audio flags outside the gallery. It refuses new
edits for those IDs even though `DT_BGMDefsData` has 89 nonzero event hashes
(IDs 0–44 and 50–93). English labels use shipped main-title keys 000–041;
the native title enum confirms the same numeric values.
Missing current arrays use the verified 100-slot tagged Bool layout;
malformed arrays remain view-only. Combined music/movie insertions regenerate
enclosing sizes and retain acknowledgement arrays. Confidence: high for this
inspected build, with constructor/vtable/indexed-read evidence and byte-level
round-trip, preservation, sparse-insertion and idempotence tests. Other
builds/platforms remain outside the verified contract.

`musou_slots.py` handles between-stage runs in `EngiSaveDataArray`. Its saved
count is retained; array positions remain slot identities. An explicit Remove
action resets a supported record to shipped `EngiSaveData` constructor defaults:
`CharaID = EPlayerCharaID::NUM`; `NowStage`, `EventFlag`, `PCColor` and DateTime
`SaveDate` are zero; `StageSPoint`/`ClearTime` remain ten zero Int32 entries;
`GuardNum` remains two zero Int32 entries; `isClearChara` and
`isNewMusouMode` become false. Each of the ten KO history records has zero
`KOCnt`, an empty `KOCommanderList` and false `isGekiMusou`. Unknown record
fields or nested layouts make only that run view-only. No permanent officer,
content availability or global completion fields are reset. Confidence:
confirmed reflected schema, native constructor and supplied active campaigns.

Maximum actions distinguish authored drop limits from existing saved values.
A normal item Max uses the highest of its normal drop cap and its original or
pending owned value. A saved positive high weapon bonus can be retained only
with its original identity, value and physical slot. New values use verified
ordinary/fusion or weapon-specific stock sets. Bodyguard Max retains existing
eligible bonus types and physical positions and adds stock bonuses only within
supported capacity. Existing higher values are not evidence of a different
natural drop cap. See [WEAPON_ROLLS.md](WEAPON_ROLLS.md).

## Existing compatibility and progression support

Counts and offsets below describe the original research save. They are not
universal layout constraints: complete tagged arrays use their saved counts.
The parser preserves additional records and unknown gameplay values; new edits
still require verified rules. See [SAVE_COMPATIBILITY.md](SAVE_COMPATIBILITY.md).

Ziluan's unique weapon IDs 191/192 occupy unique slots 102/103, so natural
acquisition expands the array to 103/104 records. All 84 stock unique weapons
are supported. Padding records use native NUM identities and DataIDs 10000+slot.
`weapon_collection.py` fills the 176 playable first-acquisition gallery entries
without replacing existing snapshots or adding ordinary inventory copies.
Tactics costumes use `CanUseCostume[3]` for officers 12/13; retro DLC uses a
separate flag and is preserved.

`progression_routes.json` records the native 39 Musou routes. Rulers 11/14/15
have ten stages; other supported routes have seven. Officers 39/40/41 have no
Musou route. Explicit clears update `EngiClearCharaArray`, officer `Progress`
and first-clear Huanglong Elixirs (three each, total capped at 999). Active run
records and timestamps stay unchanged. Side-story availability maps Wei/Wu/Shu
to ReMusou IDs 0/1/2 and Free Mode scenarios 101-106; it does not mark stages
completed. Missing optional availability arrays are created using verified
native BoolProperty serialization.

`BeansNum` stores the global Huanglong Elixir balance as a signed little-endian
Int32. The Unlocks tab supports an explicit final balance from 0 through 999;
when combined with Musou clears, that balance takes precedence over automatic
first-clear awards. See the Huanglong Elixirs section below.

Existing six-level bodyguard growth is checked for its physical representation
separately from rules for spending new points. Unknown growth representations
are preserved and shown as view-only.


This document describes the Steam Windows save structures used by editor v0.85.
The codec, tagged structures and enabled edits are supported by supplied save
copies, shipped metadata and static executable dataflow.

Offsets below are **decrypted sample offsets**, including its four-byte
envelope. They are examples, not portable fixed offsets. The editor locates
serialized tags and recalculates positions after resizing. Executable
addresses are relative virtual addresses (RVAs), not save-file offsets.

## Build and key provenance

| Evidence | SHA-256 |
|---|---|
| Inspected shipping executable | `3691d3fd41eb744c99fee8fc0a342159a0155d4aea90f910fe8985b46c5dc2e2` |
| Untouched encrypted sample | `02dd42241b70cd580c3f78e42fd4f89b3d8b832ad1230c49e5c8d19bfdf169c2` |
| Decrypted padded sample | `8ca7b8b3b91e69c158ac309b0d67046d76efe75bdcd31c64200764d83adca72b` |
| Shipped `DW3CE_RE/Config/DefaultGame.ini` | `20f83963da32630591a903abec3c9a7d80469716f425abadb868843cf8187087` |
| Shipped English `Game.locres` | `f918e60a08f3e037ae29733707ffcf64d01edabadde4bd2b7e9ae3c7d427a7eb` |

The version-11 package index is encrypted. A static eight-dword initializer
yielded the package key, verified independently against the main, directory
and path-index SHA-1s. [repak v0.2.3](https://github.com/trumank/repak/releases/tag/v0.2.3)
then extracted the shipped configuration read-only. Its section
`[/Script/WindowsSaveGameSystem.WindowsSaveLoadSettings]` sets `CryptionKey`.
The save key is the setting's **32 ASCII bytes**, with no discovered derivation.
Its SHA-256 fingerprint is
`e6f32605b924ec85f27de56ae067b67b2f30fad4521604897a98939faca239d0`.
The package key and save key differ.

Native registration `0x17EB070`/`0x17EC120` identifies the settings class and
Game config hierarchy. Constructor `0x17EB1C0` initializes an empty key string;
the configured value comes from the shipped file. No account ID, Steam
metadata or live-save lookup is required by the editor.

## Codec, envelope and integrity

The entire file is AES-256-ECB ciphertext without an IV. Decryption produces:

| Region | Representation | Sample |
|---|---|---|
| Offset `0` | Big-endian uint32 serialized payload length | 3,334,231 |
| Offset `4` | Unreal payload | Starts `GVAS` |
| End of serialized payload | Preserved UObject trailer | Four zero bytes |
| Following payload | Zero padding to a 16-byte boundary | Five bytes |

The sample ciphertext is 3,334,240 bytes. The length includes the GVAS header,
properties, final `None` terminator and UObject trailer; it excludes the
four-byte length and AES padding. Padding is zero fill, **not PKCS#7**.

`UGameplayStatics`' writer `0x443D470` writes the GVAS header and invokes object
serialization at `0x443D725`. `GameStatusSaveGame`'s Serialize vtable entry is
`0x1D77630`, the same routine used by `USaveGame`. No custom checksum, MAC,
signature, compression layer or title-specific Serialize override was found
in the inspected save paths. This is a finding about this build/sample, not
a promise about future versions or unknown properties. Backup/change-report
SHA-256 hashes are external metadata, not embedded save checksums.

The AES implementation is checked against the AES-256-ECB known-answer vector
in [NIST SP 800-38A, F.1.5](https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-38a.pdf).
Unchanged decrypt/parse/write/encrypt reproduces the original ciphertext exactly.

## Header and tagged properties

The supported header is save version **3**, UE4 package version **522**, UE5
package version **1017**, engine **5.6.1**, changelist **0**, branch `UE5`,
custom-version format **3**, 89 GUID/version entries in the sample, and class
`/Script/Refine.GameStatusSaveGame`. A serialization-control byte after the
class is zero. Compatible engine patch numbers are descriptive; the parser
requires the supported serialization versions, engine major version, save
class and property layouts. Unsupported serialization/class/control is refused.

The sample uses complete property-type trees, consistent with Unreal's
[FPropertyTag/TypeName API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/CoreUObject/FPropertyTag).
A tag contains a property-name FString, recursive type name/child types,
little-endian int32 payload size, flags/flagged metadata, then payload.
`None` terminates each property sequence. An FString uses a signed
little-endian int32 count: positive counts encode terminated UTF-8 bytes;
negative counts encode terminated UTF-16LE code units.

IntProperty is signed little-endian int32; Int64Property/DoubleProperty occupy
eight bytes. An EnumProperty identifies its enum/backing type in the type
tree, but saves its selection as an FString such as `EEquipItemID::NUM`,
**not a one-byte integer**. A standalone BoolProperty may store its value in
tag flags with zero payload. ArrayProperty begins with an int32 count;
boolean arrays use one byte per element. Struct-array elements have their
own tagged records/terminators. Unsupported opaque fields remain untouched.

There are **24 top-level properties**, including **18 arrays**:

| Property | Type/count in sample | Payload offset | Bytes | Current editing status |
|---|---|---:|---:|---|
| PCSaveDataArray | PCSaveData ×50 | 1977 | 89768 | Stats/Merit for 0–41 |
| EngiSaveDataArray | EngiSaveData ×3 | 91861 | 9350 | Preserved |
| WeaponDataArray | WeaponSaveData ×500 | 101327 | 1690048 | Normal bonus editing; other fields preserved |
| UniqueWeaponDataArray | WeaponSaveData ×84 | 1791497 | 283834 | All 84 stock uniques; native expansion for Ziluan |
| GuardWeaponDataArray | WeaponSaveData ×100 | 2075452 | 339089 | 15 definitions, legal bonuses/equipment |
| CollectedWeaponDataArray | WeaponSaveData ×255 | 2414666 | 862134 | Acquisition snapshots and playable collection gallery |
| EquipItemDataArray | EquipItemSaveData ×100 | 3276922 | 32458 | Items 0–42 |
| EquipItemSetDataArray | EquipItemSetSaveData ×8 | 3309508 | 2020 | Preserved loadouts |
| GuardEquipItemDataArray | EquipItemSaveData ×10 | 3311655 | 3354 | Nine normal items and one rare |
| GuardDataArray | GuardSaveData ×4 | 3315123 | 8064 | Legal Merit/growth and equipment |
| CanUseScenarioArray | Bool ×156 | 3323259 | 160 | Availability 0–107 only |
| ClearScenarioArray | Bool ×156 | 3323490 | 160 | Completion preserved |
| NewCanUseScenarioArray | Bool ×156 | 3323725 | 160 | Preserved |
| CanUseCharaArray | Bool ×50 | 3323954 | 54 | Availability 0–41 only |
| NewCanUseCharaArray | Bool ×50 | 3324080 | 54 | Preserved |
| EngiClearCharaArray | Bool ×50 | 3324206 | 54 | Separate explicit Musou clear actions |
| TutorialPlayedFlagArray | Bool ×20 | 3324336 | 24 | Preserved |
| ChallengeModeRankingArray | ChallengeModeRankingData ×6 | 3324496 | 3790 | Preserved |
| OptionData | OptionSaveData struct | 3328375 | 4176 | Preserved |
| RecordSaveData | RecordSaveData struct | 3332644 | 1025 | Preserved |
| isOpenOPEdit | Bool | 3333712 | 0 | Preserved |
| TipsWindowSaveData | TipsWindowSaveData struct | 3333813 | 68 | Preserved |
| BeansNum | Int32 | 3333919 | 4 | Huanglong Elixirs: final balance 0–999 |
| DLCPermissionSaveData | DLCPermissionSaveData struct | 3334030 | 192 | Preserved |

Structural parsing does not establish every field's gameplay meaning or safe
mutation. Complete arrays retain their actual saved lengths. Expansion is
implemented only for the native indexed unique acquisition path and optional
side-story availability arrays.

## Officers

PCSaveDataArray has 50 **variable-length tagged records**. Observed lengths
are 1,785, 1,802, 1,893, 1,900 and 1,906 bytes. Native runtime stride `0x60`
is not a disk stride. The indexed mapping follows shipped
`/Game/DataAsset/DT_PlayerCharaData` EPlayerCharaID rows and English display
localization; [officer_names.json](officer_names.json) records every ID.

| IDs | Officers, in index order |
|---|---|
| 0–6 | Zhao Yun, Guan Yu, Zhang Fei, Xiahou Dun, Dian Wei, Xu Zhu, Zhou Yu |
| 7–13 | Lu Xun, Taishi Ci, Diaochan, Zhuge Liang, Cao Cao, Lu Bu, Sun Shangxiang |
| 14–20 | Liu Bei, Sun Jian, Sun Quan, Dong Zhuo, Yuan Shao, Ma Chao, Huang Zhong |
| 21–27 | Xiahou Yuan, Zhang Liao, Sima Yi, Lu Meng, Gan Ning, Jiang Wei, Zhang Jiao |
| 28–34 | Xu Huang, Zhang He, Zhenji, Huang Gai, Sun Ce, Wei Yan, Pang Tong |
| 35–41 | Meng Huo, Zhurong, Daqiao, Xiaoqiao, Fuxi, Nuwa, Ziluan |

Indices 42–49 are preserved placeholders. `GeneralNameID` is a title/progression
enum, not officer identity. `Progress`, `GeneralNameID`, costume permissions
and equipped weapon/bodyguard selections remain unchanged by stat presets.

| Field | Type | Officer 0 sample | Sample payload offset | Proven maximum |
|---|---|---:|---:|---:|
| MaxHealth | Int32 | 190 | 2020 | 250 |
| MaxMusou | Int32 | 210 | 2062 | 250 |
| Attack | Int32 | 132 | 2102 | 150 |
| Defence | Int32 | 135 | 2143 | 150 |
| SPoint (Merit) | Int32 | 99999 | 2559 | 99999 |
| Progress | Int32 | 7 | 2761 | Explicit Musou clear: route length 7 or 10 |

Getter `0x1514C40` resolves permanent officer records. Gameplay writes
`0x15DFC95..0x15DFD26` clamp HP/Musou to 0–250 and Attack/Defense to 0–150;
the editor requires HP/Musou at least 1. Merit normalization
`0x1508832`/`0x150883B` and result accumulation `0x1518648..0x151876A`
cap SPoint at 99,999.

## Items

Ownership is an indexed EquipItemDataArray slot whose `EquipItemID` matches
its item ID. `EEquipItemID::NUM` is the unowned sentinel; `Value` is Int32.
Direct acquisition `0x1516E50`, especially `0x1516F0F..0x1516F43`, and result
commit `0x1518273..0x15182B2` establish slot index = EEquipItemID. Ownership
changes resize enum strings; they are not fixed one-byte patches.

Shipped EquipItemBaseData defines 16 normal and 27 rare items. IDs 43–99 are
unsupported placeholders. Names, enum names, effects and definition IDs are
in [game_metadata.json](game_metadata.json). Rare ownership writes its enum
and scalar value zero. Normal owned values use 1 through the verified cap.

| ID | Normal item | Effect | ValueRand | Legitimate maximum |
|---:|---|---|---:|---:|
| 0 | Speed Scroll | Speed | 4 | 20 |
| 1 | Wing Boots | Jump | 4 | 20 |
| 2 | Dragon Amulet | Musou | 15 | 75 |
| 3 | Peacock Urn | HP | 15 | 75 |
| 4 | Tiger Amulet | Attack | 5 | 25 |
| 5 | Tortoise Amulet | Defense | 10 | 50 |
| 6 | Huang's Bow | Bow Attack | 10 | 50 |
| 7 | Shell Armor | Bow Defense | 10 | 50 |
| 8 | Horned Helm | Mounted Attack | 10 | 50 |
| 9 | Cavalry Armor | Mounted Defense | 10 | 50 |
| 10 | Seven Star Orb | Luck | 5 | 25 |
| 11 | Wind Scroll | Reach | 5 | 25 |
| 12 | Elixir | Musou Charge | 5 | 25 |
| 25 | Mountain Quiver | Starting Arrows | 8 | 40 |
| 26 | Mountain Pouch | Meat Bun Recovery | 5 | 25 |
| 27 | Bronze Flask | Charge | 3 | 15 |

These exceed the original game's commonly quoted four-tier rolls. Remastered
normal generation `0x15363D0..0x1536588` computes
`tier * ValueRand + randomInteger(1, ValueRand)`. The normal branch uses five
thresholds; weapon attributes use a different branch. Shipped
DT_DropRandomTable ranks 13–15 select tier 4. Scenario initialization
`0x1567EC0` combines Remastered base difficulty 7 with VeryHard correction
6, giving reachable rank 13. Native BattleSettings constructor `0x12AA0C0`
supplies +6; cooked DA_GameParameterDataAsset omits that property, retaining
the default. Ordinary pickup `0x1375DB7` passes this rank with the normal flag.
Thus a legitimate normal maximum is **5 × ValueRand**.

| Rare IDs | Item names, in index order |
|---|---|
| 13–18 | Red Hare Saddle, Hex Mark Saddle, Imperial Saddle, The Art of War, Bodyguard Manual, The Way of Musou |
| 19–24 | Survival Guide, Defender, Fire Arrows, Buckler, Power Scroll, Gold Harness |
| 28–33 | Divine Helm, Scroll of Accuracy, Imperial Harness, Seven Stars Blade, Lightning Bow, Seal of Darkness |
| 34–39 | Beast Harness, Marching Drum, Divine Gauntlet, Master's Cloak, Legendary Scroll, Musou Armor |
| 40–42 | Six Secret Teachings, Guardian Secrets, Red Hare Saddle (Retro) |

## Weapons and collection cache

WeaponSaveData has `WeaponID` and `ID` enum strings, `Skill` (nine tagged
EquipItemSaveData records), `Attr` (Int64 bitmask), `DataID` (Int32), and
`GetTime` (Double). Unique stock attributes and skill slots come from shipped
WeaponBaseData, UniqueWeaponData and WeaponRankData tables.

Builder `0x1516040..0x1516265`, insertion `0x150AC10..0x150AFE9` and
initializer `0x1502E20` establish:

| Unique weapon IDs | Shipped template index | Unique save index |
|---|---|---|
| 89–129 (4th weapons) | weapon ID −89 | weapon ID −89 (0–40) |
| 132–172 (5th weapons) | weapon ID −91 | weapon ID −89 (43–83) |
| 191–192 (Ziluan) | 82–83 | 102–103 |

In the supplied save, unique DataID = **10000 + unique save index**. A second
CollectedWeaponDataArray record is indexed by the **weapon ID**, with DataID
= weapon ID. Acquisition updates both inventory and collection cache using
the stock template. Existing owned/fused records and timestamps are preserved.
[unique_weapons.json](unique_weapons.json) lists each officer, ID, name,
exact bitmask, skill values and mappings.

The original 84-record UniqueWeaponDataArray contains slots for 82 unique
weapons at 0–40 and 43–83. Slots 41/42 remain blank placeholders. Ziluan's
slots 102/103 require at least 103/104 records respectively. The writer
reproduces native insertion by padding missing slots with constructor-style
NUM identities, zero skills/attributes/time and indexed DataIDs, then acquiring
only the requested weapon. Existing rows, fused properties and timestamps
remain unchanged. All 84 unique definitions are supported.

Ordinary/fused weapon data supports verified normal bonus editing. Fusion
copies material ID/value directly; rank limits are 6/6/6/7/8 normal bonuses.
Exact donor value sets,
per-weapon stock exceptions, preserved rare slots and inventory/cache
dependencies are documented in [WEAPON_ROLLS.md](WEAPON_ROLLS.md).
Rare bonuses and single elements are now editable under the verified rules
in [WEAPON_ATTRIBUTES_FIX.md](WEAPON_ATTRIBUTES_FIX.md). Material consumption
and fusion achievements remain unsupported.

## Bodyguards

The original sample has four GuardDataArray teams; a second supplied save has two.
The record count is variable, and the editor preserves the actual saved teams. SPoint is Int32 Merit (first team's sample
offset 3317075); BGLevels is an Int32 array of six entries. Native team stride
`0x58`/SPoint offset `0x50` establish identity, not disk offsets. Battle writes
`0x1518977..0x1518986` and normalization `0x1508EA7`/`0x1508EB1` cap Merit
at **99,999**.

The final shipped DT_BGTotalLevelPoint row provides **25 allocation points**
at ServicePoint 99,999. There is no 25,000-Merit cap. Getter `0x145E6B0`
and allocation code `0x1506262..0x1506275` use the threshold table. BGLevels
indices 0,1,2,4 share the budget; count and AI progression use separate
thresholds. Summing all six levels is not a valid allocation-budget formula.

v0.2 supports legal final Merit and growth combinations. BGLevels 0/1/2
have caps 11, index 4 has cap 3; only indices 0/1/2/4 consume the budget.
Count (index 3) and Bow/Moveset (4) require 25,000/50,000/75,000 Merit for
ranks 1/2/3; AI (5) requires 30,000/60,000/90,000. Growth actions synchronize
Count/AI to earned ranks, validate the final budget and update associated
playable officers' selected MemCnt only when it equalled the previous maximum
or exceeds a reduced maximum. Smaller selected counts remain unchanged.

The Balanced maximum-Merit allocation is `[8,7,7,3,3,3]`, spending 25 points,
with growth-base Life/Musou 260 and Attack/Defense 110. Individual allocated
maxima cannot all fit in the budget. Favor Life/Attack/Defense presets are
other legal allocations. Growth previews exclude equipment, bodyguard type,
orders, battle modifiers and converted Unreal movement units.

GuardEquipItemDataArray has ten indexed records: nine normal rolls with
caps `[40,40,25,25,15,15,15,15,15]`, and rare BG Healing Scroll ownership
with Value zero. Ownership uses GuardEquipItemID; EquipItemID stays NUM.
Normal generation `0x15175D0..0x15176F0` uses the reachable five-tier formula
`tier*ValueRand+randomInteger(1,ValueRand)`. MemberItem must reference an owned
item; removal is refused while a team or officer BGMusouEquipItem references it.

GuardWeaponDataArray has 100 records and definitions 173–187: three tiers in
each of Sword/Spear/Pike/Bow/Crossbow. Acquisition adds missing definitions
to first NUM slots and sets DataID to inventory index. Attr is zero for
native guard drops. Collection cache at the weapon-ID index is populated only
on first ownership, with DataID = weapon ID, then preserved. MemberWeapon's
first five Int32 entries are inventory-slot references for those families;
its remaining five entries are preserved. Full pools are refused, not expanded.

Weapons allow at most three distinct normal GuardEquipItemID bonuses.
Melee excludes Bow Attack; ranged excludes Attack and Reach; rare Healing
Scroll is excluded. Tier-1 Life/Musou rolls are `{1,5,10,15}`, Attack/Defense
`{1,5}`, others `{1}`. Tier-2/3 rolls are Life/Musou `{1,5,10,15,20,25,30}`,
Attack/Defense `{1,5,10,15,20}`, others `{1,5,10}`. These are conservative
native-drop bounds; guard fusion is not assumed. Explicit max actions replace
bonuses with legal melee Life/Attack/Defense or ranged Life/Defense/Bow Attack
profiles while preserving weapon identities, references, Attr and timestamps.

Detailed fields, IDs, tables, formulas, native RVAs and user controls are in
[BODYGUARDS.md](BODYGUARDS.md), [bodyguard_growth.json](bodyguard_growth.json),
[bodyguard_items.json](bodyguard_items.json),
[bodyguard_weapons.json](bodyguard_weapons.json) and
[BODYGUARD_WEAPONS.md](BODYGUARD_WEAPONS.md). Team names, appearance/type,
unmapped extra equipment references and story completion remain unchanged.

## Availability and story completion

CanUseCharaArray supports playable officers 0–41; 42–49 are placeholders.
CanUseScenarioArray has 156 booleans, but only **0–107** are playable shipped
ScenarioSettingData rows. Indices 108–149 are empty placeholders, 150 is
DEBUG_DUMMY, 151/152 are action-test maps, and 153–155 are promotional PV rows.
They are excluded from stage editing/unlock actions.

Availability edits are separate from EngiClearCharaArray, ClearScenarioArray
and EngiSaveDataArray. Stat/item/weapon/Merit presets preserve story/Musou
completion. Explicit Musou clear actions update the completion flag and route
Progress for the 39 supported officers, with three Huanglong Elixirs per first
clear unless an explicit final Elixir balance is supplied. They preserve active
runs, battle records and timestamps. Title/rank fields and DLC permissions remain
unchanged. Side-story actions enable the three rulers' side campaigns and their
six Free Mode variants without marking those stages completed.

## Huanglong Elixirs

`BeansNum` is a top-level `IntProperty` with a four-byte signed little-endian
payload; its sample offset is 3333919. The editor exposes it as
`Change('progression', 0, 'HuanglongElixirs', value)`, independently of officer
stats and item values.

Edits require an ordinary scalar tag (`flags == 0`, `array_index == 0`), a
payload matching its parsed integer, and a saved balance within 0–999. New
values must have exact integer type and be within that same range; booleans,
floats, strings, negative numbers and values over 999 are rejected. Missing or
unfamiliar counter layouts remain view-only. No counter offset is hard-coded.

Without an explicit balance, newly cleared Musou routes award three Elixirs
each, capped at 999. Repeating an already-cleared route awards nothing. An
explicit balance is the final total even when the same batch clears stories:
setting 10 and clearing a route writes 10, rather than 13. The writer produces
one counter patch, regardless of request order. A counter-only edit changes
just these four payload bytes and their corresponding encrypted blocks; story
flags and unrelated fields remain unchanged. Applying the saved balance with
no other edits produces byte-identical output.

## Safe writes and validation boundaries

The writer verifies the source document, refuses unsupported fields/indices,
plans nonoverlapping patches and preserves unedited bytes. Enum acquisition
rewrites the FString count/content, regenerates every containing property's
payload size, updates the big-endian envelope length and pads to the new
16-byte boundary. It reparses encrypted output before writing.

Fixed-length edits are checked against expected changed AES blocks. Officer
0 Merit 99,999 →99,998 changes one plaintext byte at 2559 and ciphertext block
159. String resizing shifts later offsets and can change many subsequent
ECB blocks; this is expected. Unchanged structured regions are compared at
their newly parsed positions. Change reports record reasons, original/output
hashes, byte patches, lengths and changed ciphertext blocks.
The audit report is published before the save commit, avoiding a report-write
failure after the source copy has already been replaced.

Automated tests cover byte-identical unchanged output, targeted Merit edits,
verified officer/item maxima, rare acquisition, unique stock templates/cache,
preserving completion/placeholders/unedited regions, backups/restore, stale sources,
malformed versions and forbidden live/cloud paths. Backups contain original
ciphertext plus a hash/size manifest. Temporary output is verified and safely
committed. Replacing an opened copy requires explicit overwrite and a backup;
restore refuses existing destinations and mismatching manifests.
The game live-save tree, Steam userdata/remote locations and Steam Cloud
metadata are refused. Editing is performed on separately selected copies.

Confidence is high for the codec, supported layout, mapped fields, native
caps and template mappings.
Unknown/unsupported areas include material-consuming fusion, new combined elements, nontransferable rare weapon donors, bodyguard appearance/type changes,
officer title/rank edits, detailed meanings of
preserved opaque fields and other builds/platforms. Unknown regions are not
assigned invented offsets or values.

## Evidence confidence by finding

| Finding | Confidence and basis | Editing status |
|---|---|---|
| AES key/mode, envelope, padding | High: shipped configuration, decoded GVAS, exact ciphertext round trip and NIST vector | Implemented |
| Version/header/property sizes | High for the inspected layout: full bounded parse and size regeneration | Other layouts refused |
| Officer identity/Merit/permanent stats | High: native enum, parsed fields and actual getter/write clamp paths | Implemented for 42 officers |
| Officer Progress/title/rank fields | Native Musou route lengths mapped; safe title/rank transitions incomplete | Progress updated by explicit clear actions; title/rank preserved |
| Normal-item IDs/ownership/values/caps | High: shipped enums/tables, pickup and normal drop-generation dataflow | Implemented for 16 normal items |
| Rare-item ownership | High: shipped IDs and indexed equipment records | Implemented for 27 rare items |
| Weapon ownership/4th/5th stock properties/cache | High for 84 entries: native acquisition mapping and shipped templates | Implemented; owned entries preserved |
| Ziluan unique slots and expansion | High: native insertion pads through slots 102/103; confirmed 104-row reported save | Implemented native padding and indexed acquisition |
| Playable weapon collection/Tactics costumes | High: native 176-definition collection predicate and two-officer costume setter | Gallery completion and separate Lu Bu/Sun Shangxiang costume flags implemented |
| MUSIC gallery availability | High: native 42-entry constructor, unchanged ID list population and direct bPlayBGM[id] reads | IDs 0–41 implemented; old acknowledgement flags and all later slots preserved |
| Officer weapon normal fusion outcomes | High: native direct-copy path, exact donor value sets, rank limits and stock exceptions | Per-copy bonus editing/max; material workflow remains unsupported |
| Bodyguard Merit/growth/count/AI | High: native 99,999 clamp, shipped level/gate/budget tables and associated officer count dataflow | Legal final allocations and presets implemented |
| Bodyguard normal/rare items | High: shipped IDs/roll tables and actual generation/acquisition/equipment paths | Nine normal caps, one rare ownership and team equipment implemented |
| Bodyguard weapon ownership/bonuses/equipment | High for native drops: 15 definitions, family/tier limits, allocator/cache and slot references | Acquisition, legal max profiles and first-five equipment implemented |
| Bodyguard model/type/extra references/fusion | Safe transition rules incomplete or unverified | Preserved or refused |
| Officer/stage availability | High: boolean arrays, native IDs and shipped 108 playable scenario rows | Implemented separately |
| Musou completion/progression | High: 39 native routes, completion flags/progress and first-clear award dataflow | Separate explicit clears; active runs and battle records preserved |
| Side-story availability | High: native three-story IDs, optional BoolProperty arrays and six Free Mode mappings | Separate unlock actions; completion preserved |
| Huanglong Elixir balance | High: BeansNum Int32 scalar, native 0–999 clamp and first-clear award | Explicit typed final balance; one combined counter patch |
| Custom checksum/compression/signature | None found in inspected save paths; exact round trip verified | No invented integrity algorithm |
| Unknown/opaque fields and other platforms | Outside the identified save contract | Preserved or refused |

## v0.3.1 review corrections

Nested property payloads must fit both the enclosing record and the physical
buffer. Truncated primitive reads become validation errors. New ordinary item
edits enforce indexed ownership, zero values on removal/rare acquisition and
verified normal rolls. Unchanged historical values and reserved slots remain
preserved, with compatibility notes where their profiles are unfamiliar.

Reserved native officer weapon bonus IDs can be viewed and round-tripped,
but their weapon copies are read-only. Repeating an unlock action preserves an
existing owned unique copy, including its references, bonuses and timestamp.

Overwrite commits recheck the destination against the exact backed-up bytes
after serialization and temporary-file verification. New destinations use
no-overwrite publication even when a caller requested overwrite. This is an
optimistic concurrency check, not a filesystem-wide lock against every possible
concurrent rename. Keep other save editors closed while replacing a copy.

Backup manifest reads are bounded, schema-checked and path-checked; failed
manifest creation removes only the new incomplete backup. Resolved aliases of
Steam Cloud metadata, Windows device names and alternate streams are refused.

## v0.3.2 compatibility corrections

GuardDataArray cardinality is not fixed at four. Require the exact supported
GuardSaveData struct-array type, complete records and count consistency.
Every team receives structural validation; unfamiliar saved growth/equipment
profiles are preserved while newly authored changes remain strict. Edits to
absent indexes are refused. Existing positive distinct normal bodyguard weapon
bonuses outside the verified drop profiles are read-only and preserved.
Authored bonuses retain strict original generation limits. See
[COMPATIBILITY_FIX.md](COMPATIBILITY_FIX.md) for evidence and limitations.

## v0.3.3 officer weapon rare bonuses and elements

Rare skills use the existing nine-slot Skill array. Verified transferable
IDs are 13–24 and 28–39, with Int32 Value zero and at most one rare bonus.
Explicit rare edits normalize it to final slot 8; numeric-only edits retain
earlier saved positions. Attr is Int64: element bits are Fire 4, Lightning 8,
Steel 16 and Wind 32, with mask 0x3c. Element additions/replacements preserve
every other bit, including hit and unique flags. Newly authored combined
elements and removal of existing rare bonuses/elements are disabled.

Variable-length enum relocations can cancel in total size. The writer uses
complete plaintext differences to verify the expected encrypted block set
for an equal-size result, rather than assuming field offsets remain stable.
The audit adds fields_relocated; total-size resized remains separate.

Confidence is high for the supported native transfer outcomes and storage.
See [WEAPON_ATTRIBUTES_FIX.md](WEAPON_ATTRIBUTES_FIX.md) for evidence RVAs,
limits, authoring policy and preserved dependencies.
