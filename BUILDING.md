# Building the Windows executable

Build on 64-bit Windows with Python and Tkinter installed. The build dependency
pins PyInstaller 6.22.3. Python and PyInstaller are needed to build from source;
users of the finished executable only need to extract the Windows ZIP and run it.

```powershell
python -m pip install -r build-requirements.txt
python build_windows.py
```

The result is `dist/DW3RemasteredSaveEditor-v1.1.exe`. It bundles the GUI,
Windows CNG AES wrapper, Tk runtime, parser/writer and twelve JSON
metadata files. It does not bundle research saves or installed game files.

Check startup and the complete file workflow after building. Wait for each
windowed test process to finish before checking its exit code/report:

```powershell
$smoke = Start-Process -FilePath .\dist\DW3RemasteredSaveEditor-v1.1.exe -ArgumentList '--smoke-test' -WindowStyle Hidden -Wait -PassThru
$smoke.ExitCode
$selfTest = Start-Process -FilePath .\dist\DW3RemasteredSaveEditor-v1.1.exe -ArgumentList '--self-test "D:\SaveCopies\GameStatusData.sav" "D:\SaveCopies\BundledTest"' -WindowStyle Hidden -Wait -PassThru
$selfTest.ExitCode
```

The second command writes `self-test-report.json` in a new/empty output
folder. Exit code 0 and `success: true` confirm completion. The report also
confirms the supplied input's hash stayed unchanged. The executable is a
windowed app, so the JSON report is the useful result rather than console
output.

PyInstaller's one-file executable extracts its bundled runtime into a
temporary directory at startup. That does not access the game installation
or save directories. No installer or administrator access is required.

## Release packaging

`SOURCE_MANIFEST.json` records the version, length and SHA-256 hash of every
public source file. Regenerate it after final source edits, then run:

```powershell
python package_release.py --verify-only
python package_release.py --verify-executable
python package_release.py
```

The packager creates the standalone Windows EXE, Windows ZIP, source ZIP and `SHA256SUMS.txt` in
`release/`. The source ZIP contains only verified manifest entries and the
manifest itself. Save files, research folders, build output and personal home
paths are excluded or rejected. The Windows ZIP contains the executable,
README, changelog and licenses. Existing output files are never replaced;
use `--output` with a new directory to package again.

The executable check inspects its embedded archive in memory, including
compressed Python modules. It rejects private save/research entries and
personal home paths, and compares bundled metadata with the verified source.

The Windows release workflow uses Python 3.14 and the pinned build dependency.
It verifies the manifest, runs the public tests and checks both source and
packaged GUI startup before packaging. Private fixture cases skip in CI.
A push to `main` with `[release]` in its final commit message, or a manual run
on `main`, publishes an official release for that exact commit. Existing tags
or releases stop publication. The workflow's GitHub token has only repository
contents permission; no personal access token is required.
