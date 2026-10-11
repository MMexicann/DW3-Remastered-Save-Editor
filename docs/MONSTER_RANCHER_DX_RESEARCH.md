# Monster Rancher 1 & 2 DX Windows qualification

## Outcome

Monster Rancher 1 DX and Monster Rancher 2 DX remain unregistered. No complete,
freely shared, genuine Windows gameplay save was acquired in this pass. Native
title/revision recognition, framing, integrity coverage and gameplay offsets are
unproved; exposing edits would therefore violate the adapter qualification
contract. There is no synthetic playable-save generator or runtime-address
adapter. No downloaded executable was run or third-party implementation copied.

The target is Steam app 1716120, with each game qualified separately. Community
tools target executable version 1.0.0.2; that version is a research target, not
proof of an on-disk revision. PS1, Switch and iOS inputs are separate formats.
The publisher confirms DX expands save, freezer and Hall of Fame capacity and
includes content absent from the original Western releases. Original-console
record counts must therefore be established afresh for DX.
[Publisher announcement](https://www.koeitecmoamerica.com/news/the-monster-rancher-series-makes-its-triumphant-return-to-the-west-with-monster-rancher-1-2-dx-now-available/)

## Sources inspected and licence boundaries

| Source / exact public snapshot | Findings and use |
| --- | --- |
| [MR1 Advanced Viewer, 4ca186a8](https://github.com/EntityMike/mr1av-repo/tree/4ca186a8eb9f8d24c5596e3f76643eabe61fee7a) | GPL-3.0 licence file. `AdvancedViewer/MRProcessWrapper.cs` reads the running game's memory with `ReadProcessMemory`; README limits it to MR1 DX 1.0.0.2. Mechanic distinctions inspected; code, tables and addresses not imported. |
| [MR2 Advanced Viewer, e029521d](https://github.com/Lexichu/mr2av_repo/tree/e029521d365b4365e5b86cb4c56637fc3a996e1f) | No licence file found in this snapshot. `MR2AdvancedViewer/Forms/ViewerWindow.cs` uses `ReadProcessMemory`/`WriteProcessMemory`. Its save backup feature copies directories, without decoding native gameplay files. No implementation imported. |
| [Reloaded-II mods, c9e95e62](https://github.com/ranchercommunity/mrdx_reloaded/tree/c9e95e62d8eb1a1a3667aa493e06df7df6870cca) | No licence file found in this snapshot. `MRDX.Base.Mod/Monster.cs` explicitly maps RAM; `SaveFileManager.cs` observes file-access events, not serialization. `MRDX.Qol.InfiniteFreezer/Mod.cs` reads/writes its own `ifreezer_*.bin` sidecars. These do not qualify native saves. No code/assets imported. |
| [LegendCup downloads](https://legendcup.com/gamesaves.php#steam) | The previously shared DX save has been removed because saves contain a unique player ID used for online uploads. Current DX downloads are Cheat Engine tables, not saves. PS1/PS2 saves still listed there cannot establish Windows DX identity. No removed fixture was recovered or republished. |
| [Steam save-location discussion](https://steamcommunity.com/app/1716120/discussions/0/3830919351660966402/) and [save-transfer discussion](https://steamcommunity.com/app/1716120/discussions/0/6337144732944029862/) | Windows location and extensionless slot names are reported. The latter contains one reply and no fixture URL; it reports single-file MR1 transfer but whole-directory MR2 transfer, including failure with Steam Cloud disabled. The underlying MR2 companion dependency remains unproved. |
| [MR2DX mod forum](https://www.tapatalk.com/groups/monsterrancher4520/mr2dx-mods-t4017.html) | PS1-like save layout and a historical DOS `MR Manager` freezer-copy utility are leads, not serializer proof. No usable source or native DX fixture located. |
| [Nexus discussion](https://forums.nexusmods.com/topic/13498425-will-there-ever-be-mods-for-monster-rancher-12-dx-on-steam/) | Requests for hidden-stat UI, without a save-format implementation or fixture. |
| [Japanese PS1 Monster Farm 2 save notes](https://emu.web-g-p.com/info/bbs/patchcode/ps1/bbs.cgi?list=pickup&num=1913) | Explicitly describes PS1 checksums and offsets relative to an MCR first block. Neither those offsets nor checksum coverage were transferred to DX. |

LegendCup's pages prohibit reproduction of their data without permission. The
links below identify mechanics to investigate; no catalogue, artwork, training
table or source implementation is redistributed. Searches covered GitHub,
English/Japanese save documentation, Nexus, Steam/community forums and current
save-sharing links. Runtime trainers and asset archive passwords were excluded
as native-save evidence.

## Mechanic checklist and exact blockers

Each row is blocked independently for both Windows games until native identity,
serialization and integrity are established. These are controlled capture
requirements, not proposed edits or natural-cap claims.

| Mechanic | MR1 DX distinction and missing evidence | MR2 DX distinction and missing evidence |
| --- | --- | --- |
| Money | Breeder cash is distinct from monster stats and rank. Need unchanged control plus buy/sell pair with displayed balances, price and inventory change, proving current cash separately from history. | Same capture, additionally retaining the original companion files; prove current money independently of tournament prize/history state. |
| Monster stats | LIF, POW, INT, SKI, SPD, DEF are separate stats; LIF is battle life, not remaining lifespan. Need labelled active and frozen occupied records and multiple controlled gains; prove widths, bounds and identity. | Same six stats; distinguish stored stats from form-adjusted SPD/DEF. Need controlled drill pairs and displays of form and base/effective values. |
| Training | Work and training affect stats and condition; training also has technique acquisition prerequisites. Need before/after work and training pairs, known techniques and requirement state. No generic experience field is assumed. | Drills, errantry, stat-growth aptitudes and learned-technique/use counters are distinct. Need successful/failed drill and errantry pairs, displayed gains and technique prerequisites. |
| Fatigue | Hidden current condition differs from stress and lifespan. Need a known-condition control, one work/training action, rest and a fatigue-reducing item pair. Prove saturation and any persisted derived index. | Same capture with light/hard drill and rest at known life stage; retain nature, form, training style and item state. |
| Stress | Hidden condition interacts with fatigue and care. Need known-condition control and stress-reducing item pair; isolate from fear/spoil and calculated loyalty. | Same; include scolding/denial state when used, separating nature/style and loyalty components. |
| Age / lifespan | Age and remaining lifespan are separate values; do not infer either from the other or write calculated Life Index. Need weekly/rest captures and a qualified lifespan-changing action, including event flags. | Age, remaining lifespan and initial lifespan are distinct in runtime research. Need weekly captures, controlled lifespan-item use with one-use flags, and expedition captures; DX expedition can advance age differently from lifespan consumption. |
| Ownership / progression | Active monster, frozen records, breed identity, shrine permission and event/rank history are distinct. Need freeze/thaw pairs, an empty slot, and genuine unlock pairs with prerequisites/reward items. Do not create monsters by stat writes. | Same; additionally distinguish mod sidecars from vanilla freezer data and online owner identity. Need original owner context kept private and documented unlock/reward captures. |

Mechanic references: [MR1 Advanced Viewer](https://legendcup.com/advanced-viewer-mr1dx.php),
[MR1 raising methods](https://legendcup.com/raisingmethodsmr1.php),
[MR1 unlock prerequisites](https://legendcup.com/faqmr1unlock.php),
[MR2 Advanced Viewer](https://legendcup.com/advanced-viewer-mr2.php),
[MR2 training planner](https://legendcup.com/mr2trainingplanner.php),
[MR2 unlock prerequisites](https://legendcup.com/faqmr2unlock.php).
The training planner documents fatigue/stress contributing to extra lifespan
loss and a DX expedition age/lifespan distinction; these are mechanic evidence,
not disk mappings. The unlock guides establish event and reward relationships,
so resource edits must not silently complete progression.

## Inputs needed to implement and validate

1. Private copies of complete native Windows `mfdx_en` (English) or `mfdx`
   (Japanese) directory contents, captured with the game closed; exact game,
   language, executable version, unmodified/modded status and slot association.
   The community reports `BISLPS-009100` and `BISLPS-00910F`, plus `bu00` and
   `bumf1` backup directories. Preserve all actual filenames rather than
   assigning those example names to both games. Reloaded-II watches
   `psdata001.bin` during save events; preserve it and other companions to
   investigate MR2's directory dependency. Its event heuristic is not a proven
   integrity relationship.
2. At least an unchanged re-save control and independent new/progressed saves
   for each game, then the one-action pairs in the checklist. Keep player IDs,
   source paths, hashes and saves outside the checkout and release assets.
3. A save-specific serializer/checksum reference, or private static analysis of
   owner-supplied native save/load routines, sufficient to prove revision
   recognition, integrity coverage, record occupancy and the companion-file
   relationship. An arbitrary `BISLPS-` filename, PS1 header or plausible stat
   pattern cannot satisfy title/platform/revision qualification.
4. Actual edited Windows game-load and re-save validation after an implemented
   adapter passes unchanged roundtrip, surgical preservation, malformed/foreign
   input, dependency, backup/restore, source-safety and GUI tests.

Validation in this pass: **0 procedural adapter tests, 0 genuine-file
roundtrips, 0 edited game-load validations** for either MR1 DX or MR2 DX.
No adapter exists to exercise backup, Undo, Review Changes or safe Save As for
these titles. Shared existing-game tests do not count as MR qualification.
