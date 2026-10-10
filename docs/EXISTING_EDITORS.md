# Existing save-editor review

Reviewed 2026-10-09 against Windows PC editions, published source, licences and
actual test data. This is contributor evidence, not an application research menu.
The tables below retain the earlier review and access results. Later native
research and newly acquired samples supersede its unresolved download claims;
see [current coverage](EXPANSION_COVERAGE.md) and the linked game documents.
Finding an existing editor is useful, but an asset unpacker, process trainer or
console editor does not establish a compatible native PC disk-save writer.

## Later expansion findings

- The licensed Musou expansion independently implements qualified Gundam and
  Ken's Rage PS3 export controls from public patches and genuine-file evidence.
  See [exact profiles, dependencies and blockers](LICENSED_MUSOU.md). Console
  reimport/signing and actual edited game-load tests remain external.

- Native executable analysis and genuine files now support DW7 XL Definitive,
  WO3 Ultimate Definitive, SW4 DX, PW4, Orochi Z and All-Stars PC controls.
  DW9 Empires SYSTEMDATA quantity editing is native-source-backed; a genuine
  current PC fixture and campaign maps remain missing.
- Independent implementations now cover DW6 PC and specific decrypted DW7,
  DW7 Empires and SW4 PS3 profiles. Apollo patches provide factual leads;
  signing/import stays with the console export tool.
- Hyrule Warriors Wii U, Definitive Edition Switch, Age of Calamity Switch and
  Fire Emblem Warriors Switch have native player-file qualification. Published
  editor/catalog observations informed independent mappings, with source and
  licence boundaries recorded in their individual format documents.
- Legacy Xbox360 editor downloads and PS4 commercial-editor screenshots do
  not qualify a gameplay profile or grant implementation-reuse permission.
  Independent research remains possible with extracted/decrypted native files,
  integrity rules and controlled pairs listed in [REMAINING_INPUTS.md](REMAINING_INPUTS.md).

## Usable source and implemented work

| Source | Platform and licence | Result |
| --- | --- | --- |
| [Tartarshia/Sophie2SaveEditor](https://github.com/Tartarshia/Sophie2SaveEditor/tree/93d807072a852c73799394af4d32fb164841cd3e) | Atelier Sophie 2, Steam Windows 1.08; MIT | Codec adapted and existing item/equipment quality plus two alchemy EXP fields integrated into the master editor. Exact upstream vectors, procedural edits, integrity, preservation, safety and GUI workflows tested. Independent native fixture and in-game load pending. |
| [mi5hmash/KatanaSaveDataResigner](https://github.com/mi5hmash/KatanaSaveDataResigner/tree/4c90a2b388438cb27a9752e6eab7333257de215f) | PC Nioh 1/2/3, Stranger of Paradise and Wo Long; MIT | Source-only codecs implemented. Complete supplied Nioh/SOP cipher pairs match, but their gameplay integrity is unmapped. Wo Long cipher pair matches; its supplied dummy fails native checksum and JSON checks. No gameplay cards added. |
| [alfizari/Nioh-2-Save-Editor](https://github.com/alfizari/Nioh-2-Save-Editor/tree/7de1e3d5b20b7f94b055eb228a5e3b0746ea1452) | Nioh 2 PC and PS4; Apache-2.0 | PC sample and 20 scalar offsets independently inspected. Upstream clears four integrity flags instead of recalculating checksums. Our parser preserves them, is read-only and rejects writes. Level and stat dependencies also need controlled mapping. |

The Sophie 2 adapter uses the shared GUI and copy-storage safeguards; it does not
embed the upstream executable, overwrite live saves, clone items or start another
application. See [ATELIER_SOPHIE2_FORMAT.md](ATELIER_SOPHIE2_FORMAT.md).
All reused source has its attribution and licence retained. No player save,
account context or third-party binary is included in public packages.

## Other concrete tools and leads

| Game/source | Finding and remaining requirement |
| --- | --- |
| [Persona 5 Strikers editor](https://github.com/Amuyea-gbatemp/Persona-5-Strikers-Scramble-Save-Editor/tree/7466afbb3c1bbcf550d4ff5c18e293103969e678) | GPLv3 gameplay editor, tested on Switch; README explicitly says PC/PS4 untested. Extensive mappings are a lead, but a complete native PC fixture and integrity validation are still needed. No GPL code was copied. A historical 255-value bug was reported fixed; it is not asserted as a current defect. |
| [Ninja Gaiden 2 Black editor](https://github.com/real-guilty/NG2B-Save-Editor) | Repository contains packaged builds rather than the editable implementation needed for a reviewed integration; no reusable source licence established. No binary was executed or redistributed. |
| [GokonSoftworks](https://github.com/PythWare/GokonSoftworks/tree/049d7f98eadd6670eeb7a74723fd7aade4643b5c) | Supports Warriors asset modding, not native save parsing. Its licence forbids redistribution without written permission. Not integrated. |
| [DW9 Empires disk-hex report](https://steamcommunity.com/app/1341200/discussions/0/4299250686372801354/#c4362302823051493652) | Native PC user reports successful voice swaps without DW8E-style decoding. No file, offsets, integrity coverage or revision constraints were provided, so the report is not an implemented writer. |
| [SW4 DX annotated PC save](https://steamcommunity.com/app/2719200/discussions/0/4703539571985644358/) | Links a completed native-PC save on Google Drive. A [second thread](https://steamcommunity.com/app/2719200/discussions/0/4337608193025670211/) links Easyupload. Both hosts blocked download here before bytes arrived; no cipher was tested. |
| DW7 Definitive, DW8 Empires, DW9, SW4-II/5, Warriors Orochi | Rechecked accessible repositories, Steam discussions and prior leads. No additional licensed native PC gameplay writer or usable new native fixture was acquired. Prior evidence remains in [PC_RESEARCH_RETRY.md](PC_RESEARCH_RETRY.md). |
| PW4, Berserk and Origins | New GitHub/Steam searches found no qualifying disk editor. PW4 runtime SDK and Berserk trainer remain process/asset references. Origins' published save and asset-source revisions were unchanged; no new save-specific decoder appeared. |

## Search limits

Ordinary Nexus Mods requests for Origins, PW4, Berserk, P5S, DW9/DW9E, SW4 DX
and WO4 returned proxy `Tunnel connection failed: 403 Forbidden`. Google, Bing,
DuckDuckGo, Fearless Revolution, GBATemp and save-editor.com were also blocked
for the requests made. Their contents and editor availability were not verified.
Some GitHub queries returned HTTP 429; those are rate-limit results, not empty
searches. GitHub repository HTML/git and many Steam pages were accessible.
No access controls were bypassed and no downloaded executable or trainer was run.

Nexus's inaccessible pages do not prove no editor exists. Likewise, a download
block is not a failed decryption attempt. Useful next inputs are a genuine copied
Sophie 2 Steam 1.08 `data.dat`, valid Wo Long PC data, complete native P5S data,
or the annotated SW4 DX files; Nioh/SOP additionally need native gameplay
checksum rules before editing can be enabled. Provide controlled before/after
values and an unchanged control; keep saves and account data private.
