# Hyrule and Fire Emblem mechanic depth

This review covers the existing Wii U Hyrule Warriors, Switch Definitive
Edition, 3DS Legends, Switch Age of Calamity, Switch Fire Emblem Warriors,
Switch Three Hopes and Switch Three Houses adapters. The new writable systems
are qualified Three Houses motivation and existing ability loadouts, and
owned Legends fairy trust reductions. The other games retain their existing
qualified editing scope while their deeper mechanic blockers are recorded
below. No new platform, revision, console import or edited game-load claim is
made.

## Implemented additions

| Game / system | Stored field and admission | Behavior and dependencies |
| --- | --- | --- |
| Three Houses instruction motivation | u8 character `+0xC4`, both admitted revisions 13 and 23. Original native owner ID 2–34, unique, positive level, Available/Has Joined flags set, Is Dead clear; original motivation must be 0, 25, 50, 75 or 100. Byleth IDs 0/1 are excluded. | Named choices offer precisely those five instruction levels. The normal maximum is independently documented as 100, with 25 consumed per attempt. Editing does not perform instruction or write proficiency EXP, budding talent progress, supports, professor EXP or remaining lesson activity. No Max is supplied for these choices. Unknown/higher/unusual originals stay read-only. |
| Three Houses existing equipped abilities | Five u8 equipped IDs at character `+0x7F..+0x83`; learned bitmap is 30 bytes at `+0x61..+0x7E`, native empty sentinel 240. Original unique living joined base-unit owner required. Deployment flag bit 18 must be clear. Nonempty original IDs must be below 240, distinct, and each original ownership bit `ID//8`, `1 << (ID%8)` must be set. | Each slot offers only the IDs already equipped in this opened character, plus Empty. Labels identify the opened slot of origin. Clear an old slot before moving its ability, or supply a complete valid batch. Duplicate nonempty IDs in the resulting loadout are rejected. Pending edits cannot admit another ability. Learned bits, current class, personal/class-derived abilities, proficiency/mastery and rewards never change. An empty/default, unknown, duplicate, unlearned or deployed original loadout is withheld. These are existing loadout adjustments, not arbitrary learned-ability grants. |
| Legends owned My Fairy trust | u8 fairy `+0x24`; 14 physical records at `0x1AEA`, stride `0x98`. Exact original ownership byte 1, original level `+0x1B` in 1–99 and trust in 1–100 required. | Decrease to 1..opened trust only; no increase or Max. Trust affects potency of already-existing fairy skills. Personality traits, skills, element, clothing, level, refresh count `+0x6C` and all neighboring bytes stay unchanged. The published editor's trust ceiling is an admission bound, not a newly asserted natural Max. Unusual ownership/level/trust values remain read-only and byte-exact. No feeding, refresh, skill learning or reward action is simulated. |

Every eligibility decision uses the immutable opened snapshot. All pending
edits are validated before staging another change, review, bulk actions and
serialization. Three Houses checks its native payload checksum before exposing
fields and recomputes it only after a qualified change. Legends preserves the
raw exported profile without inventing an aggregate checksum. Assigning an
opened value unstages its edit, and unknown bytes retain their original values.
The common Review Changes, Undo, backup, new-destination Save As and restore
workflows remain in use.

## Evidence and implementation independence

Three Houses record widths, flags, direct motivation setter, learned bit order,
equipped byte positions and empty sentinel are factual observations from:

- [imouto1994/fe3h-editor, historical revision](https://github.com/imouto1994/fe3h-editor/tree/5e4a73b71f28feb271ccdbc614ea934517c235b5),
  specifically `Structs/Character.cs`, `Enums.cs`, `Util.cs` and `Database.cs`.
- [hashcade/feth-save-editor, historical revision](https://github.com/hashcade/feth-save-editor/tree/b9f53f0e01a3dd2cd24c96f97f1a829e51a1f00d),
  independently corroborating the admitted later stride and the unchanged
  motivation/ability prefixes.
- [Fire Emblem Wiki: Lessons / Instruction](https://fireemblemwiki.org/wiki/Lesson#Instruction),
  documenting the natural motivation cap, 25-point steps, Byleth exception,
  instruction costs and separate support/skill rewards.
- [Fire Emblem Wiki: Ability](https://fireemblemwiki.org/wiki/Ability),
  distinguishing personal, current-class and equipped standard abilities.

The historical editor implementations have no located licence. Their code,
extracted game databases, names, icons and catalogues are not copied. The
Python gates, staged validation and tests are independently written. Ability
options reference the opened loadout rather than importing an unlicensed
ability catalogue. The numeric Byleth pair and main-character association are
also cross-checked against the public later
[class-eligibility implementation](https://github.com/jinghaihan/feth-save-editor/blob/main/core/ClassEligibility.cs);
its game database is neither shipped nor used as runtime evidence.

Legends trust positions and independent scalar writing are reviewed from
[nedron92/HWL-SaveEditor](https://github.com/nedron92/HWL-SaveEditor/blob/4259e42b4ee6d643859fc218e436c20c337cb358/source/core/HWLFairy.cpp),
which separately writes trust, level, refreshes, name and ownership. No licence
was located, so no implementation or catalogue is reused.
[Zelda Wiki: My Fairy](https://zeldawiki.wiki/wiki/My_Fairy) separately describes
personality and level skill requirements and the existing Health Regain,
Special Regain and Magic Regain effects scaling with trust. A trust reduction
does not claim to earn a skill or cross a new growth/reward threshold.

## Per-game mechanics reviewed and exact remaining blockers

| Existing adapter | Reviewed mechanics / useful distinction | Exact additional write evidence still missing |
| --- | --- | --- |
| Wii U Hyrule Warriors | Character level/EXP, ordinary base power, star-derived attack, ordinary versus Legendary/Evil's Bane seals, badges, combos, materials, map cards and collection/story rewards. The MIT source computes ordinary star-adjusted attack from stored base power; Legendary state plus an unsealed skill can override the base, and Evil's Bane can add a separate bonus. | Level/EXP curve, synchronized growth/stat/heart awards and roster ownership; badge node identities/prerequisite/cost state; legitimate per-tier base-power generation values and Legendary collection dependencies; fusion cost/transfer/equipped-reference updates. A decrease bound alone would admit impossible tier power, so no base-power reduction control is added. No Wii U My Fairy system is inferred from later editions. |
| Switch Hyrule Warriors Definitive Edition | Character/weapon records, fairy food, ordinary/sealed/Legendary weapons, all nine Adventure maps and My Fairy growth/refresh/skills/clothing. Dedicated Switch source supplies a candidate Adventure-map item base but an offset declaration alone does not establish the full card width/identity/count or all map exceptions. | Verified Switch fairy record boundaries and feed/trust/refresh/equip transitions; direct owned-fairy identity/level/trust mapping separate from 3DS; safe badge/growth rewards; per-map card records with discovery/search/reward dependencies; synchronized fusion/skill-capacity/per-tier base-power rules. The 3DS fairy base is not transplanted. |
| 3DS Hyrule Warriors Legends | New original-owned fairy trust reductions, prior fairy names/map cards, personality growth, food unlocks, refreshes and skill effects. Feeding can increase several traits and decrease others; refresh resets level and allows a trait/name choice. | Trait byte identities and coupled feed changes; skill threshold/reward bytes; refresh-induced trait growth/level reset/history synchronization; clothing/element/equipped references and ownership; character growth/badge rewards. Trust cannot be increased from this original snapshot and is excluded from Max. Source refresh ceiling 999 is not used as a gameplay cap. |
| Switch Age of Calamity | Weapon fusion EXP/level, two saved power terms, quality, level-cap codes, six seal IDs/parameter pairs, hidden seals, protection and rusty polishing; character growth, blacksmith/upgrades, quests/cooking/DLC laboratories and material/reward inventory. Existing protection remains a separate safe fusion-selection choice. | Weapon-type EXP curves, synchronized level/power terms and quest-gated 20/25/30/50 cap codes; seal units/default parameter pairs and hidden-seal dependencies; rusty-to-result mapping; natural quality/power ranges; fusion material/cost/consumption and character ownership/growth rewards. Published raw setters and source storage targets cannot prove these. Korok Seeds, Terrako Components and Ethereal Stones keep their collection/reward gates. |
| Switch Fire Emblem Warriors | Ordinary versus personal/amiibo weapon quality, innate Slayer mask, transferable attributes, KO seals, badge promotion, scroll/opus/essence rewards, class/promotion, growth and supports. Some transferable attributes require matching innate properties and ordinary nonpersonal weapons; simply clearing or granting a Slayer bit can invalidate those prerequisites. | Named innate-property/transfer rules and synchronized attribute damage/effects; promotion/growth curve and stats; badge/prerequisite/cost nodes; personal-weapon scroll/opus unlock and unique power tiers; support point/rank/reward pairs and original recruited character ownership. No raw Slayer-bit control, universal power Max or character unlock is added. |
| Switch Fire Emblem Warriors: Three Hopes | 136 character profiles, classes/arts/skills, recruitment/deployment, forging might/durability bonuses and current/max forge-step bytes, personal/rusted weapons, accessories/material categories, battalions, bonds/camp/training/facilities and renown/NG+. Forging steps are distinct from saved added might/durability; changing one alone is not a verified forge. | Per-weapon smithy/material costs, maximum/current forge dependencies and natural stat terms; learned/equipped ability/arts ownership and class requirements; facility upgrade/acquisition gates; support thresholds/conversation/reward state; recruitment starter profile/equipment and battalion capacity/dismissal/reward handling. Renown is not a free character-unlock switch. The MIT template's enum/record layout alone does not qualify arbitrary progression writes. |
| Switch Fire Emblem: Three Houses | New instruction motivation and original ability loadout controls; certification versus class mastery/reward mirrors, weapon/magic/movement proficiencies, budding talents, battalion endurance/EXP, held versus convoy equipment, professor activity/rank, support points versus conversations/ending and main-campaign versus DLC/side-story context. | Unit/class/stat-cap/reward synchronization; certification availability and class-derived floors/modifiers; proficiency/rank/learned-spell/talent mirrors; mastery reward bits; full standard-ability/class restrictions before adding unequipped learned abilities; battalion ownership/type/endurance bounds and equipped/storage copies; support pair/rank/chapter/history/ending gates; per-item repair maxima and transactions. Original loadout reuse does not supply those missing mappings. |

Additional public format and mechanic evidence reviewed:

- [MIT Wii U / AoC save sources](https://github.com/MarcRobledo/savegame-editors/tree/b4db8cd11157c6d5ae54a0a5edc88dba82aebe9d),
  especially Wii U `_calculateWeaponPower` and AoC notes; the existing factual
  tables retain applicable MIT notices.
- [MIT AoC 1.3.0 source](https://github.com/BtEtta/save-editors/tree/b77b1ac19d26f083365106ce8e8ed1ef32a23ba6/aoc),
  distinguishing protection, native revisions, EXP limits, cap codes and saved
  power/seal terms.
- [Dedicated Switch Hyrule editor](https://github.com/iAroc/iAroc.github.io/tree/15e4a928bdffb202a7893e14fde432f2dcbc10b3/hyruleWarriors),
  `Offsets.js`, `Items.js`, weapon getters/writers; no located project licence,
  so its code/catalogues/assets are not copied.
- [Wii U Legendary prerequisites](https://gamefaqs.gamespot.com/wii-u/745183-hyrule-warriors/faqs/72769/leg-skills)
  and [Hyrule weapon mechanics](https://www.zeldadungeon.net/wiki/Hyrule_Warriors_Weapons).
- [FE Warriors weapon attributes](https://fireemblemwiki.org/wiki/Weapon_attribute)
  and [generic/personal weapon list](https://fireemblemwiki.org/wiki/List_of_weapons_in_Fire_Emblem_Warriors),
  alongside the prior save-specific
  [Switch editor discussion](https://gbatemp.net/threads/fire-emblem-warriors-save-editor.505591/).
- [MIT Three Hopes save template](https://github.com/async-amethyst/few2-010-binary-templates/tree/9b6e9946e5a33e182f80fbe3553e7c2afbebbdcb),
  especially `FEW2Save.bt`'s separate increased-stat and current/max forge terms.
  The existing factual tables retain its MIT notice. Separate game-asset
  templates are not treated as save layouts.
- [Three Houses class mechanics](https://serenesforest.net/three-houses/classes/),
  [class mastery](https://fireemblemwiki.org/wiki/Class_mastery),
  [supports](https://fireemblemwiki.org/wiki/Support) and
  [Nintendo update history](https://en-americas-support.nintendo.com/app/answers/detail/a_id/46816/~/how-to-update-fire-emblem%3A-three-houses).

These sources can establish mechanics and storage facts without establishing
an edited file's successful game load. The source-specific profile/integrity
checks in the existing adapters remain unchanged. No game binary or third-party
editor binary was executed; no player save, private provenance, account data or
restricted catalogue is included in the public source.

## Validation

`tests.test_hyrule_fire_emblem_depth` adds 15 focused tests. Public procedural
checks cover all five motivation choices, both native layouts, Byleth/dead/
duplicate/unjoined/unusual ownership gates, original learned/loadout agreement,
undeployed admission, final duplicate rejection, multi-edit atomicity,
unchanged serialization and native checksum rejection. Trust checks qualify
ownership/level/trust, reject increases/zero/invalid values, preserve growth/
refresh/skill/unknown neighbors and exclude Max. Six real Tk/Xvfb workflows
cover named choices or trust controls, Apply, Review, Undo, theme, backup,
new-copy Save As and byte-exact restore, on both procedural and copied native
inputs for each new system.

Optional private native checks use the existing `THREE_HOUSES_REVIEW_COPIES`
and `HYRULE_LEGENDS_COPY` variables. Eight admitted Three Houses exports span
both revisions; every exposed new field is independently edited, reparsed,
checked against the declared byte range plus four checksum bytes, and its
original source remains unchanged. Both new systems are exercised on both
revisions. The admitted Legends export exposes trust controls that pass
individual one-byte edits and immutable-original checks.

The new module plus the existing Three Houses format/audit and Legends
format/audit/GUI modules pass **66/66 with no skips** using those private
fixtures and real Tk/Xvfb. The full seven-game regression runs 145 checks:
144 pass and one optional six-export Three Hopes control initially skips.
Supplying its six separately reviewed native files then executes that check
successfully as well. Without the optional files/display, the corresponding
checks explicitly skip. Procedural checks, native-file qualification and GUI
workflows remain distinct from actual console import/game-load/re-save testing,
which has not been performed.
