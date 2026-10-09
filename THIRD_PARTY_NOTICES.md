# Bundled runtime notices

The Windows executable includes Python, the Tcl/Tk runtime, and the PyInstaller bootloader. Their supplied license texts are retained in the `licenses` folder. PyInstaller's bootloader has an exception for distributed bundled applications; see its full notice.

The editor uses Windows CNG from the operating system; no separate crypto library is redistributed. Original editor code is covered by the MIT `LICENSE` file.

Non-Windows source development can optionally use the installed cryptography
package as an AES test provider. It is not bundled by the Windows build, which
continues to use native CNG. Origins reference metadata cites public resources;
no downloaded save or third-party research code is redistributed.

PC format research references the DW8 XL converter by koko-tsuu, the public
Pirate Warriors 3 PC save by Ceraph1216, and the Apollo save/patch databases and
PS3 save decrypters maintained by `bucanero`. These are research
references, not bundled dependencies. Their implementations, saves, game assets,
console keys and account data are not redistributed. The new cipher and editor
code was independently written from factual format observations. See
`KOEI_FORMATS.md` for inspected commits, sample fingerprints and limits.

Additional mechanics research references `gamesaves/OPPW3`, published native PC
instruction/structure annotations from `Hexorg/CheatEngineTables`, PC runtime
research by `Glubus/oppw4-sdk` and `Glubus/oppw4-data`, and tutorial translation
semantics from `ayozetr/berserk-band-of-the-hawk-es`. Those sources are not bundled;
no trainer/script is executed or redistributed. See `GAME_MECHANICS.md` for
evidence classes, exact commits, authored summaries and unresolved dependencies.

The DW4 Hyper candidate, DW8 Empires research codec and Persona 5 Strikers stream
primitive are independently authored from published format facts. Source URLs
and inspected commits are recorded in PC_RESEARCH_RETRY.md. No implementation
from the supplied DW4 repositories or P5S utility, downloaded executables,
screenshots or external guide prose is bundled. Officer/item names and numerical
layout observations are factual labels; candidate status remains explicit.
