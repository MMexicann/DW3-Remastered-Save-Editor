# Console, Pirate Warriors and XIII editor depth

This review covers twelve existing profiles, with new surgical equipment writes
for **Dynasty Warriors: Gundam PS3** and six additional appearance controls for
**Dynasty Warriors 8 Empires PS3 SYSTEM**. Other profiles retain their qualified
controls while their remaining mechanics are reviewed below. No game or external
editor executable was executed, and no external implementation, save, extracted
asset, signing data or private analysis is included in the source distribution.

## Gundam: four equipped skills per qualified pilot

The six individually proved pilot record bases remain unchanged. Four selected
skill references occupy base `+23..+26`; two inherent references occupy
`+27..+28`; the 36 learned bits begin at `+29`. New stable field IDs are
`<pilot>_equipped_0` through `<pilot>_equipped_3`, unsigned one-byte references.
They are selected only from the existing level-30 records admitted by the
learned-skill backend, with six distinct, in-range, learned references. Duplicate,
unknown, lower-level and otherwise ambiguous original records retain inspection
without equipment writes. Existing learned-bit controls remain available under
their previous qualification rules.

Four genuine US/EU exports contain twenty qualified pilot records and eighty
equipped slots. Every selected reference is learned. The two inherent references
are stable across the independent copies and agree with the public
[skill mechanics guide](https://www.k-rakuraku.com/musou/kihon/sukir.html): for
example, Amuro's Newtype/Impulse correspond to native 8/3, Kamille's
Newtype/Snipe to 8/7, Domon's School of Master Asia/Hard Strike to 11/6 and
Heero's Zero System/Snipe to 12/7. The four selected references vary between
copies; those are distinct from the two inherent skills. This corroborates the
reference roles independently of a blanket all-skills patch. Skill labels keep
native IDs: this evidence does not turn the entire guide order into a named
save-backed catalog.

The selector offers only skills learned in the **opened original snapshot** and
excludes that pilot's inherent skills. Equipping does not acquire a skill,
advance EXP, update level or claim a mission reward. A newly staged learning bit
becomes an equipment choice after saving and reopening. Four selected skills
must remain distinct. Selecting an already equipped skill swaps the two slots
atomically, so Review Changes and Undo include both dependent references. Direct
serialization of duplicate, unlearned or inherent choices is rejected. Returning
a swapped slot to its original value also restores its paired reference.
Undo reverses the entire swap. Revert Selected requires both changed slots;
dropping only one dependent reference is rejected.

Only the changed reference bytes and the existing three additive checksum words
may change. Unknown learned-mask bits, inherent references, flags, padding,
pilot/mobile-suit EXP and levels, missions and the rest of the file are retained.
Equipment choices are excluded from Max. Required original US/EU `PARAM.SFO`
identity, backups, source-change checks and external Apollo reimport/resigning
remain part of the existing workflow.

Source facts and profile qualification are recorded in
[LICENSED_MUSOU.md](LICENSED_MUSOU.md), including the individually published
[US Apollo patch](https://github.com/bucanero/apollo-patches/blob/main/PS3/BLUS30058.savepatch),
[EU patch](https://github.com/bucanero/apollo-patches/blob/main/PS3/BLES00147.savepatch)
and four independently checked [public exports](https://github.com/bucanero/apollo-saves/tree/master/PS3).
Only factual offsets and mathematical integrity definitions are independently
implemented; Apollo GPL code and patch catalogs are not copied.

## DW8 Empires: seven existing horse appearance members

The separately qualified PS3 SYSTEM table remains at payload `0x39B94`, with
150 records of `0x4C` bytes and checked ordinal identities 30–179. The six new
members are Head Size `+0x11`, Neck Length `+0x12`, Torso Length `+0x13`, Leg
Length `+0x14`, Tail Length `+0x15` and Muscle Volume `+0x16`. Each has a stable
`horse_<ordinal-index>_<member>` field ID and unsigned one-byte storage. They are
appearance controls, separate from model/type, speed, power, abilities and
ownership. The existing Body Type byte `+0x10` remains supported.

The independently published
[horse schema](https://www.tapatalk.com/groups/koeiwarriors/dw8e-modding-efforts-t17446-s10.html)
names every member. The publisher's console-inclusive
[Edit Mode page](https://www.koeitecmoamerica.com/dw8e/mode-editmode.html) and
[customization menu image](https://www.koeitecmoamerica.com/dw8e/images/mode/editmode/img3-1.jpg)
corroborate the separate appearance choices. The PS3 table, identities, occupied
states and varied positions are independently checked in the genuine
[US SYSTEM export](https://gamefaqs.gamespot.com/ps3/806920-dynasty-warriors-8-empires/saves/30046).
The PC table address is not reused. The official image is semantic corroboration,
not proof of PS3 serialized offsets.

Only Body Type has an explicit published complete 0–4 bound. For each of the six
new sliders, the selector therefore admits **only positions already witnessed
for that same member across qualified ordinary occupied horse records in the
opened snapshot**. A stored value in 0–4 is necessary for qualification but does
not independently authorize all five positions. No global natural-cap claim or
inferred endpoint is introduced. For example, the genuine sample witnesses Head
Size 0/2/3 and Tail Length 0/1/4 in qualified records; unobserved positions are
rejected. An unchanged save with fewer choices may offer fewer edits.

Four genuine ordinary horses expose twenty-eight fields. The fifth occupied
horse has unusual type/model IDs and remains read only. Qualification remains
per member: an unknown high Head Size does not suppress an independently
qualified Tail Length, and the unknown byte is preserved. Choices are determined
from original records, never staged or newly manufactured horses. Empty records,
ownership flags, names, IDs, model/type, stats and abilities are untouched.
Max excludes every appearance choice. Serialization changes only selected bytes
and the applicable outer game checksum, retaining the native cipher seed.

The exact console envelope, mandatory unchanged `NPUB31656-SYSTEM` metadata and
reimport/resigning requirements are described in [DW8E_PS3.md](DW8E_PS3.md).

### Independent PC SYSTEM qualification

The separately delegated PC DW8E adapter now exposes the same seven named
members using its **independently checked PC table** at `0x38104`, outer metadata,
seed and both native checksums. The genuine PC SYSTEM copy has all 150 expected
ordinals and two occupied ordinary horses. Its own witnessed Head Size, Neck
Length and Tail Length choices are 0/4; Torso Length and Leg Length each have
only 0, and Muscle Volume only 2. Those single-position members remain unchanged
on this input rather than borrowing console values. Four alternative Body Type
positions and one alternative in each Head/Neck/Tail slot give fourteen
independent native edits. Other original copies may provide different choices.

New PC members require original ordinary type/model IDs; previously qualified
Body Type behavior is retained. Unknown members and unusual type/model states
are preserved. The PC writer uses its original PC envelope and new `.dat`
destinations; no PS3 metadata is required and no console parser is used.
[PC profile evidence](DW8E_CUSTOM_HORSES.md) and the primary PC modding report
above provide the separate source provenance.
[test_dw8e_appearance_depth.py](../tests/test_dw8e_appearance_depth.py) verifies
PC witness choices, unusual states, fourteen surgical native edits, original
outer metadata/seed, both native checksums, and actual native Tk choice,
Review/Undo/Save/backup/restore workflows. Edited in-game acceptance is untested.

## Mechanics reviewed and exact remaining blockers

| Existing profile | Reviewed mechanics and retained/new controls | Exact remaining blocker |
| --- | --- | --- |
| Pirate Warriors 3 PC | Stats, special bars and skill-slot controls retained; reviewed Beli current/earned pairs, coins, character variants, growth, acquisition-ordered skills, costumes and logs. | Two native samples and runtime labels do not independently prove the current/earned disk update relationship. Need controlled earn/spend, standard-coin/limit-break purchases and skill/growth/equipment pairs or native disk setters. Costume associations do not prove unlock/entitlement writes. See [mechanics evidence](GAME_MECHANICS.md#pirate-warriors-3) and [PC skill guide](https://steamcommunity.com/sharedfiles/filedetails/?id=729079419). |
| Pirate Warriors 4 PC revision 15 | Beli and quantities of already obtained coins retained; reviewed earned/spent history, growth/skills, extra attacks, Soul Maps, outfits, Dramatic/Free/Treasure Logs and rewards. | Native node/catalog assets and controlled purchases/equip/reward pairs are missing. Revision 22 requires a separate complete genuine slot, ordered object/body sizes, each checksum and conversion qualification; changing revision headers is insufficient. See [native proof](PIRATE_ABYSS_RESEARCH.md), [public runtime research](https://github.com/Glubus/oppw4-sdk). No unlicensed SDK source or assets are copied. |
| DW7 PS3 US/EU | Gold and six officer-value controls retained; reviewed guardian beasts, skills/seals, weapons, unlocks, EXP/growth, campaigns and collections. | Guardian value 7 does not prove ownership/equip prerequisites. Need native PS3 full-word accessors, skill/weapon identities and controlled level/stat/reward or acquisition/equip pairs. Manual patch bounds do not prove natural Max. [Patch facts](https://github.com/bucanero/apollo-patches/blob/main/PS3/BLUS30690.savepatch). |
| DW7 Empires PS3 US SYSTEM | Bonus points retained; reviewed campaign food/information/gold, abilities/fame, weapons/items/mounts, relationships and kingdom progress. | SYSTEM cannot qualify `PLAY` campaigns. Need a complete decrypted campaign and its identity/structure, resource ownership and EXP/level/rank/reward mapping. Published campaign offsets alone do not prove a supported campaign writer. [Patch facts](https://github.com/bucanero/apollo-patches/blob/main/PS3/NPUB30846.savepatch). |
| SW4 PS3 US | Gold/gems retained; reviewed proficiency/EXP, weapon IDs, eight skills, ceilings/ranks/raw flags, rarity/fusion, mounts, bonds/Chronicle, stages and collections. | Weapon activation/upgrade reward flags and native owner/type relationships remain unqualified. Reducing a rank is not automatically safe while flags and prerequisites are unresolved. Native level/EXP/gauge dependencies and per-system controlled pairs are missing. [Patch facts](https://github.com/bucanero/apollo-patches/blob/main/PS3/NPUB31564.savepatch). |
| DW8 Empires PS3 US SYSTEM | Seven existing-horse appearance members now writable with original-record choices; reviewed combat stats/abilities, bonus rewards, campaign resources, officer growth/equipment and relationships. | Remaining members need name encoding, model/category or ability prerequisites; campaign resource order and owner bridge remain unresolved. [Official manual](https://store.steampowered.com/manual/322520) separates kingdom totals, officer allocation, Merits and ownership. |
| WO3 Ultimate PS3 US | Growth points/gems retained; reviewed promotions/proficiency/stats, weapons/reinforcement/fusion, attribute orbs/materials, mounts/equipped items, bonds, Gauntlet/Duel/story and collections. | Resource-specific public edited-load evidence does not qualify unrelated gameplay sections. Need PS3 setters/integrity and native ranked/binary attribute, ownership/equip, acquisition and promotion/reward evidence. [Direct-edit report](https://nextgenupdate.com/forums/ps3-mods-answered-questions/848494-brute-force-cheats-request-warriors-orochi-3-ultimate.html), [profile review](WO3U_PS3.md). |
| Atelier Ayesha PS3 US/JP | Cole and ordinary existing stack reductions retained; reviewed quality floats, effects/potentials, appraisal, memory-related words, synthesis/equipment and progression. | Stack acquisition/increase/delete and quality/property writes need item applicability, consumption/equipment references and legal derived effects. Two memory words demonstrably differ, so they cannot be set together as a guessed balance. [MIT factual reference](https://github.com/darkautism/AtelierAyeshaSaveEditor), [Alchemy FAQ](https://gamefaqs.gamespot.com/ps3/665780-atelier-ayesha-the-alchemist-of-dusk/faqs/66736). Chinese 1.1/PC/DX/Vita remain separate. |
| Gundam PS3 US/EU | Learned skills retained; new four-slot equipment selectors preserve learned/inherent dependencies. Reviewed pilot/mobile-suit growth, parts, missions and collections. | Lower-level skill prerequisites, coherent EXP/level/stat updates, additional records, suit parts and mission/reward/collection dependencies need native or controlled action proof. New equipment controls do not resolve these. |
| Ken's Rage PS3 US/EU | Positive existing fighter SP balances retained; reviewed Meridian Chart nodes, equipped abilities, persistent growth, battle gauges, DLC and missions. | SP is distinct from node ownership. Need native serializer/integrity confirmation, fighter entitlement/ownership, node-purchase/equip and growth/reward pairs. No native checksum-absence claim. [Mechanics guide](https://gamefaqs.gamespot.com/ps3/976861-fist-of-the-north-star-kens-rage/faqs/61481), [patch facts](https://github.com/bucanero/apollo-patches/blob/main/PS3/BLUS30504.savepatch). |
| Ken's Rage 2 PS3 EU | Locked native collection entries can be unlocked under the existing narrow rule; reviewed five growth tracks, signature moves, scroll ownership/equip/proffer/receive and Nexus effects, histories and missions. | Both genuine copies have all mapped gallery statuses nonzero, so genuine locked-entry edited validation remains missing. Growth/EXP thresholds, scroll IDs and transfer/equip/reward dependencies need labelled pairs. [Publisher PS3 manual](https://199xhokutonoken.files.wordpress.com/2013/02/shm_ps3_it.pdf), [patch facts](https://github.com/bucanero/apollo-patches/blob/main/PS3/BLES01801.savepatch). |
| ROTK XIII original PC revision 14 | Twelve city quantities retained; reviewed district ownership references, current versus maximum development/forecasts, proficiency levels, multipart durability, personal finances, officers/relationships/items and deployed armies. | No newly reacquired original-PC campaign copies were available in this review; available system/PK exports cannot qualify additional campaign records. Need exact original-PC serialized members and independent campaign correlation/dependencies before officer, army, ownership or development-cap writes. Native memory stride is not disk stride. [Static factual source](https://dl.3dmgame.com/patch/96257.html), [official manual](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/363150/manuals/SAN13Manual_en.pdf), [format proof](ROTK13_FORMAT.md). No proprietary editor code/resources are copied. |

Story completion, acquisition rewards and unlocks remain separate from resources
and equipment. Unresolved systems retain their bytes without speculative writes.
Unusual original values are never normalized by no-op serialization or Max.

## Validation and limits

[test_console_pirate_strategy_depth.py](../tests/test_console_pirate_strategy_depth.py)
covers every new equipment slot, originally learned versus inherent/unlearned
choices, atomic swaps and unstaging, direct duplicate rejection, ambiguous/high
references, all seven appearance members, original-record choices, exact surgical
preservation, checksum reparse, backups/restore, changed sources, and actual Tk
selector/Apply/Review/Undo/Max/Save workflows. Existing format, contract and GUI
tests continue to exercise strict identities, foreign/corrupt input, missing or
changed metadata, immutable originals and new-destination protection.

Optional `GUNDAM1_PS3_COPIES` and `DW8E_PS3_SYSTEM_COPY` select private reviewed
native exports; no fixture contents or private paths are published. Native checks
exercise eighty independent Gundam equipment edits and twenty-eight DW8E
appearance edits. Procedural records separately test malformed/ambiguous inputs
and invalid dependencies. Console game loading/re-saving remains **untested**;
source-backed mapping, native-file validation and GUI success are distinct from
actual game acceptance. Other existing-profile tests are reported independently
and optional unavailable native inputs remain explicit skips.

With the reviewed native fixtures and a Tk display, the six existing/new core
modules passed **53 tests**, including genuine and procedural controls. The
three additional dedicated PC depth tests passed separately. No success depends
on a zero-test run, disabled assertion or game executable.
