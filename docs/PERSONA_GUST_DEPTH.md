# Persona, Atelier and Fatal Frame editing depth

This development review expands existing adapters without changing title,
platform or revision coverage. All writes use the existing frozen documents,
staging, Undo, Review Changes, native codecs, copied-save backup/restore and
new-destination saving. Procedural checks and genuine-file qualification are
separate; no game or downloaded editor executable was run. Edited in-game
loading remains untested.

## Persona 5 Strikers PC: additional existing consumable systems

Forty additional individually checked stack mappings are now editable:
seven incenses, nine ailment remedies, and 24 selected elemental/healing skill
cards. Together with the existing 54 consumable/ingredient mappings, the adapter
now knows 94 selected stack identities. Dynamic controls still require a qualified
occupied player slot, a positive quantity byte from 1 through 99 and a zero
adjacent byte. Empty stacks, unknown adjacent data and unusual higher quantities
remain unchanged. The stable field IDs use the slot and native relative offset.

The incense quantity bytes are slot-relative `0x869C6` through `0x869D2` with
stride two. Remedy bytes are `0x86A16` through `0x86A26`, stride two. Skill-card
positions are individually selected, **not** a contiguous assumed ID range:
Agi/Agilao/Agidyne/Maragi, Bufu/Bufula/Bufudyne/Mabufu,
Zio/Zionga/Ziodyne/Mazio, Garu/Garula/Garudyne/Magaru,
Psi/Mapsi, Frei/Mafrei, Kouha, Eiha, Dia and Media.

These controls edit supplies available for later in-game use. An incense stack
edit does not apply a stat increase; a skill-card stack edit does not teach a
Persona or replace any equipped skill. Game handling of item application,
target compatibility and learned skills remains authoritative. There are no
direct stat, Persona, learned-skill, compendium, fusion or ownership writes.
The 1–99 range remains a conservative manual editor limit, not a proved natural
cap. Every P5 field remains excluded from bulk Max.

Factual evidence was cross-checked between the public
[item/offset worksheet](https://docs.google.com/spreadsheets/d/1CeCiLDemo1cmc34Mg6WTs4Y4f-5yQsjWq2bGksaPktQ/edit)
and the [published editor reference at `7466afb`](https://github.com/Amuyea-gbatemp/Persona-5-Strikers-Scramble-Save-Editor/tree/7466afbb3c1bbcf550d4ff5c18e293103969e678).
The reference is GPL-3.0; no implementation, cheat writer or complete catalog
is incorporated. Selected position/name facts were individually transcribed.
The worksheet has no separately identified redistribution licence; its full
dataset is not bundled. The existing
[PC framing evidence](P5STRIKERS_PC_FORMAT.md) qualifies the matching body layout.
The two separately obtained
[public PC player files](https://savegame.pro/pc-persona-5-strikers-savegame/)
both contain eligible incense and selected card stacks; surgical edits preserve
the adjacent byte, character levels, held Persona IDs, all other body bytes,
the stream context and checksum suffix. Those player files may be modified and
do not establish gameplay caps or item-use behavior.

| Mechanic checked | Result and exact remaining input |
| --- | --- |
| Money, Persona points, unspent BOND points | Existing individual resource controls retained; no proved natural caps. |
| Consumables, ingredients, incenses, remedies, skill cards | Existing selected positive stacks editable. Additional item identities need independent position/name/category qualification. |
| Character growth, EXP, HP/SP, stats | Published editor only supplies raw level-byte writes; it does not establish EXP/level/stat coupling or character acquisition. Need native growth transitions or a native serializer/setter audit. |
| BOND EXP, ranks and requests | Unspent points are separate. Need rank thresholds and prerequisite/reward coupling, with controlled native earn/spend/rank-up pairs. |
| Persona ownership, held capacity, compendium, fusion, skill sets | Raw IDs and skill maps alone do not prove slot/reference constraints, learned-skill applicability or growth derivation. Need native acquisition/fusion/teaching pairs and reference rules. |
| Weapons, armor, accessories | Inventory offset lists do not establish owned/equipped links or special acquisition prerequisites. Need equip/unequip and purchase/drop pairs. |
| Recipes, requests, Jail/story, NG+, collections | Preserved; native prerequisite/reward maps remain missing. Ingredient replenishment does not qualify recipe unlocks. |

## Atelier Ryza 2: unspent skill-tree SP

The native original-PC profile contains a framed `AlchemyTree` root. A new
optional resource control requires its unique `ver` child to contain
`BE32(2), BE16(4)` and its unique `SkillPoint` child to contain exactly
`BE32(4), BE32(balance)`. The balance is exposed only when it is nonnegative
as a signed four-byte integer. The write changes only the second word, in
**big endian**, independently of little-endian item-quality fields. Missing,
duplicate or unknown tree/scalar profiles do not acquire an SP control; existing
qualified item controls remain available.

The [official skill-tree manual](https://www.koeitecmoamerica.com/manual/ryza2/en/7300.html)
states that SP is earned from synthesis, quests and events, then consumed to
learn recipes and alchemy skills. The native serialized `SkillPoint` scalar is
distinct from the separate `SkillState` array. The new control allows only
reductions between zero and the opened balance. It never modifies `SkillState`,
tree focus, recipes, quest rewards, learned skills or quality-cap unlocks. Max
is disabled, and the opened balance itself supplies the upper bound; no storage
ceiling or trainer value is advertised as a gameplay maximum.

The independently qualified
[public Ryza 2 autosave](https://savegame.pro/pc-atelier-ryza-2-lost-legends-the-secret-fairy-savegame/)
contains this exact tree/scalar framing. A reduction and unchanged roundtrip
preserve every other decoded byte and the native header, seed, footer and
trailer. No source implementation was used for the new SP control. The existing
MIT-attributed Gust codec remains unchanged. Cross-platform
[SaveWizard references](https://github.com/sterben-Dev10/SaveWizard-Resources/tree/4c32596efde54af7bec390b298265f09c929d94d)
were checked as factual leads only; no patch program or catalog was imported.
Their PS4 item quantity/stat writes are insufficient to authorize new PC
quantity/stat controls. The native autosave has no occupied ordinary inventory
stack with which to independently check the proposed quantity mapping.

| Mechanic checked | Result and exact remaining input |
| --- | --- |
| Existing inventory/equipment quality | Retained 1–100 individual controls; skill nodes controlling higher caps need controlled unlock pairs. |
| Unspent skill-tree SP | New qualified reduction control; increases/natural caps need earned/spent pairs and displayed values. |
| Cole and other currencies | A nested `money` record has multiple words; current balance versus other counters is not independently correlated. Need a native purchase/earn pair. |
| Quantities, uses, traits, effects, item levels, stat bonuses | PS4 templates do not qualify PC item-specific applicability. Need occupied native records and one-action pairs, including synthesis/equipment dependencies. |
| Character growth, combat resources, equipment references | Need current/maximum/derived distinctions and equip/growth pairs; no arbitrary stored-stat writes. |
| Skill/recipe ownership, ruins, feeding, maps, quests, story | Need prerequisite/reward graphs and native unlock pairs; SP reduction never unlocks a node. |

## Remaining reviewed adapters

| Adapter | Mechanics reviewed and retained | Exact blockers for additional writes |
| --- | --- | --- |
| Original Atelier Sophie Steam PC | Cole, Tess tickets and existing integral item quality remain editable; alchemy, party, grow/friendship and item nodes reviewed against the existing native archive/schema. | Quantity/use, trait/effect and equipped-stat applicability lacks controlled native action pairs. Growth/skill/friendship thresholds and event rewards are not mapped. Original/DX schemas differ; a DX trait editor is insufficient. Existing 31 snapshots are one player's archive, not isolated one-action controls. |
| Atelier Sophie 2 Steam 1.08 | Existing quality, Sophie/Plachta alchemy EXP, and current uses bounded by each saved capacity retained. MIT source model inspected for additional fields. | `m_mixGem` is a raw named scalar but its native gameplay role/spending limits remain uncorrelated. Source generic trait/effect/stat writers use storage widths, without item-specific applicability or derived-stat proof. No independent native 1.08 copy/action pair was available; current native and edited-game qualification remain pending. |
| Fatal Frame II Crimson Butterfly REMAKE Steam PC | Shared system Photo Point reductions, gameplay possession/storage and camera records retained. Official manuals distinguish system points from per-slot purchases and item-based camera upgrades. | `ItemObjectData.key`/`key_num` lack a qualified title-specific item catalog or controlled pickup/use pair. Film types/capacities depend on bag/upgrades; camera upgrade/reset must account for beads/refunds. Practice/NG+ modified copies do not establish legitimate ownership or caps. |

Original Sophie sources and independent-format derivation are detailed in
[its format note](SOPHIE_PC_FORMAT.md), including the
[official manual](https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/527270/manuals/AtelierSophie_manual.pdf?t=1695969954)
and [public native archive discussion](https://steamcommunity.com/app/527270/discussions/0/3160848559776680273/).
The [MIT Sophie 2 model](https://github.com/Tartarshia/Sophie2SaveEditor/tree/93d807072a852c73799394af4d32fb164841cd3e)
is the existing attributed factual/layout source; no new generic writers are
imported. Fatal Frame's
[official upgrades manual](https://www.gamecity.ne.jp/manual/zero/crimson-re/eng/5300.html),
[support clarification](https://support.koeitecmo.info/hc/en-us/articles/56588368652953--FATAL-FRAME-II-CB-REMAKE-Lost-items-exchanged-for-Photo-points)
and [native practice-file source](https://www.speedrun.com/FF2R/resources/lsb69)
support the distinctions above. Its existing MIT-attributed Katana codec
evidence is recorded in [the format note](FATAL_FRAME2_REMAKE_FORMAT.md).

`tests/test_persona_gust_depth.py` exercises the new controls: existing-record
selection, empty/unusual/adjacent-byte rejection, growth/ownership preservation,
endianness, reductions/bounds, unknown scalar profiles, higher opened balances,
zero balance, unstage/review/Max exclusions and surgical payload/envelope edits.
Optional private `P5S_PC_SAVE_COPIES` and `RYZA2_SAVE_COPY` qualify native files
without publishing their paths or contents. Existing per-game format, integrity,
safe-save and GUI suites remain applicable.

The focused new-control run completed **9 tests, all passed**, including both
optional native tests and the new Tk control workflow. Existing Persona/Ryza
format and review suites completed 41 tests with three initial display skips;
those display tests subsequently passed under the configured X display. The
broader owned-adapter regression run completed **66 tests, 65 passed and one
skipped** for the missing independent Sophie 2 native fixture. This run included
native Sophie archive and Fatal Frame checks and real Tk Undo/review/save/restore
workflows. These are editor checks, not actual game-load validation.
