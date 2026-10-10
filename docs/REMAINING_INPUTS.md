# Remaining inputs by game and platform

This is a supplier checklist for further development. **Current implementation**
means the unreleased development source; published support is the inventory accompanying the
installed GitHub release. The [supported-game list](SUPPORTED_GAMES.md) identifies
registered editors; a researched format does not automatically provide a card.

Supply copies outside live game/cloud folders. Include game, platform, region,
installed build and DLC; retain original filenames and relative folder structure.
For a paired sample, save once unchanged, perform **one** recorded action, then
save again and provide the displayed before/after values. Keep originals intact.
Never put player saves, game binaries/assets, owner identifiers or personal paths
in Git or public issue attachments. Owner-dependent inputs must be shared privately;
no account passwords or console credentials are needed.

## Ten attached games

| Game | Current implementation / remaining gap | Exact useful files and next evidence |
| --- | --- | --- |
| DW7 XL Definitive, PC | Gold, officer stats/skill points and existing equipped weapon selection. Named equipment/skill rewards and progression need more evidence. | Native `save.dat` from `KoeiTecmo/Dynasty Warriors 7 DX/Savedata`; `inputmap1.dat`, `inputmap2.dat` and `inputmapm.dat` are separate input bindings. Matching `LINKDATA_CMN`, `LINKDATA_ENG`, `LINKDATA_CMN.IDX`, `LINKDATA_ENG.IDX`; one purchase, seal-learning, skill-allocation, equip or stage-reward pair. |
| WO3 Ultimate Definitive, PC | Stats/resources and existing weapon slots/attributes. Promotion/EXP, fusion, equipment, bonds and unlock rewards remain unresolved. | Native `SAVEDATA.BIN` from the qualified PC build; unchanged control and one promotion, growth allocation, fusion, equip, bond event or clear/reward pair. Matching installed parameter/localization files help name orbs/materials/weapons; preserve actual filenames. |
| Samurai Warriors 4 DX, PC | Resources, base stats, guarded standard-officer unlocks, existing own-pool equipment and attached skills. Growth and Chronicle/reward dependencies need evidence. | `SAVEDATA0000.dat`–`SAVEDATA0004.dat` gameplay copies; retain any companion system/input files under their original names. Current build/DLC labels, matching growth/weapon/skill catalogs and one level-up, proficiency, rare-weapon, mount or Chronicle event pair. |
| Pirate Warriors 4, PC | Revision15 one-step WW/JP/EA slot Beli and already obtained coin quantities. Current revision22 and other regions/system saves need separate profiles. | `OP4WINSLOT0000.dat` (or actual `OP4WINSLOT%04d.dat`) plus separate `OP4WINUSER.dat`; exact region/build/DLC. One coin gain/spend, Growth Map node, Soul Map, skill/equip or stage-reward pair. Include earlier/current unchanged copies to qualify migration. |
| Musou / Warriors Orochi Z, PC | Stock EXP, officer base attack and existing weapon attack bonus, attribute capacity and owned ranked effects. Own-pool equipment and coherent within-level EXP are also editable; level transitions, other stats, growth/rewards, new effects, alchemy and story remain protected. | Native revision2 `save.dat`, unchanged control and one growth-point allocation, level-up, fusion, attribute/rank, alchemy, proficiency reward or equip pair. Matching `LINKDATA*.BIN`/`.IDX` and `LINKDATA.ANS`/`.BNS`/`.CNS`/`.DNS`/`.ENS`, especially `/etc/unitbase.bin` and weapon/text tables, are needed for exact names and dependencies. Treasure acquisition differs from consuming a crafting material. |
| Warriors All-Stars, PC | Available gold and existing positive material quantities in campaign slots; lifetime earnings inspected separately. Existing own-pool Hero Card selection is also implemented. Card growth/properties, material names/acquisition, regard and route rewards remain unresolved. | Complete current revision `0x170302F4` `SAVEDATA.BIN`, including its global block and nine slot blocks. Build/DLC labels and one training purchase, currency gain/spend, named material acquisition/consumption, card acquisition/equip/customization, hero growth, regard event or route-clear pair; matching installed `LINKDATA.BIN` and `LINKDATA.IDX` qualify names, growth curves and card descriptors. A partial slot is insufficient for complete framing; older revisions need their own native control and migration evidence. |
| Warriors Orochi 4 / Ultimate, PC | Attached executable is a launcher; no gameplay adapter. | Exact installed-build `WO4.dll` or `WO4U.dll`, plus a same-build native `SAVEDATA.BIN`/`SAVEDATAU.BIN` copy. Public archives now provide 927,576-byte files with these names, but their exact edition/revision remains unqualified. Identify base/Ultimate edition, build and DLC. Then one resource, weapon/fusion, promotion, Infinity or stage-reward pair. |
| Samurai Warriors 5, PC | Owner-dependent AES and native classes identified; no gameplay editor. | `SAVEDATA00.BIN` or actual `SAVEDATA%02d.BIN`, with matching original save-owner context supplied privately, exact build and unchanged control. Trial `SAVEDATATRIAL.BIN` is separate. One same-owner purchase/reward, growth, weapon or castle-upgrade pair. |
| Warriors: Abyss, PC | Owner-dependent AES candidate; native inner integrity/records not qualified. | `SYSTEMDATA.BIN` and relevant `GAMEDATA00.BIN`/actual `GAMEDATA%02d.BIN`, with the matching original-owner context supplied privately. Build/DLC and one persistent recruitment/growth/Unique Weapon change, plus a separate run-resume control. |
| DW9 Empires, PC | Current SYSTEMDATA existing quantity edits and read-only custom-officer records; genuine current save and campaign support remain missing. | `SYSTEMDATA/SAVEDATA.BIN` for current header `0x210602F0`, plus `CAMPAIGNDATA000/SAVEDATA.BIN` or actual slot000–029. Separate `sinpmap.dat` is input binding, not integrity. Matching `LINKFILE_*.BIN`/`LINKIDX_*.BIN`, locale catalogs and one item, monthly budget, artifact/gem, relation or custom-officer pair. |

Detailed mechanic blockers are in [the coverage checklist](EXPANSION_COVERAGE.md)
and its linked game notes. A filename or source offset alone does not qualify
another revision, an ownership grant or an edited game load.

## Additional implemented platforms and investigated screenshot leads

Console exports below must be **extracted/decrypted gameplay files**, preserving
native names. Encrypted PS3 PFD metadata and Xbox360 signed CON/STFS containers
need their own validated container handling; a PC/raw parser must not be applied
to them. Existing console export/import tools remain responsible for signing.

| Game/platform | Current status | Further input needed |
| --- | --- | --- |
| DW6 original PC | Named officer unlocks, horse combat stats and existing named weapon elements; other growth/equipment records read-only. | Native `save.dat` with one level-up/skill purchase, horse growth/transform, weapon acquisition/equip or clear/reward pair; original Windows executable and matching catalogs if available. Empires/Special/console files are separate formats. |
| Hyrule Warriors Wii U | Resource/card, weapon-star and ordinary-seal edits; progression/collection prerequisites read-only. | Extracted `APP.BIN`, build/DLC and one growth/badge, fusion, equip, special-seal, map-card or stage-reward pair. Preserve complete original export. |
| Hyrule Warriors Definitive Edition Switch | Manual rupees/existing materials, generic weapon stars and ordinary seal KO reductions; character/food inspection. | Extracted `zmha.bin`, unchanged unmodified control and one material/discovery, fairy-feed/refresh, growth, fusion/equip or map-reward pair. Other markers/sizes require separate profiles. |
| Hyrule Warriors: Age of Calamity Switch | Rupees, discovered resources and existing weapon protection; growth/seals/special collectibles read-only. | Extracted extensionless `svdt`, exact build/DLC; one level-up, blacksmith cap upgrade/fusion, protection/equip, collectible or quest-reward pair. Earlier revisions differ. |
| Fire Emblem Warriors Switch | Gold, existing ordinary drops, generic weapon stars and ordinary-seal KO decreases; no character-growth/story grants. | Complete extracted `scenario0`, `scenario1` or `scenario2`, preserving separate `system`; exact build/DLC. Unmodified control and one material/drop, smithy fusion, ordinary-seal, character growth, crest, bond or History-mode reward pair. 3DS is a separate format. |
| DW7 PS3 US/EU | Manual gold/stats/skill points in decrypted exports. | Decrypted `APP.BIN` from `BLUS30690`/`BLES01149`, optional identity-only `PARAM.SFO`, one skill purchase/seal/equip/guardian-beast or clear/reward pair. Natural caps and named records need PS3-specific evidence. |
| SW4 PS3 US | Manual gold/eight gems; paired proficiency level/EXP inspected only. | Decrypted `DATA.BIN` from `NPUB31564`, optional `PARAM.SFO`, one proficiency level-up/EXP, growth, weapon/skill/equip, Chronicle/bond or reward pair. Japanese layouts require their own scalar profile. |
| DW7 Empires PS3 US | Manual SYSTEM bonus points; campaign unsupported. | Decrypted `NPUB30846-SYSTEM/DATA.BIN` plus `NPUB30846-PLAY*/DATA.BIN`, optional `PARAM.SFO`; one bonus purchase, campaign resource, fame/ability, relationship or territory pair. SYSTEM and PLAY are not interchangeable. |
| DW8 Empires PS3 | Source-only qualified SYSTEM/campaign codecs; resource-owner/order conflict blocks gameplay edits. | Decrypted `NPUB31656-SYSTEM/APP.BIN` and `NPUB31656-EMPIRE*/APP.BIN`; unchanged control and labelled resource/territory pair. Native PS3 ownership and resource getter/setter evidence are needed. PC layouts are different. |
| Strikeforce PS3 | Genuine decrypted exports acquired; identity/revision/integrity and item ownership still incomplete. | Decrypted `BLUS30471-SAVEDATA/APP.BIN`, optional `PARAM.SFO`, one storehouse item/acquisition/equip, growth/ability or mission-reward pair; native PS3 serializer evidence if available. |
| WO3 Ultimate PS3 | Apollo patches are factual leads; PC Definitive support does not imply PS3 support. | Decrypted `APP.BIN` from `NPUB50173`/`NPEB02052` (retain optional `PARAM.SFO`), exact DLC/build and unchanged control. Need native size/revision/integrity, progression/fusion/equipment and reward pairs. |
| SW2 / XL / HD PS3 | Japanese HD money/checksum inspection candidate only; no editor profile. | Decrypted `NPJB00439/DATA.BIN`, optional `PARAM.SFO`, complete native size/header and one money/growth/skill/weapon/guard/horse or Survival/clear pair. Original/XL/Empires variants must be labelled separately. |
| Totori DX Steam PC | No editor; source Cole offsets lack title/framing/integrity qualification. | Actual app936180 gameplay slot (`GAMEDATAxx`/`SAVEDATA`, retain the game's original name) plus `SYSDATA`, language/build and unchanged control; exact A12V-prefixed executable if available. One Cole purchase/sale, synthesis/equipment, licence/rank or calendar/event pair. Rorona app936160 is different. |
| DW5 Empires / DW6 Empires / DW7 Xbox360 | Legacy-editor leads only; no registered Xbox360 adapter. | Separately extracted native gameplay file with original basename (not yet qualified), title/region/build and unchanged control; corresponding signed container retained privately. Need STFS/container integrity, native checksums and independently mapped resources/growth/equipment/campaign dependencies. |
| SW2 / XL and WO1 / WO2 Xbox360 | Legacy-editor leads only; no Xbox360 gameplay writer. | Extracted native gameplay file retaining its actual basename (not yet qualified), exact title/edition/region and one controlled growth, weapon/fusion, skill/guard/horse or stage pair. Container and game integrity must both qualify; another platform's offsets do not apply. |
| SW4 DX / SW5 / WO4 PS4 | Save Wizard/Chaoszage commercial-editor examples do not supply a reusable implementation or native profile. | Legally obtained decrypted gameplay exports with native filenames/title IDs/build/DLC (basenames unverified here), unchanged controls and per-system action pairs; independent native identity/integrity/serialization proof. PS4 signing remains external. No commercial editor binaries are redistributed. |

For a legacy editor, public factual documentation and independently recovered
format rules can guide an original implementation. Reusing implementation code
also requires its original source and an explicit compatible licence or maintainer
permission. A binary-only download or commercial product screenshot supplies
neither that permission nor a tested native save mapping.

## Newly implemented profiles and further expansion

| Game/platform | Implemented now | Exact further input |
| --- | --- | --- |
| Dynasty Warriors 5 Special, Windows | Existing ordinary item ranks, own-family stored weapon attack adjustment/weight and existing attribute ranks; named officer, item, weapon and bodyguard inspection. | Unmodified native `save.dat`, language/build, one item pickup, weapon acquisition/equip, officer growth, bodyguard training or Shura action pair. Matching weapon/item parameter tables or original Windows executable help prove total stats and reward prerequisites. Japanese title numbering is Shin Sangokumusou 4 Special; console DW5, Empires and DW6 Special are different games. |
| Hyrule Warriors Legends, 3DS | Rupees, existing materials/base-map cards, generic weapon stars, ordinary seal decreases and existing printable ASCII My Fairy names. | Extracted `zmha.bin` with exact version/DLC; unmodified control and one fairy-name/food/skill, level/EXP/badge, fusion/equip, DLC-card or stage/reward pair. DE and Wii U layouts are different. |
| Atelier Ayesha, PS3 US/Japanese | Decrypted export Cole and qualified existing stack reductions; float quality/properties, effects and memory words inspected separately. | Decrypted `USR-DATA` copied to `.bin`, optional identity-only `PARAM.SFO` for BLUS31152/BLJM60486, one sale/purchase, synthesis/use, memory purchase or calendar/event pair. Apollo handles PFD reimport/signing; PC/DX/Chinese profiles require their own native exports. |
| Fire Emblem Warriors: Three Hopes, Switch | Gold reductions and existing owned Shez/Byleth ASCII name customization; character/weapon inspection. | Extracted extensionless `SlotData0`–`SlotData5`, exact version/DLC, one level/class/mastery, materials, forging/equip, support or route/reward pair. Existing header/body names and all 144 integrity sections are synchronized; stat/ownership grants remain blocked. |

## Other researched PC formats

| Game | Exact next input |
| --- | --- |
| DW8 Empires PC | Existing occupied custom-horse body type is implemented in qualified `SystemSave.dat`. Supply controlled examples for the other six appearance sliders, names, stats/abilities and campaign resource ownership; `EmpireSave*.dat`/`QuickSave*.dat` remain separate. |
| Sophie 2 PC | Genuine Steam1.08 `data.dat`, unchanged control and one quality/use/refill, alchemy EXP, trait/effect, equipment or recipe/action pair. Native item applicability and derived progression need separate proof. |
| Nioh 3 PC | Amrita/Gold deductions, existing common-stack reductions and tagged-pool inspection are implemented for two exact USER revisions. Need build-labelled carry/storage capacity and pickup/transfer pairs, currency-increase/purchase dependencies, native growth/skill maps, equipment/forge/owned-Scroll pairs and actual edited game-load/re-save. [Checklist](NIOH3_RESEARCH.md) |
| Nioh / Nioh2 PC | Genuine files are available and decode; the missing piece is the native active checksum algorithm, then controlled growth/equipment/dependency pairs. Integrity flags must not be erased. |
| Wo Long PC | Three currencies and existing ordinary stack reductions are implemented. Need matching item-name catalogs and controlled Virtue/level/skill, forging/equipment, acquisition and quest/reward pairs. |
| Stranger of Paradise PC | Genuine Epic launch USER/SYSTEM framing is now qualified; native gameplay integrity/update routines are still essential, followed by one-action resource/job/EXP/gear/synthesis/rift/reward pairs. Steam revision-0x23013100 USER/SYSTEM framing is separately qualified; unobserved builds and later Epic revisions require their own proof. [Checklist](SOPFFO_RESEARCH.md) |
| Persona5 Strikers PC | Native encrypted PC framing/checksum and occupied-slot money/Persona/BOND balances plus existing consumable/cooking quantities are implemented. Need one BOND purchase, character/Persona level, recipe/acquisition or quest-reward pair before expanding those systems. |
| Ninja Gaiden II Xbox 360/Xenia | Extracted revision-6 essence and stack editor implemented. Need actual edited game-load/re-save; native weapon/upgrade, health/Ninpo, ownership/reference and Karma/reward pairs. CON/STFS extraction/signing remains external. [Checklist](NINJA_GAIDEN_RESEARCH.md) |
| Ninja Gaiden Sigma, each platform | Seven PC gameplay copies establish bounded descriptive framing; native identity/revision/integrity remain unresolved. Need exact edition/platform/build proof and controlled resource, weapon/Ninpo, inventory, customization or reward pairs. Console formats need their own exports. Do not substitute Sigma 2, original II or Black. |
| Ninja Gaiden Sigma 2 Master Collection PC | Genuine story corpus acquired and metadata CRC recovered. Need the second native body-integrity algorithm/serializer and controlled essence/stack, weapon/Ninpo, ownership and reward pairs. PS3/Vita/Switch layouts remain separate. |
| Ninja Gaiden 2 Black Steam PC | Genuine GVAS story/system corpus acquired and typed wrapper bounded. Need native embedded story-body integrity at 0x14, separate SYSTEM integrity and resource/record/ownership/dependency pairs. Its Steam editor is not native integrity proof; PS5/Xbox Series are separate. |

No edited PC or console game-load/re-save was performed by this project during
this expansion. A successful file roundtrip, GUI workflow or Windows app build
is reported separately from that remaining validation.
