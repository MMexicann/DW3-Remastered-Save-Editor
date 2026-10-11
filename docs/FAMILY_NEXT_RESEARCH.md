# Unreleased Hyrule / Fire Emblem / Pirate family follow-up

This work does not change the released version. Native player exports and source
examples remain private. No game binary/editor was executed, no console-storage
crypto or owner reassignment is added, and no edited export was loaded/re-saved
in a game. Format qualification, source facts, procedural tests and actual game
loading remain distinct.

## Feasible expansion completed

| Game | New safely qualified systems | Evidence and remaining limits |
| --- | --- | --- |
| Hyrule Warriors Definitive Edition, Switch | Known existing normal/Legendary weapon stars 0–5 with natural star Max; ordinary positive known seal KO counters decrease-only; corrected factual weapon names and named inspections. | Dedicated iAroc getters/writers, original Legends relative weapon definitions and independent native Switch export. Master Sword, collection-sensitive seals, identities, state, base power, equipment and unknown records remain unchanged. [Detailed proof and checklist](SWITCH_WARRIORS_RESEARCH.md). |
| Hyrule Warriors Legends, 3DS 1.0.0 exported profile | New explicit adapter: u24 rupees, 102 named existing materials, natural star quality, ordinary seal KO decreases, 60 named base-map card locations with positive existing quantities, owned ASCII fairy-name customization, read-only named growth/food/fairy inspection. | Original 3DS width/version/record getters and exact bounded writers, public complete native `zmha.bin`, native surgical checks for every exposed field. Resource/card ceilings are manual source bounds, excluded from Max; future DLC/revisions, growth/rewards/ownership, special weapons/seals remain protected. [Detailed proof and checklist](HYRULE_LEGENDS_FORMAT.md). |

## Revisited systems and specific blockers

| Game / variant | Scope reviewed | Exact reason additional writes are withheld |
| --- | --- | --- |
| Hyrule Warriors, Wii U | Gold, materials/map cards, ordinary weapon quality/seals; character level/EXP/health/attack, badges, combos, collection/story and costumes. | Existing level/EXP writes in upstream operate independently without synchronized growth/stat/heart rewards. Unnamed damage storage targets do not prove meaning or legitimate bounds. Badge trees and ownership/reward transitions lack a qualified schema. Wii U has no Legends/DE My Fairy feature; no fairy controls are transplanted. [Checklist](HYRULE_FORMATS.md). |
| Age of Calamity, Switch | Materials/trophies/reports, resource-history distinction, protection; weapon EXP/levels/caps/power/seals/quality/fusion and character/equipment/quest systems. | Source explicitly leaves weapon EXP caps and default seal parameters unresolved. Fractional character growth encoding is incomplete; clothing ownership, quest prerequisites and fusion/hidden-seal reward dependencies are unmapped. A commented generic Hyrule character block in a source editor is not AoC evidence. [Checklist](HYRULE_FORMATS.md). |
| Fire Emblem Warriors, Switch | Generic weapon star quality, ordinary seal requirements; gold/materials versus special drops, personal weapons, forging/fusion, growth/bonds/classes. | Existing 13 ordinary seal caps are retained; True Power, Legendary, Divine Favor, personal weapons and special drops remain protected. Gold/material source targets have no independently proved natural Max. Stored attack, class/level/EXP rewards, forging-material costs and equipped references need synchronized native proof. [Checklist](FIRE_EMBLEM_WARRIORS_FORMAT.md). |
| Pirate Warriors 3, PC | Beli/earned Beli, levels/EXP and two coin-byte families beyond existing trained-stat editor. | Runtime/serialized Beli locations differ by an unresolved prefix; PS3 patch addresses do not qualify PC. Two coin bytes are distinct values with unknown acquisition/notification/reward semantics, not a guessed u16 quantity. No matching native executable or correlated display/save pairs. [Checklist](PW3_COVERAGE.md). |
| Pirate Warriors 4, PC | Existing Beli and obtained coin quantities; growth maps, equipped/available abilities, coin names/rarity and new writer revisions. | Attached writer revision22 differs from genuine admitted revision15 and invokes conversion hooks. Fixed-data assets holding named coin/growth/rarity tables are absent, and controlled growth/equip pairs are missing. No identity/reward/lifetime-history writes or revision-header substitution. [Checklist](PIRATE_ABYSS_RESEARCH.md). |
| Warriors: Abyss, PC | Fresh static wrapper/native serializer inspection, GitHub planners, Steam save/mod discussions, Nexus listing and public save-site searches. | No genuine `SYSTEMDATA.BIN`/`GAMEDATA##.BIN` plus original owner context; registered-object serialization and inner integrity remain unqualified. Known AES and revision markers cannot authenticate or map gameplay data. Research candidate stays read-only/unregistered. [Precise filename/context and native evidence](PIRATE_ABYSS_RESEARCH.md). |
| Fire Emblem Warriors: Three Hopes, Switch | New save-specific source and genuine complete slots located after the earlier asset-template lead. | MIT [async-amethyst/few2-010-binary-templates](https://github.com/async-amethyst/few2-010-binary-templates) and public discussion exports qualify 144 own-body checksums, current gold decreases and paired owned-character ASCII names. The earlier DeathChaos source remains an asset map, not save proof. [Full mechanics checklist and exact guards](THREE_HOPES_FORMAT.md). |
| Hyrule Warriors: Age of Imprisonment / other new revisions | New-title/platform distinction. | No native save or proven serializer/crypto/layout source available in this investigation. No old Zelda offsets or unsupported game card are reused. |

Public planners' team JSON/localStorage is not native save data. Source asset
maps, cheat-storage widths, unrelated-platform files and generic bitfield Max
cannot establish safe disk-save controls. Every omitted important mechanic has a
specific prerequisite in the linked coverage documents.

Further genuine PC downloads and cryptographic qualification for Dragon Quest
Heroes II, Berserk and both Attack on Titan games are documented in
[the other-title follow-up](OTHER_KOEI_PC_RESEARCH.md). They remain research-only:
native ciphertext integrity is separate from a proven gameplay field map.
