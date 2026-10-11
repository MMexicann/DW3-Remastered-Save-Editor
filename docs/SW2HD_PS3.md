# Samurai Warriors 2 with Xtreme Legends HD: Japanese PS3 research

No gameplay adapter is registered. The unregistered
[`inspection.py`](../src/koei_editor/research/sw2hd_ps3/inspection.py) offers
bounded, immutable, **read-only candidate probes**. It cannot open a qualified
game session, stage changes, serialize, repair integrity or write player files.
Neither a successful probe nor matching candidate checksums identifies the game.

## Exact editions and source-backed leads

The candidate is Japanese PS3 **Sengoku Musou 2 with Moushouden HD Version**,
PSN `NPJB00439`. The disc compilation `BLJM61092` contains both this game and
Empires; its two gameplay profiles cannot be combined. Apollo's patch title
includes “Empires,” but its money/checksum offsets are not an Empires profile.
Original PS2, PS2 virtual-memory-card exports on PS3, PC, Xbox 360 and Vita files
are separate and do not qualify this candidate.

The [official HD product description](https://www.gamecity.ne.jp/sengoku2/hd/)
distinguishes the with-Xtreme-Legends and Empires titles, their trophies and
game modes. All 32 playable with-Xtreme-Legends officers are available initially.
Officer availability therefore must not be used as proof of story completion.
The published cross-save feature does not establish identical PS3/Vita bytes.

The [Apollo mapping](https://github.com/bucanero/apollo-patches/blob/main/PS3/NPJB00439.savepatch)
identifies `DATA.BIN`, a big-endian money DWORD at `0x2758`, and the sum of bytes
`0x8..0x36DF`, stored as big-endian DWORDs at `0x36E0` and `0x23790`.
The 9,999,999 money patch target is not evidence of a natural gameplay cap.
The independently written diagnostic does not copy Apollo GPL code or patches.

Primary user research in [archived thread 7070](https://web.save-editor.com/cache/bbs_savedata_ps3/7070.html)
supplies three EXP anchors: Yukimura `0x2C`, Ina `0xE3C` and Katsuie `0x1D3C`,
with reported officer stride `0xF0`. Three proposed Yukimura weapon positions
are `0x47`, `0x5A` and `0x6D`, each `0x13` bytes: type, element, eight effect IDs,
eight effect values and a count. The source explicitly leaves acquisition flags
unmapped and reports display corruption at +99 and freezing above it. A later
post questions the first two gem offsets. The inspector exposes only those raw
EXP/weapon anchors; it does not manufacture a complete roster, infer ownership,
interpret effect IDs, normalize counts, or treat reported targets as edit bounds.
No third-party editor implementation or enumeration catalog was imported.

## Qualification blockers and per-system coverage

| System | Implemented coverage | Evidence needed for gameplay controls |
| --- | --- | --- |
| Native profile and integrity | Bounded candidate checksum diagnostics | Genuine decrypted `NPJB00439` export, exact length/header/revision and all section integrity; independently qualify disc identity before adding it. |
| Money | Read-only source-proposed DWORD | Above native profile and legitimate bound; a controlled purchase/reward pair to exclude display/history aliases. |
| Officer EXP, level and growth | Three read-only published EXP anchors | Native record identity/count and level/EXP thresholds, derived stats, skill/reward dependencies. The proposed stride alone does not qualify all records. |
| Skills | None | Purchased/acquired IDs, rank bounds and acquisition/EXP prerequisites. |
| Weapons, elements, effects and fusion | Three raw candidate weapon probes | Actual ownership/acquisition flags, equipped references, record identity/type compatibility, safe effect ranks/counts, and fusion/reward dependencies. |
| Gems and inventories | None | Resolve contradictory offsets; independent quantity/order/cap and ownership evidence. |
| Mounts and bodyguards | None | Existing-record identities, acquired/equipped references and growth dependencies. |
| Survival, Mercenary and Sugoroku | None | Mode-specific records, current versus historical counters, reward dependencies. |
| Story, stages and collections | None | Exact separate completion/collection bits and prerequisite/reward behavior; never bundle these into money or EXP. |

The published sum covers only an initial section. Changes to the header and
later sections can retain both matching sums; compensated byte changes can
also collide inside the range. Matching sums therefore prove neither complete
native integrity nor title/revision identity. The minimum probe size `0x23794`
only reaches the last published checksum DWORD; the 2 MiB ceiling limits
processing. Neither is a claimed native file size.

## Genuine inputs and validation

The independently reviewed public [upload thread 258](https://web.save-editor.com/bbs/savedata/ps3/bbs.cgi?list=pickup&num=258)
has no SW2 HD save attachment. The PS3 GameFAQs pages for
[compilation 723490](https://gamefaqs.gamespot.com/ps3/723490-sengoku-musou-2-with-moushouden-and-empires-hd-version/saves)
and [with-Xtreme-Legends 737594](https://gamefaqs.gamespot.com/ps3/737594-sengoku-musou-2-with-moushouden-hd-version/saves)
also supplied no matching downloadable native fixture. Related PS2 virtual-card
downloads are not HD exports. No matching native serializer source or qualified
full export was found in this investigation. No game/editor binary was executed.

Four procedural tests in
[`test_sw2hd_ps3_candidate.py`](../tests/test_sw2hd_ps3_candidate.py) pass:
bounded immutable input, big-endian money and duplicate sums, preservation of
unusual raw EXP/weapon values, and negative proof that partial sum matches never
enable editing or native qualification. These are **synthetic diagnostic tests**.
There is no genuine-file no-op/edit evidence and no actual game-load/re-save
test for this profile. GUI backup/save/restore tests would require a qualified
writer and are consequently not claimed.

Any future adapter would edit copied **decrypted gameplay exports** only.
Apollo/external tooling would still be required to reimport and resign the
console save. Editing `DATA.BIN` does not rebuild PS3 `PARAM.PFD`, encrypt the
export, change ownership, or establish a game-load test.
