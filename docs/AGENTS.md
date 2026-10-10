# Documentation conventions

Read the [root guide](../AGENTS.md). Keep user-facing README/release notes focused
on supported features and simple use. Put format proof, source/licence evidence,
validation distinctions and exact blockers in the relevant development document.

Update [the index](README.md) when adding a document. Use links relative to each
document's folder; code lives under `../src/koei_editor`, tools under `../tools`
and tests under `../tests`. Historical upstream commit links remain historical.

The supported-game document is generated with
`python -m tools.update_supported_games`; change registry/metadata/tests rather
than manually adding unsupported rows. Do not publish private paths, player data,
account identifiers, game assets or attached binaries. Distinguish procedural
tests, genuine-file qualification and actual game-load validation.
