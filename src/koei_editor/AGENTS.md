# Application package

Read the [root contributor guide](../../AGENTS.md). Run the installed package with
`python -m koei_editor`; use qualified package imports and package resource paths.

Keep launcher/registry/session logic here, per-game behavior in `games`, common
contracts/storage/UI in `shared`, unregistered inspection in `research`, and
reviewed JSON in `data`. Do not introduce import shims, `sys.path` manipulation
or additional flat root launchers.

A support change must update the registry, runtime metadata, canonical supported
inventory, generated README/document and tests. Run
`python -m tools.update_supported_games` and its `--check` mode. Preserve explicit
game/platform selection; never probe another parser after rejection.
