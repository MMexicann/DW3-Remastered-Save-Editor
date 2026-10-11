# Dynasty Warriors 8 Empires — native PC SYSTEM custom horses

This adapter opens a separate Windows `SystemSave.dat` copy. It edits **seven
appearance members of already occupied custom-horse slots**. Body Type accepts
0–4. Head Size, Neck Length, Torso Length, Leg Length, Tail Length and Muscle
Volume use only same-member positions witnessed in qualified original ordinary
horses in the opened PC snapshot. Appearance choices never receive Max.
Empty slots, unusual member values, names, type/model, abilities, speed, power
and campaign progression are preserved. See the independently qualified PC
expansion in [CONSOLE_PIRATE_STRATEGY_DEPTH.md](CONSOLE_PIRATE_STRATEGY_DEPTH.md).

## Evidence and native profile

The contemporary [PC modding report, post 15](https://www.tapatalk.com/groups/koeiwarriors/dw8e-modding-efforts-t17446-s10.html)
by Hero of Chaos (March 3, 2015) describes direct decrypted-save edits and their
appearance in the in-game editor. It identifies the horse table at payload
`0x38104`, 150 records of `0x4C` bytes, occupied byte `+0`, Body Type `+0x10`
and the explicit slider bounds 0–4. Its fixed DWORD `+0x44` counts from 30
through 179. A freely shared genuine PC SYSTEM save independently matches
**all 150 ordinals** and contains two occupied custom horses. No upstream
implementation or player records are included in this repository.

The supported envelope is exactly 244,952 bytes. The 1,036-byte outer header
contains a word checksum at `0x408` and seed at `0x40A`. The encrypted body
contains a 243,915-byte SYSTEM payload followed by its byte checksum. Decode
checks both checksums, revision `0x140828F1`, and every horse ordinal. Encoding
preserves the opened outer metadata and seed, updates the two integrity values,
and reparses the result. Unchanged roundtrips reproduce the original bytes.
Other editions, PS3 exports, `EmpireSave*.dat` and `QuickSave.dat` are separate
profiles and are rejected by this gameplay adapter.

## Coverage and remaining dependencies

| Mechanic | Status and exact limitation |
| --- | --- |
| Existing custom-horse Body Type | Manual 0–4; original occupied flag must be exactly 1 and opened value 0–4. |
| Head, neck, torso, legs, tail and muscle sliders | Bytes `+0x11..+0x16`; original occupied flag 1, ordinary menu type 0–7/model `0x96`–`0x9D`, and original member value 0–4 required. Choices are same-member positions witnessed in this original PC snapshot, never borrowed from PS3 or treated as full natural ranges. |
| Horse name, identity, type and model | Read-only. Menu type and actual model are distinct stored bytes; genuine records already contain mismatches, which are preserved. Name encoding and model/category prerequisites block writes. |
| Speed, power and four abilities | Read-only. The original report explicitly does not know speed/power maxima; natural category limits and ability-slot dependencies remain missing. |
| Horse creation, ownership and record IDs | No manufacture. Unoccupied or unusual flags are preserved; fixed row identities are validated. |
| Campaign materials, gold and troops | No writer. Candidate arrays lack native owner proof and PC resource order conflicts with console patch labels. A SYSTEM horse mapping does not qualify campaign resources. |
| Officer growth, merits, proficiencies, stratagems and equipment | No writer. Runtime/console leads do not establish exact native starting identities and progression dependencies. |
| Campaigns, scenarios, bonds and collections | No content unlock or story completion action. Exact flag/prerequisite mappings remain missing. |

## Validation

Procedural tests independently construct the envelope and exercise title/size,
both checksum failures, first/last ordinals, immutable snapshots, every writable
body position, unknown/unoccupied records, choice Max exclusion, backup,
restore and changed-source rejection. Optional private fixture variable
`DW8E_SYSTEM_COPY` tests same-byte native roundtrip and surgical edits of every
qualified occupied appearance field. The two ordinary native horses provide
four alternative Body Type choices per horse, one alternative per Head/Neck/Tail
member and single-position Torso/Leg/Muscle members: fourteen distinct surgical
native edits. No game executable is run. The original forum
author distinguished menu observation from battle validation; this project
likewise claims **no actual game-load or battle validation**.
