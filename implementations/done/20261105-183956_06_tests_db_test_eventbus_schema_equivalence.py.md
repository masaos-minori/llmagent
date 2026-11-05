## Goal

Add the acceptance tests for `tests/db/test_eventbus_schema_equivalence.py`: fresh-version-6 vs `3 -> 4 -> 5 -> 6`-migrated fingerprint convergence with a single `dlq_outbox` foreign key (AC-005, AC-006), and the REQ-004 fingerprint-contract deviation tests (added view, altered partial-index predicate, version mismatch via `validate_canonical`, and no false positive on the current canonical shape).

## Scope
**Release unit**: canonical-version-6

## Assumptions
- The migration chain `3 -> 4 -> 5 -> 6` runs on a scratch database built by applying the current `schema.sql` and resetting to a version-3 base (ledger + `dlq_outbox` dropped, `user_version = 3`); the runner re-creates the ledger (3 -> 4), the outbox (4 -> 5), and the FK-dedup rebuild (5 -> 6).
- `validate_canonical` (new, fingerprint row) reads the canonical version from `schema.sql`, so a freshly applied `schema.sql` database (version 6) passes and a version-stamped-to-99 database is refused.
- `lint-imports` stays clean for `tests/db`: importing `shared.*` and `eventbus.*` mirrors the existing `open_db` / `_SCHEMA_PATH` imports already in this file.

## Design decisions
- Build the migrated side and compare its `build_fingerprint` against a fresh `apply_schema_in_memory()` (version 6); equality plus a one-entry `PRAGMA foreign_key_list(dlq_outbox)` proves the rebuild converges on canonical (AC-006).
- Seed `dlq_outbox` rows (all three `status` values plus NULL optionals, referencing existing `events` parents) between the 4 -> 5 and 5 -> 6 steps so the convergence DB carries real data through the rebuild; assert the row count survives.
- Deviation tests mutate a scratch database and assert `assert_matches` raises (view, predicate) or `validate_canonical` raises (version), and that neither fires on the untouched canonical shape (no false positive).

## Alternatives considered
- Running the full `3 -> 6` chain in a single `runner.apply`: rejected — seeding `dlq_outbox` rows must happen between the 4 -> 5 and 5 -> 6 steps to prove they survive the rebuild, which needs two `apply` calls.

## Implementation
### Target file
`tests/db/test_eventbus_schema_equivalence.py`

### Procedure
1. Add imports: `import pytest`; from `shared.eventbus_schema_fingerprint` import `apply_schema_in_memory`, `assert_matches`, `build_fingerprint`, `validate_canonical` (new); from `eventbus.migrations` import `REGISTRY`; from `shared.db_migrations` import `MigrationRunner`, `read_ledger`.
2. Add helpers:
   - `_no_op_backup_verifier` (new): passing backup verifier (`_conn`, `_path` -> `None`).
   - `_fk_entry_count(conn, table)` (new): `len(conn.execute(f'PRAGMA foreign_key_list("{table}")').fetchall())`.
   - `_migrated_v6_db(db_path)` (new): open a connection, `executescript(_SCHEMA_PATH...)`, drop `dlq_outbox` and `schema_migrations`, set `user_version = 3`, seed three parent `events` rows, `runner.apply(conn, runner.plan(3, read_ledger(conn), REGISTRY, 5), _no_op_backup_verifier)`, seed three `dlq_outbox` rows (statuses `pending`/`done`/`failed`, NULL optionals) referencing those events, `runner.apply(conn, runner.plan(5, read_ledger(conn), REGISTRY, 6), _no_op_backup_verifier)`, return the connection (now at version 6).
3. Add `test_fresh_v6_and_migrated_v6_are_fingerprint_equal(tmp_path)`: build `fresh = apply_schema_in_memory()` and `migrated = _migrated_v6_db(tmp_path / "migrated.sqlite")`; assert `build_fingerprint(migrated) == build_fingerprint(fresh)`; assert `_fk_entry_count` (new) for `dlq_outbox` is `1` on both; assert the migrated database has exactly three `dlq_outbox` rows (the rebuild preserved them).
4. Add `test_fingerprint_refuses_an_added_view` (new): apply `schema.sql` in memory, `CREATE VIEW event_topics AS SELECT DISTINCT topic FROM events`, assert `assert_matches` raises `RuntimeError`.
5. Add `test_fingerprint_detects_altered_partial_index_predicate` (new): apply `schema.sql` in memory, `DROP INDEX idx_events_redelivered_from` and recreate it with a different `WHERE` predicate, assert `assert_matches` raises `RuntimeError`.
6. Add `test_validate_canonical_passes_a_canonical_connection` (new): `validate_canonical(apply_schema_in_memory())` does not raise.
7. Add `test_validate_canonical_refuses_a_version_mismatch` (new): apply `schema.sql` in memory, set `PRAGMA user_version = 99`, assert `validate_canonical` raises `RuntimeError`.

### Method
- The convergence test exercises the whole registered chain end-to-end, so it also implicitly validates that the 5 -> 6 rebuild (fingerprint row / migrations row) produces the canonical shape.
- The deviation tests use scratch in-memory databases, so they never touch a persisted database.

### Details
- Pre-change anchors: L32-L40 (`test_bootstrap_paths_produce_same_schema`), L43-L65 (`test_existing_database_is_unchanged_on_restart`); the existing tests are left unchanged and still pass (both sides stay at version 6).
- The seeded `dlq_outbox` rows must reference existing `events` rows, or the 5 -> 6 step's `PRAGMA foreign_key_check` fails the rebuild; the three parent `events` rows in `_migrated_v6_db` (new) satisfy this.
- `pytest` is not yet imported in this file; add it.

### Companion test files
- None: this document is the own-row test procedure for the eventbus schema equivalence test (its own Plan row); it is not a companion of any code row.

## Compatibility considerations
- No existing test is modified; the additions are purely additive. The full-suite run in Phase 6 confirms the new imports and helpers do not disturb other tests.

## Security considerations
- The deviation tests prove fail-closed behavior: an unexpected view, an altered partial-index predicate, or a version mismatch is rejected before any write.

## Rollback considerations
- Remove the added imports, helpers, and four tests; the pre-existing tests and imports are untouched.

## Validation plan
- `uv run pytest tests/db/test_eventbus_schema_equivalence.py -q` (new convergence + deviation tests, existing tests).
- Static + layer: `lint-imports`, `tools/check_db_separation.py`, full suite.

## Completion criteria
- The fresh-v6 and migrated-v6 fingerprints are equal with a single `dlq_outbox` FK entry; the seeded rows survive the rebuild.
- `assert_matches` rejects an added view and an altered partial-index predicate; `validate_canonical` passes a canonical connection and refuses a version mismatch; the canonical shape shows no false positive.

## Out of Scope
- The `create_eventbus_schema` three-path negative tests (seq 01 companion), the 5 -> 6 step registry/rollback tests (seq 03 companion), the version-pin move (seq 02 companion), and the doc corrections (seq 09, seq 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the convergence and REQ-004 deviation tests to `tests/db/test_eventbus_schema_equivalence.py` | Completed | 20261105-224950 | 20261105-224950 | Verification: anchors match current file. Convergence test (_migrated_v6_db: 3->4->5, seed 3 dlq_outbox rows, 5->6) + 4 deviation tests added; existing 3 tests unchanged. |
| 2 | Add or update tests per Validation plan | Completed | — | 20261105-224950 | N/A: this row IS the test procedure; no companion files. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261105-224950 | ruff/mypy clean; 8 tests passed (3 existing + 5 new); lint-imports already verified clean with tests/db run; full suite at batch end. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261105-224950 | N/A: doc updates owned by seq 09/seq 10 per Out of Scope. |

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
- **Requirement ID**: `REQ-005`, `REQ-006`, `REQ-004`
- **Source issue**: issues/20261104-143443_ebschema001_separate-eventbus-schema-create-validate-migrate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-234502_ebschema001_separate-eventbus-schema-create-validate-migrate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-183956
- **Related target files**: `tests/db/test_eventbus_schema_equivalence.py`