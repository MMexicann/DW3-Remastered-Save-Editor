# Shin Sangokumusou 6 Special: PSP research

Reviewed 2026-10-11. This edition remains **unregistered and unimplemented**.
One publicly shared save archive was inspected as data, but its gameplay payload
was not decrypted or authenticated. No downloaded executable was run, no save or
game asset is included in the checkout, and no edited file was loaded in-game.

## Product, numbering and regional qualification

| Claim | Evidence and limit |
| --- | --- |
| Japanese title and platform | Koei Tecmo's [product catalog](https://www.gamecity.ne.jp/products/products/ee/Rlsmusou6sp.htm) identifies **真・三國無双６ Special**, a PSP product on two UMDs. It separately lists a PSP download compatible with PS Vita. Vita compatibility does not establish a native Vita save format. |
| Original Japanese release | The publisher's [2011 event news](https://www.gamecity.ne.jp/media/event/2011/smusou/news/) announces the PSP title for August 25. Contemporary [release coverage](https://game.watch.impress.co.jp/docs/news/472709.html) records the August 25, 2011 launch. The current catalog dates its later Best/download SKUs separately. |
| Japanese/Western numbering | The publisher's [anniversary history](https://www.koeitecmoamerica.com/smusou25th/us/history/titles/smusou_06.html) explicitly pairs **Shin Sangoku Musou 6** with **DYNASTY WARRIORS 7**. Thus “DW7 Special” identifies this PSP candidate using Western numbering; it does not establish a Western-localized PSP release. |
| Taiwanese regional title | The official [Taiwan PSP catalog](https://www.gamecity.com.tw/products/psp.htm) lists **真・三國無雙６ Special** and links the Japanese product page. This verifies regional catalog branding, not a Traditional Chinese translation or a distinct save layout. |

The publisher quotes a 450 KB save-space requirement. This is storage allocation
for the save package, **not** a proved gameplay file size or decoder constraint.
Chinese fan translations, store descriptions and emulator reports require their
own provenance; neither translated branding nor a reported executable revision
qualifies a native serialization revision.

## Edition mechanics and dependencies

The publisher's [PSP feature description](https://www.gamecity.ne.jp/smusou6/m/psp/features.htm)
confirms Story play with a selected officer, two-player Story cooperation,
Chronicle cooperation and up to four-player score competition. It also confirms
buying growth items with money, resetting grown officer abilities, and unlocking
all characters when a PS3 base-game save is present on the Memory Stick.

The [product catalog](https://www.gamecity.ne.jp/products/products/ee/Rlsmusou6sp.htm)
describes four faction stories including Jin, two equipped weapons and switching
attacks, plus Chronicle progression and equipment acquisition. These are
mechanics evidence; their PSP byte offsets, IDs, limits and reward state are not
mapped. The cited pages do not establish PSP-exclusive added characters or an
XL roster extension. In particular, the PC XL adapter's 65 playable slots must
not be imported into this PSP profile by assumption.

| Mechanic | Required mapping before writes |
| --- | --- |
| Money and purchased growth items | Spendable balance, purchase consumption, officer stat increments, legitimate bounds and any cumulative totals must be distinguished using one-action pairs. |
| Officer abilities and reset | Prove base/current stats, growth and skill records, reset effects, field encodings and dependencies. Preserve unusual values rather than substituting PC limits. |
| Weapons and equipment | Prove native weapon IDs, ownership, inventory record structure, equipped references, switching state, seals/learning and acquisition rewards separately. |
| Character availability | Distinguish normal Story/Chronicle unlocks from the PS3-save-presence bonus. Presence of PS3 data is a bonus trigger, not proof of cross-platform save interchangeability. |
| Story, Chronicle and competition | Identify completion, selectable stages, rewards, high scores and any cooperative/competitive records separately. Stats must not silently set progress or unlock flags. |

## Public sample: envelope observation only

The [Apollo saves mirror](https://github.com/bucanero/apollo-saves/tree/c6fa97f2f4ef1b3469f0421c727997108821e188/PSP/ULJM05938)
contains one publicly shared archive. Its description reports all characters
unlocked, some maximized officer stats, almost all weapons and all animals. It
contains a Brewology download README and matches the description in
[Brewology's listing](https://psp.brewology.com/gamesaves/savedgames.php?g=780202&l=s&system=psp).
Treat the mirror and that listing as one source lineage, not two independent
native samples. Whether this progressed state was modified was not established.

Static archive/SFO inspection observed:

- `DATA.BIN`: **297,481 bytes**; `PARAM.SFO`: **4,912 bytes**.
- Metadata identifies PSP category `MS` and title `真・三國無双6 Special`.
- The package directory's public title prefix is `ULJM05938`.
- `SAVEDATA_FILE_LIST` identifies `DATA.BIN` with a nonzero file hash.
- `SAVEDATA_PARAMS` starts with `0x41`, which the pinned
  [PPSSPP implementation](https://github.com/hrydgard/ppsspp/blob/921a0d7083f2fa663c109a9d37c845017b7093a1/Core/Dialog/SavedataParam.cpp)
  interprets as PSP secure mode 5.

These are **observations of metadata**, not proof that the package MACs are valid,
that it was created on console, or that it belongs to a particular native
gameplay revision. An unaligned stored length alone does not disqualify a PSP
secure file: PPSSPP's writer stores the payload length plus the 16-byte IV while
handling alignment internally. The metadata does not disclose the title key or
prove any game-level checksum. No payload offset, natural Max limit or writer is
derived from this archive.

See [PSP Special research](PSP_SPECIAL_RESEARCH.md) for encrypted-console versus
decrypted-export handling and the separate import/encryption responsibilities.

## Source review and exact blockers

No licensed, title-specific PSP disk-save editor source was located in this
research pass. Search results for `356Editor`, Shin Sangokumusou 6 Moushouden
and PC/PS3 cheat patches concern different editions or memory editing. The
existing [PC DW7 XL format](DYNASTY_RESEARCH.md) and [PS3 profiles](PS3_EXPANSION.md)
are independently qualified formats; they do not establish PSP compatibility.
The [save-editor title thread](https://web.save-editor.com/bbs/savedata/psp/bbs.cgi?list=pickup&num=3057)
was an administrator placeholder with no posted save or field mapping.

The GameFAQs save endpoint and direct save-editor patch request returned HTTP
403 in this environment. Brewology's direct download redirected to registration.
A separate uploader advertised a modified save but required a download password;
its referenced public blog article/password was not located. Those failures are
access blockers, not failed decryption attempts or proof that no editor exists.
No registration or access control was bypassed. PPSSPP's GPL source supplied
factual envelope references only; no implementation was copied into the editor.

The next concrete inputs are a complete owner-qualified PSP save package and
matching authenticated decrypted export, with edition/language/game build and
export-tool settings recorded privately. Native title-key/mode authentication,
payload identity/revision, lengths, serialization, internal integrity and
byte-exact unchanged roundtrip remain unproved. Controlled pairs should include
one money purchase, one named officer growth/reset, one weapon acquisition/equip,
and one Story/Chronicle unlock, each with displayed values and an unchanged
control. A separate second package is needed to distinguish invariants from
this one progressed sample.

Validation in this pass was limited to archive and SFO structure inspection.
Genuine gameplay roundtrip, surgical field edits, foreign/corrupt payload checks,
integrity repair, GUI editing, backups and actual PSP/PSP-on-Vita game-load tests
were **not performed for this edition**. Registration remains blocked until the
native format and safe edits can be independently proved.
