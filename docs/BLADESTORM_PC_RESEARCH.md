# Bladestorm: Nightmare — Windows PC candidate

This optional candidate remains unsupported. A freely shared native PC save
archive was acquired privately, but the required strong PC save-format source
and independently qualified integrity/field mappings were not found. No adapter,
library entry, gameplay edits or support metadata are added on this evidence.

## Evidence and edition separation

- The [official Steam page](https://store.steampowered.com/app/350310/) identifies
  the Windows game as **Bladestorm: Nightmare**, app 350310, released in May 2015.
- A [public PC player-save listing](https://dl.3dmgame.com/patch/61378.html)
  describes a July 2015 Hundred Years' War campaign with all characters and
  four-star mercenary progress. Its freely downloadable archive was inspected
  without executing anything. Raw download URLs, player contents and hashes
  remain outside Git.
- The archive contains six `ORIGINALDATA*/SAVEDATA.BIN` manual/autosave files of
  158,140 bytes (`0x269BC`), one `PERSONALDATA/SAVEDATA.BIN` of 270,536 bytes
  (`0x420C8`), and a 96-byte `inputmap.dat`. These are distinct files; campaign
  progress and personal progression must not be treated as interchangeable.
- Summary text and sparse structured binary data are visible without decoding.
  This observation establishes neither the absence of integrity checks nor a
  writable field map. A visible summary is not a title/revision discriminator.
  The listing's language label does not qualify the actual build/region or
  localized serialization; those remain unresolved.
- [MarkH221/BladestormSaveEditor](https://github.com/MarkH221/BladestormSaveEditor)
  explicitly targets Xbox 360 and predates Nightmare's Windows release. GitHub
  reports no licence. Its code, offsets, caps and console framing were not
  imported or applied to the PC files.
- The historical [PythWare research discussion](https://www.reddit.com/r/dynastywarriors/comments/1gp94od/)
  now has a deleted main post. Current PythWare repository searches found asset
  modding tools, not a Nightmare PC save editor. Historical plaintext claims
  are insufficient integrity/identity proof and are not presented as verified
  PC format documentation.

GitHub, Steam discussions, Nexus and forum searches did not produce a qualified
Nightmare PC disk-format editor or checksum/record specification. Trainers and
commercial PS4 feature lists do not qualify native Windows saves. The 2007
console game and Nightmare console editions remain separate research lanes.

## Mechanics and exact blockers

The [official Windows manual](https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/350310/manuals/steam%28digital%29_BSN-EN.pdf)
distinguishes personal data, campaign slots, spendable gold/SP, Books, support
and action skills, owned equipment and equipped references. Equipment affects
abilities only when equipped. Book growth awards SP; spending SP can develop
skills or Book levels. Registered mercenary name and gender cannot be changed
through the game's normal edit flow. These dependencies constrain future work.

| System | Required evidence before native editing |
| --- | --- |
| Identity, framing and integrity | Untouched title/build/region-labelled native campaign and personal copies; native loading/checksum source or equivalent independently verified format research; revision markers, block boundaries and integrity coverage. No checksum is guessed from another Koei game. |
| Gold and SP | One recorded reward or purchase pair plus unchanged control; per-file/record ownership, current-versus-total semantics, storage widths and actual bounds. Existing campaign snapshots alone do not prove which value is spendable. |
| Books, EXP, proficiency and skills | Existing Book identities, acquisition masks, growth thresholds, SP awards/costs and skill prerequisites; controlled level-up and skill-purchase pairs. Resource edits must not silently grant growth rewards. |
| Equipment and inventories | Item/Book association, occupied records, quantities, natural caps and separately qualified equipped references; acquisition and equip/unequip pairs. No equipment, item or Book is manufactured from a plausible record. |
| Hired squads and Pennons | Native owned/count records, summon inventory, assignments and costs; separate purchase and summon pairs. Leadership effects must not be substituted for stored squad counts. |
| Mercenary customization and party | Occupancy and identity schema, edit-mode field dependencies, existing squad/character references; before/after appearance and party-assignment copies. Name/gender writes remain excluded without an independently qualified valid transition. |
| Fame, relationships, story, exploration and collections | Labelled campaign/diary/gallery identifiers, prerequisite and reward masks, controlled unlock/clear pairs. Fame and story completion are separate from gold/SP, and content unlocks are not inferred from campaign summaries. |
| Other regions, Nightmare campaign and revisions | Separate genuine samples and layouts. The acquired Hundred Years' War archive does not qualify Nightmare campaign serialization or every supported language. |
| Validation | A parser-qualified genuine byte-exact roundtrip, surgical edits, malformed/corrupt rejection and copied-save GUI backup/restore checks remain pending. No actual game-load test has been performed. |

Acquiring genuine files closed the missing-fixture lead only. This candidate
does not satisfy the additional-game implementation gate until the PC native
format evidence and dependencies above are independently established.
