# Agent guide

This repository builds the Universal Koei Tecmo Save Editor: one lightweight
Windows executable, separate game/platform parsers, and a shared Tkinter library.
Start with [CONTRIBUTING.md](CONTRIBUTING.md) for the mapping and contribution
workflow. Use the current code and [VALIDATION.md](VALIDATION.md) when assessing
what has actually been tested.

## Project map

- `application.py` / `launch.pyw`: one Tk root, game/platform selection, retained
  editing sessions, active-session shortcuts and close checks for hidden edits.
- `game_registry.py`: explicit `GAMES` registrations, platform, extension and
  adapter modules. Never probe another game's parser after a failure.
- DW3: `gui.py`, `save_parser.py`, `save_writer.py`, `save_codec.py` and its
  feature modules. Preserve the existing tagged schema and every DW3 feature;
  use its `Change`/patch workflow rather than replacing it with a scalar editor.
- DW8/PW3: `verified_editor.py`, `koei_codec.py`, `dw8xl_editor.py`,
  `pw3_editor.py`. Frozen documents and explicit `Field`/`Format` definitions.
- DW4 PC: `dw4hyper_parser.py` / `dw4hyper_editor.py`. DW4 PS2 USA PSU:
  `dw4xl_parser.py` / `dw4xl_editor.py`. Their containers and identities differ.
- `verified_gui.py`: injected-backend scalar editor, staged edits, batch Undo,
  review, backups and Save As. `appearance.py` shares the existing themes.
- `save_safety.py` / `copy_storage.py`: resolved-path restrictions, immutable
  snapshots, game/hash identity and atomic writes to new destinations.
- `build_windows.py`, `package_release.py`, `refresh_manifest.py`: standalone
  build and manifest-whitelisted public packaging.

## Editing conventions

Keep game logic out of the launcher and keep binary parsing out of Tk callbacks.
Reuse working modules, the standard library and the existing backend interface:
`read_save`, `fields_for`, `stage`, `review`, `serialize`, `save_as`, `backup`,
`restore`. DW3 retains its own established API. Changes remain separate from the
immutable original document; assigning the original value should unstage an edit.

Give each writable field a stable ID, offset, width/endianness, storage encoding,
label/group and evidence-based bounds. Dynamic fields must come from validated
existing records. Keep unknown IDs, bytes, bitfields, padding and unusual existing
values intact. Bulk Max must not lower higher existing values or use an integer's
storage ceiling as a gameplay maximum. Uncertain relationships belong in
read-only inspection until mapped; do not invent offsets or character labels.

Validate title/platform/revision, size, structure and all applicable checksums
before accepting a file. Re-encode from the original snapshot, preserve original
seeds/container metadata, and reparse the result. A no-edit operation must be
byte-exact. Recompute integrity only as part of a validated edit; do not silently
repair corrupt input. PSU offsets depend on directory entries, not one example's
absolute payload position.

Route file operations through the safety/storage helpers. Do not edit live game
or Steam Cloud data, bypass resolved aliases, or overwrite existing destinations
in the new scalar backends. Preserve automatic backups, source-change detection,
Undo, Review Changes, Save As and game-specific restore checks. Retain Mexican's
branding and shared Light/Dark behavior. Research-only work must not create
unsupported library cards or return removed research screens to the user flow.

## Tests and evidence

```text
python -m unittest discover -s tests -v
python -m unittest discover -s tests -p 'test_verified_editors.py' -v
python application.py --smoke-test
```

Run the focused suite for the changed format, then relevant regression/GUI and
packaging checks. GUI tests and smoke tests need Tk and a display. Non-Windows
DW3 development optionally uses `python -m pip install -r dev-requirements.txt`;
a Linux build is not a Windows EXE/CNG test.

Useful test generators are `synthetic_raw()` in
[tests/test_verified_editors.py](tests/test_verified_editors.py), `procedural_raw()`
in [tests/test_dw4hyper_format.py](tests/test_dw4hyper_format.py), and
`procedural_inner()` / `procedural_psu()` in
[tests/test_dw4xl_format.py](tests/test_dw4xl_format.py). They construct test data;
they are not independent save or in-game evidence. Include corruption, foreign
format rejection, targeted-byte preservation, bounds/dependencies, no-op
roundtrip, backups/restore and source preservation where relevant. Report passed,
failed and skipped tests separately. Private fixture environment variables and
copied-save self-tests are documented in [CONTRIBUTING.md](CONTRIBUTING.md).

## Build and packaging

On 64-bit Windows:

```powershell
python -m pip install -r build-requirements.txt
python package_release.py --verify-only
python build_windows.py
python package_release.py --verify-executable
```

Keep `VERSION` in `application.py` and `build_windows.py` consistent; the legacy
DW3 module version is separate. Add registered adapter imports and required
public metadata to the build inputs. Only reviewed paths belong in
`SOURCE_MANIFEST.json`; refresh hashes after source edits and explicitly add new
public files with `python refresh_manifest.py --add FILE...`. In shared work,
coordinate the final refresh with the person owning packaging. Never add saves,
game assets, account identifiers, private reports, external binaries or personal
paths. Do not weaken archive/privacy checks to make a build pass. See
[BUILDING.md](BUILDING.md) for executable smoke checks and local packaging.
