# Dynasty Warriors 8 Empires: US PS3 SYSTEM custom horses

The `dw8e_ps3` adapter edits **Body Type of an already occupied custom-horse
record**, manually from 0 (leftmost position) to 4 (rightmost position). The
standard GUI provides searchable fields and horse inspection, Apply, Undo,
Review Changes, automatic backups, safe Save As and validated backup restore.
Body Type is an appearance choice and is excluded from automatic Max.

Open a separate **decrypted** US PS3 SYSTEM `APP.BIN` copy. Keep the matching
`PARAM.SFO` beside it; its save-directory identity must be exactly
`NPUB31656-SYSTEM`. Save or restore to a new `.bin` in a folder containing that
matching metadata, so the result can be reopened with the same region check.
Apollo can export decrypted gameplay data and reimport/resign edited copies.
This editor changes the game-layer bytes and checksum only. It does not rebuild
`PARAM.PFD`, encrypt console files, resign saves or change account ownership.
Keep the original console directory and export separately.

## Exact console profile and evidence

| Property | Qualified PS3 SYSTEM profile |
| --- | --- |
| Region / edition | US PSN `NPUB31656`, Dynasty Warriors 8 Empires, SYSTEM only |
| Copied input | PFD-decrypted `APP.BIN`, exactly 251,036 bytes |
| Game layer | Symmetric byte cipher, seed `0x14082801`; final byte stores decoded byte sum modulo 256 |
| Decoded revision / length | Little-endian `0x140828F1`; 251,035 bytes |
| Console horse table | Payload `0x39B94`, 150 records, stride `0x4C` |
| Record identity | Little-endian DWORD `+0x44` must equal row ordinal + 30 for every row, 30 through 179 |
| Writable selector | Original occupied byte `+0` equals 1, Body Type byte `+0x10` is 0–4, menu type `+0x0F` is 0–7, model byte `+0x1E` is `0x96`–`0x9D` |
| Allowed writes | One selected original Body Type byte per field, plus the outer game byte checksum |

The genuinely shared [US PS3 GameFAQs export 30046](https://gamefaqs.gamespot.com/ps3/806920-dynasty-warriors-8-empires/saves/30046)
contains both SYSTEM and an EMPIRE3 campaign. Console encryption was removed
privately without executing a game/editor binary. SYSTEM's game checksum and
revision match, its independently located console horse table contains all
150 expected native identities, and five existing occupied records contain
varied appearance positions. Four have ordinary documented horse types/models
and expose Body Type; one has an unusual type/model and stays inspection-only.
The console table is **not the PC table address**
(`0x38104`), and the complete console envelope is not the PC envelope.

The independently published [horse schema, post 15](https://www.tapatalk.com/groups/koeiwarriors/dw8e-modding-efforts-t17446-s10.html)
names the relative bytes and explicitly identifies Body Type positions 0–4.
That report is PC-origin evidence for the shared record schema, not proof of a
PS3 input. Its full record shape is independently corroborated in the genuine
PS3 SYSTEM table: fixed identities, occupied records, seven appearance bytes,
type/model distinction, two stats and four ability slots. The official
[PS3-inclusive DW8 Empires product site](https://www.koeitecmoeurope.com/dw8e/)
and its [Edit Mode documentation](https://www.koeitecmoamerica.com/dw8e/mode-editmode.html)
independently identify custom-warhorse Body Type as an editable appearance
choice; the linked official [warhorse customization screenshot](https://www.koeitecmoamerica.com/dw8e/images/mode/editmode/img3-1.jpg)
shows the named appearance sliders. The screenshot's controller glyphs are
Xbox-style; it is semantic corroboration from the console product documentation,
not evidence of PS3 serialized offsets.

These facts establish the narrow source-backed mapping with genuine-file
qualification. A controlled PS3 before/after action pair and edited console
load/re-save remain untested. No player records, images, account context,
external source code or game assets are distributed. The implementation uses
independently checked format facts and this project's shared cipher/safety
helpers; it does not import an external editor or Apollo GPL implementation.

`PARAM.SFO` is mandatory because the payload does not independently distinguish
US from other regions with potentially matching serialized shapes. Only its
`SAVEDATA_DIRECTORY` is parsed. PC, campaign, unsupported region/edition,
truncated, corrupted-checksum and invalid-ordinal inputs are rejected before
exposing controls. Unknown or unusual values, names, models, abilities, padding
and every unedited system remain byte-exact. No-edit serialization returns the
original bytes; edits are re-encoded and reparsed without repairing bad input.

## Per-system coverage and blockers

| System | Implemented result / exact remaining blocker |
| --- | --- |
| Existing custom-horse Body Type | Manual 0–4 for original occupied, in-range rows with qualified ordinary type/model IDs; no horse creation or ownership changes. |
| Remaining six horse appearance sliders | Named read-only values. Per-slider legitimate console bounds and controlled action pairs are needed before writes. |
| Horse names, menu type, model and record identity | Read-only. Type and actual model are distinct; unusual/DLC records are excluded from writes, and existing ordinary-type/model mismatches are preserved. Exact name encoding and model/category dependencies block writes. |
| Horse speed, power and four abilities | Read-only. Native natural category limits, ability acquisition/slot prerequisites and battle effects are unqualified. |
| Campaign materials / gold / troops | Existing separate research codec inspects raw candidate rows. Actual native PS3 resource order and owner identity bridge remain unresolved. Single offsets `0x5F84/0x5F88/0x5F8C` are row 4 of the 40-row array, not a global resource pool. |
| SYSTEM bonus points / reward purchases | No writes: no independently qualified PS3 scalar mapping or acquisition/purchase dependency proof was found. |
| Officer EXP / Merits, levels, skills, stats and compatibility | No writes. Published PS3 patch targets do not qualify native officer identities, level thresholds, position-dependent growth, gauge rewards or proficiency caps. |
| Weapons / fusion, equipment and inventory | No writes. Existing ownership, serialized item/weapon identities, equipped references and acquisition/attribute prerequisites need native PS3 routines or controlled saves. |
| Relationships, spouse/family, bodyguards and mounts in campaigns | No writes. A SYSTEM custom-horse appearance change does not alter campaign ownership or unlocks; native relationship and equipment bridges are missing. |
| Stages, collections, scenarios and story completion | No completion/unlock action. Exact flag identities and reward dependencies remain missing; completion stays separate from appearance and resources. |
| Other regions, editions and save kinds | No fallback to PC or campaign parser. Separate native identity/context and table/integrity qualification are required. |

The [published PS3 Apollo patch](https://github.com/bucanero/apollo-patches/blob/main/PS3/NPUB31656.savepatch)
provides campaign resource/officer leads, not a custom-horse mapping or a proven
resource-owner bridge. Its money/troop order conflicts with a PC runtime table;
no writer uses those candidate labels. The official
[game manual](https://store.steampowered.com/manual/322520) distinguishes current
resources, kingdom troop totals, officer allocations, level/Merits,
position-dependent stat growth, weapon compatibility and item effects.
Those dependencies prevent treating resource/stat cheat targets as independent
natural gameplay controls.

## Validation

Public procedural fixtures use distinctive unknown bytes and construct the
PS3 envelope and complete 150-ordinal table independently. Tests cover first
and last existing records, bounds, malformed edits, immutable snapshots,
identity/revision/checksum corruption, unsupported input sizes, original
unstaging, Max exclusion, unusual/empty records, required region metadata,
changed sources, backups, restore and new destinations. GUI tests exercise
actual Tk controls for search, Apply, Review, Undo, inspection, Light/Dark,
Save, automatic backup and restore.

`DW8E_PS3_SYSTEM_COPY` optionally selects a private genuinely sourced
PFD-decrypted SYSTEM export with its original matching `PARAM.SFO`. Genuine
checks separately establish byte-exact no-op and surgical edits of every
qualified occupied Body Type, preserving every other decoded byte. Console
loading/re-saving and battle validation are **not tested**. Procedural and GUI
success do not claim in-game verification.

The registered copied-save command-line self-test propagates the mandatory
context by copying the entire bounded original `PARAM.SFO` opaquely into its
new, private output directory. It parses only the directory identity, preserves
all metadata bytes and does not regenerate, sign or rewrite that file. These
local test outputs retain the original private console metadata: keep them
outside Git and do not publish them. The resulting JSON report records native
game-checksum verification separately from `in_game_load_tested: false`.
