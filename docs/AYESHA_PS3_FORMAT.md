# Atelier Ayesha: qualified decrypted PS3 exports

The unreleased adapter supports the observed US `BLUS31152` and Japanese `BLJM60486` **PS3** `USR-DATA` layout after external decryption. Rename a separate working copy to `.bin`, edit it outside managed/cloud save folders, then use Apollo to reimport and resign the result. It does not handle PS3 account signing, encrypted `USR-DATA`, PC/DX, Vita or the Chinese 1.1 profile used by the older editor.

Three freely shared player exports were decrypted privately using the project's independent mathematical PFD/AES research helper. No game or third-party executable was run. Two Japanese saves provide independent published literal money checks: 110,999 Cole and 304,204 Cole both match the exact big-endian DWORD at `0xBD4C`. The US modified save contains 9,999,999 there. These prove the field and endian mapping; a modified save's advertised maximum is not a legitimate natural-cap proof. No edited save was loaded in an actual game by this project.

## Implemented features and safety

- Individual Cole edits from 0–999,999, a conservative **editor limit**, with higher opened values preserved unchanged. Max does nothing.
- Existing ordinary basket/container stack reductions to 1–their opened quantity. The record must be within the existing occupied prefix, have opened quantity 2–255, a finite quality from 0–120 and the observed zero appraisal word. Empty, unusual or ambiguous records remain inspection only. Stacks cannot be increased, created or deleted. Equipment identities and count-one records stay unchanged.
- Searchable numeric inventory inspection: pool/slot, item ID, instance word, exact float quality rendering, five potential IDs, four effect IDs, quantity and raw appraisal word. Unknown item/property IDs are not assigned guessed names or applicability.
- Two memory-related words inspected separately. They differ in both genuine Japanese files, so the older editor's practice of writing both identically is deliberately excluded. Their precise available/earned/history roles remain unresolved.
- Shared themes, Undo, Review Changes, original snapshot backups, same-read validated restore and atomic new-destination saving. The original export is never replaced.

Changed copies preserve every other byte, including fractional float qualities, record identities, potential/effect IDs, array capacities, unknown tail data and story/progression words. The existing source's lossy quality approximation and unrestricted potential/effect assignment are not incorporated.

## Native profile and record evidence

All three complete decrypted files are exactly 742,400 bytes, start with `0132dc5700000000` and share the same reviewed surrounding inventory serializer markers. The basket has a big-endian capacity word 120 immediately before `0x392BC`, with 32-byte records; its end falls exactly before the next capacity word. The container capacity word is 10,000 at `0x3A1BC`, followed by 32-byte records at `0x3A1C0`. The next structure begins with capacity 100 at `0x883C0`. A preceding serializer word `0004FD98` at `0x392B4` is also required. Other sizes/markers are rejected.

Within a record, the item ID is a big-endian word at +2, quality is a big-endian **float32** at +4, five potential words occupy +8 through +17, the raw appraisal word is at +18, four effect words occupy +20 through +27, and quantity is a big-endian word at +30. The first instance word and remaining words are preserved. The source's packed C# structures and native files corroborate these spans. The older editor reads quality by shifting a little-endian ushort; that loses native fractional values such as 45.555557. Native quantities of 106 and 156 also demonstrate that a display truncated to one byte must not be mistaken for the entire storage type.

The occupied prefix stops at the first `FFFF` item ID; the container also stops at zero quantity, matching the published reader. Dormant records beyond the sentinel are preserved and never activated. A bounded scalar reduction touches only the two quantity bytes of its opened record. Money touches only its four bytes. This adapter does not relocate or serialize whole inventory records.

Optional neighboring `PARAM.SFO` metadata is checked only for the bounded `SAVEDATA_DIRECTORY` title identity, never account values. A conflicting game or unsupported region is rejected for opening, saving and restoring. Standalone structurally qualified copies work without metadata; the profile cannot independently establish the original owner's console account.

## Integrity and console import

`INTEGRITY_KIND` is `external`: PS3 encryption and `PARAM.PFD` authentication are outside the decrypted payload and must be restored through Apollo. The published editor writes these fields directly and updates/re-encrypts the external PFD; no inner game checksum operation is identified in that source. Accordingly, this adapter does **not** claim an aggregate payload checksum or detection of arbitrary corruption in otherwise unknown bytes. It rejects wrong type/size/header/capacity/serializer markers, validates staged fields and verifies byte-preserving reconstruction. Successful codec/GUI checks do not prove a successful console load.

## References and licensing

- [darkautism/AtelierAyeshaSaveEditor](https://github.com/darkautism/AtelierAyeshaSaveEditor/tree/5d70d5abb05ce38324105ba4c6cb3b9d2c6b0732), MIT, explicitly **PS3 Chinese 1.1**. `AtelierAyeshaDataType.cs`, `BasketItem.cs`, `BoxItem.cs`, `Form1.cs` and `Utility.cs` supply factual candidate fields and record spans. This adapter is an original implementation using the project's storage/GUI contracts, not a copy of that editor or its external tools. Chinese support is not inferred from this reference.
- [GameFAQs US/Japanese save index](https://gamefaqs.gamespot.com/ps3/665780-atelier-ayesha-the-alchemist-of-dusk/saves): [US modified export](https://gamefaqs.gamespot.com/ps3/665780-atelier-ayesha-the-alchemist-of-dusk/saves/22964), [Japanese clear export](https://gamefaqs.gamespot.com/ps3/665780-atelier-ayesha-the-alchemist-of-dusk/saves/22729) and [Japanese pre-ending export](https://gamefaqs.gamespot.com/ps3/665780-atelier-ayesha-the-alchemist-of-dusk/saves/22751). Author-supplied Cole descriptions corroborate the two Japanese known answers. All archives, player bytes, metadata and decrypted copies remain outside the repository.
- [Apollo PS3 title catalog](https://github.com/bucanero/apollo-patches/blob/main/PS3/games.conf): title-specific secure-file identity used by the private independent PFD research helper. No account identifiers or console keys are exported by this adapter.
- [GameFAQs Alchemy FAQ](https://gamefaqs.gamespot.com/ps3/665780-atelier-ayesha-the-alchemist-of-dusk/faqs/66736): quality, synthesis, properties and equipment interactions, including endgame quality around 118–120. A guide's synthesis recipe does not prove safe direct edits of property dependencies.

## Coverage and exact blockers

| Mechanic | Implemented / remaining blocker |
| --- | --- |
| Cole | Manual mapped balance; natural maximum and related economy/reward history remain unqualified, so no Max. |
| Basket/container quantities | Reduce existing ordinary positive stacks only; higher/unknown states preserved. Increasing/acquiring/deleting needs item-specific capacity, acquisition and equipped-reference evidence. |
| Item quality, effects and potentials | Read-only exact float/ID inspection. Need item applicability, legal combinations and derived equipment/consumption interactions before writes. |
| Named items/properties | Numeric IDs currently. Need an independently qualified localized ID catalog for these actual profiles; the older editor expects external text tables not present in its source checkout. |
| Alchemy level/EXP and battle levels/stats | Preserved. Need exact native mappings and growth/EXP curves; an edited max-EXP file does not establish legitimate dependencies. |
| Memory points / notebook progression | Two distinct stored words inspected read only. Need controlled spend/earn pairs to identify their roles and unlock requirements. |
| Equipment, accessories, registered items and shop inventories | Preserved. Need references, ownership, item-category constraints and valid derived-value mapping. |
| Calendar/time limit, endings, friendship, requests, events, collectibles and story | Preserved. Need story/prerequisite/reward dependency maps; calendar rewinds are separate from resource edits. |
| Chinese 1.1 / EU / PC-DX / Vita | Unsupported. Need complete genuine exports with matching identity, serialization, integrity and independent field evidence; region/platform cannot be inferred from an editor's title. |
| PS3 reimport and game load | Not performed. Need an owner-operated Apollo reimport/resign and observed game load of an edited copy. |

Focused tests optionally use `AYESHA_PS3_SAVE_COPIES`: three private paths in US-modified, Japanese-clear, Japanese-pre-ending order, separated by the platform path separator. Public tests generate procedural data; no player bytes or personal paths are committed.
