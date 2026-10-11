# PSP Orochi and Samurai Special edition research

Reviewed 2026-10-11. These are **unregistered research candidates**, with no
implemented gameplay editor or claimed save compatibility. This note separates
product evidence, observed archives, PSP transport integrity and the still
unmapped game payload. For Dynasty Warriors 7 Special, see
[DW7_SPECIAL_PSP_RESEARCH.md](DW7_SPECIAL_PSP_RESEARCH.md).

## Product identity and numbering

| Candidate | Verified Japanese product and platform | Numbering and qualification |
| --- | --- | --- |
| Warriors Orochi 3 Special | **無双OROCHI２ Special / Musou Orochi 2 Special**, PSP. The publisher's [Japanese catalog](https://www.gamecity.ne.jp/products/products/ee/Rlorochi2sp.htm) lists UMD and downloadable PSP editions; its download also runs on PS Vita as a PSP title. | Japanese Orochi **2** belongs to the Western Warriors Orochi **3** family. The publisher's same Steam product is [Orochi 2 Ultimate in Japanese](https://store.steampowered.com/app/1879330/WARRIORS_OROCHI_3_Ultimate_Definitive_Edition/?l=japanese) and [Warriors Orochi 3 Ultimate in English](https://store.steampowered.com/app/1879330/WARRIORS_OROCHI_3_Ultimate_Definitive_Edition/?l=english). That verifies family numbering, not PSP save compatibility. “Warriors Orochi 3 Special” is a Western-numbered research alias; no official Western PSP Special release was verified here. |
| Samurai Warriors 3 Z Special | **戦国無双３ Z Special / Sengoku Musou 3 Z Special**, PSP, original Japanese release **2012-02-16**, confirmed by the [publisher's series history](https://www.gamecity.ne.jp/sengoku/history.html) and [original product site](https://www.gamecity.ne.jp/sengoku3/zsp/). | This is the **3** family in Japanese and Western numbering; [Nintendo's Western Wii product](https://www.nintendo.com/en-gb/Games/Wii/Samurai-Warriors-3-282959.html) is Samurai Warriors 3. “Samurai Warriors 3 Z Special” is an English family alias, not evidence of a Western PSP release. The later [publisher catalog](https://www.gamecity.ne.jp/products/products/ee/Rlsengoku3zsp.htm) lists PSP UMD/download and PS Vita execution of the PSP download. |

The Orochi publisher catalog now describes the **2014-09-11 PSP the Best**
reissue; it must not be cited as the original release date. Contemporary
[coverage of the publisher announcement](https://game.watch.impress.co.jp/docs/news/540310.html)
reports **2012-07-19** for the original PSP product. The Samurai catalog describes
the **2014-01-16 PSP the Best** reissue, distinct from its verified original date.
UMD, download and budget reissues need independent save-revision qualification.
No Chinese, Taiwanese or other regional payload variant of either PSP product
was demonstrated. A translated listing or fan translation is not a native
regional edition or a verified parser profile.

## Edition mechanics and dependencies

The [Orochi catalog](https://www.gamecity.ne.jp/products/products/ee/Rlorochi2sp.htm)
confirms Rachel and Abe no Seimei as PSP additions, more than 130 playable
characters, inter-character bonds affecting actions and story, three-person
teams, editable/shared battlefields, four-person Battle Royal and two-person
cooperative play. Its [mobile product page](https://www.gamecity.ne.jp/orochi2/m/)
also confirms a character-growth reset. Presence of PS3 **無双OROCHI２** save data
on the Memory Stick supplies an initial character-unlock bonus. This is a
documented bonus, not evidence of direct PS3-to-PSP progression serialization.
The [PSP DLC list](https://www.gamecity.ne.jp/orochi2/psp_dlc/) documents additional
content separately from the base product.

The [Samurai catalog](https://www.gamecity.ne.jp/products/products/ee/Rlsengoku3zsp.htm)
confirms 40 playable characters with individual stories, custom officers,
Musou/Free/Creation/Challenge/Sengoku History modes, two-person cooperation and
four-person Challenge competition. The inherited Z roster makes Gracia,
Masanori Fukushima and Aya playable, as documented by the
[publisher's Z catalog](https://www.gamecity.ne.jp/products/products/ee/Rlsengoku3z.htm).
Presence of PS3 **戦国無双３ Z** or
**戦国無双３ Empires** saves supplies an initial character-unlock bonus. The
[publisher's social-campaign page](https://www.gamecity.ne.jp/sengoku3/zsp/zspnob100/)
links story-clear passwords and social-game rewards to unlock currency; it
records the service end, so that historical dependency must not be presented as
a currently usable online feature. [Costume DLC](https://www.gamecity.ne.jp/sengoku3/zsp/dlc/)
is separately documented. The [Special-compatible official guide listing](https://www.gamecity.ne.jp/media/book/game/musou/sengoku3z_cpg_sp2.htm)
identifies the PSP and PS3 products separately and describes their story/mode
coverage; it does not publish serialization offsets.

The following work remains blocked on controlled game-action pairs. None of
these concepts currently has a writable offset, valid-value domain or proved
maximum in this project:

| Candidate | Required mechanic qualification |
| --- | --- |
| Orochi 2 Special | Separate officer identity/unlock, current growth, accumulated resources and growth reset; identify Rachel/Seimei records; prove weapons, fusion/attributes, inventory versus equipped references, bond changes, battlefield records and clear/reward dependencies. DLC ownership/content and PS3-presence bonus must remain distinct from story completion. |
| Samurai 3 Z Special | Separate officer/custom-officer identity, current growth, unlock currency, story and mode completion; prove weapon/armor acquisition, skills, upgrades/material consumption, equipped references, rare-equipment prerequisites and challenge records. DLC and historical campaign rewards require their own evidence. |

## Archive observations and source review

Three public archive copies listed in the [Apollo Samurai PSP collection](https://bucanero.github.io/apollo-saves/PSP/ULJM06024/)
were inspected statically outside the checkout. No downloaded binary or game
was executed, and no player content, identifiers, hashes or assets are committed.
These are third-party submitted references, **not independently owner-qualified
native fixtures or controlled before/after pairs**.

All three have a `DATA.BIN` of **159,792 bytes** and a `PARAM.SFO` of **4,912
bytes**. Their SFO files structurally declare `DATA.BIN` in
`SAVEDATA_FILE_LIST` and have `SAVEDATA_PARAMS` first byte **0x41**. The pinned
[PPSSPP savedata implementation](https://github.com/hrydgard/ppsspp/blob/921a0d7083f2fa663c109a9d37c845017b7093a1/Core/Dialog/SavedataParam.cpp)
classifies that flag as encrypted mode 5. This establishes an encrypted-container
lead, not successful authentication, decryption or a game-layout revision.
One archive also contains `PARAM.PFD` and `PLAYDATA.BIN`, characteristic PS3
export artifacts. Those extra entries are not qualified PSP data and prevent
blind reuse of the entire archive as a clean console fixture.

The Samurai publisher's **256 KB** save requirement and Orochi publisher's
**600 KB** requirement are storage requirements, not exact decoded payload
sizes or parser acceptance rules. No decoded payload size is proved here.

The [Orochi GameFAQs save listing](https://gamefaqs.gamespot.com/psp/670348-musou-orochi-2-special/saves)
is a candidate source, but direct retrieval returned **HTTP 403**. The attempted
Brewology and The Tech Game save-page requests also returned **HTTP 403**. No
Orochi payload bytes or complete authenticated export were acquired. The
Apollo collection did not provide an Orochi Special directory during this
review; its support for other Orochi PSP products is not interchangeable.

Searches found runtime cheat lists, public save submissions and a general
web-based PSP editing service, but no reviewed licensed source mapping these
two games' disk payloads and native integrity. Cheat targets are not natural
gameplay maxima, and RAM addresses are not disk offsets. Existing Orochi 2
modding tools target **Western Warriors Orochi 2 / Japanese Maou Sairin**, a
different game. The project's existing PC Orochi Z, PC Orochi 3 Ultimate and
PS3 Samurai adapters establish no PSP compatibility.

PPSSPP's savedata implementation is GPL-2.0-or-later. It was read for factual
transport behavior; no implementation or key tables were copied. Public save
availability grants neither owner context nor permission to redistribute player
data or assets. No third-party gameplay editor code is incorporated by this note.

## PSP envelope and import responsibilities

A console Memory Stick save directory, an authenticated decrypted export,
an emulator's decrypted disk save and an emulator save state are different
inputs. PPSSPP's [pinned savedata implementation](https://github.com/hrydgard/ppsspp/blob/921a0d7083f2fa663c109a9d37c845017b7093a1/Core/Dialog/SavedataParam.cpp)
shows encrypted payloads carry a 16-byte IV and secure-file hash; `PARAM.SFO`
stores secure-file list hashes and savedata integrity parameters. Encryption
depends on secure mode, SDK/secure version and game key, and PPSSPP can also
write unencrypted disk saves. SFO identity strings alone cannot authenticate a
foreign payload or establish its edition/revision.

A future payload-only editor must require a separately authenticated decrypted
export with exact product/build and export-tool context. The qualified export
tool remains responsible for console decryption, reinsertion, encryption and
the associated SFO hashes. Preserve the complete original directory. The editor
must still prove and validate any **game-specific payload integrity**; PSP
transport authentication does not replace it. Successful emulator parsing does
not prove real-console import. Do not copy PPSSPP's compatibility paths that
retry without an expected hash, repair corrupt input or drop integrity checks.

The historical [PPSSPP transfer issue](https://github.com/hrydgard/ppsspp/issues/5821)
explicitly names both products. A later comment reports Orochi Special working
again; neither the old failure nor that resolution qualifies this editor's
payload writer, transport roundtrip or real-PSP load.

## Implemented read-only structural inspector

[envelope.py](../src/koei_editor/research/psp_special/envelope.py) independently
implements `inspect_envelope(profile_id, sfo_bytes, encrypted_data)`. It is
unregistered research code with no GUI card, serializer, decryption or MAC
verification. These are the only observed profiles accepted:

| Profile ID | Exact public SFO product title | Exact observed directory | Encrypted DATA.BIN bytes |
| --- | --- | --- | --- |
| `dw6special_psp` | 真・三國無双５ Special | `ULJM055240000` | 168,592 |
| `dw7special_psp` | 真・三國無双6 Special | `ULJM05938SAVEDATA08` | 297,481 |
| `sw3zspecial_psp` | 戦国無双３ Z Special | `ULJM06024SAVEDATA00` | 159,792 |

The Dynasty observations and provenance are recorded in
[DW6_SPECIAL_REGIONAL_RESEARCH.md](DW6_SPECIAL_REGIONAL_RESEARCH.md) and
[DW7_SPECIAL_PSP_RESEARCH.md](DW7_SPECIAL_PSP_RESEARCH.md). Orochi Special has no
profile because no export was acquired. The exact slot suffixes are observations,
not inferred acceptance of all slots, languages or reissues.

Each inspected SFO must be 4,912 bytes, version 0x101, category `MS`, and have
the selected public product title and directory. The parser bounds index/key/data
regions, field types, declared sizes, allocation overlap and duplicate keys.
It requires the observed 128-byte secure parameters with flag 0x41 and the
3,168-byte file list with one `DATA.BIN` entry declaring a nonzero MAC. The
[native file-list declaration](https://github.com/hrydgard/ppsspp/blob/921a0d7083f2fa663c109a9d37c845017b7093a1/Core/Dialog/SavedataParam.h)
places 13 filename bytes before the 16-byte hash and three padding bytes. Those
padding bytes are preserved and cannot substitute for a missing hash. That
stored MAC is **not verified**. Only whitelisted product labels, declaration and
lengths are returned, alongside `envelope_authenticated=False` and
`payload_layout_verified=False`. Player strings, keys, stored MACs, owner context
and unknown metadata are never returned or included in errors. All bytes stay
unchanged in memory; no save is written.

The [focused tests](../tests/test_psp_special_envelope.py) contain 12 procedural
cases for malformed/foreign/truncated input, exact profiles, duplicate keys,
overlapping ranges, secure flags, file-list bounds/duplicates and private-text
non-disclosure. A same-length altered encrypted payload deliberately still
matches structure and retains both false verification flags; this makes the
authentication limit explicit. Three optional submitted-file cases use
`DW6_SPECIAL_PSP_ENVELOPE_ZIP`, `DW7_SPECIAL_PSP_ENVELOPE_ZIP` and
`SW3Z_SPECIAL_PSP_ENVELOPE_ZIP` for privately copied ZIP archives. They check only
the selected SFO/DATA pair and byte preservation of the input archive, not its
unrelated contents or complete-export authenticity.

The focused suite passed **15 tests, zero skips**, with all three acquired
references configured. With no fixture variables it passed 12 cases and skipped
the 3 optional cases. The additional two Samurai reference archives also matched
the inspector's SFO/DATA profile; the mixed archive's PS3 extras remain unqualified.

## Exact remaining inputs and validation status

Independent review reproduced a file-list hash-offset error in the first
implementation: padding could substitute for the final hash bytes, while a hash
present only at its native first byte could be rejected. The corrected parser
and procedural generator follow the native declaration, with both adversarial
regressions. The full suite was restarted after this correction; no pre-fix run
is counted as final validation.

For each product obtain a complete, unmodified console export with privately
recorded product/region/build, firmware and DLC context; a matching decrypted
export whose tool validates the console envelope; an unchanged control; and
single-action pairs with displayed values for the mechanics above. Determine
native identity/revision markers, record layout, encoding, integrity algorithm
and coverage before enabling writes. Keep keys and player context private.

Once mapped, use the existing scalar contract and shared GUI to prove byte-exact
unchanged serialization, surgical field/integrity edits, unusual-value
preservation, malformed/foreign rejection, dependency handling, staged Undo,
Review Changes, automatic backups and safe Save As. Transport reimport and
actual load/re-save on the exact game/platform remain separate checks.

**Current results:** three static Samurai archives inspected and a read-only
structural inspector implemented; zero
authenticated decrypt/encode roundtrips; zero proved gameplay fields; zero
surgical edit tests; zero game-load validations. No GUI/editor integration was
added for either candidate. Missing keys/authenticated decrypted references,
native payload integrity, edition/revision identity and controlled-action
evidence are concrete blockers, so neither candidate belongs in the supported
inventory.
