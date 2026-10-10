# Universal application architecture

`application.py` owns the single Tk root, selector, global appearance, shortcut
dispatch and application close flow. `launch.pyw` opens it. Registered workspaces
are cached in separate frames, so switching retains open documents, form values,
selection and pending changes. Shortcuts dispatch to the visible game only;
closing checks pending changes in hidden sessions too.

`game_registry.py` declares each game's ID, presentation, extension, editor module
and parser module. Registration is explicit, not inferred from file names. Add a
new entry with its dedicated modules and verified format support; PyInstaller
collects the registered modules explicitly. Include new metadata in
`build_windows.DATA` and the source manifest. No dynamically downloaded plugins
or external services are needed.

`GAMES` contains implemented platform-specific editors. Independent native-file
verification (`editing_verified`) is separate from cited published-format support
(`published_format`). The six PC entries and PS2 XL entry are filtered by their
explicit `platform`; switching platforms retains game sessions. `RESEARCH_TOOLS`
is currently empty; opaque Origins copy tools remain source-only. `ALL_ADAPTERS`
includes registered gameplay editors and any explicit research sessions for packaging and startup.
`support_catalog.py` checks independent verification flags against the registry. Research rows never create parsers.

Platforms with more than four entries use a scrollable three-column library.
The footer stays visible, focus reveals the selected card, and scrolling applies
only to the visible library. Scalar field groups refresh from the loaded document,
allowing adapters with dynamic occupied-record maps to use the same GUI.
Shared scalar search matches field labels, groups and record labels. It combines
with the selected group, preserves hidden pending edits and survives switching;
Max Visible applies only to displayed rows.

`preferences.py` stores only the chosen Light/Dark theme in the user's application
config directory, independently of game copies. The application owns persistence
for embedded sessions; standalone DW3 uses the same preference. Bounded, strict
reads fall back to Light, failed atomic replacements leave the editor usable,
and smoke/self-test workflows do not write settings.

`koei_codec.py` independently implements the verified DWORD and byte save ciphers.
`verified_editor.py` owns immutable documents, explicit layouts, native checksums,
bounded scalar changes and serialization for DW8 XL and Pirate Warriors 3 PC.
`dw8xl_editor.py` and `pw3_editor.py` are explicit adapters. `verified_gui.py` shares
the scalar editing workflow, retaining separate game sessions, Undo, review and
new-destination Save As. Format evidence and unsupported fields are documented
in `KOEI_FORMATS.md`. In-game load validation is tracked separately from file tests.
`game_knowledge.py` retains contributor reference data, with evidence
documented in `GAME_MECHANICS.md`. It has no application menu. PW3 level/XP inspection is read only; its sample
health model is not a progression writer. Bulk-limit helpers preserve higher
values already present in a copied save.

The shared scalar GUI retains its injected `backend` for game-specific data
presentation; core operations go through `adapter_contract.BoundScalarAdapter`.
It checks backend completeness, game/platform identity and extensions before
delegating to the dedicated reader/writer. `Game.scalar_backend` declares that
same module for registry reads and copied-save CLI tests, removing their lists of
individual scalar game IDs. Editor construction also checks declared identity,
backend/extension agreement and the launcher `EditorSession` contract. DW3 uses
only the session contract and keeps its established document/patch APIs.

`scalar_presentation.py` defines optional data-only inspector tables, field hints,
record labels and filename guidance. `musou_presentations.py` supplies DW8/PW3
views through their adapter classes; shared Tk code contains no branches for
those games. Other backends use their existing optional hooks or a basic field
table. The unregistered `adapter_template/` scaffold documents the format seams
and registration workflow, while `tests/scalar_contract.py` supplies behavioral
tests reused across existing scalar games. It never probes another game's parser.

`dw4hyper_editor.py` injects `dw4hyper_parser.py`: strict published size,
checksum and roster checks, bounded semantic item edits and surgical byte writes.
Its sample-qualified flag remains false; contributor documentation and copied-save
self-tests record that genuine PC fixture and in-game validation are pending. Availability
uses the published native PC editor as provenance, rather than claiming that a
procedural fixture is a real save. `dw4xl_parser.py` separately walks USA PS2 PSU
exports, validates BASLUS-20812 and its native checksum, and preserves wrapper
metadata/padding. Its adapter requests `.psu`; Hyper requests `.dat`. Distinct
game IDs prevent cross-platform backup restore and parser fallback.

The Sophie 2 adapter separately qualifies the published Steam 1.08 tagged layout.
Its MIT codec rebuilds compression and both integrity values while preserving
header, seed, opaque metadata, trailer and unrelated decoded data. Existing item
and equipment quality fields are discovered dynamically; alchemy EXP is excluded
from bulk Max. Source and provenance are recorded in ATELIER_SOPHIE2_FORMAT.md.
`katana_codec.py` implements source-only explicit PC envelope profiles, and
`nioh2_parser.py` exposes inspection only. Nioh/SOP writes stay disabled because
their native gameplay integrity is not mapped; no hidden checksum bypass or
gameplay library card is supplied. Wo Long codec checks do not supply a game map.

`p5s_codec.py` is a source-only research primitive with a published PC stream vector
and read-only structural inspection. `dw8e_candidate_codec.py` is a source-only
candidate for the independently classified Empires system/battle cipher layers.
Neither supplies gameplay fields, an application adapter or file I/O. A checksum
or stream-vector match cannot establish complete native title identity.

`appearance.py` contains the existing DW3 v1.1 palettes and theme behavior, shared
by all workspaces. Appearance changes leave document and pending-edit state alone.
Segoe UI is used on Windows, with a portable Helvetica fallback for GUI tests.

DW3 retains `gui.Editor` and all existing parsing/editing modules. Its constructor
accepts an optional container for embedding; default construction still supports
the existing tests. Its module version remains 1.1 while the universal application's
release version is 1.5. DW3's tagged Unreal schema, AES envelope, metadata,
edit limits, atomic save writer and audit reports remain game specific. Explicit
DW3 self-test and compatibility-test command lines continue to work.

Origins uses `origins_game_editor.py`, `origins_parser.py` and `origins_codec.py`.
The native Steam slot reader qualifies integrity, serialized block length and
revision 16, 17 or 29 before exposing Gold and base-game Skill Points; revision
29 also exposes its separate DLC Skill Point pool. `origins_progression.py` and
`origins_weapons.py` supply document-specific field definitions for formed bonds,
provincial peace and qualified existing weapon reinforcement. Training counts
and supported battle-clear history are editable but excluded from bulk Max;
history only permits clearing supported original 0/1 records and cannot reset
an opened clear. Active campaigns, endings and rewards remain separate.
Unmapped flags and records, original
seeds and revision metadata are preserved. `USER.dat` system envelopes
are rejected by the gameplay adapter. The shared GUI and registry-driven scalar
self-test provide staging, Undo, review, backup/restore and new-copy saving.
Native evidence, copied-file qualification and remaining in-game validation are
tracked separately in `ORIGINS_FORMAT.md` and `origins_evidence.json`.

`origins_gui.py` / `origins_editor.py` retain the earlier source-only opaque copy
tools and their immutable `OriginsCopy`; they are no longer registered library
editors. Their copy/comparison tests exercise those tools directly.

`save_safety.py` supplies the shared live-save/Steam Cloud path policy, including
resolved aliases. `copy_storage.py` implements immutable Origins snapshots,
hash manifests and restore to a new destination. DW3 retains its established
writer and backup naming convention. Windows uses native CNG for DW3 AES;
non-Windows development can optionally use `cryptography` without adding that
library to the Windows runtime.

Native adapters can supply a validator to qualify the same bounded backup bytes
that restore will atomically write; Origins uses this to reject changed system
or foreign-format backups even if the reread manifest and hash agree.

`build_windows.py` builds the universal entry point into one standalone Windows
EXE. `package_release.py` verifies the source manifest, bundle metadata, private
file exclusions, and personal-path protections before making local archives.
Manual workflow runs produce build artifacts. A matching version tag publishes
a new release; a `[release]` main commit can create the version tag at its tested
commit. Both paths require native Windows tests, executable startup, bundle privacy
checks and artifact hash validation. Existing releases are not overwritten.


## v1.5 native adapters and inspection

DW7 XL, WO3 Ultimate, Samurai Warriors 4 DX and Pirate Warriors 4 each have
separate immutable parsers and scalar editors. DW7 and SW4/PW4 use independently
qualified native envelope/checksum profiles; WO3 uses its native plaintext
serialized title/layout qualification. Equipment dependencies are evaluated on
existing records. Content unlocks and progression stay separate from stat/resource
Max actions; unknown and unusual values remain intact.

Inspector tables support independent token searches across all columns and keep
the original record order. Sophie 2 supplies occupied-inventory presentation;
DW8 supplies compatibility, affinity and read-only ally records. Restore adapters
qualify the exact bounded snapshot bytes passed to atomic_new.

Source-only research codecs do not register library cards. Packaging traverses
registered flat-module dependencies, including keyword registrations, and rejects
local packages until their paths have an explicit reviewed whitelist policy.
