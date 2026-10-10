# Expansion coverage and remaining inputs

This checklist records the implemented scope of this expansion and the evidence
still required for deeper editing. The linked game checklists contain native
addresses, format details, sources, test commands and individual mechanic
blockers. A qualified codec is distinct from a gameplay editor; a successful
file roundtrip is distinct from loading an edited file in the game.

The v1.6 implementation has 22 registered game/platform profiles, compared with
11 in v1.5. The registry-derived [inventory](SUPPORTED_GAMES.md) is authoritative;
research-only formats below remain separate from those editors.

Attached executables were investigated as static data. They were never run.
Private static analysis copies, freely shared player saves, owner identifiers,
game assets and personal paths are excluded from source packages and releases.
The initial oversized Dynasty Warriors 9 Empires transfer was resolved with an
accessible replacement. Its native save code was inspected statically.

## Ten attached games

| Attachment / game | Delivered scope | Qualification and remaining essential input |
| --- | --- | --- |
| `SM6EN.exe` / Dynasty Warriors 7: Xtreme Legends Definitive Edition | Native PC editor: gold; health, attack, defense, power, speed and spendable skill points for 65 playable records; selection between already equipped owned weapons; searchable weapon/seal/equipment/skill inspection | Genuine native sample, native cipher/checksum and exact revision qualified. External `LINKDATA_CMN` / `LINKDATA_ENG` parameter/localization containers and indexes, or controlled action pairs, are needed for weapon/skill/title identities and dependencies. [Full checklist](DYNASTY_RESEARCH.md#dynasty-warriors-7-xtreme-legends-definitive-edition) |
| `WO3U.exe` / Warriors Orochi 3 Ultimate Definitive Edition | Native PC editor: five stats for 145 playable records, growth points/gems, 58 orb balances, 295 crafting balances, existing weapon slots and eight proven attribute types; read-only progression and weapon inspection | Genuine copied native file and static packed serializer qualified. Names, natural resource clamps, promotion/EXP rewards, fusion, equips, bonds and clear/unlock dependencies need parameter tables or controlled pairs. [Full checklist](OROCHI_RESEARCH.md#warriors-orochi-3-ultimate-definitive-edition) |
| `SamuraiWarriors4DX.exe` / Samurai Warriors 4 DX | Native PC editor: gold/eight gems, five base stats for 55 standard officers, guarded standard-character unlocks, existing own-pool weapon selection, attached skill levels/activation; searchable weapon and progression inspection | Genuine current-revision copy, full envelope and four gameplay checksums qualified. Growth/proficiency tables, record dictionaries and Chronicle/reward pairs remain necessary for derived progression and further content edits. [Full checklist](SAMURAI_RESEARCH.md#samurai-warriors-4-dx-implemented-native-pc-adapter) |
| `OPPW4.exe` / One Piece: Pirate Warriors 4 | Native revision-15 resource editor: spendable Beli and quantities of already obtained qualified coin records; current/lifetime counters and coin history are kept separate | Genuine slot, ordered object layout, outer checksum and object checksums qualified. Only one-step WW/JP/EA region family and revision 15 qualify; attached writer revision 22 needs separate migration evidence. [Full checklist](PIRATE_ABYSS_RESEARCH.md#pirate-warriors-4) |
| `OROCHI_Z.exe` / Musou / Warriors Orochi Z | Native revision2 PC editor: Stock EXP, base attack for 96 officers, existing weapon attack bonus, attribute capacity and owned ranked effects; searchable officer/weapon inspection | Genuine native save qualifies plaintext size/revision/marker, byte-sum integrity, unchanged roundtrip and surgical writes. Other stats, growth/reward coupling, exact names, new attributes/weapons, alchemy and story unlocks need native catalogs and controlled pairs. [Full checklist](OROCHI_RESEARCH.md#musou--warriors-orochi-z) |
| `Star_US.exe` / Warriors All-Stars | Native current-revision PC editor: available gold and existing positive material quantities in campaign slots, with separate lifetime earnings and slot inspection | Complete genuine save, native packed serializer and grant/spend paths qualify revision `0x170302F4`, ten-block AES framing and scalar semantics. Native active serializers perform no extra payload checksum; original seeds/padding and untouched blocks preserved. Fingerprint is not a payload checksum. Hero/card growth, material names/acquisition, regard and story rewards need record/dependency maps. [Full checklist](STARS_WO4_RESEARCH.md#all-stars-coverage-checklist) |
| `WO4.exe` / Warriors Orochi 4 / Ultimate | No gameplay adapter; supplied binary identified as a launcher | Matching **`WO4.dll` or `WO4U.dll` from the exact installed build**, plus a genuine PC save, is essential. Launcher imports/strings do not contain a recovered save codec. [Full checklist](STARS_WO4_RESEARCH.md#wo4ultimate-coverage-checklist) |
| `SW5.exe` / Samurai Warriors 5 | Research only: owner-dependent AES/key generation and distinct native save classes identified | Genuine native save with its correct original-owner context, confirmed framing/integrity and supported revision are missing. Trial/legacy variants require separate qualification. [Full checklist](SAMURAI_RESEARCH.md#samurai-warriors-5-research-only-no-editable-library-adapter) |
| `WARRIORSAbyss.exe` / Warriors: Abyss | Unregistered source-only owner-context AES envelope candidate and unchanged re-encryption | Original-owner context and a matching genuine system/game copy are missing. Native inner integrity and gameplay serialization remain unqualified; known markers do not authorize writes. [Full checklist](PIRATE_ABYSS_RESEARCH.md#warriors-abyss) |
| `DW9Emp.exe` / Dynasty Warriors 9 Empires | Source-backed current PC SYSTEMDATA editor: manual existing ordinary inventory quantities; searchable 800 native item IDs and 900 read-only custom-officer records | Exact native plaintext serializer/revision/size recovered; no save checksum/cipher/owner key in this path. A genuine current PC SYSTEMDATA file, active catalog/ownership evidence and controlled pairs remain missing. Campaign saves and older layouts are unqualified. [Full checklist](DYNASTY_RESEARCH.md#dynasty-warriors-9-empires) |

The native editors above retain existing branding/themes and
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
| DW9 Empires | Current SYSTEMDATA only, exact `0x2F1C28` size and `0x210602F0` revision. Existing item quantities 1..999 edited manually; zero/higher entries, identities and acquisition state preserved. All inventory controls excluded from Max; campaign currency and custom-officer records are not writable. |
| PW4 | Beli 999,999,999; eligible current coin quantities 999. Only native IDs 0–399 with an obtained flag and positive earned history qualify. Max preserves higher values. Ownership, earned/spent history, lifetime Beli and growth rewards remain unchanged; no empty coin record is created and no guessed character/rarity name is assigned. |
| Orochi Z | Stock EXP 99,999; 96 officers' stored base attack uses ID-specific floors 70..120 and ceilings 400..480. Existing weapon attack bonus 20, attribute capacity at least owned-mask bit count and at most eight, owned ranked effects 1..10 stored as level minus one. Unknown/empty weapons, malformed masks/capacity and enum5 remain read-only. Max preserves higher values; masks, alchemy, equipment, collections, officer EXP/other four stats and story stay untouched. |
| All-Stars | Available gold 9,999,999 in each existing slot whose native selected-hero identity is 0..99. Existing 45 material IDs expose only positive ordinary quantities for manual 1..9,999 edits; zero/higher stacks remain read-only and material Max is disabled. Empty/unknown slots are not created. Gold Max preserves higher balances; lifetime earnings, acquisition, purchases/training/rewards and progression remain unchanged. Only current F4 revision accepted; all ten encrypted fingerprints and campaign selections validated. |

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
| Orochi Z | Stock EXP, native bounded base attack and existing weapon bonus/capacity/owned ranks are implemented. Exact officer names require native `/etc/unitbase.bin` association; embedded surname/given fragments cannot be indexed directly. Other four stats, level/EXP and proficiency are inspected but need label/field proof, native growth thresholds and linked skill/costume/wallpaper rewards. New weapons/attributes and full fusion transactions require collection/ownership/cost maps; alchemy requires recipes, crafted stock and equipped-mask dependencies. Treasures are permanent prerequisites, not consumable material counts; mounts derive from Cavalier skill/faction rather than an invented inventory. Story/Dramatic/Versus/Survival and gallery need labelled eligibility, result and reward pairs. |
| All-Stars | Spendable slot gold, existing material quantities and lifetime-gold inspection are implemented separately; edits do not grant material acquisition, training, purchase history or rewards. Material names need native ID association; community alphabetical lists do not establish storage order. Hero levels/EXP/actions differ from battle-local Bravery; hero cards differ from conventional weapons. Card rarity/attack/affinity/elements/traits/material consumption/equip, regard/Hero Skills, requests, faction rosters/Opoona/ending routes and gallery need record IDs, legitimate bounds and dependency pairs. Regard, card affinity and temporary team effects must remain distinct. Earlier revisions need native layouts/migration controls. |
| WO4 / Ultimate | Matching gameplay DLL and native save are needed for every row: officer EXP/skills/promotions/stat stones; gold/growth points/crystals; weapon rarity/attack/attributes/fusion and Infinity crafting; camp upgrades; bonds/party/support; sacred treasures/deification; mounts; stage/rank/objective rewards; Infinity towers/fragments; costumes/gallery. Base and Ultimate limits differ and are not interchangeable. |
| SW5 | Owner-qualified decode and gameplay integrity precede maps for money/castle materials/facilities; officer progression/unlocks; weapon-type mastery; skills/gems; weapon reinforcement/crafting/attributes; horses/stable; Musou/Citadel scenarios, bonds/companions and gallery/customization. Each needs stored/derived distinction, valid references and prerequisites. |
| Abyss | Owner-qualified system/game copies precede maps for persistent Karma Embers/recruitment, permanent growth/transcendence, Unique Weapons/limit breaks, emblems/traits, summons/Unique Tactics, parties/formations, treasure/consumables, traversal/clear history, run resume/boss rewards, DLC heroes/costumes and collections. In-run levels/resources and computed team totals are not presumed permanent saved scalars. |
| DW9 Empires | Current SYSTEMDATA quantity pool and 900 CAW records are mapped; active item-name/category/ownership evidence, genuine current fixture and controlled pairs remain necessary. Campaign metadata/full layout precede gold/rations/army, merit/reputation, officer growth, trained/inherited compatibility, artifacts/gems/secret plans, kingdom/territory/stroll progression, bonds/spouse/children/recruitment, mounts/arrows/furniture and gallery. Read-only CAW inspection does not qualify inheritance, stat or appearance writes; older revisions require separate profiles. |

## Additional games and existing-editor expansion

| Game | Delivered scope | Remaining blockers and checklist |
| --- | --- | --- |
| Dynasty Warriors 6, original Windows PC |41 named one-way playable unlocks, four combat stats for existing qualified horses (0..500), named officer/weapon/horse inspection | Genuine native save and public author reload evidence support mapped categories. Level/EXP-derived rewards, skill-tree bits, weapon bonus bounds/equips, horse growth/transform/skill masks, stages and gallery need native routines or controlled pairs. Other platforms and DW6 Empires are separate formats. [Checklist](DW6_RESEARCH.md) |
| Dynasty Warriors 7, PS3 |US/EU copied decrypted APP.BIN: manual gold and 62 officer stat/skill-point records | Three genuine public exports qualify exact profile and surgical edits; no edited console load. Published targets do not justify Max; named roster, seals/skills/beasts/equipment and unlock/progression/reward maps need PS3 routines or controlled pairs. [Checklist](PS3_EXPANSION.md) |
| Samurai Warriors 4, PS3 |US copied decrypted DATA.BIN: manual gold and eight gems, with read-only paired proficiency level/EXP inspection and four gameplay checksums | Genuine regional exports qualify US profile and distinguish rejected Japanese layouts. Natural caps, proficiency level/EXP thresholds and growth dependencies, weapons/skills, Chronicle/bonds/mounts and unlock/reward maps remain unresolved. External console PFD signing/import is separate. [Checklist](PS3_EXPANSION.md) |
| Dynasty Warriors 7 Empires, PS3 |US copied decrypted SYSTEM DATA.BIN: manual bonus points | Genuine native system export qualifies exact 121,030-byte revision `0x12072200` and surgical edits. Campaign PLAY files, currency/army/fame/abilities, weapon/item/mount ownership, relationships, territories and progression need distinct profiles and dependency maps. Bonus-point edits preserve bought/unlocked rewards; Max is disabled. [Checklist](PS3_EXPANSION.md#dynasty-warriors-7-empires-us-ps3-system-profile) |
| Hyrule Warriors, Wii U |Rupees, existing named materials/map cards, qualified weapon stars and ordinary seal KO countdowns; named character/weapon/skill inspection | Two independently shared genuine APP.BIN exports qualify the observed profile; progression curves, badge prerequisites, ownership/equips, special collection seals, stage/gallery dependencies and other layouts require further qualification. [Checklist](HYRULE_FORMATS.md#wii-u-coverage-checklist) |
| Hyrule Warriors: Age of Calamity, Switch |Rupees bounded by opened lifetime total, discovered named materials/trophies/DLC reports, existing weapon protection and named weapon/seal inspection | Independently shared genuine svdt qualifies the observed profile; character/weapon growth coupling, cap quests, seal/fusion/polishing rules, special collectibles, ownership/DLC and stage/quest/gallery rewards remain unresolved. [Checklist](HYRULE_FORMATS.md#age-of-calamity-coverage-checklist) |
| Hyrule Warriors: Definitive Edition, Switch |Manual rupees and existing ordinary named material quantities; read-only 31 named character and 129 fairy-food records, named weapon/skill inspection | Genuine publicly shared modified native zmha.bin qualifies observed 252,132-byte marker/size and surgical quantity edits. No natural cap is inferred from hacked values, and all controls exclude Max. Discovery/food/fairy growth, progression, weapon ownership/equips and fusion/seal prerequisites, all map layouts and rewards remain unresolved. [Checklist](SWITCH_WARRIORS_RESEARCH.md) |
| Fire Emblem Warriors, Switch |Manual gold and positive ordinary drops, existing generic weapon stars and ordinary-seal KO decreases; named characters/weapons and special-material inspection | Genuine publicly shared modified 1.5.0 native scenario qualifies observed94,892-byte header/size and surgical writes. Resources exclude Max; special scrolls/opus/essences/Master Seals, unique/amiibo stars, True Power/Legendary seals, character growth/crests, bonds/roster/DLC and Story/History rewards remain read-only until exact caps, ownership and dependencies qualify. [Checklist](FIRE_EMBLEM_WARRIORS_FORMAT.md) |
| Dynasty Warriors 8 Empires | Strict source-only native SystemSave and Battle/Empire/Quick codec: exact sizes, title revision, applicable checksums and unchanged roundtrips of five files from one public bundle | No gameplay writer/card. Conflicting currency order and unqualified officer/array identities block resources/troops/stats/merit, aptitude/stratagems, equipment, relationships/offspring, custom content, territories and collections. Native executable/parameter data or controlled pairs required. [Checklist](DYNASTY_RESEARCH.md#dynasty-warriors-8-empires) |
| Nioh 3 | Source-only qualified USER identity/revisions, decryption, native body checksum and unchanged ciphertext return, supported by two genuine files and an encrypted/decrypted pair | No gameplay writer/card. Published fixed stat/inventory/scroll bases do not qualify acquired revisions. Equipment level and pre-forge level are distinct; pool ownership, reinforcement/affix category bounds, equipped references, scroll attempts, progression/skills/story need native records and controlled pairs. No integrity flags are cleared. [Checklist](NIOH3_RESEARCH.md#coverage-and-precise-blockers) |
| Dynasty Warriors 8 XL | Existing native editor expanded with four weapon-action aptitudes for 82 officers (25/50/75/100), qualified existing weapon affinity choices (0/1/2), and read-only 838 physical ally records | Affinity is a choice excluded from Max; numeric Heaven/Earth/Man association is not guessed. Weapon attack/identity/equips, skill ownership, ally recruitment/rewards, mounts, Ambition facilities, story/gallery and costumes need qualified limits/IDs and controlled dependencies. Existing resource/stat/attribute editing retained. [Checklist](DW8_COMPATIBILITY.md#coverage-checklist) |
| Atelier Sophie 2 | Existing tagged Steam PC 1.08 editor expanded with searchable occupied inventory/equipment inspection and remaining-use edits/refill bounded by each record's existing positive capacity; existing quality and Sophie/Plachta alchemy EXP edits retained | Independent genuine native file and game-load qualification remain pending. Traits/effects/stat bonuses need catalogs and per-item applicability; item creation, capacity, combat skills/AP, alchemy levels/recipes/catalysts/essences, resources, money/bonds/quests/story/exploration require native ownership, threshold and reward pairs. Alchemy EXP has no Max. [Checklist](SOPHIE2_COVERAGE.md) |
| One Piece: Pirate Warriors 3 | Existing genuine-qualified stats, special bars and equipped skill-slot editing retained; added currency/coin/progression mechanics coverage and PC runtime evidence review | No new uncertain currency/coin/story writer. Current/earned Beli save-to-runtime correspondence and legitimate cap remain unproved; two-byte coin semantics, limit breaks, skill acquisition, Kizuna progression, costume ownership, Legend/Dream Log and event/shop gallery require controlled pairs. [Checklist](PW3_COVERAGE.md) |

## Other investigated game leads

| Game | Result and exact remaining input |
| --- | --- |
| Legacy Xbox360 DW5 Empires/DW6 Empires/DW7; SW2/XL and WO1/WO2 | No registered Xbox360 adapter. Need extracted native files with title/edition/region/build, qualified STFS/container and game integrity, record ownership and controlled growth/equipment/campaign pairs. Legacy binary downloads do not supply a reusable licensed implementation. [Supplier checklist](REMAINING_INPUTS.md) |
| PS4 SW4 DX/SW5/WO4 commercial-editor leads | No PS4 profile or writer. Need legally obtained decrypted gameplay copies, exact title/build, native identity/integrity and independent semantic maps; original source and licence/permission are prerequisites for implementation reuse. No proprietary binary is redistributed. [Supplier checklist](REMAINING_INPUTS.md) |
| PS3 WO3 Ultimate | Apollo APP.BIN patches identify useful candidates, but exact native profiles, game integrity, complete genuine exports and independent progression/fusion/unlock dependencies must qualify before writes. PC Definitive Edition layouts do not apply. [Supplier checklist](REMAINING_INPUTS.md) |
| Atelier Totori DX, Steam PC | No gameplay adapter. Published Cole offsets lack disk identity/revision/integrity, and a mislabeled download was Rorona DX. Need complete app 936180 gameplay slot plus SYSDATA and unchanged control; installed A12V-prefixed executable would enable static loader/writer analysis. Inventory/equipment/synthesis/traits, adventurer licence/exploration, friendships/events/calendar/endings and collections have separate detailed blockers. [Checklist](TOTORI_PC_RESEARCH.md) |
| Samurai Warriors 2 HD, Japanese PS3 | Unregistered read-only candidate money/checksum inspection; no gameplay profile or writer. Need decrypted NPJB00439 DATA.BIN, complete size/header/revision and native record identities. Growth/skills, weapons/attributes, guards/horses, Survival/story/stages and collections require mappings and dependency pairs. [Checklist](PS3_EXPANSION.md#totori-dx-and-samurai-warriors-2-hd-investigation) |
| Dynasty Warriors: Strikeforce, PS3 | Genuine public exports were obtained/decrypted, but state-like first bytes do not establish a revision and published slot/storehouse facts do not prove native integrity/ownership. Need title/revision/integrity qualification and controlled progression/acquisition/equip pairs before resources, storehouse, growth/abilities or story editing. [Checklist](PS3_EXPANSION.md#further-ps3-leads-investigated) |

## Validation boundaries and follow-up inputs

Genuine privately held copies qualify unchanged roundtrips and targeted file
edits for DW7 XL, WO3 Ultimate, SW4 DX and PW4. Existing DW8 XL/PW3 genuine-file
qualification is retained. DW8 Empires and Nioh 3 genuine files qualify codecs
only. DW6 and PS3 DW7/SW4/DW7 Empires native public samples qualify their specific profiles;
Wii U Hyrule Warriors and Switch Age of Calamity have independently shared
complete native exports as well as upstream reference examples.
Switch Definitive Edition and Fire Emblem Warriors use publicly shared modified
native files; hacked values are not treated as natural gameplay caps.
DW9 Empires is source-backed without a genuine current native fixture.
Sophie 2 uses procedural/differential layout tests. All-Stars and Z have
genuine native qualification and targeted gameplay-field edits; Abyss remains a
procedural owner-context candidate. Optional native tests skip honestly when their input is absent.

Format tests check bounds/dependencies, unknown-byte preservation, malformed
input, immutable snapshots and applicable native integrity. GUI and integration
checks exercise editing/search, Undo, Review Changes, backups, Save As and
themes. **No edited save was loaded and re-saved in an actual PC or console game
during this expansion.** Windows application build/smoke/package checks are
separate from that missing game-load validation; their results belong in the
release/build validation record, not an inferred claim of gameplay success.

The shared implementation preserves existing higher or unusual values,
preserves unknown ID bytes and exposes only independently qualified fields.
Storage ceilings and public cheat targets are not
automatically natural gameplay limits. Legitimate array/revision variations
are supported only when separately qualified; arbitrary foreign, migration,
console or modded layouts are rejected rather than repaired or normalized.

Exact filenames and edition-specific supplier requirements are listed in
[REMAINING_INPUTS.md](REMAINING_INPUTS.md).
Useful follow-up inputs are copied native saves with build/region/DLC labels,
an unchanged control, displayed values, and one action between before/after
copies (purchase, promotion, fusion, equip, recruitment, stage clear or unlock).
The missing matching WO4 gameplay DLL, SW5/Abyss original-owner context and
a genuine current DW9 Empires SYSTEMDATA file address distinct blockers. Inputs stay private;
they do not belong in the source manifest, test fixtures or release downloads.

Licence/provenance details remain in each game note and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Public editors, patches,
runtime tables and planners informed factual investigation; their offsets,
runtime pointers and asset IDs were not promoted to native mappings without
qualification. Restricted-source implementations and extracted catalogs are
not included in the expansion.
