# Universal development validation

## Independent development-branch validation — 2026-10-11

This review started at remote `codex/prepare-next-update`, commit
`f7ca0121d4e98a7caf09f8545a5a7413a0b8dc3e`, on
`codex/independent-validation`. Parallel audits reviewed all 28 registered
adapters. Results below are from this review, not inherited qualification claims.
The final complete suite ran **1,136 tests in 356.160 seconds: 824 passed,
312 skipped, no failures or errors**, using Python 3.12 and actual Tk on a virtual
Xorg display. Qualified copied-native inputs were explicitly configured for all
six new editors, Wii U Hyrule, Age of Calamity and Pirate Warriors 3.
Skips require unavailable private fixtures, except one Windows filename-rule
check; two fixture-dependent GUI skips also require Windows. There were no
display-only skips. A prior full run had 1,123 tests, two stale GUI expectation
failures and 328 skips; those expectations were corrected before the final run.

The [non-publishing Windows run](https://github.com/MMexicann/Universal-Koei-Tecmo-Save-Editor/actions/runs/38094440495)
was dispatched with `publish=false` at application/test commit `a969687`.
It was still running when this report was finalized; the draft PR tracks its
result. The following commit updates only this report and its manifest hash.

### Confirmed defects and narrow fixes

- Registered scalar Stage, limits and Max could retain invalid prior edits or
  normalize them into valid values. The bound adapter now checks complete pending
  mappings, dynamic field identities and values before delegation. DW8/PW3 and
  Origins also enforce these checks in their direct backend APIs. Exact-type
  unusual opened values remain preservable and removable. Cached immutable
  validation and prevalidated Max targets avoid repeated native decryption.
- DW8/PW3 exposed fields from forged payload/raw/seed snapshots. Field lookup now
  qualifies the immutable snapshot before exposing writable fields.
- Legends rejected unchanged above-limit rupees/stars in pending edits. Original
  equality now precedes edit-bound validation without accepting booleans/floats.
- DW5 Special and DW8 Empires leaked `TypeError` for malformed field IDs. Those
  requests now raise `SaveError` without changing pending edits or source bytes.
- Wo Long's inspector crashed on an unmapped optional companion value such as
  `null`, an integer or a boolean. Only qualified companion arrays are inspected;
  other optional data survives unchanged.
- Inspector filtering reset the selected sort order. Filtering now reapplies
  that order; the regression also checks selection retention and visible-row copy.

The new adversarial regressions failed before these fixes. Two existing GUI
tests also had stale expectations: DW7 Undo restores the opened input, and
All-Stars has three supported inspector groups. Corrected tests retain their
original save/backup and byte-preservation assertions.

### Procedural and GUI checks

Independent generated inputs for the 21 older scalar adapters passed byte-exact
no-op roundtrips, one targeted edit per adapter, unstage, immutable originals,
Max exclusions and preservation of higher originals. All 420 ordered foreign
scalar-fixture combinations rejected. DW3 separately passed a surgical officer
skill-point edit and rejected 21 foreign fixtures, three damaged encrypted
inputs and two oversized-array counts. Sophie 2's documented optional zero
trailer permits changing its length; that was not classified as corruption.

Focused results (test totals include skips):

| Check | Tests | Passed | Skipped |
| --- | ---: | ---: | ---: |
| DW5 Special, DW8E, Legends, genuine copies and actual Tk | 55 | 55 | 0 |
| Bound pending-edit, scalar contract and shared pending regressions | 31 | 31 | 0 |
| Shared DW8/PW3 contract, snapshot, affinity and format regression | 79 | 74 | 5 |
| Origins pending, parser, snapshot, progression and weapons | 29 | 28 | 1 |
| Storage/source/restore adversarial regressions | 15 | 15 | 0 |
| Actual Tk library, named choices, tables and new-game workflows | 45 | 41 | 4 |
| DW7/All-Stars corrected GUI and format regressions | 22 | 21 | 1 |
| Package, dependencies, inventory and publication-gate regressions | 46 | 46 | 0 |

The shared focused skips were four missing copied-native inputs and one absent
display in that separate run. Origins lacked a genuine copy; All-Stars lacked
its genuine sample. The GUI batch lacked two Legends workflows, native P5S and
native Ayesha; subsequent actual-Tk copied-native checks covered those workflows.
The complete suite uses actual Tk on a virtual Xorg display with qualified native
copies for all six new editors, Wii U Hyrule, Age of Calamity and Pirate Warriors 3.

### Genuine-file verification

All downloaded/exported saves, private hashes and provenance remain outside Git.
Public tests generate their own inputs; optional native checks use environment
variables and skip when copies are absent.

| Game/platform | Independently checked input and limits |
| --- | --- |
| DW5 Special PC | Public premodified 46,000-byte native save; all 728 qualified fields checked surgically, plus actual Tk save/backup/restore. |
| DW8 Empires PC | Public native SYSTEM copy; both qualified horse-body fields checked. Campaign, quick-save and custom-officer profiles rejected. Actual Tk and copied-save CLI self-test passed. |
| Hyrule Legends 3DS | Public 234,594-byte export; all 323 fields and combined resource/card/fairy/seal edits checked. Master Sword data preserved. Actual Tk and CLI self-test passed. |
| Persona 5 Strikers PC | Three distinct public 5,627,552-byte saves; native checksum rejection, no-op and surgical edits across qualified occupied slots, plus actual Tk. |
| Wo Long PC | One public trainer-modified revision-1.302 gameplay save; native checksums, no-op, resource/stack edits and actual Tk passed. Byte-identical mirrors count as one fixture. Same-size SYSTEM data rejected. |
| Atelier Ayesha PS3 | Three public US/Japanese exports decrypted independently outside Git; published Cole values, no-op, Cole/stack edits and actual Tk passed. An encrypted unsupported digital-region export rejected. External PFD authentication and PS3 reimport were not checked. |
| Hyrule Wii U / Age of Calamity Switch | Two cached public Wii U exports and one AoC export; every qualified field checked surgically (495, 689 and 367 fields), Max exclusions/high values and unchanged source hashes passed. |

No edited save was loaded or re-saved by a game. Premodified and trainer-modified
files provide genuine-file evidence, not pristine gameplay or game-load evidence.

### Installed package, packaging and remaining limits

A non-editable wheel installed in an isolated environment outside the checkout
loaded all 28 editor/parser/backend registrations and all 14 runtime JSON files.
Its 191 entries contained no tests, tools, saves or binaries; runtime JSON bytes
matched the wheel exactly. Module listing and actual-Tk all-interface/theme
smoke startup passed. The source manifest verifies 401 public entries, and the
generated-inventory check passed.
The version remains 1.6. Linux checks do not validate Windows CNG or an EXE;
native build status belongs to the explicitly non-publishing workflow run.

Direct calls bypassing the bound adapter remain a legacy API limitation:
16 older backends can retain unknown prior keys during `stage`; PW4 and Sophie 2
can also normalize malformed pending values in direct `maximums` calls. For
example, direct PW4 Max with pending `{'beli': -1}` becomes a maximum, and
`{'beli': '1'}` raises `TypeError`. Their review/writers reject unknown keys.
Registered/GUI Stage, limits and Max are guarded and have adversarial regressions;
no corrupt output from the unknown-key case was established. The affected direct
modules are DW7 XL, PW4, DW4 Hyper/PS2 XL, Sophie 2, WO3U, SW4 DX, DW9E, Orochi Z,
Wii U Hyrule, AoC, Hyrule Definitive, FE Warriors, DW7E PS3, DW7 PS3 and SW4 PS3.

Coordination: this branch changes shared contracts/GUI, Origins and narrow
DW5/DW8E/Legends/Wo Long edge cases. It adds no game registrations or mechanics.
Concurrent implementation branches should preserve these regressions and refresh
the reviewed source manifest after integrating overlapping edits.

Run the complete public suite and all-interface startup check from the repository root:

```text
python -m pip install -e .
python -m unittest discover -s tests -v
python -m koei_editor --smoke-test
python -m tools.package_release --verify-only
python -m tools.build_windows --print-config
```

On Windows, Python/Tkinter and native CNG are sufficient for source tests. On
non-Windows, install the optional AES development provider with
`python -m pip install -r tools/requirements/dev.txt` and provide a graphical display
for Tk tests (for example, a locally installed Xvfb). Windows remains the target
for the standalone EXE and native CNG validation.

A prior cloud run completed **486 tests: 236 passed, 250 skipped, no failures
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

See [BUILDING.md](BUILDING.md) for executable build instructions and
[SAVE_FORMAT.md](https://github.com/MMexicann/Universal-Koei-Tecmo-Save-Editor/blob/main/docs/SAVE_FORMAT.md)
for the supported structures and editing rules. Technical reference files are
also included in the source download.

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

## v1.5 PC expansion

Linux Python 3.12/Tk 9 with a real Xvfb display ran the full public regression
suite: **777 discovered, 497 passed, 280 skipped, zero failures**. The skipped
cases require private DW3/native fixtures or platform-specific inputs; generated
fixtures remain procedural evidence. An inspector-search test initially expected
one match despite its token appearing in several columns; its assertion was
corrected and the full run repeated successfully.

A separate **113-test run passed with zero skips**, using privately held genuine
public DW7 XL, WO3 Ultimate, SW4 DX, PW4 and DW8 XL saves, five DW8 Empires files,
and two Nioh 3 native revisions plus an encrypted partner. It includes unchanged
roundtrips, surgical resource/stat/equipment/coin edits, native integrity,
malformed inputs, dependencies, high/unknown-value preservation, shared adapter
contracts and actual Tk workflows. DW8 Empires and Nioh 3 qualify source-only
codecs; their checks do not establish gameplay editing.

The final DW8/PW3 snapshot/restore hardening then passed **50 focused tests with
zero skips**, including five new adversarial cases, both genuine PC samples,
compatibility/affinity edits and GUI backup/Undo/Review/Save As. Sophie 2's new
refill/inventory and independent boundary/layout/filter tests pass using generated
and published differential data; its independent genuine save is still missing.
Additional source-only Orochi Z, All-Stars and Abyss tests use procedural data.

A further shared Max guard preserves PW3 bar/skill-slot values below their
qualified minimum. Its new regression, snapshot/restore checks and existing Max
regressions passed nine focused tests after that final change.

The universal startup smoke test passes with all eleven registered editors,
platform selection, retained sessions and both themes. The reviewed source
manifest verifies 210 public entries. The source and Windows archives exclude
player saves, attached binaries, private static-analysis outputs and owner data.
The Windows ZIP includes the coverage checklists; source-only modules remain
outside the writable game library.

Native Windows publication is gated by the existing Windows workflow: full
public tests, source GUI startup, Windows PyInstaller build, standalone EXE
startup, bundled metadata/privacy validation, archive generation and SHA-256
verification. Workflow logs provide the platform-specific test/skip counts.
Linux checks are not a substitute for those Windows checks.

**No edited file was loaded and re-saved by an actual game in this expansion.**
File-level qualification, procedural GUI checks and packaged application startup
are separate evidence. See [EXPANSION_COVERAGE.md](EXPANSION_COVERAGE.md) and its
per-game checklists for exact revisions, editable mechanics, legitimate bounds,
dependencies and remaining input blockers. In particular, SW4 manual base-stat
storage bounds and WO3 resource edit bounds are excluded from Max.

## v1.6 organized-package pre-release checks

The final cloud run completed **958 tests in 180.893 seconds: 689 passed,
269 skipped, no failures or errors**, using Python 3.12, Tk under Xvfb and
22 privately configured fixture/reference inputs. Skips include unavailable
private DW3 fixtures, unsupported platform checks and the missing genuine
DW9 Empires SYSTEMDATA sample. Procedural DW9 Empires tests verify the
source-backed current profile; they are not genuine-file or game-load tests.

All 22 registered game/platform editors passed application startup, theme and
game-switching checks. Independent isolated wheel installation verified all
22 editor/parser/backend imports, 14 runtime JSON resources, both module and
console launch commands and three published AES provider checks. The wheel
contained 162 entries and no tests, fixtures or attached binaries.

Independent native reviews checked 433 Orochi Z fields surgically, including
all 96 per-officer base-attack bounds, and separate available-gold/material
fields in All-Stars without changing lifetime earnings. Orochi Z passed 23
focused format/contract/GUI/review tests. Reacquired genuine SW4 DX checks
passed 21 focused tests. Fire Emblem Warriors passed 19 focused and independent
checks; its genuine public export was already modified. Special weapon and
progression restrictions remain preserved. No edited save was loaded or
re-saved in an actual game during this expansion.

The reviewed source manifest contains 331 public files and requires 116 runtime
dependency files. Independent source-ZIP extraction verified every source byte
and hash, installed the extracted package without repository import paths,
loaded all 22 editors and 14 JSON resources, initialized both GUI launch
commands, and passed 45 packaging/workflow/provider regressions. Windows ZIP
documentation comes only from explicitly reviewed manifest entries; private
files and source Python modules cannot be discovered into that ZIP.

The native [Windows workflow](../.github/workflows/windows-release.yml) must
pass the full public suite, source GUI startup, PyInstaller build, frozen EXE
startup, executable privacy/metadata verification and release-archive hashes
before publishing. Linux checks do not substitute for those Windows checks.
Release preparation respects protected merges and checks the exact tested
commit before dispatching publication.

The first native Windows run executed 958 public tests and found one test-only
path comparison: a temporary `RUNNER~1` folder resolved to its long Windows
name. The test now compares canonical destination paths while retaining exact
source, output and backup-byte checks. The unchanged runtime and corrected test
passed 24 focused genuine-file/GUI/integrity checks locally; native verification
must pass again before publication.
