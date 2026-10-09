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
(`published_format`). The four PC entries and PS2 XL entry are filtered by their
explicit `platform`; switching platforms retains game sessions. `RESEARCH_TOOLS`
contains Origins copy tools. `ALL_ADAPTERS` includes both for packaging and startup.
`support_catalog.py` checks independent verification flags against the registry. Research rows never create parsers.

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

The shared scalar GUI calls its injected `backend`, with optional record labels,
field hints and read-only inspection rows. It does not fall back to another game's
parser. `dw4hyper_editor.py` injects `dw4hyper_parser.py`: strict published size,
checksum and roster checks, bounded semantic item edits and surgical byte writes.
Its sample-qualified flag remains false; contributor documentation and copied-save
self-tests record that genuine PC fixture and in-game validation are pending. Availability
uses the published native PC editor as provenance, rather than claiming that a
procedural fixture is a real save. `dw4xl_parser.py` separately walks USA PS2 PSU
exports, validates BASLUS-20812 and its native checksum, and preserves wrapper
metadata/padding. Its adapter requests `.psu`; Hyper requests `.dat`. Distinct
game IDs prevent cross-platform backup restore and parser fallback.

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
release version is 1.2. DW3's tagged Unreal schema, AES envelope, metadata,
edit limits, atomic save writer and audit reports remain game specific. Explicit
DW3 self-test and compatibility-test command lines continue to work.

Origins uses `origins_gui.py` and `origins_editor.py`, with evidence separate in
`origins_evidence.json`. `OriginsCopy` is an immutable opaque artifact; it has no
decoded gameplay fields or edit capabilities. Unknown artifacts remain visibly
unverified, and gameplay serialization is unavailable. Adding a serializer needs
the evidence and acceptance checks in `ORIGINS_FORMAT.md`.

`save_safety.py` supplies the shared live-save/Steam Cloud path policy, including
resolved aliases. `copy_storage.py` implements immutable Origins snapshots,
hash manifests and restore to a new destination. DW3 retains its established
writer and backup naming convention. Windows uses native CNG for DW3 AES;
non-Windows development can optionally use `cryptography` without adding that
library to the Windows runtime.

`build_windows.py` builds the universal entry point into one standalone Windows
EXE. `package_release.py` verifies the source manifest, bundle metadata, private
file exclusions, and personal-path protections before making local archives.
Manual workflow runs produce build artifacts. A matching version tag publishes
a new release only after native Windows tests, executable startup, bundle privacy
checks and artifact hash validation succeed. Existing releases are not overwritten.
