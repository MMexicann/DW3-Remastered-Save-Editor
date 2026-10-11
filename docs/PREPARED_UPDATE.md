# Prepared update — unreleased

This branch prepares the next update without a version bump, tag, release,
main-branch merge or public executable upload. The latest published download
remains **v1.6**. The registry-derived [supported inventory](SUPPORTED_GAMES.md)
reflects the development source. Build artifacts from pull-request checks are
validation artifacts, not a new GitHub release.

## Added game/platform profiles

| Game | Platform | Implemented controls |
| --- | --- | --- |
| Samurai Warriors 4-II | Windows PC, revision `0x31A4` | Manual current gold, five held strategy-tome resources, five stored base stats on qualified existing standard officers, existing own-pool weapon selection and attached attribute magnitudes, and occupied-mount combat stats. Exact native checksum spans are qualified. Growth, skill trees, acquisition and story/reward transitions remain separate. |
| Dynasty Warriors 5 Special / Shin Sangokumusou 4 Special | Windows PC | Existing ordinary item ranks; existing own-family stored weapon attack adjustment, named weight choices and existing attribute ranks; searchable named officers, weapons, items, bodyguards and separate Shura resources. |
| Dynasty Warriors 8 Empires | Windows PC | Existing custom-horse body type; searchable appearance, stats and ability records in SystemSave.dat. Campaign files remain separate. |
| Hyrule Warriors Legends | Nintendo 3DS | Rupees, existing named materials and base-map cards, generic weapon stars, ordinary seal KO reductions and existing ASCII My Fairy names; named character/food/fairy inspection. |
| Persona 5 Strikers | Windows PC | Occupied-slot money, Persona points, unspent BOND points and existing named ordinary consumable/cooking quantities; character-level and held-Persona inspection. |
| Wo Long: Fallen Dynasty | Windows PC | Available Genuine Qi, copper, accolades, existing ordinary stack reductions and searchable inventory/equipment/companions/progression. |
| Fire Emblem Warriors: Three Hopes | Nintendo Switch | Existing gold reductions and owned Shez/Byleth name customization with synchronized mirrors; named character and weapon inspection. |
| Atelier Ayesha: The Alchemist of Dusk | PlayStation 3, US/Japanese decrypted exports | Cole and existing ordinary stack reductions; searchable inventory with float qualities, potentials/effects and distinct memory values. Apollo handles reimport/resigning. |
| Atelier Sophie: The Alchemist of the Mysterious Book | Original Steam PC | Cole, Tess exchange tickets and existing integral basket/container quality; numeric inventory and alchemy level/EXP inspection. DX is a separate unqualified format. |
| Atelier Ryza 2: Lost Legends & the Secret Fairy | Original Steam PC | Existing ordinary inventory/equipment quality 1–100 with native checksum preservation. Higher skill caps are not mapped; Max is disabled. |
| Fatal Frame II: Crimson Butterfly Remake | Steam PC | Shared system Photo Point reductions; gameplay inventory, camera and collection inspection. Native checksums, lexical JSON and binary photos are preserved. |

| Nioh 3 | Windows PC, USER revisions 0x01030001 / 0x01040000 | Existing known common-item quantity reductions in native tagged pools; equipment current level, pre-forge level and reinforcement inspection. |
| Ninja Gaiden II | Original Xbox 360 / Xenia, extracted revision-6 story | Manual Yellow Essence and existing unique ordinary consumable/ammunition reductions; searchable inventory and separate Karma inspection. CON/STFS signing remains external. |

Each has its own parser and explicit identity/revision gates. Resource ceilings
without natural-cap proof are manual editing limits and are excluded from Max.
Unknown items, unrelated regions, empty records, acquisitions and dependent
story/level/reward transitions are preserved.

## Expanded existing editors

| Editor | Addition |
| --- | --- |
| DW4 Hyper and DW4 Xtreme Legends PS2 | Already-owned harness/orb assignment with item-ownership protection; Hyper additionally supports guarded existing created-officer cosmetics and consistent paired progression mirrors. Independent genuine exports now qualify both profiles. |
| Warriors All-Stars PC | Select already-owned ordinary Hero Cards from the same hero pool; searchable occupied card records, preserving special gifts and card properties. |
| DW7 XL Definitive PC | Named first/second existing equipped-weapon choices reference only valid owned inventory slots. |
| DW6 PC | Named element choices for existing qualified weapons: Fire, Ice, Lightning or none. |
| Warriors Orochi Z | Existing own-pool equipped weapon selection and coherent progressed EXP confined to the already opened level. |
| Warriors Orochi 3 Ultimate Definitive PC | Additional qualified ranked weapon attributes and guarded attack-reinforcement reductions; binary/dormant effects remain preserved. |
| Hyrule Warriors Definitive Edition Switch | Existing generic weapon stars and ordinary positive seal KO reductions; special weapons and collection-dependent seals stay protected. |
| Samurai Warriors 4 PS3 | Searchable native weapon and attached-skill records, separate from proficiency EXP/level inspection. |
| Dynasty Warriors: Origins | Searchable existing weapon slots, upgrades and six stored trait IDs/levels; reserved records preserved. |

Other implemented games were reviewed for additional save-backed systems; the
per-game notes record specific dependency or input blockers. DW3 Remastered's
existing rich editor is retained. No runtime trainer address or another
platform's mapping is presented as a native save field.

## Interface and maintenance

- Search games by name, short name, platform or feature; filter by series and
  platform, including All platforms. Ctrl+F focuses global library search and
  Enter opens a single result.
- Compact cards, result counts, clear filters and visible resume-session buttons.
- Named choice controls and bounded backend-validated text fields; multi-field
  staging stays atomic and preserves Undo and Review Changes.
- Sort field, inspector and review tables by clicking columns; copy selected
  inspector rows with headings. Large integers retain exact sorting precision.
- Keep per-game modules under `src/koei_editor/games`, common utilities under
  `shared`, unregistered research under `research`, and notes under `docs`.
- Keep supported games synchronized in the registry, code index, runtime
  catalog, README and generated document. AGENTS/CONTRIBUTING require this.
- Guard the additional official live save directories and preserve source-copy,
  backup, new-destination and restore protections.

## Research and validation

The three newly supplied files identify Orochi Z, WO3 Ultimate Definitive PC
and SW4 DX respectively; the file described as DW7 is an Orochi Z file.
[The supplier table](REMAINING_INPUTS.md) lists exact remaining inputs.
[Additional research](ADDITIONAL_EDITOR_SURVEY.md) and game notes distinguish
real save editors, asset tools, runtime trainers and unsupported platform leads.
The [Team Ninja coverage](TEAM_NINJA_RESEARCH.md) records native integrity and
mechanic blockers for Nioh 1/2, Stranger of Paradise, Sigma/Sigma 2 and Black.
Each edition/platform stays separate; active integrity flags are retained.

The separate hunting/monster-development investigation acquired public PC save
archives for [Toukiden Kiwami](TOUKIDEN_KIWAMI_RESEARCH.md) and
[Toukiden 2](TOUKIDEN2_RESEARCH.md), but neither native codec/integrity nor
writable mappings qualified. [Monster Rancher 1 & 2 DX](MONSTER_RANCHER_DX_RESEARCH.md)
also remains blocked on complete native Windows files and serialization proof.
These four titles add no library card or runtime support claim; each note records
mechanic dependencies, source/licence boundaries and exact next inputs.

Native shared player exports qualify unchanged roundtrips, targeted byte edits,
checksums where present, malformed inputs, GUI workflows and backups. Procedural
fixtures cover independent adversarial cases. No attached executable was run;
no edited save was loaded/re-saved in a game. Native Windows build checks and
full regression totals are recorded after integration. No player files,
account identifiers, attached binaries or personal paths are included in Git.
