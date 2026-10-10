# Scalar adapter starter

This scaffold is unregistered and rejects every file until the native format
and storage encoding are implemented. It supplies no game offsets or support
claim. DW3's tagged editor should continue using its existing dedicated workflow.

1. Copy and rename `new_game_parser.py` and `new_game_editor.py` into the project
   root. Choose an ID that includes the platform where editions differ.
2. Follow `CONTRIBUTING.md` to qualify title/revision, size, structure, integrity,
   codec/container metadata and occupied records. Implement the two codec seams,
   a frozen field type satisfying `adapter_contract.ScalarField`, evidence-based
   bounds and each field's actual encoding in `changed_payload`.
   Use optional `maxable=False` for fields requiring a deliberate choice or
   separate preset; `limit_values` must exclude them from bulk Max operations.
3. Register the qualified game in `game_registry.GAMES`, declaring
   `scalar_backend='your_parser_module'`, plus editor/parser modules, extension,
   platform and honest provenance. This automatically enables scalar self-tests.
   Research without an implemented editor stays outside the gameplay library.
4. Optional backend `record_label(slot, group)`, `field_hint(document, field_id)`
   and `inspection_rows(document)` customize the default data view. For richer
   read-only tables, subclass `ScalarPresentation` and set `presentation_type`
   in your editor. Add no game-ID branches to the launcher or shared scalar GUI.
5. Rename `contract_test.py` to `tests/test_your_game_contract.py` and supply
   `fixture_bytes()`. The inherited checks verify no-op/stage/unstage, targeted
   payload writes, rejection, immutable source, backup/restore, new destination
   and source-change safety. Add format-specific corruption, identity, dynamic
   records and dependency tests; synthetic success is not native/in-game evidence.
6. Run the focused tests, shared contract/GUI suite and smoke test. Coordinate
   build metadata, backend hidden imports and explicit source-manifest additions
   before releasing. Include a format/evidence document and required licenses.

The copied-save CLI accepts `--game YOUR_ID --self-test INPUT EMPTY_OUTPUT_DIR`.
It preserves the input and writes a private report and edited/restored copies.
Reports and fixtures do not belong in public source archives.
