# Dynasty Warriors: Origins — evidence and remaining work

The universal application has a dedicated Origins workspace. **Gameplay editing
is not implemented:** encryption, authentication/checksum rules, the save schema,
and safe gameplay limits remain unverified. Copying, backup/restore, inspection,
and byte comparison are functional. These operations preserve the original bytes.

## Public evidence inspected

| Source | What it establishes | What it does not establish |
| --- | --- | --- |
| [VdustR/game-save-dwo-d4h](https://github.com/VdustR/game-save-dwo-d4h), commit `b5e853eec865417edf473eb9b39330b1cf0f74e8` | Publisher identifies `SLOT0008.dat` as an Origins Steam Dream of the 4 Heroes DLC save; README documents `%LOCALAPPDATA%\KoeiTecmo\Dynasty Warriors Origins\Savedata\<steam_user_id>\` | Native save schema, executable version, editable fields, integrity rules, independent game-load validation |
| [Kelebek1/dwo](https://github.com/Kelebek1/dwo), commit `5de9b3e615691f2280ceeb6100416275adfbe75c` | Origins LINKDATA asset and stage-script research | A save-specific decoder or save offsets |

The public slot file is 2,561,636 bytes, SHA-256
`1e0e1668c6398bc9c67d47d5510833c30d0720e2eddb2c11795bfa49ce4ac758`.
It has no visible GVAS signature. It was inspected outside the application source
tree. It is not included in source archives or the executable.

AES hypotheses using the published asset key and the existing DW3 key were
checked against this file at offsets 0, 4, and 16, using ECB and the asset CBC IV.
They produced no recognizable save structure (output byte entropy remained near
8 bits/byte). This does not establish an alternative cipher, nor prove every
possible use of those keys impossible. The application does not use them for
Origins, and does not infer offsets from encrypted byte differences.

`origins_evidence.json` contains public reference metadata only. A fingerprint
match means **exact equality to that published artifact**, not checksum validation
or an editable save format. Unknown files can be inspected as unverified artifacts;
the gameplay parser rejects them. All Origins gameplay serialization is rejected.
Changing an extension or choosing a game never selects a different parser as a
fallback.

## Needed samples

Use separate copies from the **same Steam game version and DLC configuration**.
Record version/build, whether DLC is installed, slot type, and the exact values
displayed in game. Keep saves and detailed reports private.

| Sample pair | Change between copies | Evidence needed before enabling edits |
| --- | --- | --- |
| Control A/B | Save twice without intentional gameplay changes | Timestamp, randomness, account binding and other background changes |
| Money A/B | Earn or spend an exact documented amount | Resource encoding, integrity rules, legal range |
| Skill points A/B | Gain/spend a known point amount | Counter and spent/unspent dependencies |
| Level/progression A/B | One known level or experience change | XP thresholds, derived stats and rank dependencies |
| Proficiency A/B | Increase one weapon family's proficiency | Family identities, progression representation and caps |
| Weapons/equipment A/B | Acquire or equip one known item | Inventory IDs, slot references, attributes and bounds |
| Gems A/B | Acquire/equip one gem or change one level | Inventory/equipment linkage and upgrade limits |
| Horses A/B | Acquire/equip one horse or gain one level | Stable identities, equipment reference and progression |
| Battle Arts A/B | Unlock/equip one art | Ownership and equipped-slot dependencies |
| Bonds A/B | One recorded bond increase | Character IDs, thresholds and event flags |
| Story/unlocks A/B | Complete one known mission/route | Completion, unlock, reward and replay dependencies |

A fresh early-game slot, a mid-game slot, and an end-game slot are also useful.
One completed DLC save alone cannot map these relationships. If controlled pairs
remain opaque, a verified public save decoder or locally supplied game executable
with the native save reader/writer will be needed to establish encryption and
integrity. Never transplant DW3's schema or a trainer's memory addresses into a
save file.

Before enabling any field: verify identity and structure, exact no-edit round trip,
localized edit preservation, rejection of malformed input, safe range and bulk
behavior, and a successful game load of an explicitly edited test copy. Story
editing additionally needs verification of dependent flags and rewards.

## Functional copy tools

Open explicitly selected `.dat` copies outside live/Steam Cloud folders. The
workspace creates an automatic hash-verified backup and identifies the known
public reference when applicable. Save Copy As and Restore create new files and
refuse existing destinations, including races. Comparison shows byte counts and
up to 128 changed regions; totals include all regions. Reports use
`.changes.json`, contain fingerprints and sizes but no file payloads or absolute
paths, and are excluded by the repository's privacy rules.
