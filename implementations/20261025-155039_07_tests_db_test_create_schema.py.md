## Goal

Make the patched EventBus shapes in `tests/db/test_create_schema.py` structurally canonical so the post-DDL shape validation from `REQ-003` accepts them, and preserve the legacy old-shape DDL-failure boundary on its real failure type (`REQ-006`).

## Scope

- Modify `tests/db/test_create_schema.py` only: correct the `_EVENTBUS_SCHEMA_NO_VEC0` DDL string to match `scripts/eventbus/schema.sql`, and keep `test_unstamped_old_shape_fails_explicitly` on `sqlite3.OperationalError`.
- Do not add new test functions here. The malformed-stamped rejection path is covered by the runtime startup gate (`REQ-002`), the `init_db.sh` strict gate (`REQ-003`), and the fingerprint equivalence/rejection cases in the shared-validator procedure (`REQ-001`).

## Assumptions

- `create_eventbus_schema()` (`scripts/db/create_schema.py`) validates shape against the shared validator after DDL runs (`REQ-003`); a non-canonical patched shape therefore raises inside those tests unless the patched DDL is corrected.
- The shared validator (`scripts/shared/eventbus_schema_fingerprint.py`, `REQ-001`) compares structural fingerprint only (tables/columns/types/nullability/defaults/pk, indexes, table-level constraints, FKs, triggers) and ignores `PRAGMA user_version`, so leaving the patched string unstamped does not affect the comparison.
- The old-shape database cannot accept the current DDL, so `executescript` raises before any shape validation runs.

## Design decisions

- **Patch `_EVENTBUS_SCHEMA_NO_VEC0` to be structurally identical to `schema.sql`.** Two deviations exist relative to `scripts/eventbus/schema.sql`: an extra `events.consumer_delivery_failure_count` column absent from `schema.sql`, and a missing low-water-mark index on `consumer_delivery (consumer_id, acked)`. Remove the extra column and add the index so the patched shape passes strict validation and every test that patches it keeps passing.
- **Keep the old-shape test on `sqlite3.OperationalError`.** The old-shape `events(seq, event_id)` database cannot accept the current DDL (`CREATE INDEX ... ON events(topic)` references a `topic` column that the old table lacks), so `executescript` raises `OperationalError` before shape validation. Switching the expectation to `RuntimeError` would break the currently-passing test; the real boundary is a DDL failure, which `OperationalError` records correctly.

## Alternatives considered

- **Move the patched-shape tests to explicit rejection tests.** Rejected: those tests assert valid creation (tables, columns, timestamps), not rejection; correcting the DDL preserves their intent with a smaller change.
- **Drop only the extra column and leave the missing index.** Rejected: the fingerprint still rejects a shape missing an index, so strict validation would still fail; both deviations must be corrected for the shape to be canonical.

## Implementation

### Target file

`tests/db/test_create_schema.py`

### Procedure

1. Open `tests/db/test_create_schema.py` and locate the `_EVENTBUS_SCHEMA_NO_VEC0` DDL string (lines 111-148).
2. Delete the extra `consumer_delivery_failure_count` column from the `events` table (line 125); it is absent from `scripts/eventbus/schema.sql` and strict validation rejects it.
3. Add the low-water-mark index on `consumer_delivery (consumer_id, acked)` after the `consumer_delivery` table closes (after line 141), matching the index defined at `scripts/eventbus/schema.sql` lines 31-33, so the patched shape is structurally identical to `schema.sql`.
4. Leave `test_unstamped_old_shape_fails_explicitly` (lines 1022-1035) expecting `sqlite3.OperationalError` at line 1030 unchanged; do not switch it to `RuntimeError`.
5. Confirm the tests that patch `_EVENTBUS_SCHEMA_NO_VEC0` pass after the canonical fix.

### Method

- The extra column is the single line `    consumer_delivery_failure_count INTEGER NOT NULL DEFAULT 0,` inside the `events` block (line 125); delete only that line so the remaining `events` columns match `schema.sql`.
- Do NOT remove the identically named column on the `consumer_delivery` table (test line 138, `schema.sql` line 26) — that column is canonical and must stay. Only the `events` copy at line 125 is removed.
- Insert the index with a comment mirroring `schema.sql`'s low-water-mark note, placed between the `consumer_delivery` table (closes at line 141) and the `consumer_offsets` comment (line 143).
- Do not touch `PRAGMA user_version`: the patched string stays unstamped, which is intentional for the "no vec0" variant and irrelevant to the structural fingerprint.
- Verify `test_eventbus_schema_timestamps` (line 902), `test_create_eventbus_schema_produces_new_tables` (line 947), and the `TestEventBusTablesExist` / `TestEventBusSchemaNewColumns` classes (which call `create_eventbus_schema()` with the patched string) all pass under the post-DDL shape gate.

### Details

- The correction makes `_EVENTBUS_SCHEMA_NO_VEC0` equivalent in structure to `scripts/eventbus/schema.sql`: same `events` columns, same `consumer_delivery`/`consumer_offsets` tables, and the complete index set including the low-water-mark index.
- `test_unstamped_old_shape_fails_explicitly` still verifies the v0 legacy boundary: an incompatible legacy `events` table is not migrated, the DDL fails, and nothing is stamped (`user_version` stays 0 at line 1035).
- No new function, class, or symbol is introduced; only the existing DDL literal changes and the exception expectation is preserved.

## Compatibility considerations

- The change is test-only and confined to one DDL literal plus one untouched assertion; production code (`scripts/db/create_schema.py`, the shared validator) is unchanged.
- After `REQ-003` adds post-DDL shape validation, the previously-non-canonical patched shape would have failed these tests; the canonical fix restores them.

## Security considerations

- N/A: test-only change; no runtime, config, or secret handling touched.

## Rollback considerations

- Revert the edit to `tests/db/test_create_schema.py` (or `git checkout` the parent commit); no other file is touched.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/db/test_create_schema.py` | Unit: patched shape now canonical; old-shape boundary preserved | `uv run pytest tests/db/test_create_schema.py` | patched-shape tests pass under strict validation; `test_unstamped_old_shape_fails_explicitly` passes with `sqlite3.OperationalError` |

## Completion criteria

- `_EVENTBUS_SCHEMA_NO_VEC0` matches `scripts/eventbus/schema.sql` structurally (same `events` columns, same tables, and full index set).
- The tests that patch `_EVENTBUS_SCHEMA_NO_VEC0` pass with the post-DDL shape validation in place.
- `test_unstamped_old_shape_fails_explicitly` still passes expecting `sqlite3.OperationalError` and leaves `user_version` at 0.
- `ruff`, `mypy`, `bandit`, `lint-imports`, the `tests/db` suite, and diff-cover pass.

## Out of Scope

- The shared validator (`REQ-001`), the runtime startup gate (`REQ-002`), the `create_eventbus_schema()` / `init_db.sh` strict gates (`REQ-003`), the deploy readiness/config gates (`REQ-004`, `REQ-005`), and the malformed-stamped rejection tests covered by the runtime and deployment procedures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the `_EVENTBUS_SCHEMA_NO_VEC0` DDL to match `schema.sql` (drop extra `events` column, add missing index) | Pending | — | — | REQ-006 |
| 2 | Keep `test_unstamped_old_shape_fails_explicitly` on `sqlite3.OperationalError`; confirm patched-shape tests pass | Pending | — | — | REQ-006 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test-only |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-006`
- **Source issue**: `issues/20261023-154326_eventbus003_startup-gate-schema-health.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-111552_eventbus003_startup-gate-schema-health.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-155039
- **Related target files**: `tests/db/test_create_schema.py`
