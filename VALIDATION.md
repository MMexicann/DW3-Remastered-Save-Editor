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
