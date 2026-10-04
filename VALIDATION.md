# v0.3.1 validation results

Validation date: 2026-10-04. All save tests used the supplied workspace copy
or working copies created from it. No live saves or Steam Cloud files were
opened or modified. Installed game data was inspected read-only; the game
was not launched.

## Completed checks

| Check | Result |
|---|---|
| Full automated suite | 112 tests passed, including 18 new review regression tests; zero failures, errors or skips |
| Prior bodyguard GUI review (v0.2 behavior retained) | 29 checks passed |
| Independent weapon-roll integration suite | 22 methods passed, included in the full suite |
| Prior bodyguard inventory/cache/equipment audit | All 15 definitions; round trips passed; nine invalid requests rejected |
| Hidden source-app end-to-end workflow | 216 assertions passed |
| Windows executable startup | Exit code 0 |
| Windows executable end-to-end workflow | Exit code 0; 216 assertions passed; packaged runtime confirmed |
| Original uploaded fixture | SHA-256 unchanged |
| Edited save loaded in game | Not performed |

The original 3,334,240-byte fixture SHA-256 remained:

```text
02dd42241b70cd580c3f78e42fd4f89b3d8b832ad1230c49e5c8d19bfdf169c2
```

The checked `DW3RemasteredSaveEditor-v0.3.1.exe` SHA-256 is:

```text
634f010374c50c0fd46751354c2e94818c066606643c4e65dd232b32da952870
```

The hidden GUI checks exercised opening, automatic backups, officer/item
editing, custom officer weapon rolls and duplicate rejection, selected/all
roll maxima, pending unique acquisition plus stock-specific values, empty
weapon searches, growth budgets and four presets, legal Merit decreases, bodyguard
items/weapons, per-copy bonus choices, explicit equipment changes, undo,
discard, both global presets, Save As, confirmed replacement, restore and a
simulated post-save reopen warning. Expected validation errors were checked
and cleared; no unexpected save errors occurred.

The executable tests used a normal Windows user token with temporary
extraction files confined to the workspace. A restricted test token cannot
access the one-file bootloader's Windows extraction ACL. No game/save-folder
permissions were changed. Normal use requires no administrator access.

## Bytes and integrity

Unchanged decrypt/parse/serialize/encrypt reproduces the original encrypted
file exactly. AES-256-ECB also passes the independent NIST known-answer test.

The first officer's Merit 99,999 to 99,998 changes its little-endian Int32
from `9f 86 01 00` to `9e 86 01 00`. Only decrypted byte 2559 and encrypted
AES block 159 change. BG Tortoise Amulet value 17 to 18 changes its Int32
from `11 00 00 00` to `12 00 00 00`: only decrypted byte 3,312,997 and
encrypted AES block 207,062 change. These offsets describe the original
fixture; the editor locates each field by parsing, rather than hard-coding
those offsets. Neither scalar edit changes sizes or padding.
Each saved copy's `.changes.json` reports actual offsets, before/after bytes,
parent sizes, envelope sizes and encrypted blocks.

Ownership strings differ in length. Acquisition rebuilds the changed
FStrings, enclosing property sizes, envelope length and zero padding.
Untouched fields are compared at newly parsed positions. Combined edits
preserve every unrelated top-level region and reserialize byte-identically.

Bodyguard growth modifies only Merit/levels plus the proven playable-officer
`MemCnt` dependency when Count changes. Smaller chosen counts are preserved;
counts above a lowered capacity are clamped. All reserved officer records,
extra five weapon references, team appearances/types, bodyguard-Musou item
selections and story completion remain unchanged.

The fixture owns 21 bodyguard weapon copies representing seven definitions.
Unlocking the missing eight definitions uses free slots 21-28 and preserves
all 21 original copies. First-acquisition collection caches are populated
only when missing. Explicit Max Bonuses changes inventory bonus records
while preserving identities, DataIDs, timestamps and existing caches.

## v0.3.1 regression review

All 18 new review methods pass. They cover reserved native bonus IDs,
redundant unique acquisition with inconsistent references, transactional GUI
opening, truncated scalar payloads, nested reader boundaries, changed and
newly appearing destinations, changes during temporary-file verification,
incomplete backups, malformed/oversized manifests, metadata aliases, reserved
Windows file names and invalid ordinary item identities/rolls.

The source and packaged GUI checks also exercise failed opening without losing
pending edits, a concurrent overwrite refusal and malformed-manifest restore.
See [BUG_REVIEW.md](BUG_REVIEW.md) for the findings, changes and limits.

## Failure-path review

The writer validates final combined allocation and equipment state, rather
than rejecting legitimate combinations based on request order. Invalid
growth, over-cap rolls, wrong item identities, unowned equipped items,
blank/wrong-family weapon references, wrong DataIDs and noncanonical item
values are refused. Source saves with unsupported bodyguard bonuses
(discrete/tier/family limits, duplicate IDs, rare IDs, more than three bonuses
or empty upgraded weapons) are refused. Original no-bonus tier-one weapons
remain valid. The GUI requires at least one custom bonus.

Removing an item referenced by any of the 50 officer bodyguard-Musou records
is refused; reserved records are protected without rewriting them. Full
weapon inventories are refused without replacing existing weapons.

Existing backup, atomic-write and path-safety tests remain passing. Injected
backup, audit-report and final replacement failures preserve destinations
and clean prepared temporary files/reports. Corrupt backups, unsupported
versions, forbidden live/Cloud paths, stale documents/sources, wrong output
extensions, invalid indexes/types and missing unique slots are refused.

## Officer weapon edit evidence

Regular copy36's first normal bonus changes from10to1 as Int32
`0a 00 00 00` to `01 00 00 00`. Only plaintext byte224,858 and
encrypted AES block14,053 change. These are fixture offsets found
by parsing, not hard-coded editor locations. All other tags/sizes/padding
remain identical for this scalar edit.

Custom normal identity replacement and new slots reparse after FString size
changes. Max Existing preserves all nine slot identities/positions, including
the rare bonus at slot6. Separate tests preserve WeaponID/ID, Attr, DataID,
GetTime, every PC weapon equipment reference and collection-cache bytes.
Pending unique acquisition plus bonus editing writes final inventory skills
once and initializes only a missing stock acquisition cache.

Unique stock Attack43 is limited to Volcano Staff. Ordinary weapons refuse
43, and unavailable values below that number remain excluded. New malformed
slot counts, unknown enums, oversized scalar fields, duplicate bonuses,
invalid references and changed rare slots are rejected. Backup replacement
and restore passed; invalid edits leave existing destinations/audits unchanged.

## Remaining limits

Native evidence and structural tests support the implemented edits. These
checks do not establish in-game acceptance or achievement/Cloud behavior.
Material-consuming fusion, element/rare changes, bodyguard model/type changes,
direct title/rank edits,
story completion editing, missing unique-slot expansion and different save
versions remain unsupported. Stat previews show growth bases before
equipment and battle modifiers. See [SAVE_FORMAT.md](SAVE_FORMAT.md) and
[BODYGUARDS.md](BODYGUARDS.md) and [WEAPON_ROLLS.md](WEAPON_ROLLS.md)
for evidence and boundaries.
