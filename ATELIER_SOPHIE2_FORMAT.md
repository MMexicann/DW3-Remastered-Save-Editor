# Atelier Sophie 2 PC format

The adapter targets the published **Steam Windows 1.08 layout** for
`data.dat` in `AutoSave` / `GameDataNN` slots. It is separate from the Warriors
parsers and rejects other tagged layouts before exposing fields.

Source: [Tartarshia/Sophie2SaveEditor](https://github.com/Tartarshia/Sophie2SaveEditor/tree/93d807072a852c73799394af4d32fb164841cd3e),
MIT licensed. The adapted codec's notice is retained in
[licenses/atelier-sophie2-save-editor-MIT.txt](licenses/atelier-sophie2-save-editor-MIT.txt).
The source describes native Steam 1.08 use and private copied-save integration
tests. Its private saves are not in this project; independent real-save and
in-game checks remain pending.

## Codec and identity

The original 0x100-byte header and codec seed are preserved. The body uses
palette and zero-code compression, word/byte RNG transforms and a bit
permutation. Both integrity values are checked before decoding. Edited output
is rebuilt with its integrity values, decoded again, and compared with the
expected payload and unchanged header/seed/trailer. No-edit serialization
returns the original bytes exactly, including noncanonical compression and
trailing zero data.

The parser requires all five named inventory pools with the published physical
capacities (9999, 150, 50, 15, 25), 0x2c-byte item records, six 0x314-byte Party
records with unique character identities, and the distinctive Sophie/Plachta
alchemy tags. A generic Gust codec match alone cannot select this editor. These
structure checks qualify the implemented layout; they do not prove every future
game build has the same format. Processing limits are defensive bounds, not
native fixed save sizes.

## Editing surface

| Data | Supported behavior |
| --- | --- |
| Existing material, important-item, consumable, gathering-tool and adventure-equipment records | Quality 0–999; empty slots are not created |
| Existing equipment for Sophie, Plachta, Ramizel, Alette, Olias and Diebold | Quality 0–999 in weapon, armor, two accessory and four battle-item records |
| Sophie and Plachta alchemy EXP | Individual/bulk value editing, using the upstream signed 32-bit storage bound; excluded from Max |
| Higher existing quality values | Preserved by Max |
| Inventory counts, equipped item IDs, Plachta raw level and `m_mixGem` | Read-only inspection |

EXP storage width does not establish a gameplay maximum or its relationship to
the separately stored raw level. Item names beyond source-proven character and
slot labels are not guessed. Item IDs, instance IDs, ownership, traits, effects,
usage counts, bonuses, story progress and unknown bytes remain unchanged.
This adapter does not clone items, manufacture unlocks or reinterpret `m_mixGem`.

The common GUI stages changes, supports batch Undo and review, and writes only
to a new destination after backing up and checking the source has not changed.
Live game directories, Steam Cloud folders and resolved aliases are blocked.

## Reproducible checks

```text
python -m unittest discover -s tests -p 'test_atelier_sophie2_format.py' -v
python application.py --game atelier_sophie2 --self-test INPUT_COPY NEW_OUTPUT_DIRECTORY
```

The public suite includes independently constructed tagged records, frozen
upstream codec vectors, malformed input, exact no-op, surgical edit preservation,
Max exclusions, immutable destinations and backup/restore. Upstream differential
checks establish implementation agreement; constructed files are not game saves.
Set `SOPHIE2_SAVE_COPY` to an unchanged native Steam 1.08 copy to run the optional
real-file case. Useful controlled pairs are one item-quality change and one
alchemy EXP gain, with displayed before/after values, language/build labels and
an unchanged control. Keep copies and detailed reports outside the public tree.
