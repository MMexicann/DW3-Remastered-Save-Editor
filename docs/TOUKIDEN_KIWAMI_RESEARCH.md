# Toukiden: Kiwami — Windows investigation

No editor is registered. Two freely shared PC save archives were acquired and
inspected outside the checkout; **zero complete native files qualified for
decoding, integrity validation or editing**. An opaque byte copy is not a
serialization roundtrip. There were no edited game-load tests.

## Native evidence and qualification boundary

The [Steam Windows manual](https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/363130/manuals/steam_digital_TKDK-EN.pdf?t=1729051108)
identifies the game and its three character slots. Steam's published cloud
configuration, recorded by [SteamDB](https://steamdb.info/app/363130/ufs/), uses
`DATA*.BIN` in `KoeiTecmo/TOUKIDEN KIWAMI/Savedata`, `Savedata_JP` and
`Savedata_TW` beneath Documents. This is filename/platform provenance, not a
proof that a file belongs to a supported serialization revision.

The [SaveGame.Pro PC listing](https://savegame.pro/pc-toukiden-kiwami-savegame/)
provided a 7z archive containing `DATA0.BIN`, `DATA1.BIN`, `DATA2.BIN` and
`DATASYS.BIN` under the documented English Windows directory. Each numbered
slot is 392,216 bytes; system data is 6,764 bytes. Two numbered slots are
byte-identical. The listing does not identify the executable build, DLC or
whether the save was previously edited. No account context or player data is
published here.

The independently hosted [K73 PC initial-save listing](https://www.k73.com/down/save/103778.html)
provided one 392,216-byte `DATA1.BIN`; the downloaded archive is RAR despite
its `.zip` filename. Its advertised equipment/Mitama state is modified and is
not a controlled natural-progression sample. The matching size does not prove
the same revision or a valid checksum. Only data was extracted; no downloaded
shortcut, game, trainer or editor binary was executed.

The candidate files are opaque and have high byte entropy. Direct zlib/raw
deflate trials in their initial 256 bytes did not produce a usable payload.
The repository's existing Koei word/byte algorithms did not establish a decoded
structure and passing integrity checks. Repeated ciphertext spans across slots
are observations, not demonstrated field offsets, a safe XOR key or an integrity
algorithm. There is no proved native title/revision marker, decoded occupied
record schema or checksum coverage. Consequently even Haku cannot be exposed.

## Mechanics and exact missing captures

Mechanics below come from the official Windows manual, principally pages
33 and 46–52. The table describes game behavior; it assigns no disk offsets.
For every capture, supply a separate unchanged save/re-save control and record
the displayed before/after values. Copy the affected native `DATA0.BIN`,
`DATA1.BIN` or `DATA2.BIN` and `DATASYS.BIN` into private before/after folders;
include the Windows language, executable version/build and installed DLC.

| Mechanic | Confirmed distinction | Specific remaining input |
| --- | --- | --- |
| Haku | Currency buys/upgrades equipment and upgrades Mitama. | One ordinary purchase with known price, unchanged inventory aside from that purchase, and both displayed balances. Native codec and checksum coverage first. |
| Existing materials | Materials are used in equipment creation/upgrades; owned materials can be sold. | Sell exactly one named owned material; record quantity and Haku delta. Establish existing-record ID, quantity width and capacity without creating absent ownership. |
| Weapons/armor | Nine weapon types; armor occupies four body parts. | Switch one owned weapon or armor piece without buying/forging; record old/new item identity and equipment references. Separate ownership, equipped references and derived stats. |
| Fortify/reinforcement | Maximum compatibility or soul steel permits fortifying, up to nine times; sockets may increase. | Fortify one identified owned item once, capturing compatibility, reinforcement, soul steel, Haku, sockets and displayed stats. Recipe/compatibility dependencies remain unproved in saves. |
| Reforge | Reforging spends Haku/materials and destroys the previous item. | One ordinary reforge with exact source/target IDs and costs; prove deletion/replacement and equipped-reference behavior together. No unlock or resource shortcut is inferred. |
| Mitama | Haku raises level; ownership and equipping are separate. Tenko assignment temporarily prevents weapon equipping. | One donation/level increase plus one unchanged-level donation, and a separate Tenko assignment pair; record ownership, level, accumulated Haku and equipped/assigned references. |
| Skills/Boosts | Primary Mitama determines battle style. Ultimate level permits three learned Boosts plus an automatic fourth. | Change one selected learned Boost without changing ownership/level; record selected Boost identities and Ultimate state. Battle skill stocks are distinct from learned Boosts. |
| Persistent progression | Red missions advance story. Bonds respond to battles, quests and conversations. | Complete one normal story mission, one side quest/reward claim, and separately one bond-only conversation. Prove prerequisites, rewards, claim flags and history before allowing progression actions. |

No category has a proved writable mapping. Resource edits must not silently
grant missions, equipment, Mitama, learned Boosts, DLC or claimed rewards.
Natural limits for currency/materials and serialized unusual values also remain
unproved; trainer targets cannot serve as Max values.

## Source and licence survey

- [FearLess Kiwami table](https://fearlessrevolution.com/viewtopic.php?t=1353):
  inventory/equipment runtime-memory editing; no demonstrated Windows disk map.
  The page was inaccessible directly in this environment, so no table was run.
- [Vita checksum tool](https://web.save-editor.com/tool/wse_checksum_fix_psvita_title_Toukiden_Kiwami.html)
  and [Vita modification discussion](https://web.save-editor.com/bbs/cfw/psvita/bbs.cgi?list=pickup&num=12643):
  explicitly different platform; no PC offset or checksum compatibility is assumed.
- [PC modification thread](https://web.save-editor.com/bbs/community/pc/bbs.cgi?list=pickup&num=2427)
  and [PC save thread](https://web.save-editor.com/bbs/savedata/pc/bbs.cgi?list=pickup&num=2143):
  inspected title threads contain links and thread guidance, with no usable
  save-specific codec or field mapping.
- [RogelRC/toukcsc](https://github.com/RogelRC/toukcsc) is a Mitama build
  calculator, not a save reader/writer. Its README does not grant a reusable
  software/catalogue licence; none of its code, catalogue or assets is imported.
- [PythWare/Kybernes-Tools](https://github.com/PythWare/Kybernes-Tools) and
  related unpackers concern game assets/audio, not qualified gameplay saves.
  [Nexus listings](https://www.nexusmods.com/games/toukidenkiwami/mods) supplied
  no accessible native save schema or source editor in this pass.
- [Ali213 story-save listing](https://patch.ali213.net/showpatch/43467.html)
  explicitly describes a trainer-modified Japanese PC save; its current download
  routes are scripted resource searches. It was not counted as an acquired or
  qualified fixture. [GamerSky's initial-save listing](https://down.gamersky.com/pc/201507/618997.shtml)
  had an unavailable download route. The [GamesKeys listing](https://gameskeys.net/toukiden-kiwami-save-game/)
  CDN returned HTTP 403 with the initial fetch method; the independent
  SaveGame.Pro archive was acquired with curl instead.

## Validation status

Acquired archive data was inspected read-only outside Git. Complete-gameplay
identity/revision qualification: **0**; native integrity-qualified files: **0**;
genuine unchanged codec roundtrips: **0**; genuine surgical edits: **0**;
actual edited game-load/re-save validation: **0**. No procedural editor tests,
backup/Undo/Review/Save As or GUI claims are made for this unregistered game.

The immediate blocker is a verified Windows save codec/integrity reference or
lawfully supplied native serialization analysis establishing title/revision and
all native checksums on the acquired files. Controlled action pairs above are
then required for each field/dependency. A working cipher alone cannot qualify
an editor. Keep all player files, account context, game assets and external
implementations outside the checkout and public source manifest.
