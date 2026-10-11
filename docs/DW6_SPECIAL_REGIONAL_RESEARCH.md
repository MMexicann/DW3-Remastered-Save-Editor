# Dynasty Warriors 6 Special and regional product qualification

Research reviewed 2026-10-11. **No Special adapter or additional regional
compatibility is registered by this research.** The original Windows editor
remains scoped as described in [DW6_RESEARCH.md](DW6_RESEARCH.md).

## Products, titles and numbering

The publisher's [25th-anniversary history](https://www.koeitecmoamerica.com/smusou25th/us/history/titles/smusou_05.html)
explicitly equates **Shin Sangoku Musou 5** with **Dynasty Warriors 6**, listing
the original game on PS3, Xbox 360 and PC. Japanese/Traditional Chinese 5 is
Western 6 here; Japanese 6 Special is the separate Western 7 generation.

| Product | Established platform and regional evidence | Format status |
| --- | --- | --- |
| 真・三國無双５ Special / Shin Sangoku Musou 5 Special; commonly called Dynasty Warriors 6 Special | Japanese publisher catalog explicitly offers PS2 and PSP. The Western PS2 product uses the title Dynasty Warriors 6. | Independent PS2/PSP format qualification required; the existing original-PC map is not reused. |
| 真．三國無雙５ Special, Chinese PS2 | Taiwan publisher catalog lists release on 2008-10-30, one DVD; Japanese PS2 listing is two DVDs. | Different disc packaging does not establish different save serialization. No Chinese PS2 native fixture qualified. |
| 真．三國無雙５ Special, Chinese PSP | Taiwan publisher's 2009 history records Japanese PSP release on 2009-10-22 and Chinese PSP release on 2009-11-26. | Both products exist; language-specific gameplay layout and crypto compatibility remain unproved. |
| 真‧三國無雙５, Traditional Chinese Windows | Taiwan publisher catalog and 2009 history establish an ordinary Windows release on 2009-07-02, without Special in its product title. | Product existence does not independently qualify the existing Windows parser against this region/build. |
| Reported Chinese Windows “真三国无双5 Special / 特别版” | Third-party download labels found, but no publisher evidence for a native Windows Special product or save profile was established. | Unverified candidate; no adapter, aliases asserting support, offsets or Max values added. |

Primary sources for the platform, packaging and dates above are the
[Japanese mobile catalog](https://www.gamecity.ne.jp/i/catalog/pr/musou5sp.htm),
[Taiwan Special catalog](https://www.gamecity.com.tw/products/products/ee/Rlsmusou5sp.htm),
[Taiwan 2009 release history](https://www.gamecity.com.tw/info_c/history_2009.htm),
and [Taiwan original-game catalog](https://www.gamecity.com.tw/products/products/ee/Rlsmusou5.htm).
The [Japanese PSP delay notice](https://www.gamecity.ne.jp/smusou5sp/index2.htm)
confirms the final October 22 release date; earlier September announcements
are not final-release proof. The Western PS2 branding is visible in the
[publisher's PS2 manual](https://www.videogamemanual.com/PS2/Dynasty%20Warriors%206%20%28USA%29.pdf),
hosted by a manual archive. This does not establish an English PSP release.

The [Japanese catalog](https://www.gamecity.ne.jp/products/products/ee/Rlsmusou5sp.htm)
lists a PSP storage requirement of 704 KB and installation data of 260 MB.
These are storage requirements, **not verified gameplay-payload lengths**.
Similarly the Taiwan PS2 requirement of at least 300 KB does not identify a
native file size, record boundary or checksum range.

## The reported Chinese Windows Special lead

[3DM's listing](https://dl.3dmgame.com/pc/41839.html) illustrates why a PC category
is insufficient evidence: its headline explicitly says PSP version while its
platform metadata says PC; its introduction describes a PSP port of PS2 Special.
The page also mixes Empires mechanics into the Special description. The
[Ali213 “特别版中文pc版” listing](https://3g.ali213.net/down/ss5gfzwzs.html)
provides a Windows label but no independently identified Special build or native
save profile. Neither listing was treated as proof of a publisher Windows port,
and no game download or executable was run.

The publisher's contemporaneous Taiwan record distinguishes ordinary Chinese
Windows from PSP Special. The evidence therefore supports **an unresolved or
conflated download label**, not a categorical claim that no unofficial port or
emulator package could exist. Qualifying a claimed native Windows Special would
first require publisher/distributor product evidence or independently inspected
build provenance, then native saves and its own format proof. An emulator-hosted
PSP edition remains a PSP save format.

## Edition mechanics and dependencies

The Japanese mobile catalog establishes Special story modes and new weapons/
actions for **Cao Pi, Ling Tong, Ma Chao, Zhang He, Taishi Ci and Yue Ying**.
These six are additional Musou-mode participants, not six newly invented roster
identities. PSP additionally introduces **Meng Huo** and ad hoc cooperative play.
Those edition-specific changes prevent assuming that original PC roster,
weapon IDs or progression structures qualify the Special editions.

Publisher catalogs describe Renbu combat and character growth through earned
merit, levels, basic-stat increases and skill points allocated to a skill tree.
That establishes progression dependencies conceptually; it does not prove disk
offsets, valid node masks, EXP thresholds, natural caps or a safe level setter.
Story eligibility, character availability, weapon ownership/equips and gallery
rewards must be mapped separately. Horse growth, transformation, descriptors,
skills and combat limits also require Special-specific evidence rather than
importing the original-PC writer's limits.

| System | Exact remaining proof/input |
| --- | --- |
| Native identity and revision | A complete copied save for each target platform/region/build, companion metadata and reliable edition provenance; native marker/revision/structure checks independent of a filename. |
| PS2 serialization and integrity | Three US exports establish outer framing and a matching additive stored-value relation described below. Native identity/revision beyond the outer basename, independent checksum-routine proof and unchanged native roundtrip remain required. |
| PSP serialization and integrity | A matched encrypted console directory and explicitly decrypted export from the same state; exact filenames/lengths, payload revision, secure mode/key requirements and any game-level integrity. |
| Characters, levels and skill trees | Named before/after/control saves for one legitimate unlock, level-up and skill purchase; Special-specific record identities, reserved bits, costs and stat/reward dependencies. |
| Weapons and equipment | Controlled acquisition/equip pairs and active weapon/element/skill catalogs for the edition; native ownership/equip references, valid combinations and bounds. |
| Horses | Controlled acquisition, level/growth/skill/transform pairs and displayed values; native descriptor/model/element domains and slot rules. |
| Story, stages, challenges and collections | Named clear/objective/reward pairs and unchanged controls; difficulty, first-clear rewards, prerequisite and gallery links kept distinct. |
| Regional reuse | Corresponding same-state native exports from the candidate regions and demonstrated identity/layout/integrity equivalence; translated branding alone is insufficient. |

## Save and editor-source leads

[GameFAQs PSP saves](https://gamefaqs.gamespot.com/psp/961098-shin-sangoku-musou-5-special/saves)
lists three Japanese player submissions. The
[Apollo database listing](https://bucanero.github.io/apollo-saves/PSP/ULJM05524/)
offers one Japanese save described as containing king horses and some level-50
characters. These are leads, not controlled clean/action pairs or proof of the
listed state. [GameFAQs PS2 saves](https://gamefaqs.gamespot.com/ps2/952257-dynasty-warriors-6/saves)
also lists North American CodeBreaker and X-Port exports. Its PS3 uploads are
separate platform evidence and were excluded from PS2 inspection.

The Apollo archive was acquired privately after enabling the execution tool's
network grant. No assets, player save, private hashes or owner context enter
the checkout. Inspection established the following **outer-save observations**:

| Observation | Qualified fact and limit |
| --- | --- |
| Directory/title | Product directory `ULJM055240000`; bounded `PARAM.SFO` title is 真・三國無双５ Special. This identifies the archive's Japanese product metadata, not an authenticated inner gameplay revision. |
| Gameplay container | `DATA.BIN`, 168,592 bytes. This is the observed encrypted container length, not a decoded payload-length requirement. |
| Companion metadata | `PARAM.SFO`, 4,912 bytes; secure parameters are 128 bytes and the first flag is `0x41`; secure file list contains `DATA.BIN` with a nonzero stored file hash. |
| Encoding evidence | `DATA.BIN` has approximately 7.999 bits/byte entropy. Combined with the SFO secure flag/file hash and the PPSSPP mode interpretation, this supports an encrypted PSP secure-save representation. Entropy alone does not authenticate or decrypt it. |

No matching decrypted export or edition-specific key was available. The stored
file/SFO hashes were **not validated**. Inner revision, layout, game checksums,
gameplay field bounds, native serializer and controlled action pairs remain
unqualified. No file was silently decrypted, normalized, re-signed or repaired.

### Native Western PS2 export inspection

Three public submissions were acquired privately: one X-Port export and two
CodeBreaker exports from the PS2-specific sections of the GameFAQs listing.
They are independent submission leads, not controlled clean/action pairs;
submitted completion descriptions were not independently verified. No saves,
icons, player identifiers, extracted payloads or downloaded source enter the
checkout, and no downloaded executable was run.

Container facts were checked using an independently written scratch inspector
and the published framing facts in Ross Ridge's
[public-domain mymc source](https://github.com/ps2dev/mymc/blob/db5d9e1c141cbbc4ba4e374f73a0518a8d75b7ef/ps2save.py).
The X-Port header and bounded entries exposed its directory and files; its
trailing outer checksum was **not validated**. Both CodeBreaker containers
successfully decoded their outer stream using the documented RC4 permutation
and zlib framing. Each zlib stream matched its declared uncompressed length of
289,100 bytes. This is memory-card export framing, not a gameplay encryption or
serializer claim. The existing DW4 parser was not reused or changed.

| Observation | Qualified fact and limit |
| --- | --- |
| Outer regional identity | All three exports name directory `BASLUS-21774` and a same-named gameplay file. This is US PS2 product/container evidence, not an independently authenticated native title or revision marker. |
| Entries and lengths | Each contains `icon.sys` (964 bytes), `musou.ico` (119,016 bytes) and the native gameplay file (168,928 bytes). Only bounded entry metadata and gameplay bytes were inspected; game assets remain private. |
| Inner representation | All three native gameplay files are directly inspectable structured byte streams rather than the observed PSP secure-save representation. This does not establish a shared PC/PSP record layout. |
| Stored additive relation | In all three gameplay files, the little-endian 32-bit value at offset 0 exactly equals the sum of bytes from offset 4 through EOF. The three matching stored values differ, establishing an empirical relation across different submissions. No native game checksum routine was located; completeness, other integrity dependencies and a safe writer remain unproved. |

No gameplay offset acquired a verified semantic meaning from these submissions.
Memory cheats and [the original-PC hex guide](https://game.ali213.net/thread-2189543-1-1.html)
cannot bridge that gap: the guide explicitly targets the ordinary Windows save
under its Documents path, and runtime addresses do not identify serialized
fields. No native revision marker, title-independent format discriminator,
character record identity, level/skill dependency or conservative editable field
was proved. The exact remaining writer inputs are a native serializer/checksum
bridge or controlled PS2 before/after/control exports, followed by unchanged and
surgical native roundtrips and actual game-load/re-save validation. Japanese and
Chinese PS2 regional compatibility still require their own genuine exports.

The existing [cnopt original-PC research](https://github.com/cnopt/dynastywarriors6-reverse-engineering/tree/f2152f67b031091a0268154203d25fa9f65d2664)
and GUI reader remain original Windows leads, with no explicit reusable project
licence established in the existing review. Their code is not copied and their
offsets are not transferred to Special. Searches found binary editor and memory
cheat leads, but no reviewed Special gameplay editor source with a reusable
licence and independently qualified native serialization. Runtime cheat
addresses are not converted into save offsets.

## PSP import/encryption responsibility

The [PPSSPP savedata implementation](https://github.com/hrydgard/ppsspp/blob/921a0d7083f2fa663c109a9d37c845017b7093a1/Core/Dialog/SavedataParam.cpp)
distinguishes encrypted secure saves from decrypted output and maintains
`PARAM.SFO` secure file hashes and parameters when encrypting. Its crypto-mode
and key handling show why a decrypted payload is not automatically a console
importable save. This is general PSP evidence, not proof of Special's exact mode
or key. PPSSPP source is GPL-2.0-or-later; no source was incorporated.

Any future decrypted-export editor must document the exact export tool/version
and accept only its qualified payload profile. Returning an edited payload to a
console requires the appropriate external import/re-encryption workflow and
matching secure metadata. Until independently implemented and tested, this
project cannot promise that operation, alter companion hashes, or disable game
or console integrity to make an edit load.

## Validation status

For Special/regional candidates in this document: **four public save archives
acquired privately**: one Japanese PSP archive and three US PS2 exports. The
PSP SFO/container bounds were inspected; its gameplay payload was not decrypted
and its secure hashes were not validated. All three PS2 native payloads were
bounded and extracted; two CodeBreaker outer streams passed zlib decode and
exact declared-length checks, while the X-Port outer checksum was not checked.
The additive stored-value relation matched **3/3 genuine PS2 payloads**. These
are factual inspections of public submissions, not registered-adapter tests,
controlled gameplay pairs or game integrity validation.

There were **zero unchanged or surgical gameplay codec roundtrips, zero gameplay
field edits, and zero game-load/re-save validations**. No candidate editor GUI
workflow was exercised because no Special adapter was registered. Existing
original-PC test results remain separate in [DW6_RESEARCH.md](DW6_RESEARCH.md).
This work establishes product distinctions, native outer observations and
precise follow-up inputs; it does not extend the supported-game inventory.
