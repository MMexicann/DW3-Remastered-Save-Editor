# Tests

From the repository root with Python/Tkinter, install the source package and run:

```text
python -m pip install -e .
python -m unittest discover -s tests -v
```

Public rule and boundary tests run without a save. Private-fixture integration tests are skipped when the research copy is absent; no player save is distributed. See ../docs/VALIDATION.md for the completed checks.


The universal application adds `test_universal_app.py`, `test_origins_tools.py`,
`test_save_provider.py` and `test_universal_packaging.py`. Origins synthetic files
exercise opaque copy operations only; they are not real gameplay fixtures.
GUI tests need a display. The optional non-Windows crypto provider is in
`tools/requirements/dev.txt` (relative to the repository root). `python -m koei_editor --smoke-test` initializes the
selector and all registered interfaces. See ../docs/ORIGINS_FORMAT.md for Origins evidence.

`test_verified_editors.py` adds independently generated PC fixtures, published
cipher known answers, native checksums, corruption rejection, bounded scalar
edits, unchanged-byte round trips, backup/restore, source-change detection and
the explicit game/platform support gate. GUI tests exercise both new PC editing workflows.
To validate explicit copies of real samples without adding them to the source tree:

```powershell
$env:DW8XL_SAVE_COPY = 'D:\SaveCopies\dw8xl\save.dat'
$env:PW3_SAVE_COPY = 'D:\SaveCopies\pw3\OP3WIN0000.dat'
python -m unittest discover -s tests -p 'test_verified_editors.py' -v
```

These two sample tests skip when no path is supplied. They verify files, not
game loading. See ../docs/KOEI_FORMATS.md for public reference evidence and PC scope.

Game-mechanics tests cover the inferred/read-only PW3 progression model,
bounded-limit behavior, higher-value preservation and read-only inspection.
See ../docs/GAME_MECHANICS.md for source evidence and unresolved gameplay dependencies.

`test_dw4hyper_format.py` uses procedural fixtures alongside independent genuine-file qualification of
the native PC profile. To run its genuine-file check, set `DW4HYPER_SAVE_COPY` to an
unchanged copied native Hyper `save.dat` outside live save folders. The real-file
case skips without that path; procedural tests never imply genuine sample validation.

`test_p5s_codec.py` reproduces the attributed 32-byte PC stream vector and checks
read-only candidate spans; its research-only partial vector is distinct from complete native PC
qualification in `test_p5strikers_pc.py` and the independent review tests.
`test_dw8e_candidate_codec.py` exercises independent procedural envelope/checksum
arithmetic; the newer registered custom-horse editor and genuine
SystemSave checks live in `test_dw8e_horses.py`.

`test_dw4xl_format.py` covers the separate USA PS2 PSU parser with procedural
containers, directory-order/padding preservation and native inner checksum
validation. Its genuine-file test uses `DW4XL_PSU_COPY` and skips without an
explicit copied export. Console metadata and PC Hyper saves are rejected.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the mapping and copied-save workflow
and [AGENTS.md](../AGENTS.md) for project conventions.


Unreleased expansion tests cover DW5 Special, DW8 Empires custom horses, Hyrule
Warriors Legends, native PC Persona 5 Strikers, Wo Long and decrypted PS3 Ayesha
separately. Optional fixture environment variables are documented in their game
notes; private native bytes never enter the source tree. Independent audit tests
exercise field eligibility, malformed staging, all-field surgical edits and
preserved integrity/dependencies. Library search, named choices, text controls,
column sorting, Ctrl+C and existing editor sessions have real Tk regression
checks. Native-file tests are not actual edited game-load tests.

The Gust expansion adds format, scalar-contract, independent-audit and GUI tests
for original PC Sophie, original PC Ryza 2 and PC Fatal Frame II Remake. The GUI
checks use the registered editors and cover editing, Undo, Review Changes,
themes, Save As, backup and Restore. Optional genuine-file checks use copied
inputs outside live save folders:

| Environment variable | Copied input |
| --- | --- |
| `SOPHIE_SAVE_COPIES` | Folder of original Sophie extensionless `GAMEDATA*` snapshots |
| `SOPHIE_SAVE_COPY` | One original Sophie gameplay copy for the GUI check |
| `RYZA2_SAVE_COPY` | Original Ryza 2 PC gameplay `.dat` copy |
| `FF2_REMAKE_SYSTEM_COPY` / `FF2_REMAKE_GAMEPLAY_COPY` | Native Fatal Frame II Remake system/gameplay `.bin` copies |
| `FATAL_FRAME2_SYSTEM_COPY` | Native Fatal Frame II Remake system copy with positive Photo Points for the GUI check |
| `RORONA_DX_CANDIDATE_DIR` / `MERURU_DX_CANDIDATE_DIR` | Folders of native PC gameplay copies for read-only structural checks |

The Arland checks qualify layout and byte preservation, not integrity or writable
support. Procedural checks do not establish genuine-file or actual game loading.
