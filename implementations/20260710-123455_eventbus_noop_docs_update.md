# Implementation: Update eventbus documentation for no-op field removal (Phase B-3)

## Goal

Bring `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`, `docs/06_eventbus_05_configuration_deploy_and_operations.md`, and `docs/06_eventbus_06_reference_api.md` in line with Phase B-1's removal of `poll_interval_ms` / `offset_checkpoint_interval`, replacing "deprecated no-op, emits DeprecationWarning" language with "removed; presence in TOML raises a startup error."

## Scope

**In:**
- `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`: replace the single `offset_checkpoint_interval` deprecation note (line 52) with a removal note
- `docs/06_eventbus_05_configuration_deploy_and_operations.md`: remove the entire `#### Deprecated config fields` subsection (lines 29-38, including its two-field table) and replace with a short removal note
- `docs/06_eventbus_06_reference_api.md`: remove the `#### Deprecated fields (no-op, will be removed)` subsection (lines 31-36) and its table

**Out:**
- The "Active config fields" table in `06_eventbus_05` (lines 16-27) — unchanged, still accurate
- `EventBusConfig`'s class shape shown in `06_eventbus_06` (lines 19-29) — already correctly omits the two removed fields from the shown dataclass body (they were listed separately as "Deprecated fields" below it); only the deprecated-fields subsection needs deletion

## Assumptions

1. These three files were identified via `grep -rln "poll_interval_ms\|offset_checkpoint_interval" docs/` against the current (pre-Phase-B-1) codebase — no other doc references either field.
2. The reader-facing message should shift from "these are no-op, don't worry, just don't set non-default values" to "these keys no longer exist at all; if your TOML has them, the server will refuse to start" — reflecting the harder failure mode introduced in Phase B-1.

## Implementation

### Target file

1. `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
2. `docs/06_eventbus_05_configuration_deploy_and_operations.md`
3. `docs/06_eventbus_06_reference_api.md`

### Procedure

1. In `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`, change line 52 from:
   ```
   **Deprecated**: `offset_checkpoint_interval` config field is no-op. Setting this in TOML emits a DeprecationWarning. Offset checkpointing was replaced with ack-only model.
   ```
   to:
   ```
   **Note (2026-07-10)**: `offset_checkpoint_interval` was removed (it was a no-op field; offset checkpointing was replaced with the ack-only model). Setting this key in `eventbus.toml` now causes the Event Bus to fail at startup — remove it from the config file.
   ```
2. In `docs/06_eventbus_05_configuration_deploy_and_operations.md`, replace lines 29-38:
   ```markdown
   #### Deprecated config fields

   > **Deprecated**: The following fields are no-op compatibility fields. Setting them to non-default values emits a `DeprecationWarning`. These fields will be removed in a future version.
   >
   > **Do not include these fields in TOML configuration.** They have no effect and will be removed. If you need to suppress the warning, set them to their default values (500, 10) or remove them entirely.

   | Field | Type | Default | Description |
   |---|---|---|---|
   | `poll_interval_ms` | int | 500 | No-op. Subscribe polling was replaced with push-mode delivery via EventBroker. Non-default values emit DeprecationWarning; values <1 raise ValueError. |
   | `offset_checkpoint_interval` | int | 10 | No-op. Offset checkpointing was replaced with ack-only model. Non-default values emit DeprecationWarning; values <1 raise ValueError. |
   ```
   with:
   ```markdown
   #### Removed config fields

   > **Note (2026-07-10)**: `poll_interval_ms` and `offset_checkpoint_interval` have been removed (both were no-op fields). If either key is present in `eventbus.toml`, `load_config()` raises `ValueError` at startup — delete these keys from the config file.
   ```
3. In `docs/06_eventbus_06_reference_api.md`, replace lines 31-36:
   ```markdown
   #### Deprecated fields (no-op, will be removed)

   | Field | Type | Default | Description |
   |---|---|---|---|
   | `poll_interval_ms` | int | 500 | No-op; push-mode delivery via EventBroker |
   | `offset_checkpoint_interval` | int | 10 | No-op; ack-only model in place |
   ```
   with:
   ```markdown
   **Note (2026-07-10)**: `poll_interval_ms` and `offset_checkpoint_interval` were removed. `load_config()` raises `ValueError` if either key is present in the TOML file.
   ```
4. Run `grep -rn "poll_interval_ms\|offset_checkpoint_interval" docs/` — expect matches only inside the three "Note (2026-07-10)" sentences added above, not in any table or "Deprecated" heading.

### Method

Direct prose/table replacement, consistent with the "Note (YYYY-MM-DD): X was removed" convention already used elsewhere in this documentation set for prior removals (e.g., `docs/06_eventbus_02_http_api_and_runtime.md`'s `POST /ack` removal note from the earlier cleanup cycle).

### Details

- Keeping a one-line "Note" (rather than deleting all mention outright) preserves a pointer for anyone who still has the old TOML keys and is confused by the startup failure — the note explains what happened and what to do.
- No changes needed to `docs/06_eventbus_03_persistence_schema_and_replay.md` or `docs/06_eventbus_90_inconsistencies_and_known_issues.md` — neither references these two fields (confirmed by grep).

## Validation plan

```bash
grep -rn "poll_interval_ms\|offset_checkpoint_interval" docs/
grep -rn "DeprecationWarning" docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md docs/06_eventbus_05_configuration_deploy_and_operations.md docs/06_eventbus_06_reference_api.md   # expect no output
```

Expected outcome: the only remaining references to the two field names are inside the three "Note (2026-07-10)" removal sentences; no lingering "Deprecated"/"DeprecationWarning" language remains for these fields.
