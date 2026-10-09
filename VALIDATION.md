# Universal development validation

Run the complete public suite and all-interface startup check from the repository root:

```text
python -m unittest discover -s tests -v
python application.py --smoke-test
python package_release.py --verify-only
python build_windows.py --print-config
```

On Windows, Python/Tkinter and native CNG are sufficient for source tests. On
non-Windows, install the optional AES development provider with
`python -m pip install -r dev-requirements.txt` and provide a graphical display
for Tk tests (for example, a locally installed Xvfb). Windows remains the target
for the standalone EXE and native CNG validation.

The current cloud run completed **486 tests: 236 passed, 250 skipped, no failures
or errors**. Skips are predominantly private-fixture integration tests, plus
Windows-only checks. Existing regressions were retained. New tests cover game
switching, hidden pending changes, active-game shortcut routing, theme retention,
DW3 synthetic edit/Undo/Review/Save As, Origins artifact identity, original-byte
preservation, backup hash/game validation, existing-file and destination-race
rejection, live-save aliases, copy comparisons, packaging metadata/privacy and
single-entry build configuration. AES ECB/CBC use published NIST vectors.

The run explicitly supplied both genuine public PC samples using
`DW8XL_SAVE_COPY` and `PW3_SAVE_COPY`. Without those paths, two additional sample
tests skip. New PC regressions cover published cipher vectors, native checksum
rejection, cross-game identity and revision checks, 485 core scalar fields and
supported existing DW8 weapon-attribute ranks,
unchanged ciphertext round trips, unrelated plaintext preservation, bounds,
backup/hash/game checks, read-only PW3 currency, concurrent source changes,
immutable destinations, full copied-save workflows and the verified PC support
gate. Tk workflows cover individual/bulk edits, Undo, Review, Save As, restore,
retained hidden edits, minimum-window accessibility and DW3 CLI argument order.

Mechanics regressions additionally cover read-only PW3 level/XP inspection,
the explicitly inferred health curve, rejection of unobserved zero bar/slot
capacities, preservation of higher existing values during bulk-limit actions,
read-only inspection callbacks and research notes that cannot activate parsers.
The second genuine low-progression PW3 PC save was validated separately through
the same copied-save workflow; both PC samples corroborate the observed model.

Independent review also decoded DW8 original and max-edited outputs with the
published converter and independently reconstructed the PW3 word cipher/checksum.
PW3 Beli editing was withheld because the published money patch changes two
fields whose relationship needs controlled PC samples. Character stat edits
remain enabled; both currency fields are preserved.

The real public Origins reference was separately inspected and copied through
backup, restore and Save Copy As. Every output matched its original bytes; an
unchanged comparison reported zero differences. This verifies copy operations,
not gameplay parsing or game loading. Origins gameplay edits remain unavailable.

The universal source GUI and existing DW3 GUI initialize under Xvfb. The rebuilt
local Linux one-file PyInstaller validation bundle initializes all six registered
interfaces, including the DW4 candidate, and passes archive checks: 390 entries,
14 matching metadata files and 266 Python modules. It was built with the system Python 3.13/Tk 8.6 after the hosted runtime
bundle failed strict privacy checks. The retained validation bundle omits the
optional non-Windows DW3 crypto provider. Bundled copied-save self-tests
validated the genuine DW8 and PW3 PC samples, checking 3,968 and 235 fields
respectively, original preservation, backups and restoration. The DW4 candidate
bundled workflow checked 331 fields on an explicitly procedural fixture, retaining
false sample-qualification and in-game-validation flags. Those workflows record that in-game loading is untested.
This is a development validation bundle, not a Windows executable. A native Windows build, its archive verification and packaged
source/fixture workflows must be checked on Windows before distribution. Private
DW3 integration checks still need the original explicitly supplied fixtures.

The latest pass includes 23 passing DW4 candidate format tests and one skipped
genuine-PC sample test, 19 DW8 Empires candidate arithmetic tests and 17 Persona 5
Strikers stream/structure tests. A published 32-byte PC screenshot is the P5S
known answer; constructed files do not establish full native integrity. GUI tests
exercise the injected DW4 backend, Undo/review/copy writes, retained session and
fully visible status/hints at the minimum window size. The user-authorized platform split makes source-backed DW4 Hyper and PS2 XL
selectable while their independent sample flags remain false. The current 123-entry source manifest
verifies; candidate implementations and the renewed research report are included
in reviewed public source inputs, while no sample save is included.

No code, branches, tags, releases or workflow runs were published.

# Contributor validation

Use separate save copies for development and testing. Private player saves and game files are not included in public downloads.

Run the automated suite on Windows:

```powershell
python -m unittest discover -s tests -v
```

Integration cases that require private fixtures skip when those fixtures are unavailable. Check the test output for failures and skips; do not describe skipped cases as passed.

To exercise the GUI against your own explicit save copy, choose a new or empty output directory:

```powershell
python gui.py --self-test "D:\SaveCopies\GameStatusData.sav" "D:\SaveCopies\EditorTest"
```

The workflow creates working copies and a `self-test-report.json`. Confirm the process exits successfully and the report records success and input preservation. The Windows executable supports the same arguments.

For changes to parsing or editing, check:

- Unchanged saves round-trip byte-for-byte.
- A targeted edit preserves unrelated records and properties.
- Resized strings/arrays regenerate enclosing sizes, envelope length and padding.
- Malformed input and invalid new values fail before writing.
- Backups, restore, pending-change rollback and Undo preserve the original copy.
- Explicit Huanglong Elixir balances remain the final count when combined with Musou clears; repeated clears do not award Elixirs twice.

Review each output's `.changes.json` for the actual byte patches and encrypted blocks. Keep detailed validation reports private; summarize reproducible failures when contributing a fix.

See [BUILDING.md](BUILDING.md) for executable build instructions and [SAVE_FORMAT.md](SAVE_FORMAT.md) for the supported structures and editing rules.

The final platform pass adds 23 passing PS2 XL procedural tests and one skipped
genuine export test. GUI integration exercises PSU opening, edits, Undo/review,
Save As with the correct extension, copied-save self-test and cross-platform
rejection. Platform filtering preserves PC sessions and defaults to Windows PC.
The library contains four PC editors and one PS2 editor; the two DW4 entries use
published-format provenance and retain false independent-sample flags.

## v1.2 preparation

The final v1.2 source suite passed 486 tests: 236 passed and 250 skipped, with
no failures or errors. Removed consumer research/mechanics controls and format
badges while preserving editing, safety and read-only inspection. Twenty-two
GUI tests exercise both platforms, themes, minimum-window layouts and complete
copy editing workflows. Source and Linux one-file startup checks pass. The v1.2 Linux archive contains
390 entries, 14 matching JSON files and 263 Python modules; privacy checks pass.
The contributor save-edit example was executed on a procedural DW8 fixture;
local documentation links were checked. Native Windows build and game loading
remain separate checks. New contributor and AI-agent guides are included in
the public source whitelist. The matching-version tag workflow gates publication
on native Windows tests, executable startup, archive privacy and artifact hashes.
