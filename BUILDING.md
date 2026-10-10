# Building the Windows executable

Build on 64-bit Windows with Python and Tkinter. The Windows workflow uses
Python 3.14, and `build-requirements.txt` pins PyInstaller 6.22.3. The application
itself requires no third-party runtime package on Windows.

```powershell
python -m pip install -r build-requirements.txt
python package_release.py --verify-only
python build_windows.py
```

The output is **`dist/UniversalKoeiTecmoSaveEditor-v1.4.exe`**, a single standalone
executable containing the game library, all five game editors, Tk runtime and
public application metadata. Native Windows CNG handles DW3 encryption. Save
samples, installed game files and private reports are excluded.

`build_windows.py` requires Windows for compilation. Inspect the build inputs on
any OS with:

```text
python build_windows.py --print-config
```

## Build checks

```powershell
python -m unittest discover -s tests -v
python application.py --smoke-test
$smoke = Start-Process -FilePath .\dist\UniversalKoeiTecmoSaveEditor-v1.4.exe -ArgumentList '--smoke-test' -WindowStyle Hidden -Wait -PassThru
$smoke.ExitCode
python package_release.py --verify-executable
```

The smoke test initializes the library and registered editors, switches games and
appearance, then exits. Require exit code 0. Save-format and game-load validation
are separate; see [VALIDATION.md](VALIDATION.md) for coverage and limitations.

Direct startup supports `--game dw3`, `--game dw4hyper`, `--game dw8xl`,
`--game pw3` and `--game dw4xl_ps2`.

## Copied-save workflow checks

The executable retains the DW3 copied-save self-test:

```powershell
$selfTest = Start-Process -FilePath .\dist\UniversalKoeiTecmoSaveEditor-v1.4.exe -ArgumentList '--self-test "D:\SaveCopies\GameStatusData.sav" "D:\SaveCopies\DW3Test"' -WindowStyle Hidden -Wait -PassThru
$selfTest.ExitCode
```

Other editors use an explicit game ID:

```powershell
.\dist\UniversalKoeiTecmoSaveEditor-v1.4.exe --game dw4hyper --self-test "D:\SaveCopies\save.dat" "D:\SaveCopies\DW4Test"
.\dist\UniversalKoeiTecmoSaveEditor-v1.4.exe --game dw8xl --self-test "D:\SaveCopies\save.dat" "D:\SaveCopies\DW8Test"
.\dist\UniversalKoeiTecmoSaveEditor-v1.4.exe --game pw3 --self-test "D:\SaveCopies\OP3WIN0000.dat" "D:\SaveCopies\PW3Test"
.\dist\UniversalKoeiTecmoSaveEditor-v1.4.exe --game dw4xl_ps2 --self-test "D:\SaveCopies\DW4XL.psu" "D:\SaveCopies\DW4XLTest"
.\dist\UniversalKoeiTecmoSaveEditor-v1.4.exe --game atelier_sophie2 --self-test "D:\SaveCopies\data.dat" "D:\SaveCopies\Sophie2Test"
```

Use a separate input copy and a new/empty output folder. Require exit 0,
`success: true` in `self-test-report.json` and preservation of the input hash.
These workflows create edited copies, backups and restored copies. Source
invocations use `python application.py` in place of the executable. They do not
establish actual game loading.

## Package integrity

`SOURCE_MANIFEST.json` records public source file versions, lengths and SHA-256
hashes. Refresh it after reviewed edits with `python refresh_manifest.py`; use
`--add FILE...` only for reviewed public sources. Then run:

```powershell
python package_release.py --verify-only
python package_release.py --verify-executable
python package_release.py --output work/local-universal-package
```

The packager produces the EXE, Windows ZIP, source ZIP and `SHA256SUMS.txt`.
Existing outputs are never replaced. It checks the embedded archive, metadata and
source hashes, and rejects save/game-file entries and personal paths.

The Windows workflow runs the tests, builds the executable and verifies its
startup and archive before creating downloadable build assets. Building locally
uses the same scripts. A completed build is a prerequisite for packaging.
Manual workflow runs only build artifacts. Pushing a tag matching the application
version, such as `v1.4`, publishes a new release after the native build and checks
succeed. Existing releases are not replaced.

PyInstaller's one-file runtime extracts into a temporary directory at startup.
An already-built executable requires no installer, game-directory access or
administrator privileges.

Release-marked main commits (`[release]` in the commit message) run the same native
build and checks, then create a new matching tag at that tested commit. Existing
tags and releases are never replaced.
