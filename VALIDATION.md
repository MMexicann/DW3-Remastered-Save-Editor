# v0.7 validation results

Validation date: 2026-10-05. Tests used four explicitly supplied private save
copies and new workspace copies. No live game save or Steam Cloud file was
opened or modified. The copied game executable was inspected read-only;
the game was not launched for this release.

## Completed checks

| Check | Result |
|---|---|
| Full automated regression suite | 209 tests passed; zero failures, errors or skips |
| Windows executable startup | Exit code 0 |
| Packaged full GUI workflow | 221 checks passed; exit code 0 |
| Packaged reported-save workflow, bodyguard-growth case | 21 checks passed; exit code 0 |
| Packaged reported-save workflow, expanded unique-array case | 21 checks passed; exit code 0 |
| Supplied research inputs | All four saves and copied executable retain their original SHA-256 |
| Privacy inspection | No personal identifiers in public source or executable, including decompressed bundled code |
| v0.7 edited save loaded in game | Awaiting player confirmation |

The owner reported in-game success with the older v0.3.1 release. That does not
confirm these new v0.7 controls in-game. Private fixtures and game files are
excluded from all public downloads. Integration cases skip when those private
fixtures are absent from a contributor's workspace.

## Compatibility and safety

Both newly reported encrypted saves round-trip byte-for-byte with no changes.
The tests cover zero, one, initial and expanded tagged-array counts, additional
reserved records, engine patch versions with the same serialization contract,
unknown proper-namespace gameplay enums and inconsistent existing profiles.
Untouched unfamiliar data is preserved. Unsupported edit profiles are view-only;
new values and references must pass verified editing rules.

Truncated arrays, count/payload mismatches, invalid bool encodings, duplicate
fields, malformed enum namespaces and unsupported serialization still fail.
Backups, hash manifests, malformed restores, concurrent changes, verified
temporary writes, atomic replacement and live/Cloud path blocks remain tested.

## Feature and GUI checks

- Ziluan's fourth/fifth acquisition uses native slots 102/103 and constructor
  padding; existing 104-record unique arrays and fused records are preserved.
- Pending acquisition, normal rolls and elements can be combined in one save.
  Short or unfamiliar skill arrays clear/disable unsupported GUI controls.
- Gallery collection adds 176 playable first-acquisition entries, preserving
  existing snapshots and ordinary inventory. Bodyguard gallery edits coexist.
- Tactics changes only Lu Bu/Sun Shangxiang's verified costume flag. Retro DLC
  flags and story progress stay unchanged.
- All three side-story availability IDs and six Free Mode stages are covered;
  missing optional availability properties can be inserted safely. Stage
  completion flags stay unchanged.
- Explicit Musou clears use 39 real routes, with 7/10-stage progress and
  idempotent three-Elixir first-clear rewards capped at 999. Active runs and
  timestamps stay unchanged. Officers without routes are excluded.
- Existing bodyguard Bow growth above the current allocation gate opens and
  displays derived stats correctly. New allocation and Merit decreases still
  require valid final growth. Unmapped profiles remain view-only.
- Grind presets preserve Musou completion. Undo, discard, review, Save As,
  backups and input-copy preservation pass in the bundled application.

## Bytes and integrity

A scalar edit changes its parsed numeric field and corresponding AES blocks.
Record acquisition, gallery insertion and optional story-array insertion change
only their targeted records/properties plus enclosing size and envelope fields.
The writer rebuilds padding, encrypts and reparses before any file replacement.
Every output's `.changes.json` lists actual plaintext offsets, before/after
bytes, size updates and changed encrypted blocks. No offsets are guessed.

Unknown top-level properties, reserved records and unrelated payloads are
compared byte-for-byte across combined changes and relocation. Repeated
parse/serialize of edited saves is exact. The AES codec also passes an independent
NIST known-answer test.

The checked `DW3RemasteredSaveEditor-v0.7.exe` SHA-256 is:

```text
0a8c5ddae38644f60eb5ae7f103e0a5dc342afe105ad586853edd556dbee4553
```

Thanks to OrdinalSumo, Domenikus and revidwi for reproducible reports and
requests, and to GoooD1 and austinkun for earlier compatibility and weapon
attribute feedback. See [SAVE_COMPATIBILITY.md](SAVE_COMPATIBILITY.md) for
structural evidence and supported limits.
