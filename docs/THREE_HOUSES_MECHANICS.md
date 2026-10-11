# Fire Emblem: Three Houses — mechanics and dependency evidence

Reviewed against public documentation on 2026-10-11. Scope is
the Nintendo Switch tactical RPG **Fire Emblem: Three Houses**. None of the
Three Hopes or Fire Emblem Warriors mechanics below are used as evidence.
This document establishes gameplay distinctions, not save offsets or native
revision qualification. No third-party code, extracted tables, assets, or saves
are incorporated.

## Systems that an editor must keep separate

| System | Gameplay facts | Required editing distinction |
| --- | --- | --- |
| Character level and EXP | Level does not reset on certification/reclass. Three Houses uses level-dependent EXP requirements rather than a universal 100 EXP bar. Playable units have a reported level cap of 99. [1][2][3] | Level, current EXP, growth-derived stats, current HP, and maximum HP are different values. A storage ceiling is not an EXP cap. Do not claim that raising EXP performs level-up processing or growth rolls. |
| Character stats | Core displayed stats are HP, Strength, Magic, Dexterity, Speed, Luck, Defence, Resistance, and Charm. Character caps vary; some HP caps exceed 99. Class base-stat floors on certification and temporary class modifiers are distinct. [1][4][5] | Determine whether a byte represents permanent/base or effective/displayed stats. Preserve pre-existing values and modifiers rather than subtracting an assumed class bonus. |
| Stat-cap prerequisites | Saint-statue rewards can raise paired non-HP stat caps by 5: Strength/Speed, Luck/Charm, Magic/Dexterity, and Defence/Resistance. [6] | Do not expose a universal “Max stats” action from published character caps alone. Prove the cap-increasing reward state and how the serialized stat corresponds to the displayed stat before enabling Max. |
| Weapon/magic/movement skill levels | There are eleven skill subjects: Sword, Lance, Axe, Bow, Brawling, Reason, Faith, Authority, Heavy Armour, Riding, and Flying. Rank progression runs E, E+, D, D+, C, C+, B, B+, A, A+, S, S+. Skill EXP is independent of unit EXP and class EXP. Increasing rank can affect weapon use, abilities, combat arts, spells, or certification. [7][8] | The Heavy Armour/Riding/Flying subjects are proficiencies, not the character's movement stat. Character strengths/weaknesses affect training gains; changing EXP is not automatically changing those talents. Rank/EXP and learned/equipped rewards must be mapped separately. |
| Budding talents | Repeated instruction in a character-specific subject unlocks a talent, changes its training aptitude, and awards a character-specific ability or combat art. [9] | A high rank alone does not prove the budding-talent unlock, its star/instruction progress, or the awarded ability record. |
| Class certification and mastery | Certification grants access to a class; class mastery accumulates a separate per-class EXP value and awards abilities/arts. Reclass selects an already accessible class. [1][10] | Class availability, current class, per-class mastery EXP, mastered-state/rewards, and New Game+ historical mastery are separate concepts. Do not grant access to an unqualified class merely by editing mastery. |
| Abilities | Each unit has one fixed personal ability, up to three current-class abilities, and up to five equipped standard abilities. Standard abilities come from skill levels, talents, or class mastery. Higher Prowess versions replace weaker versions in normal progression. [8][11] | Learned ownership and equipped slots are different. Preserve personal/class-derived abilities. Equipping an arbitrary internal ID does not prove that the unit owns or can use that ability. |
| Combat arts | Up to three learned arts can be equipped. Arts require the corresponding weapon type and consume durability. Some advanced/special/master/unique class mastery arts require the matching current class; relic-specific arts require their corresponding weapon and crest-related conditions. [10][12][13] | Learned ownership, equipped arts, weapon compatibility, class restriction, crest effect, and durability cost are separate. Do not advertise all learned arts as usable in all classes. |
| Spells | Reason/Faith progression unlocks character-specific spell lists; spell use depends on a magic-capable class. [1][8] | Magic is not an inventory of generic tomes. Learned spells and per-battle uses are distinct from physical weapon durability. |
| Battalions | Battalion instances have their own level/EXP and endurance; levels run 1–5. Equipping requires sufficient Authority; flying units can equip only flying battalions. Endurance can fall to zero without deleting ownership, and must be replenished at the battalion guild. Gambit uses refresh after battle. [14][15] | Battalion catalog/type, owned instance, unit assignment, instance EXP, current/max endurance, derived bonuses, and current gambit uses must not be conflated. Low endurance intentionally activates some battalion abilities; blanket healing changes those setups. |
| Existing equipment durability | Ordinary weapons can reach a broken state at zero durability rather than disappearing. Combat arts consume additional durability. Repair/forge requires the blacksmith, materials, gold, and sometimes professor rank; the blacksmith unlock quest is in Chapter 5. [12][16] | Repair edits must target proven existing item instances. Their type, forge variant, uses, equipped reference, and storage location are separate. An item-specific maximum uses value is needed; 99/255 is not a natural cap. Accessories and materials are not durability-bearing weapons merely because they share storage records. |
| Inventories | Unit inventory capacity is six items. The convoy and unit inventories are separate; the convoy groups otherwise identical items, including remaining durability. [17][18] | A stack/quantity, repeated weapon instances, unit ownership, equipped slot, and convoy location require independent mapping. Do not invent a weapon, duplicate a relic/reward, or move an instance by editing a quantity byte. |
| Gold, Renown, professor progression | Gold and Renown are different resources. Renown purchases statue upgrades and, in New Game+, previously earned professor/support/skill/mastery progress. Professor rank runs E–A+ and determines instruction/exploration/battle resources, adjutant slots, forge access and master-class access. [6][13][19] | Current currency, historical purchases, clear-history bonuses, professor EXP/rank, and today's remaining activity points are different. A documented 50,000 bonus Renown threshold is a revision-specific clear-bonus rule, not a cap on spendable Renown. [20] |
| Supports | Pairs differ in available ranks/conversations; + ranks occur, and only Byleth can select an S support at the end of the game. Conversation availability can depend on chapter, route, time windows, and both characters. Anna has no supports. [20][21][22] | Pair identity, accumulated points, attained/conversation state, gallery history, recruitment easing, and ending selection are separate. Raising points must not be sold as unlocking a conversation, recruiting a unit, or choosing a paired ending. |

## Concrete prerequisites

Certification normally requires unit level 5/10/20/30 for beginner/intermediate/
advanced/master classes, the corresponding seal, sufficient exam success
probability, and professor rank C for master classes. Dark Mage and Dark Bishop
use Dark Seals; Dark Bishop requires Dark Mage certification. Certain classes
are limited by gender or character. Dancer and the story-specific classes are
event awards rather than unrestricted ordinary certification. [1]

Expansion special classes require level 20 and an Abyssian Exam Pass. Trickster
also requires Thief certification; Dark Flier and Valkyrie are female-only;
War Monk/War Cleric correspond to the male/female class variants. Their access
requires the relevant expansion progress, independently of a stored mastery
value. [1][10]

Published mastery requirements are 20 for Noble/Commoner, 60 for beginner, 100
for intermediate, 150 for advanced/special and certain unique classes, and 200
for master and certain unique classes. Mastery gain can be modified by the
Cethleann statue reward, Knowledge Gem, and Mastermind. These are gameplay
thresholds, not evidence of the save's stored counter representation. [10]

Support-point gain pauses at conversations that have not been viewed. Some
conversations become available only later, some expire, and some depend on a
specific route. New Game+ support purchases depend on inherited progress rather
than simply on the global Support Log. [13][21] This rules out a generic “set
all support ranks to S” action.

Recruitment has its own requirements and route restrictions. Support with
Byleth can ease recruitment requirements, but a stat/support edit must not
toggle unit ownership or make an NPC/enemy record a recruited character. A
record existing in a save is not enough evidence that it is an owned playable
unit. [21]

## Revision and expansion scope

Nintendo's official update history lists 1.0.1, 1.0.2, 1.1.0, and 1.2.0; it does
not establish the internal save-revision bytes used by any particular export.
Never infer installed DLC entitlement from a character ID, save size, or a
mastery field. Revision markers and region/title ownership require native-file
proof, separate from the following documented gameplay changes. [20]

| Variation | Documented differences that matter to scope |
| --- | --- |
| Launch / 1.0.1 | Five main-game save slots before 1.1.0. 1.0.1 adds Expansion Pass outfit support. Native launch and 1.0.1 format equivalence is not proved by this note. |
| 1.0.2 | Adds Maddening and changes New Game+ clear-history Renown bonuses; prior saves recorded route types rather than repeated clear counts. Expansion wave 2 supplies and auxiliary battles remain pass content. |
| 1.1.0 without pass | Main-game save-slot count increases from 5 to 25; Jeritza is added as a Crimson Flower Part II ally through the free update. This is not proof of DLC ownership. |
| 1.1.0 with pass | Anna recruiting, sauna, feeding animals, new quests/battalions/outfits are pass features. Anna does not gain support relationships. |
| 1.2.0 without pass | Includes free Rhea interactions and a new Crimson Flower Bernadetta support partner, plus fixes. Free update changes do not imply the expansion is owned. |
| 1.2.0 with pass, main campaign | Cindered Shadows progress makes Abyss and related content available; Ashen Wolves recruitment is limited to Part I. New classes, quests, paralogues, support conversations and rewards have their own prerequisites. |
| Cindered Shadows side story | Separate save data and autosave, three save slots, Normal/Hard only. Do not identify a side-story slot as an ordinary main-campaign slot merely because the payload resembles one. Main-campaign DLC unlocks depend on side-story progress. |

New Game+ carries Renown, hired battalions/EXP, shop inventories, and statue
levels. It can purchase previously earned progress from the selected clear
data. The current campaign's recruited roster, current proficiency, historical
progress, and clear/route outcome records must remain separate. [13]

## Precise remaining evidence inputs

This mechanics review supplies no native save and no controlled before/after
pair. Before adding a writable system, obtain reviewed extracted saves outside
the repository with known title, region, installed software revision, DLC
installation/entitlement, main-campaign or side-story scope, and displayed
values. Keep raw samples and private identifiers out of public reports.

For stats/EXP, obtain one level-up plus unchanged control and separate
stat-booster/class-certification pairs. For skill progression/mastery, obtain a
rank threshold/talent unlock and class mastery reward pair showing both the
counter and learned/equipped state. For battalions, obtain hire/equip/swap,
level-up, endurance loss/replenishment and gambit-use pairs. For items, obtain
single-instance use/repair, trade-to-unit/convoy and equip changes. For supports,
obtain a pair gaining points and separately viewing a gated conversation.
Currency/renown spending must distinguish spendable balance from rewards and
historical progression. Repeat relevant actions across qualified revisions,
base/pass profiles and side-story data before claiming equivalence.

Passing parser, unchanged-roundtrip, integrity and surgical byte-difference
tests on genuine files establishes file evidence. Actual Switch game load and
re-save of the edited copy is a further validation step and is not established
by any documentation citation or synthetic test.

## Sources and licensing

The following sources were inspected for facts. The prose above is independent;
no website table, prose, artwork, game asset, or implementation was imported.
Serenes Forest carries a copyright notice for uncredited content, with no
permissive code/data reuse licence established by this review. Fire Emblem Wiki
pages identify **GNU Free Documentation License 1.3**, not a permissive software
licence. Nintendo support is copyrighted official documentation. Source links
are supplied as factual evidence; do not scrape or copy their catalogs into
runtime metadata. No downloaded save-editor or game executable was run during this research.

1. <https://fireemblemwiki.org/wiki/Class_change/Nintendo_Switch_games>
2. <https://fireemblemwiki.org/wiki/Experience>
3. <https://fireemblemwiki.org/wiki/Level>
4. <https://serenesforest.net/three-houses/characters/base-stats/>
5. <https://serenesforest.net/three-houses/characters/maximum-stats/>
6. <https://serenesforest.net/three-houses/monastery/renown-saint-statues/>
7. <https://serenesforest.net/three-houses/characters/skill-levels/>
8. <https://serenesforest.net/three-houses/characters/learned-abilities-arts/>
9. <https://serenesforest.net/three-houses/characters/budding-talents/>
10. <https://fireemblemwiki.org/wiki/Class_mastery>
11. <https://serenesforest.net/three-houses/miscellaneous/abilities/>
12. <https://serenesforest.net/three-houses/miscellaneous/combat-arts/>
13. <https://fireemblemwiki.org/wiki/New_Game_%2B> (Three Houses section only)
14. <https://fireemblemwiki.org/wiki/Battalion> (Three Houses section only)
15. <https://serenesforest.net/three-houses/miscellaneous/battalions/>
16. <https://serenesforest.net/three-houses/miscellaneous/forge-repair/>
17. <https://fireemblemwiki.org/wiki/Inventory>
18. <https://fireemblemwiki.org/wiki/Supply_convoy>
19. <https://fireemblemwiki.org/wiki/Professor_level>
20. <https://en-americas-support.nintendo.com/app/answers/detail/a_id/46816/~/how-to-update-fire-emblem%3A-three-houses>
21. <https://fireemblemwiki.org/wiki/Support> (Three Houses section only)
22. <https://fireemblemwiki.org/wiki/List_of_supports_in_Fire_Emblem:_Three_Houses>

Serenes Forest's older class-mastery page explicitly expresses uncertainty over
combat-art portability and groups Jeritza under a “DLC Exclusive” heading.
The restrictions above instead use the class-mastery article and the official
update history; those uncertain/misleading labels are not format evidence.
