# Game adapters

Read the [root guide](../../../AGENTS.md) and relevant [format checklist](../../../docs/README.md).
Keep each game's codecs, parser, editor, mechanics and presentation in its own
package. DW3 retains its dedicated tagged schema and patch workflow.

Qualify identity/revision/structure/integrity and existing records before writes.
Preserve unknown bytes, seeds, unusual values and higher values during Max. Keep
stored values, derived stats, ownership, equipment references and reward flags
distinct; story completion is separate from resources and content unlocks.

Use shared scalar and safe-storage contracts. Test byte-exact no-op, surgical
edits, corruption/bounds/dependencies, backups/restore, source safety and GUI
workflows. New support also needs registry/metadata/inventory/README/test updates.
No player saves, game binaries or assets belong in this folder.
