# Building the Windows executable

Build on 64-bit Windows with Python and Tkinter installed. The tested build
used Python 3.14.2 and PyInstaller 6.22.3. PyInstaller is needed for building;
it is not needed to run the finished executable.

```powershell
python -m pip install -r build-requirements.txt
python build_windows.py
```

The result is `dist/DW3RemasteredSaveEditor-v0.3.1.exe`. It bundles the GUI,
standard-library AES wrapper, Tk runtime, parser/writer and ten JSON
metadata files. It does not bundle research saves or installed game files.

Check startup and the complete file workflow after building. Wait for each
windowed test process to finish before checking its exit code/report:

```powershell
$smoke = Start-Process -FilePath .\dist\DW3RemasteredSaveEditor-v0.3.1.exe -ArgumentList '--smoke-test' -WindowStyle Hidden -Wait -PassThru
$smoke.ExitCode
$selfTest = Start-Process -FilePath .\dist\DW3RemasteredSaveEditor-v0.3.1.exe -ArgumentList '--self-test "D:\SaveCopies\GameStatusData.sav" "D:\SaveCopies\BundledTest"' -WindowStyle Hidden -Wait -PassThru
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
