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
not gameplay parsing or game loading. Those earlier checks covered opaque copies only. Native Origins editing is now
qualified separately as described below.

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

## v1.3 existing-editor integration

The final source run passed **544 tests: 289 passed, 255 skipped, no failures
or errors**, with DW8/PW3 copies, the published native Nioh 2 user copy and all
five upstream Katana encrypted/decrypted pairs explicitly selected. Missing
private DW3, genuine DW4/Sophie2 and other copied-native cases remain skipped.

Sophie 2's focused suite passed 19 tests, with its one real-copy case skipped.
Frozen upstream vectors and a separately loaded upstream model establish codec
and field agreement on procedural data, not independent game-save qualification.
Peer review reproduced and fixed opaque encrypted-footer loss, scalar range
crossing into equipment, extra palette data and live-backup-directory aliases.
The copied-save self-test checks 14 procedural fields, changes 10 supported
quality values, preserves higher qualities and both EXP fields, verifies all
integrity/payload expectations, and restores original bytes. Its sample/in-game
flags remain false. Twenty-four GUI tests cover retained sessions, dynamic
field groups, quality/EXP edits, Undo, review, inspection, Save As, restore and
scroll/focus accessibility in both themes at the minimum window size.

Katana source-only tests passed 17 with four copied-native cases skipped. Full
Nioh1/2/3 and SOP cipher pairs match in both directions with original header key
material retained; all gameplay edits are rejected where integrity is unmapped.
Wo Long's dummy demonstrates CBC only and is rejected for malformed JSON and
stale native checksums. Independent literal-C checksum/custom-cipher vectors and
procedural corruption/identity tests pass. Nioh 2's 14 inspection tests pass,
including its genuine 2,715,432-byte PC user fixture, with active runtime
integrity flags unchanged. These sources add no selectable gameplay editor.

Source and Linux bundled startup checks pass. The validation archive has 393
entries, 14 exact JSON files, 266 Python modules and three exact embedded
notices; privacy checks pass. The bundled procedural Sophie2 copied-save
workflow also passes all 14 fields and original/backup restoration checks.
The standalone build embeds the
Sophie 2 MIT notice and checks its exact bytes as well as public JSON metadata;
saves/account data and third-party binaries remain excluded. Native Windows
release validation runs through the matching-tag workflow. No in-game reload
was performed in this cloud environment. See EXISTING_EDITORS.md for exact source
licences, platform distinctions and download failures.

## v1.4 Origins and adapter contracts

Origins native envelope checks and serializer lengths were independently traced
in the installed Steam executable. All nine copied slots, spanning revisions
16, 17 and 29, decrypt with matching checksums and re-encrypt unchanged byte for
byte. Resources, existing bonds, provincial peace, catalogue-qualified weapon
reinforcement and persistent battle clear history have native serializer and
limit evidence in ORIGINS_FORMAT.md. The DLC point field is absent from older
profiles. Independent tests cover exact revision offsets, empty/reserved/special
weapon exclusion, monotonic manual history and training/history exclusion from
Max; history edits preserve active story and reward state.

Procedural and copied-file tests cover unchanged round trips, field-only plaintext
and ciphertext changes, legitimate maxima, preserved higher existing balances,
malformed checksums and layouts, forged documents, wrong-game selection, backup
restore and source/destination safety. Shared adapter contract and Tk workflow
regressions cover the existing editors and the new Origins interface. Native
Origins edited saves have not been loaded into the game during this task.

Theme regression tests restart both the universal application and standalone DW3
with isolated preference files, including actual appearance selector callbacks,
corrupt settings, failed atomic writes and no-write smoke mode. DW3 weapon label
tests verify stat names in selectors and review while item tabs, numeric IDs and
the opened save remain unchanged.
