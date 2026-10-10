# Dragon Quest Heroes I/II and Fate/Samurai Remnant — Windows status

Reviewed 11 October 2026 against `codex/prepare-next-update` at
`bdb3833a1ad4169c12d3f889d5e971dc481c9cc2`.

**Implementation is blocked for all three titles. This branch adds no gameplay
editor, writable field or library card for them.** The requested integrated
editors could not be delivered with the acquired evidence. Their registration
and supported-game inventory remain unchanged; runtime research metadata records
the narrower evidence below. Native saves, owner context, downloaded source,
binaries and assets stay outside the public checkout and source manifest.

## Evidence acquired and qualification gaps

| Windows candidate | Privately acquired evidence | Missing proof before editing |
| --- | --- | --- |
| Dragon Quest Heroes: Slime Edition, Steam app 410850 | A [3DM PC save contribution](https://dl.3dmgame.com/patch/114595.html) contains a 102,400-byte (`0x19000`) `SAVEDATA.BIN`. Independent decoding identifies an `LZP2` wrapper, observed wrapper word `1`, 61,648 compressed bytes at `0x10`, and 642,716 decoded bytes. | Native title/revision acceptance, integrity algorithm and coverage, slot/record identities, owner-context requirements and persistent resource semantics. The wrapper word is not a qualified game revision. Decompression establishes no gameplay checksum or edited-save validity. |
| Dragon Quest Heroes II, Steam app 574050 | The [SaveGame.Pro contribution](https://savegame.pro/pc-dragon-quest-heroes-ii-savegame/) was reacquired: complete `SAVEDATA.BIN`, 1,575,744 bytes (`0x180B40`), observed prefix `031028160800000003000000`, without an `LZP2` wrapper. | Header semantics, title/revision acceptance, all integrity, serialized slot boundaries and semantic field/dependency maps. A date-looking prefix or repeated record pattern is insufficient. |
| Fate/Samurai Remnant, Steam app 1902690 | Publisher title/mechanics documentation and Windows cloud filename patterns; official demo app 2659950 exists. | A complete genuine Windows save, matching serializer or source-backed disk editor, title/revision/slot schema, serialization, integrity and resource maps. No native save or serializer bytes were acquired. |

The DQH contributions advertise progressed or completed states; these are uploader
claims, not controlled in-game observations, unmodified provenance, checksum
proof or natural caps. Their unusual/higher values must be preserved. Neither
DQH sample underwent an edited game load or re-save.

The DQH1 bounded scratch decoder consumed the complete declared compressed
stream and produced the exact declared decoded length. Two download mirrors
contained identical save bytes, so they supply one fixture, not independent
qualification. Recompression and native unchanged serialization remain untested.

Steam's [DQH1 cloud metadata](https://steamdb.info/app/410850/ufs/) and
[DQH2 cloud metadata](https://steamdb.info/app/574050/ufs/) distinguish native
`SAVEDATA.BIN` from `inputmap.dat` bindings. [Fate full-game metadata](https://steamdb.info/app/1902690/ufs/)
lists `Savedata/SAVEDATA*.BIN` and `SavesDir/*.sav`; the role of `.sav` remains
unqualified. [Fate demo metadata](https://steamdb.info/app/2659950/ufs/) uses a
separate demo folder. The [publisher's Steam listing](https://store.steampowered.com/app/1902690/FateSamurai_Remnant/)
allows demo transfer only when the full game has no existing save. This does not
prove identical demo/full serialization, integrity or entitlement state.

## Source and licence review

These sources were inspected as evidence; their implementations/catalogs are
not imported, executed or redistributed.

| Source | Reviewed commit / licence | Why it does not qualify a Windows editor |
| --- | --- | --- |
| [synch12/DW5Tools LZP2 documentation/source](https://github.com/synch12/DW5Tools/blob/acb36c8b7012744fa69a85349e1d4b263c3601f9/lzp2Extract.py) | `acb36c8b7012744fa69a85349e1d4b263c3601f9`; GPL-3.0 | Corroborates literal, repeated-byte and overlapping history-copy compression facts. Independent private decoding proves DQH1 stream framing, but supplies no native gameplay identity, checksum or semantic map. No implementation is copied into this project. |
| [marcussacana/DQHEditor](https://github.com/marcussacana/DQHEditor/tree/599769d8dee2516b463d66b6323e9d867ffd64a3) | `599769d8dee2516b463d66b6323e9d867ffd64a3`; no declared project licence located | Edits `.strs`/`.lx` strings/assets, not native saves. |
| [ExcaliburZero/dqhrs_save_editor](https://github.com/ExcaliburZero/dqhrs_save_editor/tree/0a9ef40e4f4e64ebed80e973a8686e975fb3e841) | `0a9ef40e4f4e64ebed80e973a8686e975fb3e841`; MIT | Targets Nintendo DS Rocket Slime, a different game. |
| [Apollo DQH1 PS4 patch](https://github.com/bucanero/apollo-patches/blob/0ccc07ed39ea378db83e9901dbfa610b04637d7d/PS4/CUSA02769.savepatch) / [DQH2 PS4 patch](https://github.com/bucanero/apollo-patches/blob/0ccc07ed39ea378db83e9901dbfa610b04637d7d/PS4/CUSA06740.savepatch) | `0ccc07ed39ea378db83e9901dbfa610b04637d7d`; GPL-3.0-or-later | Both expressly untested; console direct patches provide no native Windows serialization/integrity contract. Cheat targets are not gameplay caps. |
| [DeathChaos25/fdata_dump](https://github.com/DeathChaos25/fdata_dump/tree/7690d0cb587b3849a543d77c1c6aae19c7620736) | `7690d0cb587b3849a543d77c1c6aae19c7620736`; GPL-3.0 | Fate asset-archive extractor, not a player-save serializer. |
| [Lyall/FateSamuraiRemnantFix](https://github.com/Lyall/FateSamuraiRemnantFix/tree/24fdfd7ce3a00304ad1078f2fac753b426ecdf48) | `24fdfd7ce3a00304ad1078f2fac753b426ecdf48`; MIT | Runtime display plugin. |
| [Fate Infinite Items](https://www.nexusmods.com/fatesamurairemnant/mods/3) | Uploader's restrictive reuse terms | Cheat Engine attached to the process; no persistent disk-format proof. |

The [DQH2 Vita ver.1.00 checksum fixer](https://web.save-editor.com/tool/wse_checksum_fix_psvita_title_DragonQuest_Heroes_2.html)
posts saves to a server CGI; reviewed client scripts contain no algorithm or byte
coverage. Its page warns that checks were principally verified on PS3 and Vita
compatibility may differ. The [DQH2 PS3 discussion](https://web.save-editor.com/bbs/patchcode/ps3/bbs.cgi?list=pickup&num=346)
reports checksums and revision-dependent addresses but supplies no Windows
integrity contract. It also reports story failures after creating unowned quest
materials. The [Chaoszage editor](https://modwithchaoszage.com/editor/dqh2) targets
decrypted PS4 inputs, requires login and exposes no public implementation.
No save was uploaded to these services. PS3 CCAPI memory addresses and other
console patches cannot be promoted to Windows disk fields.

## Mechanics and dependency checklist

This is a research checklist, not a serialized schema. Gameplay descriptions do
not supply offsets, record IDs, storage widths, integrity or natural Max bounds.

| Title / system | Distinctions and required controlled evidence |
| --- | --- |
| DQH1 gold and mini medals | Current available balances versus earned/spent history and claimed rewards; capture one ordinary gain/spend. |
| DQH1 existing items/materials | Qualified occupied ordinary ingredient/item identities, quantities and acquisition flags; quest items/keys stay separate. Capture one existing stack gain/use. |
| DQH1 character growth and skills | Character EXP, level, base versus equipment-derived stats, spendable points, learned nodes and prerequisite/reward state; capture a level-up and a separate skill allocation. Do not import DQH2 vocations/proficiency. |
| DQH1 equipment and alchemy | Owned weapons, shields, defensive orbs, accessories, equipped references and accessory recipe/effect outcomes; capture acquisition, equip and alchemy separately. No generic weapon reinforcement system is assumed. |
| DQH2 currencies/materials | Available gold and mini medals, lifetime/reward history, ordinary alchemy ingredients versus quest/ownership records; capture one spend and one already owned ingredient change. |
| DQH2 vocation growth | Lazarel/Teresa have per-vocation growth and trees; vocation switching/availability and shared bonuses are distinct. Companion character growth is separate. Capture each category independently. |
| DQH2 weapon proficiency | Character/weapon-type proficiency is separate from vocation level and companion growth. Training rewards and tier prerequisites require their own map; no universal level-20 Max is justified. |
| DQH2 skills | Spendable points, learned nodes, vocation availability, proficiency rewards and replay bonuses are separate dependencies. Level alone cannot prove the skill budget. |
| DQH2 equipment/accessory enhancement | Existing weapons/orbs/accessories, equipped references, ingredient costs, accessory upgrading and appraised reward properties require separate records. Shop quests, mini-medal purchases and dungeon rewards are ownership transitions, not resource quantities. |
| Fate Iori progression | Iori EXP/level/base stats, stances, magic, spendable points and learned skills require synchronized native proof. Equipment bonuses and temporary battle gauges stay separate. |
| Fate Servant progression | Saber growth, other Servants' possible shared-level relationships, separate skill trees and availability require native verification. Do not manufacture a writable independent level for each Servant. |
| Fate resources and mountings | Available money, existing ordinary materials/items, owned mounting IDs/properties, upgrades, disassembly and equipped references; capture resource and equipment actions separately. DLC bonus ownership is not implied by inventory bytes. |
| Fate workshop | Purchased renovations, costs/prerequisites and workshop state are distinct from materials. Mastery Gem reward tiers, statue recipes/quality, carving history, inventory and sale eligibility need separate controlled pairs. |
| All three titles: story/ownership/rewards | Recruitment, quest completion, reward claims, recipes/shop stock, collections, costumes, expansion entitlement and replay state must not change as a side effect of resource/growth edits. |

DQH2 [publisher-supplied system details reported by Gematsu](https://www.gematsu.com/2016/03/dragon-quest-heroes-ii-details-class-changes-ability-acquisition-multiplayer-more)
distinguish vocations, point-based skills and weapon proficiency. The
[Windows equipment discussion](https://steamcommunity.com/app/574050/discussions/0/2119355556474412010/)
is a primary player report, not serializer proof. DQH1's [publisher listing](https://store.steampowered.com/app/410850/)
describes accessory alchemy; native recipe/ownership maps remain missing.
The [DQH1 publisher equipment article](https://www.square-enix-games.com/en_US/news/dragon-quest-heroes-social-diary-5-slime-sword-goomerang-and-costumes)
also distinguishes equipment and edition bonuses. Acquiring or equipping an
item, consuming recipe ingredients and granting bonus ownership require separate
native records; quantity edits cannot stand in for those transitions.

Fate's [official system description](https://www.koeitecmoamerica.com/fate-sr/system/)
separates Iori, Saber and bonded Rogue Servants. The [publisher's skill FAQ](https://support.koeitecmo.info/hc/en-us/articles/23866021710489--Fate-Samurai-Remnant-PS4-Unlocking-a-new-skill-tree)
requires connected prior nodes and node-specific requirements; it documents PS4
mechanics without Windows record proof. The [community mechanics reference](https://koeitecmo.wiki/wiki/Fate/Samurai_Remnant)
reports shared Servant combat levels and separate trees; that remains a native
verification question. A [player achievement guide](https://steamcommunity.com/sharedfiles/filedetails/?id=3042883586)
provides workshop/statue/reward capture leads. No catalogs or guide tables are
redistributed. A [PS4 editor-forum report](https://web.save-editor.com/bbs/patchcode/ps4/bbs.cgi?list=pickup&num=32793)
warns that overrange EXP can reset progression after battle; its console targets
are not Windows offsets, growth curves or caps.

## Exact enabling inputs and validation boundary

For each title, obtain a matching original Windows serializer/getter for private
static inspection, or a source-backed native editor with sufficient licence and
format evidence. Pair it with complete original save-folder copies, exact
edition/build/DLC labels, required owner context retained privately, an unchanged
control, and one-action before/after saves with displayed values. Start with
current money and one already owned ordinary material; then capture the growth,
skill, equipment, alchemy/workshop and reward actions separately as above.

Before registration, prove title/revision/structure and every applicable native
integrity layer, a genuine byte-exact unchanged serializer roundtrip and surgical
writes. Use the existing scalar backend, GUI, backups, Undo, Review Changes and
safe storage; preserve unknown bytes, owner context, original seeds, unusual and
higher values. Disable Max for fields lacking evidenced natural bounds, rather
than substituting storage ceilings or cheat targets. Reparse every qualified
edit and separately record actual Windows game load/re-save.

This investigation completed DQH1 decompression and DQH2 framing inspection,
**not** checksum-qualified native roundtrips or surgical gameplay edits. There
are no new title-specific malformed-input, dependency, backup/restore or GUI-edit
tests because no adapter could be qualified. Existing regression and GUI checks
are recorded separately in [VALIDATION.md](VALIDATION.md). No edited save was
loaded or re-saved in any of these games; no Windows executable build was tested.

Fate public acquisition checks found a 404 at the direct SaveGame.Pro candidate
URL, no saves on [Speedrun resources](https://www.speedrun.com/FateSR/resources),
and a [Steam save offer](https://steamcommunity.com/app/1902690/discussions/0/3960413699057091393/)
without a public download. These checks do not establish that no public save
exists. No player was contacted. Automatic approval review rejected a proposed
Steam demo-depot key request as access-controlled secret acquisition beyond the
research authorization, potentially enabling protected-content access. The
request did not execute and no workaround was attempted. Public metadata/source
research continued; matching demo/full serializer bytes remain missing.
