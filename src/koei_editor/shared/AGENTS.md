# Shared contracts and utilities

Read the [root guide](../../../AGENTS.md). Shared code supplies contracts, scalar
UI, crypto primitives, themes/preferences and safe copied-save storage. Keep
game offsets, limits and ID dictionaries in game packages or reviewed metadata.

Avoid game-ID branches in launcher/GUI operations; use injected backends and
presentations. Preserve immutable staging, Undo, Review Changes, higher-value
Max behavior, automatic backups, source-change detection and atomic new-copy
saving. Restore must qualify the exact bytes being written.

Changes can affect every adapter: run meaningful shared contract, GUI, path,
crypto and packaging regressions appropriate to the change.
