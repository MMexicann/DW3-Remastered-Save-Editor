# v0.3.1 code review and bug fixes

Reviewed on 2026-10-04. This review covered the codec, bounded Unreal parser,
officer/item/weapon/bodyguard edit planners, GUI callbacks, backup/restore,
atomic output and release tooling. Every save test used the supplied workspace
copy or an additional working copy. No live save or Steam Cloud file was read
or changed. Prior editor versions and release artifacts are retained.

## Reproduced findings

| Finding | Corrected behavior | Verification |
|---|---|---|
| A reserved native officer bonus ID could abort the Weapons tab | Reserved IDs remain visible; affected copies are read-only and round-trip unchanged | Synthetic ID43, GUI opening, exact unchanged ciphertext, edit refusal |
| A redundant unlock request bypassed checks on an already-owned unique weapon | Only genuinely new acquisitions use synthesized identity; owned references are always checked | Wrong DataID plus repeated acquisition and bonus request refused |
| A file changed during serialization could be overwritten with an obsolete backup | Existing destinations are compared with backed-up bytes immediately before replacement | Changed during serialization and temp verification: competing bytes preserved, no save/audit committed |
| A new destination appearing during saving could be overwritten without a backup | A destination initially absent uses no-overwrite publication | Concurrently created file preserved |
| A display failure after opening a new save discarded prior pending edits | Opening rolls back document, backup, edits and history on failure | Injected GUI refresh failure preserves the previous state |
| Truncated scalar data could escape as a low-level unpack error | Reader bounds include the physical buffer and enclosing payload; short plaintext is rejected | Aligned truncated save raises SaveError; primitive/parser bounds checked |
| A failed backup manifest left an unusable orphan save | Only the new incomplete backup is removed; existing backups remain | Injected manifest failure leaves previous backup intact |
| Backup restore accepted invalid manifest shapes and unbounded manifest reads | Object schema and 4KiB manifest limit enforced; save reads bounded to 16MiB | List, malformed JSON and oversized manifest create no output |
| Resolved metadata aliases and special Windows names escaped path validation | Check lexical and resolved metadata names, exact protected directories, device names and alternate streams | Mocked aliases refused before access; reserved names tested without opening them |
| Ordinary item records could accept impossible stored values | Registered slots require correct identity, verified normal ranges, zero unowned/rare values and no guard ID | Invalid identity, negative/over-cap values, unowned nonzero value and rare numeric value refused |

Also corrected the README title's text encoding and excluded all private test
run directories from version control. The editor's supported features remain
the same; this release focuses on correctness and failure handling.

## Completed verification

- Full suite: **112 tests passed**, zero failures/errors/skips. This includes
  **18 new regression methods**, with additional boundary subcases.
- Source GUI: **216 checks passed**.
- Rebuilt standalone Windows executable: startup passed and **216 checks passed**.
- The original supplied save's SHA-256 remained unchanged:
  `02dd42241b70cd580c3f78e42fd4f89b3d8b832ad1230c49e5c8d19bfdf169c2`.
- Original unchanged serialization remains byte-identical; targeted edits
  preserve unrelated fields, dependencies and completion flags.
- The new Windows/source archives are built from an explicit allowlist and
  checked separately for integrity, manifests and personal paths.

See [VALIDATION.md](VALIDATION.md) for byte-level examples and executable hash.
Automated tests are included in the public source, with private-fixture checks
skipped when that fixture is absent; your save is not distributed.

## Remaining limits

No edited save has been loaded in the game. Structural checks and round trips
do not establish in-game acceptance, or prove an absence of every possible bug.
Other save versions/layouts are refused rather than guessed. Unknown weapon
bonus rules remain read-only; unknown nonedited regions are preserved.

The overwrite recheck protects against changes observed before commit. It is
an optimistic check, not a filesystem-wide lock against every possible
simultaneous rename. Close other editors while replacing a working copy;
Save As and intact backups remain the preferred workflow. Live game and Steam
Cloud locations are blocked by the editor.
