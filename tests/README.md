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

Console expansion tests keep US PS3 WO3 Ultimate (`test_wo3u_ps3.py`) separate
from PC Definitive, and US PS3 DW8 Empires SYSTEM (`test_dw8e_ps3_horses.py`,
`test_dw8e_ps3_gui.py`) separate from PC and console campaigns. Genuine copies
use `WO3U_PS3_US_COPIES` and `DW8E_PS3_SYSTEM_COPY`, with original `PARAM.SFO`
beside each input. Actual Tk workflows and the registered copied-save self-test
cover private opaque metadata propagation, backups, Undo/Review and restore.
`test_console_expansion_registry.py` verifies platform separation and that
unqualified candidates cannot create library cards.

Strikeforce and Xbox SW2 tests are read-only native observations, not editing
qualification. Their optional inputs are `STRIKEFORCE_PS3_US_COPY`,
`STRIKEFORCE_PS3_US_SECOND_COPY` and `SW2_XBOX360_EXPORT_COPY`. SW2 HD's four
procedural probe tests demonstrate partial-sum collisions and uncovered bytes;
no genuine HD file is claimed. See each console checklist for exact blockers.

Additional Musou PC tests cover the separately qualified SW4-II revision
`0x31A4` adapter and unregistered read-only Spirit of Sanada outer framing.
Set `SW4II_SAVE_COPY` and optionally `SW4II_SECOND_SAVE_COPY` to separate native
gameplay copies; set `SANADA_PC_SAVE_COPIES` to a copied directory containing
`SAVEDATA0000.dat`, `SAVEDATA0001.dat` and `SYSDATA.dat`. Genuine-file cases skip
when those inputs are absent. `test_sw4ii_gui.py` uses the genuine copy when
provided, otherwise a procedural fixture, and requires Tk with a display.
See [SW4-II](../docs/SW4II_FORMAT.md) and
[Sanada](../docs/SANADA_PC_RESEARCH.md) for exact qualifications and blockers.
