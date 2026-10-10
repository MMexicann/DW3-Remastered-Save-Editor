# Hyrule Warriors Legends — Nintendo 3DS exported save

This explicit adapter opens a separately extracted `zmha.bin` copy. It does not
open encrypted console save archives, handle console accounts/keys or import
anything to a 3DS. The supported profile has exactly **234,594 bytes (`0x39462`)**,
first five bytes `0026101500`, embedded complete size at little-endian u32 `0xC`,
and a zero low nibble at `0xD3`, source-mapped game version 1.0.0. Other revisions,
size variations and Wii U/Switch formats are rejected. Keep the complete original
export and save-management context unchanged; Save As creates a separate edited
copy with automatic backup.

## Source and genuine-file proof

[nedron92/HWL-SaveEditor](https://github.com/nedron92/HWL-SaveEditor) at commit
`4259e42b4ee6d643859fc218e436c20c337cb358` independently supplies explicit file
identity/size, a version-nibble decoder, raw little-endian readers/writers,
per-field widths, split material-region iteration, character/food positions weapon records and 14 fixed My Fairy records. We inspected its C++ source without executing the original
editor. No licence was located for its project implementation; no upstream
program, translated UI catalogue, dependency or game assets are copied into this
project. Python storage/parser/editor logic is independently written. Factual
English weapon identities are cross-corroborated against the dedicated Hyrule
Switch editor's weapon-ID definitions; neither its absolute offsets nor its
profile identity/size are used for 3DS saves.

The original [editor discussion, page 12](https://gbatemp.net/threads/release-hyrule-warriors-legends-save-editor-ntr-plugin.411349/page-12)
contains public attachment `zmha.zip` (37445) with one complete native `zmha.bin`.
The uploader explicitly says it has almost everyone unlocked and maxed out, and
links the save-management program used for export/import. This is a freely
shared player native export; its progressed/edited values are not an untouched
control or proof of natural caps. It stays private and is not distributed.
A similarly named title-ID ZIP on the first page is an NTR plugin, not a save;
we inspected its archive entries and did not execute it or mistake it for
qualification. The separate Switch export has a different complete size.

The 3DS reader/writer operates directly on raw bytes with no mapped aggregate
checksum fixup. Structural qualification checks the header, exact size, stored
size and admitted version nibble. All unknown bytes are preserved, and no
checksum is invented. This does not detect arbitrary corruption in opaque body
bytes and is not edited-console game-load/re-save validation.

## Proven field layout and dependency gates

| Field / system | Proven layout and implemented behavior |
| --- | --- |
| Rupees | **u24 little endian**, `0xDE..0xE0`; 0..9,999,999 manual published-editor ceiling. The adjacent byte `0xE1` is preserved. Natural gameplay clamp is uncorroborated; no Max action. |
| Ordinary material inventory | 102 named u16 slots: bronze begins `0x1924` with a late 3-slot group at `0x19BE`; silver `0x194A` with late 12-slot group `0x19C4`; gold `0x1992` with late 10-slot group `0x19DC`. Only existing positive quantities 1..999 qualify manual 1..999 edits. No unknown/higher/empty slot, discovery/reward flag or DLC ownership is changed. No material Max without independent natural-cap proof. |
| Weapon pool | `0x2F372` to EOF; exactly 1,030 physical 40-byte records. Empty ID `0xFFFF` omitted; unknown and future DLC IDs remain numeric/read-only. The source-mapped base-profile catalogue admits IDs 0..126. |
| Existing weapon stars | u16 +`0x14`, 0–5, states `0x03` normal and existing `0x13` Legendary; natural star-quality Max only. Master Sword ID 60 excluded even with a normal-looking state, reserved Ganon/Cucco 108/109 excluded, unknown states/IDs excluded. Existing higher star values survive Max and can be unstaged. |
| Existing ordinary seals | Eight u16 remaining-KO counters +`0..0xE` correspond to eight u8 skill IDs +`0x16..0x1D`. Existing positive known ordinary counters ≤5,000 may decrease 0..opened count, normal state `0x03` only. IDs, empty/unused slots and capacity never change. Every KO control is excluded from Max; Evil's Bane 41, Legendary 42, Master Sword and later special skills stay read-only. |
| Weapon power/state/references | u16 base power +`0x12`, state +`0x1E`, ID +`0x10` and opaque references remain unchanged. Source computes displayed attack from base power and stars, rather than saving a second derived attack scalar. No base-power cheat, Legendary-state conversion, weapon creation/swap or equip action. |
| Characters | 26 base-profile physical rows, stride `0x30` from `0x2EBF2`, named read-only unlock byte +`0xA`, EXP u32 +`0x12`, stored level index +`0x1A`. Reserved rows are inspected without granting ownership. |
| Adventure map consumables | 60 named one-byte quantities for the five base-profile maps. Noncontiguous shared-card exceptions in Great Sea/Twilight/Termina are mapped individually from original getters. Only existing positive quantities 1..5 admit manual 1..5 edits; source ceiling is not independent natural-cap proof, so no Max. No empty acquisition, DLC-map inventory, stage/discovery/search/reward/ownership flag changes. |
| Owned My Fairy names | Fourteen records from `0x1AEA`, stride `0x98`; eight-byte name array at +`0xA`. Exact existing ownership byte 1 and decodable printable ASCII names qualify nonempty 1–8 ASCII-character edits. Source direct writer explicitly pads shorter names with zero bytes within that array. Unchanged names preserve original stale padding. Unknown ownership/non-ASCII names, all growth/trust/refresh/clothing/skill data and neighboring bytes are preserved. No Max. |
| Fairy food | 132 source-named u8 quantities from `0x233A`, inspection only. Discovery/ownership and natural quantity limits are not independently qualified; source's storage-width target is not a gameplay cap. |

The native specimen contains 198 occupied weapons, including one protected
Master Sword; it exposes 323 qualified editable fields: rupees, one existing My Fairy name, 12 positive map-card quantities, 102 already-owned
material quantities, 197 weapon-star fields and 10 ordinary positive seal
counters. Public progressed values do not license resetting any reward history,
collectible dependencies or entitlement state.

## Per-mechanic coverage and exact blockers

| Mechanic | Implemented feature or remaining prerequisite evidence |
| --- | --- |
| Rupees / repeatable materials | Existing resource quantities, named inventory and validated manual edits; natural resource caps/discovery bits still needed before resource Max/acquisition/exhausted refill. |
| Weapon stars / ordinary sealed skills | Qualified existing-record star quality and decrease-only ordinary seal KOs; named record/skill inspection, surgical preservation tests. |
| Master Sword / Evil's Bane / Legendary | Read-only; collection flags at general-state bytes have different bit meanings and depend on weapon collection/KO rewards. No blanket unlock or state conversion. |
| Weapon fusion / smithy / new attributes | No creation or swap. Skill-slot availability, forging costs, learned/collection prerequisites and equipped references are not fully qualified. |
| Character level / EXP / attack / hearts | Read-only; source setters conflate growth with derived stats/heart containers and can leave irreversible progression mismatches. Need native synchronized growth/stat/reward proof or controlled level-up/allocation pairs. |
| Badges / combos / acquired skills | No writes; node/cost/material consumption/prerequisite/reward schema not proven for this profile. |
| My Fairy / companion skills / trust / refresh / clothing | Existing owned ASCII-name customization and named level/trust/refresh inspection. No acquisition or growth writes; refresh/growth/skill-claim/clothing reward and ownership dependencies remain unqualified. |
| Adventure map consumables | Named existing base-map inventory and validated manual quantities, with shared-card noncontiguous positions proven. Empty acquisition, exhausted refill, DLC maps, search/discovery/reward transitions and natural-cap Max remain unqualified. |
| Adventure/Legend/Dream/stage/rank/objective progress | Separate from resources; source blanket flag writes do not qualify individual rewards/unlocks. Controlled stage/reward pairs missing. |
| Character / costume / weapon / DLC unlocks | No writes; ownership alone does not create starter records/rewards. Version-dependent DLC checks are preserved, future records not admitted for editing. |
| Gallery / music / movies / medals | Collection identities and acquisition/reward transitions remain unqualified. |
| Other revisions/regions/platforms | Only the demonstrated 1.0.0 layout is admitted. Other native full exports and independent layout/revision evidence required; no Wii U/Switch parser fallback. |

## Verification

`tests.test_hyrule_legends` supplies ten format/contract checks and
`tests.test_hyrule_legends_gui` five real-Tk copy workflows. With a private native
fixture supplied, **15/15 pass without skips**. Tests distinguish procedural data
from the native player export. They cover byte-exact unchanged serialization,
u24 adjacency, exact eight-byte name writes, null padding, non-ASCII/ownership admission gates, string Undo/no-op and invalid strings, malformed shape/marker/stored-size/revision rejection, immutable
snapshots, special/foreign/future weapon exclusions, higher originals, invalid
pending edits before Max, source-change detection, suffix/collision guards,
backups and exact-byte restore. Every one of the 323 exposed native fields was
independently changed and serialized/reparsed with byte differences confined to
its declared field; the complete Master Sword record remains identical.

Real Tk tests on procedural and copied native data cover named search, Apply,
Review, Undo, weapon/item inspection, themes, backup/new-copy Save As and restore.
The genuine original remains unchanged. No save was newly imported, loaded or
re-saved on a 3DS. Without `HYRULE_LEGENDS_COPY`, three genuine-dependent checks
skip explicitly. Keep that optional fixture and its export context private.

Independent review in `tests.test_hyrule_legends_audit` adds six checks for
exact snapshot/format/raw-type qualification, native mixed-field surgical edits,
the fourteenth fairy boundary, future/unknown records, original ownership and
ASCII/padding gates, atomic invalid batches and pending-change validation before
Undo/Max. **All 21 Legends format, GUI and independent review checks pass** with
the private native input. Pending containers must be ordinary dictionaries;
selected field identifiers must be strings, and all existing pending edits are
validated before a new edit or Undo action.
