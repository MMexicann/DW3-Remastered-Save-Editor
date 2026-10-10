# PC expansion coverage and remaining inputs

This checklist records the implemented scope of this expansion and the evidence
still required for deeper editing. The linked game checklists contain native
addresses, format details, sources, test commands and individual mechanic
blockers. A qualified codec is distinct from a gameplay editor; a successful
file roundtrip is distinct from loading an edited file in the game.

Attached executables were investigated as static data. They were never run.
Private static analysis copies, freely shared player saves, owner identifiers,
game assets and personal paths are excluded from source packages and releases.
The Dynasty Warriors 9 Empires attachment could not be transferred because it
exceeds the file-download tool's **32 MiB ceiling**; its code was not inspected.

## Ten attached games

| Attachment / game | Delivered scope | Qualification and remaining essential input |
| --- | --- | --- |
| `SM6EN.exe` / Dynasty Warriors 7: Xtreme Legends Definitive Edition | Native PC editor: gold; health, attack, defense, power, speed and spendable skill points for 65 playable records; selection between already equipped owned weapons; searchable weapon/seal/equipment/skill inspection | Genuine native sample, native cipher/checksum and exact revision qualified. External `LINKDATA_CMN` / `LINKDATA_ENG` parameter/localization containers and indexes, or controlled action pairs, are needed for weapon/skill/title identities and dependencies. [Full checklist](DYNASTY_RESEARCH.md#dynasty-warriors-7-xtreme-legends-definitive-edition) |
| `WO3U.exe` / Warriors Orochi 3 Ultimate Definitive Edition | Native PC editor: five stats for 145 playable records, growth points/gems, 58 orb balances, 295 crafting balances, existing weapon slots and eight proven attribute types; read-only progression and weapon inspection | Genuine copied native file and static packed serializer qualified. Names, natural resource clamps, promotion/EXP rewards, fusion, equips, bonds and clear/unlock dependencies need parameter tables or controlled pairs. [Full checklist](OROCHI_RESEARCH.md#warriors-orochi-3-ultimate-definitive-edition) |
| `SamuraiWarriors4DX.exe` / Samurai Warriors 4 DX | Native PC editor: gold/eight gems, five base stats for 55 standard officers, guarded standard-character unlocks, existing own-pool weapon selection, attached skill levels/activation; searchable weapon and progression inspection | Genuine current-revision copy, full envelope and four gameplay checksums qualified. Growth/proficiency tables, record dictionaries and Chronicle/reward pairs remain necessary for derived progression and further content edits. [Full checklist](SAMURAI_RESEARCH.md#samurai-warriors-4-dx-implemented-native-pc-adapter) |
| `OPPW4.exe` / One Piece: Pirate Warriors 4 | Native revision-15 resource editor: spendable Beli and quantities of already obtained qualified coin records; current/lifetime counters and coin history are kept separate | Genuine slot, ordered object layout, outer checksum and object checksums qualified. Only one-step WW/JP/EA region family and revision 15 qualify; attached writer revision 22 needs separate migration evidence. [Full checklist](PIRATE_ABYSS_RESEARCH.md#pirate-warriors-4) |
| `OROCHI_Z.exe` / Musou / Warriors Orochi Z | Unregistered source-only native size/revision/integrity inspection and byte-exact unchanged roundtrip | Plaintext sections and native byte-sum record recovered statically. No independently acquired genuine PC save; candidate officer/weapon strides lack labelled field, cap and dependency qualification. [Full checklist](OROCHI_RESEARCH.md#musou--warriors-orochi-z) |
| `Star_US.exe` / Warriors All-Stars | Unregistered source-only ten-block AES envelope inspection and unchanged reconstruction | Static global/nine-slot key/IV/framing facts recovered. No complete genuine native PC save, inner gameplay integrity or semantic record map. A fingerprint trailer is not a payload checksum. [Full checklist](STARS_WO4_RESEARCH.md#all-stars-coverage-checklist) |
| `WO4.exe` / Warriors Orochi 4 / Ultimate | No gameplay adapter; supplied binary identified as a launcher | Matching **`WO4.dll` or `WO4U.dll` from the exact installed build**, plus a genuine PC save, is essential. Launcher imports/strings do not contain a recovered save codec. [Full checklist](STARS_WO4_RESEARCH.md#wo4ultimate-coverage-checklist) |
| `SW5.exe` / Samurai Warriors 5 | Research only: owner-dependent AES/key generation and distinct native save classes identified | Genuine native save with its correct original-owner context, confirmed framing/integrity and supported revision are missing. Trial/legacy variants require separate qualification. [Full checklist](SAMURAI_RESEARCH.md#samurai-warriors-5-research-only-no-editable-library-adapter) |
| `WARRIORSAbyss.exe` / Warriors: Abyss | Unregistered source-only owner-context AES envelope candidate and unchanged re-encryption | Original-owner context and a matching genuine system/game copy are missing. Native inner integrity and gameplay serialization remain unqualified; known markers do not authorize writes. [Full checklist](PIRATE_ABYSS_RESEARCH.md#warriors-abyss) |
| `DW9Emp.exe` / Dynasty Warriors 9 Empires | Mechanics research only; no codec or editor | Executable transfer exceeds 32 MiB, and no genuine native gameplay copy or independent disk serializer was obtained. An accessible binary, genuine save and possibly matching codec DLL/configuration are required. [Full checklist](DYNASTY_RESEARCH.md#dynasty-warriors-9-empires) |

The four native editor additions above retain existing branding/themes and
copied-save workflows: automatic backups, staged Undo, Review Changes,
source-change detection and atomic Save As to a new destination. Story
completion is separate from resource/stat edits. SW4 DX's guarded content unlock
does not complete a story or create a missing starter weapon. Unregistered
candidates have no editable library card or gameplay writer.

## Implemented limits and dependency guards

| Game | Validated bounds and safeguards |
| --- | --- |
| DW7 XL | Gold 999,999; health 1,000; attack/defense 1,400; power/speed 100; skill points 9,999. Native NPC records remain unchanged. Active weapon is a choice, excluded from Max, and must resolve to an already equipped owned valid record. Seal meters and purchased-skill flags remain inspection-only. |
| WO3 Ultimate | Health/Musou/attack/defense 999; natural speed 180. Existing higher values, including the acquired sample's speed 200, survive Max. Resource limits are published edit bounds rather than recovered natural clamps, so growth points/gems/orbs/materials are excluded from Max. Standard proven attribute ranks are 1–10; Verity is rank 1. Empty/unknown weapons, zero/unknown attributes and unsupported slot layouts are read-only; slot changes cannot hide or activate dormant attributes. |
| SW4 DX | Gold 999,999 and eight gems 99. Base stat edits use the stored u16 range and have no Max because growth caps are unresolved. Skill Max respects each existing ceiling, unusual values and locked state; IDs/ceilings are preserved. Equip selection stays in the officer's occupied own pool. Character unlock requires an occupied qualified equipped weapon and applies the native new-character marker without setting stage completion. |
| PW4 | Beli 999,999,999; eligible current coin quantities 999. Only native IDs 0–399 with an obtained flag and positive earned history qualify. Max preserves higher values. Ownership, earned/spent history, lifetime Beli and growth rewards remain unchanged; no empty coin record is created and no guessed character/rarity name is assigned. |

## Deeper mechanics: investigated coverage and blockers

These rows summarize the important mechanics in the linked checklists. Grouped
categories retain separate stored values, rewards and dependencies; a currency
edit does not simulate a purchase, fusion, promotion or stage reward.

| Game | Further systems requiring specific evidence |
| --- | --- |
| DW7 XL | Named roster/equipment, seal learning and system seal rewards require the native parameter/localization tables. Purchased skills/EX unlocks need officer definitions, costs, prerequisite masks and stat rewards. Guardian beasts, titles, bonds/sworn allies, Story/Conquest/Legend/town progression and gallery require ownership/record identities and reward pairs. No persistent level/EXP mapping has been proved; another game's level field is not substituted. |
| WO3 Ultimate | Stored level/EXP/promotions/item slots are inspected, while level reset, allocated/remaining upgrade stones and promotion rewards require controlled pairs. Proficiency/abilities, compatibility/reinforcement and derived attack need exact semantics and grade caps. Full orb/material names, recipes, attribute acquisition/fusion, equipment, mounts, bonds/companions, costumes/colors, Story/Redux/stage rewards, Gauntlet/keystones/allies, Duel cards and gallery need native ID tables and one-action acquisition/equip/clear pairs. |
| SW4 DX | Level/EXP/proficiency are inspected; external threshold/growth tables block consistent writes. Rare/DLC weapon creation, skill replacement and ceilings need templates and exclusion rules. Personal skills/gauges, consumables, mounts, custom character appearance/names, Chronicle goals/mentors/friendship/companions/biographies and stage/rare-weapon/collection unlocks need qualified asset dictionaries or controlled pairs. Historical kills/spending remain records rather than spendable resources. Older migration revisions need genuine samples and layouts. |
| PW4 | Coin rarity/name catalogs, acquisition and growth-map spending remain separate from quantity edits. Character/DLC unlocks, beginning/character Growth Maps, derived stats, skill ownership/equips/specials, Soul Maps, costumes, Dramatic/Free/Treasure Log, DLC challenges and gallery need native named record maps and prerequisite/reward pairs. System saves, three-/four-step regional variants and revision 22 migration are unqualified. Conventional weapon fusion/mount controls are not invented for this title. |
| Orochi Z | A genuine native PC fixture must first qualify title/layout. Candidate roster stats, level/EXP/proficiency, skills, weapon/fusion/element records, equipment/mounts, Story/Dream/Survival results and gallery require labelled fields, natural bounds and acquisition/reward pairs. Static integrity alone is insufficient. |
| All-Stars | A genuine complete PC `SAVEDATA.BIN` containing global/nine-slot blocks and inner identity/integrity must first qualify. Hero levels/EXP/actions differ from battle-local Bravery; hero cards differ from conventional weapons. Card rarity/attack/affinity/elements/traits/materials/equip, regard/Hero Skills, requests, faction rosters/Opoona/ending routes and gallery need record IDs and dependency pairs. Regard, card affinity and temporary team effects must remain distinct. |
| WO4 / Ultimate | Matching gameplay DLL and native save are needed for every row: officer EXP/skills/promotions/stat stones; gold/growth points/crystals; weapon rarity/attack/attributes/fusion and Infinity crafting; camp upgrades; bonds/party/support; sacred treasures/deification; mounts; stage/rank/objective rewards; Infinity towers/fragments; costumes/gallery. Base and Ultimate limits differ and are not interchangeable. |
| SW5 | Owner-qualified decode and gameplay integrity precede maps for money/castle materials/facilities; officer progression/unlocks; weapon-type mastery; skills/gems; weapon reinforcement/crafting/attributes; horses/stable; Musou/Citadel scenarios, bonds/companions and gallery/customization. Each needs stored/derived distinction, valid references and prerequisites. |
| Abyss | Owner-qualified system/game copies precede maps for persistent Karma Embers/recruitment, permanent growth/transcendence, Unique Weapons/limit breaks, emblems/traits, summons/Unique Tactics, parties/formations, treasure/consumables, traversal/clear history, run resume/boss rewards, DLC heroes/costumes and collections. In-run levels/resources and computed team totals are not presumed permanent saved scalars. |
| DW9 Empires | Accessible format inputs precede all resource/item/weapon/gem/secret-plan maps; officer progression/merit/fame; bonds/marriage/children/recruitment/custom officers; campaigns/territories/exploration; mounts/equipment/gallery. Native ownership, inheritance and campaign reward dependencies require controlled copies. |

## Additional games and existing-editor expansion

| Game | Delivered scope | Remaining blockers and checklist |
| --- | --- | --- |
| Dynasty Warriors 8 Empires | Strict source-only native SystemSave and Battle/Empire/Quick codec: exact sizes, title revision, applicable checksums and unchanged roundtrips of five files from one public bundle | No gameplay writer/card. Conflicting currency order and unqualified officer/array identities block resources/troops/stats/merit, aptitude/stratagems, equipment, relationships/offspring, custom content, territories and collections. Native executable/parameter data or controlled pairs required. [Checklist](DYNASTY_RESEARCH.md#dynasty-warriors-8-empires) |
| Nioh 3 | Source-only qualified USER identity/revisions, decryption, native body checksum and unchanged ciphertext return, supported by two genuine files and an encrypted/decrypted pair | No gameplay writer/card. Published fixed stat/inventory/scroll bases do not qualify acquired revisions. Equipment level and pre-forge level are distinct; pool ownership, reinforcement/affix category bounds, equipped references, scroll attempts, progression/skills/story need native records and controlled pairs. No integrity flags are cleared. [Checklist](NIOH3_RESEARCH.md#coverage-and-precise-blockers) |
| Dynasty Warriors 8 XL | Existing native editor expanded with four weapon-action aptitudes for 82 officers (25/50/75/100), qualified existing weapon affinity choices (0/1/2), and read-only 838 physical ally records | Affinity is a choice excluded from Max; numeric Heaven/Earth/Man association is not guessed. Weapon attack/identity/equips, skill ownership, ally recruitment/rewards, mounts, Ambition facilities, story/gallery and costumes need qualified limits/IDs and controlled dependencies. Existing resource/stat/attribute editing retained. [Checklist](DW8_COMPATIBILITY.md#coverage-checklist) |
| Atelier Sophie 2 | Existing tagged Steam PC 1.08 editor expanded with searchable occupied inventory/equipment inspection and remaining-use edits/refill bounded by each record's existing positive capacity; existing quality and Sophie/Plachta alchemy EXP edits retained | Independent genuine native file and game-load qualification remain pending. Traits/effects/stat bonuses need catalogs and per-item applicability; item creation, capacity, combat skills/AP, alchemy levels/recipes/catalysts/essences, resources, money/bonds/quests/story/exploration require native ownership, threshold and reward pairs. Alchemy EXP has no Max. [Checklist](SOPHIE2_COVERAGE.md) |
| One Piece: Pirate Warriors 3 | Existing genuine-qualified stats, special bars and equipped skill-slot editing retained; added currency/coin/progression mechanics coverage and PC runtime evidence review | No new uncertain currency/coin/story writer. Current/earned Beli save-to-runtime correspondence and legitimate cap remain unproved; two-byte coin semantics, limit breaks, skill acquisition, Kizuna progression, costume ownership, Legend/Dream Log and event/shop gallery require controlled pairs. [Checklist](PW3_COVERAGE.md) |

## Validation boundaries and follow-up inputs

Genuine privately held copies qualify unchanged roundtrips and targeted file
edits for DW7 XL, WO3 Ultimate, SW4 DX and PW4. Existing DW8 XL/PW3 genuine-file
qualification is retained. DW8 Empires and Nioh 3 genuine files qualify codecs
only. Sophie 2 uses procedural/differential layout tests; All-Stars, Z and Abyss
candidates use procedural envelope tests unless a private fixture is explicitly
provided. Optional native tests skip honestly when their input is absent.

Format tests check bounds/dependencies, unknown-byte preservation, malformed
input, immutable snapshots and applicable native integrity. GUI and integration
checks exercise editing/search, Undo, Review Changes, backups, Save As and
themes. **No edited save was loaded and re-saved in an actual Windows game
during this expansion.** Windows application build/smoke/package checks are
separate from that missing game-load validation; their results belong in the
release/build validation record, not an inferred claim of gameplay success.

The shared implementation preserves existing higher or unusual values,
preserves unknown ID bytes and exposes only independently qualified fields.
Storage ceilings and public cheat targets are not
automatically natural gameplay limits. Legitimate array/revision variations
are supported only when separately qualified; arbitrary foreign, migration,
console or modded layouts are rejected rather than repaired or normalized.

Useful follow-up inputs are copied native saves with build/region/DLC labels,
an unchanged control, displayed values, and one action between before/after
copies (purchase, promotion, fusion, equip, recruitment, stage clear or unlock).
The missing matching WO4 gameplay DLL, SW5/Abyss original-owner context and
an accessible DW9 Empires binary address distinct blockers. Inputs stay private;
they do not belong in the source manifest, test fixtures or release downloads.

Licence/provenance details remain in each game note and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Public editors, patches,
runtime tables and planners informed factual investigation; their offsets,
runtime pointers and asset IDs were not promoted to native mappings without
qualification. Restricted-source implementations and extracted catalogs are
not included in the expansion.
