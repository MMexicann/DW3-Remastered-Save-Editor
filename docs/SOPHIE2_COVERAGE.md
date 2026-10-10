# Atelier Sophie 2 development coverage

The adapter qualifies the published Steam PC 1.08 tagged layout. Its complete
codec, integrity validation and occupied record locations are implemented.
Independent native-save and actual game-load testing remain pending; the new
tests construct procedural records and never claim to be player saves.

| System | Implemented behavior or specific blocker |
| --- | --- |
| Material, important and consumable inventories | Edit quality of existing occupied records, 0–999. Max preserves higher values. Empty slots and item/instance identities remain unchanged. |
| Gathering tools and adventure equipment | Existing-record quality edits; no ownership or capacity changes. |
| Six characters' equipment | Named character and weapon/armor/accessory/battle-item slots; existing quality edits. |
| Battle-item remaining uses | Consumable container and equipped battle-item records with a positive saved capacity and consistent current count. Individual edits and Max refill only up to that existing capacity. Zero-capacity and inconsistent records are inspection only. Maximum uses are never increased. |
| Traits, effects and stat bonuses | Occupied-record inspection of trait/effect IDs and raw stat bytes. A reviewed item/trait/effect ID dictionary, item-specific applicability and legitimate bonus limits are needed before writes. No arbitrary IDs or byte-ceiling Max actions. |
| Inventory identity and item creation | Inspection of item and instance IDs. Item creation/duplication remains blocked on ownership/reference relationships and native before/after validation; no empty records are manufactured. |
| Alchemy EXP | Sophie and Plachta's published EXP fields are editable, excluded from Max. Raw level/EXP thresholds and recipe reward dependencies need controlled native mapping before a level/unlock action. |
| Alchemy resources | `m_mixGem` inspection. Its native resource limits and spending/unlock dependencies are not independently qualified; no resource Max is offered. |
| Combat progression, skills and AP | No qualified serialized field map, level/stat derivation or purchase prerequisites; need native one-change pairs and an unchanged control. |
| Recipes, catalysts, essences and synthesis unlocks | No qualified flag/record map or reward/prerequisite graph; require native acquire/synthesize pairs. |
| Money, bonds, quests and story | No qualified named node map and dependencies; require purchase, bond, quest-clear and chapter-clear pairs separately. Story completion is never coupled to stat/resource actions. |
| World exploration, collections, trophies and presentation unlocks | No qualified save-backed map. Need native discovery/unlock pairs; a menu category alone does not establish stored fields. |

The inventory inspector searches across character/container, slot, item/instance
IDs, quality, uses, traits, effects and raw bytes. Its values describe the opened
snapshot; pending changes remain in the main edit/review workflow. Unknown IDs
are labelled as IDs rather than assigned invented names.

## Evidence and validation

Record facts come from the MIT-licensed
[published model](https://github.com/Tartarshia/Sophie2SaveEditor/blob/93d807072a852c73799394af4d32fb164841cd3e/sophie2_model.py):
record width `0x2C`, quality at `+6`, traits at `+0x0A`, effects at `+0x10`,
current/max uses at `+0x24/+0x25`, and five stat bytes at `+0x27`.
This extension independently implements the record inspection and bounded current
uses; it retains the existing adapted codec's MIT attribution and licence.

`tests/test_sophie2_inventory.py` checks current-use bounds, surgical writes,
capacity/identity/trait/effect preservation, no-op roundtrip, invalid and empty
records, higher/inconsistent values, inventory search, Undo, review, automatic
backup and saving to a new copy. Existing format corruption, codec integrity,
path safety and source-change tests also remain applicable. No native game was run.
