# PC editor qualification results

Original research cutoff: 2026-10-09; Origins qualification updated for v1.4.

Following the requested scope, further gameplay implementation concentrates on
games for which native Windows PC decoding and evidenced field editing have been
demonstrated. A candidate, console patch or memory trainer does not qualify.

## Qualified editors

| Native PC edition | Verified development functionality |
| --- | --- |
| Dynasty Warriors 3: Complete Edition Remastered | Existing full v1.1 editor retained; original native schema and rules |
| Dynasty Warriors 8: Xtreme Legends Complete Edition | Genuine PC sample decoded; gold, gems, materials, 82 officer stat records and supported existing weapon attribute ranks edited; both integrity layers regenerated |
| One Piece: Pirate Warriors 3 | Two genuine PC samples decoded; 47 numbered records' health, attack, defense, special bars and skill slots edited; native checksum regenerated |
| Dynasty Warriors: Origins | Nine native Steam slots across revisions16/17/29; resources, existing bonds, peace, qualified weapon reinforcement and persistent battle history with native checksum preservation |

For the two new editors, unchanged files round-trip byte for byte and unrelated
plaintext is preserved. **Actual game loading and re-saving remain untested.**
DW3's private fixtures and native Windows executable checks are also outstanding.
See [KOEI_FORMATS.md](KOEI_FORMATS.md) and [VALIDATION.md](VALIDATION.md).

## Unqualified and blocked investigations

These results describe the checks actually completed, rather than treating every
missing sample as a failed decryption. Origins' earlier cipher trials did not
establish a valid payload; v1.4 supersedes them with native codec evidence. None of the renewed candidates reached a demonstrated
PC decryption failure. Public links blocked before download have not been tested
with a decoder. See [renewed attempts, original URLs and precise sample requirements](PC_RESEARCH_RETRY.md).

| PC edition | Current result | Evidence and remaining blocker |
| --- | --- | --- |
| Dynasty Warriors 4 Hyper | Published-format PC editor available | 331 fields and surgical checksum-preserving serialization implemented from the supplied native PC editor. Independent genuine-file and in-game validation pending. |
| Dynasty Warriors 6 | Plaintext PC reader lead | Native PC save.dat reader and author-reported successful edits found. Officer/weapon/unlock layouts partly corroborated by screenshots; no independent complete save validation. |
| Dynasty Warriors 7: Xtreme Legends Definitive Edition | PC save link; download blocked | Steam users share annotated PC saves and restoration instructions. Google Drive archive blocked here; no bytes reached a decoder trial. |
| Dynasty Warriors 8: Empires | Candidate codec; PC sample blocked | Independently implemented published two-layer cipher candidate passes procedural checksum/preservation tests. Steam users share a PC save, but its Google Drive download is blocked; title identity and fields remain unverified. |
| Dynasty Warriors 9 | PC save link; download blocked | Steam users confirm a public PC save and describe unlock/story coverage; savegame.pro blocked here. PC gem guide maps runtime taxonomy, not serialized fields. |
| Dynasty Warriors 9: Empires | PC mechanics mapped; sample missing | PC guides distinguish reputation/title, artifact/gem, proficiency/inheritance and CAW dependencies. Public hex and .caw tools edit process memory, not native saves; no disk codec verified. |
| Samurai Warriors 2 | Save search unresolved | Located PC Sugoroku tool modifies SW2.exe map properties rather than saves. It is not a save decoder; no native PC sample or integrity evidence verified. |
| Samurai Warriors 4-II | Sample link blocked; platform check pending | Steam PC discussion links a Dropbox save; download blocked and uploaded filename still needs platform verification. PC runtime maps weapons, mounts and strategy tomes without proving disk offsets. |
| Samurai Warriors 4 DX | PC path identified; no codec | Published PC backup manifest identifies the Windows save location and Steam edition. No native PC decoder or gameplay edit was verified. |
| Samurai Warriors 5 | PC path identified; no codec | Published PC backup manifest identifies the Windows save location and Steam edition. No native PC decoder or gameplay edit was verified. |
| Samurai Warriors: Spirit of Sanada | PC path identified; no codec | Published PC backup manifest identifies the Windows save location and Steam edition. No native PC decoder or gameplay edit was verified. |
| Warriors Orochi (original PC) | Save search unresolved | Bounded native PC decoder/sample search found no applicable disk reader. This is a missing-evidence blocker, not a demonstrated decryption failure. |
| Warriors Orochi 3 Ultimate Definitive Edition | PC archive link; download blocked | Annotated Steam PC save archive found; Mediafire blocked here. Promotions, growth, crafting, upgrade stones and bonds researched; console layouts remain unverified for PC Definitive. |
| Warriors Orochi 4 / Ultimate | Console format leads only | Public decrypted PS4 sample indexed; no verified PC editing layout. |
| One Piece: Pirate Warriors 4 | PC archive link; download blocked | Steam PC guide links save_data.rar with Windows import instructions and successful-load reports; Mediafire blocked. Runtime Beli/medal/crew/Soul systems are separate; no disk decoder verified. |
| Berserk and the Band of the Hawk | PC mechanics evidence; sample missing | PC tutorials/guides distinguish character progression, accessory enhancement +9, skill rank and per-character/global Eclipse rewards. No native PC save or disk codec verified. |
| Persona 5 Strikers | PC stream vector verified; integrity pending | Independent byte-stream recovery reproduces a published 32-byte PC vector without an account ID. Read-only structural inspection implemented; no complete sample/checksum/gameplay writer verified. |
| Dragon Quest Heroes | PC runtime evidence only | PC progression runtime tables describe level, EXP, skill points and skill trees. No native save decoder or serialized offsets verified. |
| Dragon Quest Heroes II | PC path identified; no codec | Native PC backup path identified; no usable sample, disk codec or editable schema verified. |
| Warriors: Abyss | PC path identified; no codec | Native PC edition and GAMEDATA*.BIN filenames identified; no file decoding/editing verified. |

Other unimplemented titles stay outside the library; Origins now uses a native
qualified slot parser. DW4 Hyper is available from the published PC format, with independent
genuine-file validation still pending. DW4 XL is available in the separate PS2
platform library. DW4–7 Empires have no PC editions. See DW4_PLATFORM_FORMATS.md.

Other broad catalog entries have not all received equivalent format investigation.
The catalog records 37 PC game/series entries plus DW4 XL PS2; grouped series are not an exact
count of Steam titles or verified adapters.

## Source record and limits

- Existing project metadata and regression tests provide DW3 evidence.
- [PC layout evidence](KOEI_FORMATS.md) records the actual DW8/PW3 sample hashes,
  codec sources and field references; [Origins evidence](ORIGINS_FORMAT.md)
  records its actual encrypted reference and unsuccessful codec trials.
- [Game mechanics research](GAME_MECHANICS.md) records the inspected PC runtime,
  tutorial and console references. Runtime addresses are never used as disk offsets.
- [Ludusavi manifest](https://github.com/mtkennerly/ludusavi-manifest/blob/f956ad520f4bea18097ec21af6418bcc37a3bb9d/data/manifest.yaml),
  commit `f956ad520f4bea18097ec21af6418bcc37a3bb9d`, corroborates Windows paths
  and Steam app IDs: DW7 DE 968790, DW8 Empires 322520, DW9 730310, DW9 Empires
  1341200, SW4-II 348470, SW4 DX 2719200, SW5 1591530, Sanada 595740,
  WO3 DE 1879330, WO4 831560, Persona 5 Strikers 1382330, Dragon Quest Heroes
  410850, Dragon Quest Heroes II 574050 and Warriors: Abyss 3178350. This proves neither
  save decryption nor current storefront availability.
- [Persona 5 Strikers PC utility](https://github.com/zarroboogs/p5spc.saveutil/tree/2462a2043aba3bc551d2eb6b732a81d2374aa826),
  commit `2462a2043aba3bc551d2eb6b732a81d2374aa826`, explicitly handles PC saves
  using account-seeded encryption. The independent `src/koei_editor/research/p5s/p5s_codec.py` now reproduces
  a published 32-byte vector without an account ID; complete-file integrity and
  gameplay editing remain unverified. Third-party implementation/account data are not shipped.
- [Dragon Quest Heroes PC runtime table](https://github.com/Hexorg/CheatEngineTables/blob/0e7092b235f62ee5af4d3942c4323eb6c414f9c6/tables/dqh_966.ct),
  commit `0e7092b235f62ee5af4d3942c4323eb6c414f9c6`, distinguishes EXP, level,
  skill points and skill-tree state, but supplies no validated disk offsets.

The Persona 5 Strikers utility declares account-seeded byte encryption, ten slots
and PC size `0x55DEA0`. Its source does not establish editable gameplay fields and
does not independently validate the incoming checksum before rewriting a trailer
byte. A production adapter needs stronger identity/integrity checks against a real
PC sample; the utility was inspected, not run.

Repository searches were bounded and some became rate limited. Steam guides
and discussions were accessible in the renewed pass; several download hosts,
manuals and wiki requests remained blocked by the environment network policy. These
results describe the evidence inspected, not an exhaustive search of the internet.
No downloaded trainer or third-party utility was executed.

Further titles can qualify when an actual native PC file can be identified,
decoded, edited at corroborated gameplay fields, re-encoded with correct integrity
data and reparsed while preserving unrelated bytes. Controlled game load/re-save
checks remain a separate requirement before claiming in-game validation.
