# Contributing

Contributions can improve an existing editor, document a format, or establish a
new game/platform mapping. Start with this workflow; AI coding agents should also
read [AGENTS.md](AGENTS.md). The application stays a single lightweight Windows
executable with dedicated game logic and a shared Tkinter interface.

## Run and understand the project

On Windows with Python and Tkinter:

```powershell
python application.py
python -m unittest discover -s tests -v
python application.py --smoke-test
```

Windows uses native CNG for DW3 encryption and needs no third-party runtime
package. Non-Windows development may install `dev-requirements.txt`; GUI work
requires a display. Read the parser and tests for the format you change.
[ARCHITECTURE.md](ARCHITECTURE.md), [SAVE_FORMAT.md](SAVE_FORMAT.md),
[KOEI_FORMATS.md](KOEI_FORMATS.md) and
[DW4_PLATFORM_FORMATS.md](DW4_PLATFORM_FORMATS.md) provide background;
[VALIDATION.md](VALIDATION.md) records evidence and remaining checks.

`application.py` owns the library and sessions, while `game_registry.py` declares
explicit adapters. `verified_gui.py` delegates scalar editing to an injected
backend. DW8/PW3 share `verified_editor.py`; DW4 Hyper and PS2 XL have separate
parsers. DW3 keeps its existing schema, feature modules and patch writer.

## Add a scalar adapter

Start with [adapter_template/INSTRUCTIONS.md](adapter_template/INSTRUCTIONS.md).
Its parser/editor/test scaffolds stay unregistered and reject unmapped files.
[adapter_contract.py](adapter_contract.py) defines `ScalarField`, `ScalarFormat`,
`ScalarDocument`, `ScalarBackend` and the common launcher `EditorSession` contract.
Existing game writers keep their own codec/container logic. The bound adapter
checks the selected game/platform and extension before delegating; it never tries
another backend after rejection. DW3 implements the launcher session contract
while retaining its tagged document and established patch workflow.

A scalar `Game` registration declares `scalar_backend='your_parser_module'`.
That enables the shared copied-save self-test and binds the backend to the exact
game/platform. The shared GUI's core operations use the same contract, preserving
staging, batch Undo, review, automatic backups, source-change checks and atomic
Save As to a new destination. Save As returns a freshly validated frozen document;
assigning an opened value unstages it. `SaveError` rejects invalid formats/values;
`FileExistsError` rejects an existing destination.

Use `maxable=False` for fields that permit deliberate individual edits but should
be excluded from bulk Max, such as historical counters or dependency-sensitive
choices. The backend's `limit_values` and `maximums` must honor that metadata,
preserve higher existing values and use validated original records to select fields.

Optional backend `record_label`, `field_hint` and `inspection_rows` hooks supply
data for the standard inspector. Richer read-only views subclass
`ScalarPresentation` in [scalar_presentation.py](scalar_presentation.py), returning
`InspectionTable` objects and field guidance. The game's editor declares its
`presentation_type`, summary and subtitle. Keep game-specific presentation in
adapter modules; adding a game should require no shared GUI or CLI ID branches.

Subclass [tests/scalar_contract.py](tests/scalar_contract.py)'s
`ScalarContractTests` alongside `unittest.TestCase`, providing `game_id` and
`fixture_bytes()`. Its shared checks exercise no-op round trips, immutable staged
changes and unstage, review, surgical payload edits, invalid fields/values,
cross-platform documents, backup/restore, existing destinations and source
changes. Declare `payload_integrity_offsets` only for mapped native integrity
stored inside the decoded payload. Add separate format-specific corruption and
dependency checks and record copied-native/in-game evidence honestly.

```powershell
python -m unittest tests.test_adapter_contract -v
python -m unittest tests.test_universal_app -v
python application.py --smoke-test
```

## Map a save format

1. Identify the exact game, platform, region, build and DLC. Record source/license
   evidence. A console export, asset decryptor or memory trainer is not proof of
   a PC disk format, and related editions can differ.
2. Work on reviewed copies outside live save and cloud folders. Record input
   hashes locally. Keep saves, account context and detailed private reports out
   of Git, public documents and release archives.
3. Identify the container, native title/revision markers, lengths, alignment,
   encoding/encryption layers and integrity coverage. Establish a byte-exact
   no-edit decode/encode roundtrip before gameplay writes.
4. Capture a before/after pair with one controlled game action and displayed
   values, plus an unchanged control. Use mechanics documentation to distinguish
   current values, lifetime totals, ownership, equipped references and derived
   stats; correlate those concepts with the actual serialized bytes.
5. Document each field's offset, width/endianness, stride/count, encoding, IDs,
   valid values, dependencies and source/version. Confirm boundaries against
   additional records/copies; do not promote plausible patterns to proven fields.
6. Implement surgical writes, recompute integrity, reparse, and compare decoded
   payloads. Only declared fields and their required integrity/size metadata may
   change. Preserve unknown bytes, original seeds and container entries/padding.
7. Test valid edits, invalid values, corruption/truncation, wrong editions,
   immutable input, backups/restore and Undo/review. Record actual game
   load/re-save separately, including the tested edition/build.

Use read-only inspection for uncertain fields. Research notes and candidate
codecs can be contributed without adding a game card. A library entry needs an
implemented editor with explicit platform provenance; record source-backed
format support separately from independent native-save validation. A stream
vector or a passing procedural test never substitutes for a complete real save.

## Building an edited save

Here, building a save means **modifying a validated copy and recomputing its
codec/container integrity**. It does not mean inventing a playable file from
zeros or treating a synthetic test fixture as a player's save.

For example, the existing DW8 backend stages a supported field, serializes in
memory, then writes through its guarded Save As workflow:

```python
from pathlib import Path
import verified_editor as backend

original = backend.read_save(Path(r'D:\SaveCopies\dw8-copy.dat'), 'dw8xl')
assert backend.serialize(original, {}) == original.raw
changes = backend.stage(original, {}, 'gold', 12345)
encoded = backend.serialize(original, changes)
reopened = backend.decode(encoded, 'dw8xl')
assert reopened.payload == backend.changed_payload(original, changes)
backend.save_as(original, changes, Path(r'D:\SaveCopies\dw8-edited.dat'))
```

The destination must be new. `save_as()` checks the opened source, preserves a
backup and uses atomic storage. Avoid direct `write_bytes()` on player data.
Reuse `verified_self_test.py` rather than building an alternate file-write path:

```powershell
python application.py --game dw8xl --self-test "D:\SaveCopies\dw8-copy.dat" "D:\SaveCopies\DW8Test"
```

Use a new/empty output directory. Require exit 0, `success: true`, input-hash
preservation and the reported backup/roundtrip checks. `--game pw3`,
`--game dw4hyper`, `--game dw4xl_ps2`, `--game atelier_sophie2` and `--game origins`
select their own registered scalar backends and extensions. Origins accepts
native slot copies; `USER.dat` system data is excluded.
DW3 uses `python application.py --self-test INPUT OUTPUT`. These reports do not
establish in-game loading or turn a procedural input into genuine-file evidence.

## Fixtures and focused tests

The public suite uses generated fixtures and published known-answer vectors.
Good examples are `synthetic_raw()` in
[tests/test_verified_editors.py](tests/test_verified_editors.py), `procedural_raw()`
in [tests/test_dw4hyper_format.py](tests/test_dw4hyper_format.py), and
`procedural_psu()` in [tests/test_dw4xl_format.py](tests/test_dw4xl_format.py).
Use distinctive unknown data so unintended zeroing becomes visible. Crypto
provider vectors are in [tests/test_save_provider.py](tests/test_save_provider.py).

Optional copied real saves are selected locally:

| Environment variable | Copied input |
| --- | --- |
| `DW8XL_SAVE_COPY` | Native PC DW8 XL `.dat` |
| `PW3_SAVE_COPY` | Native PC Pirate Warriors 3 `.dat` |
| `DW4HYPER_SAVE_COPY` | Native PC Hyper `save.dat` copy |
| `DW4XL_PSU_COPY` | USA PS2 XL `.psu` export |
| `SOPHIE2_SAVE_COPY` | Native Steam 1.08 Atelier Sophie 2 `data.dat` copy |
| `ORIGINS_SAVE_COPIES` | Folder of copied native Steam `SLOT*.dat` Origins saves |
| `NIOH2_SAVE_COPY` | PC Nioh 2 user `.bin` copy for read-only inspection |
| `KATANA_GOLDEN_DIR` | Locally reviewed upstream encrypted/decrypted reference-pair directory |
| `DW3_TEST_REPORTED_SAVE` | Explicit DW3 regression copy used by `test_save_variants.py` |

For example:

```powershell
$env:DW8XL_SAVE_COPY = 'D:\SaveCopies\dw8-copy.dat'
python -m unittest discover -s tests -p 'test_verified_editors.py' -v
```

Tests requiring a missing fixture skip. Count skips honestly. A real-file
roundtrip is stronger than a generator test, but still does not prove that the
edited file loads in-game. Do not commit fixture contents or private source URLs.
See [EXISTING_EDITORS.md](EXISTING_EDITORS.md) for source/licence checks and
[ATELIER_SOPHIE2_FORMAT.md](ATELIER_SOPHIE2_FORMAT.md) for the new tagged adapter.

## Submit code and build artifacts

Fork the repository, create a focused branch, and open a pull request against
`main`. Link supporting public evidence and describe the exact game/platform
and revisions affected. Use issues to share reproducible bugs or format findings
without attaching private saves or game files.

Keep patches focused and preserve existing features, themes and author branding.
Explain the problem, resulting behavior, format/evidence source, validation and
remaining uncertainty. Prefer meaningful regressions around byte preservation,
identity, integrity or dependencies over tests that merely repeat a constant.
Keep parsers independent from GUI callbacks and route user operations through
backups, staged changes, Undo, review and new-destination Save As.

Build on 64-bit Windows using [BUILDING.md](BUILDING.md). The key checks are:

```powershell
python -m pip install -r build-requirements.txt
python package_release.py --verify-only
python build_windows.py
python package_release.py --verify-executable
```

PyInstaller produces one standalone Windows EXE. A Linux validation bundle does
not test Windows CNG or constitute a Windows release. Add new public metadata to
`build_windows.DATA` and explicit adapter imports through the registry as needed.

Packaging uses an explicit source whitelist, not every file in the checkout.
After reviewing public changes, refresh existing hashes with
`python refresh_manifest.py`; include new public paths explicitly with
`python refresh_manifest.py --add FILE...`, then run the verifier. Preserve the
matching application/build/manifest version. Exclude game files, saves, account
identifiers, personal paths and third-party binaries; document dependency licenses
instead of weakening the packager. Build/package integrity and privacy checks
must pass before distributing assets.
