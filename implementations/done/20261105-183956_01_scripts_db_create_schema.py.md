## Goal

Give `create_eventbus_schema` three mutually exclusive, validate-first lifecycle paths for `eventbus.sqlite`: fresh creation applies canonical DDL once; an existing database is validated (version + shape) before any mutation and stamped only when it matches; any other case is refused unchanged (REQ-001, REQ-002, REQ-003 / AC-001, AC-003).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `eventbus_schema_version()` reads `schema.sql` dynamically, so after schema.sql stamps 6 this function stamps 6 without a code change; the fresh-path test asserts `eventbus_schema_version()`, not a literal `6`.
- `validate_canonical` (new) (created in the fingerprint row, seq 04) composes the `PRAGMA user_version` gate with `assert_matches`; the unstamped path (c) validates shape only via `assert_matches` because enforcing version 6 on a version-0 database would refuse the stamp this path must perform.
- Layering: `scripts/db/create_schema.py` already imports `assert_matches` from `shared.eventbus_schema_fingerprint` (a `shared` module); adding `validate_canonical` (new) to that same import keeps `db -> shared` and never imports `eventbus.*`.
- Dependency: the dbmigsafe001 Plan rewrites the shared runner and the eventbus passages of `docs/41_db/db_03...`; this function's refusal message points at `scripts/eventbus/migrate.py --apply`, whose exit-code mapping lives in the dbmigsafe001-amended `migrate.py`. Re-verify that path when implementing.

## Design decisions
- Validate-before-mutate ordering: move the fingerprint check out of the post-DDL branch and into a pre-mutation gate so a refusal leaves `sqlite_master` and `user_version` byte-identical (AC-001). The fresh path needs no check because it just applied canonical DDL.
- Shape-only stamping for the unstamped path: `assert_matches` (structural, version-agnostic) rather than `validate_canonical` (new), so a matching version-0 database is stamped instead of refused.

## Alternatives considered
- Delegating to `MigrationRunner` from `create_schema`: rejected — the registry lives in the isolated `eventbus` layer (`db` may not import `eventbus`), so upgrades belong to the eventbus CLI and startup path, not the db-layer create function.
- Reusing `validate_canonical` (new) on the unstamped path: rejected — it enforces version 6, which would refuse the very stamp the unstamped matching path must apply.

## Implementation
### Target file
`scripts/db/create_schema.py`

### Procedure
1. Extend the existing `from shared.eventbus_schema_fingerprint import assert_matches` import (L26) to also import `validate_canonical` (new) (created in the fingerprint row, seq 04): `from shared.eventbus_schema_fingerprint import assert_matches, validate_canonical`.
2. Rewrite `create_eventbus_schema` (L137-L172) into four branches selected before any DDL:
   - (a) No `events` table (fresh): `db.executescript(build_eventbus_schema_sql())`; then `_record_eventbus_baseline(db.conn)`. No validation.
   - (b) `events` present and `user_version == eventbus_schema_version()`: call `validate_canonical` (new) on the connection BEFORE any DDL; on success stamp the baseline row only if absent (`_record_eventbus_baseline`); zero `executescript`.
   - (c) `events` present and `user_version == 0`: call `assert_matches(db.conn)` (shape only); on success stamp `PRAGMA user_version = eventbus_schema_version()` explicitly and insert the baseline via `_record_eventbus_baseline`; on `RuntimeError` refuse unchanged. Verification finding found during execution: `_record_eventbus_baseline` only inserts the ledger row and does NOT stamp `user_version`, so the procedure's earlier wording "stamps via `_record_eventbus_baseline`" required this explicit PRAGMA statement on path (c).
   - (d) `events` present and any other version: refuse unchanged with a message naming the registered CLI and the recreate route (no row content).
3. Delete the existing-database `db.executescript(build_eventbus_schema_sql())` call currently at L150 and the `if existing and before == 0:` reset branch at L154-L158 (the `PRAGMA user_version = 0` line).
4. Keep `_record_eventbus_baseline` as-is (it reads `eventbus_schema_version()` dynamically and uses `INSERT OR IGNORE`).
5. On every refusal, raise `RuntimeError` with a message that names `scripts/eventbus/migrate.py --apply` or "recreate the database" and contains no table/column/row content.

### Method
- Branch selection mirrors `scripts/eventbus/schema.py` `_init_schema` (version gate, column-match stamping, runner delegation) but with the db-layer rule that no `eventbus.*` is imported; the upgrade path stays the eventbus CLI.
- Path (b) stamps the baseline only when absent so re-running `create_schema.py` on an already-current database is a no-op after validation.
- Path (c) stamps to `eventbus_schema_version()` through `_record_eventbus_baseline`, mirroring `scripts/eventbus/schema.py` column-match stamping.

### Details
- Pre-change anchors: L139-L143 (events-table + `user_version` probe), L144 (differing-version refusal), L150 (existing-database `executescript` — remove), L154-L158 (version-0 reset — remove), L159-L170 (current-version branch that currently asserts after DDL — replace with validate-first).
- `assert_matches(conn, *, label="eventbus.sqlite")` raises `RuntimeError` naming the first differing object; its message carries schema text (normalized DDL), never row content, satisfying the refusal-content constraint.
- The differing-version refusal message may carry the numeric version (schema, not data).

### Companion test files
- `tests/db/test_create_schema.py`
  - Procedure: add snapshot-based negative tests for each refusal branch (differing version, unstamped mismatching shape, unregistered version) asserting `sqlite_master` rows and `user_version` are byte-identical before/after; add a spy asserting `SQLiteHelper.executescript` is never called on an existing database and IS called on the fresh path; assert the fresh database ends stamped at `eventbus_schema_version()` with the `eventbus_ledger_baseline` row; assert an unstamped matching-shape database is stamped with zero DDL. Update the two now-outdated tests: `test_unstamped_existing_database_is_not_stamped` (L1135) now stamps a matching-shape database, so assert `version == eventbus_schema_version()`; `test_unstamped_old_shape_fails_explicitly` (L1150) now raises a shape-refusal `RuntimeError` instead of `sqlite3.OperationalError`, so match that and keep `version == 0`.
  - Validation: `uv run pytest tests/db/test_create_schema.py -q`.

## Compatibility considerations
- `init_db.sh` calls `create_schema()` for fresh four-database initialization; the fresh path (a) is behaviorally unchanged (applies canonical DDL + baseline), so fresh production initialization is unaffected. Verify in Phase 6.
- The former current-version path ran DDL then asserted; the new path validates then stamps. A database already at the current version now receives zero DDL — the fingerprint baseline row is still stamped when absent.

## Security considerations
- Fail-closed preserved: an unrecognized or malformed existing database is refused without mutation; no DDL runs on a non-canonical database, so a hostile schema cannot inject objects through the create path.

## Rollback considerations
- Revert the `create_eventbus_schema` rewrite (and the one-line import change) to the pre-change L137-L172; the reverted function restores the old executescript-then-stamp behavior.

## Validation plan
- Unit: for each refusal branch snapshot `sqlite_master` rows and `user_version` before and after `create_eventbus_schema()` and assert byte-identical (no added object, no stamp change).
- Spy: patch `SQLiteHelper.executescript` and assert it is never called on an existing database (paths b/c); it IS called on the fresh path.
- Fresh path: assert the fresh database ends stamped at `eventbus_schema_version()` with the `eventbus_ledger_baseline` row.
- Unstamped matching shape: assert the database is stamped to `eventbus_schema_version()` with no DDL call.
- Static + layer: `lint-imports` (no new `db -> eventbus` import), `tools/check_db_separation.py`, full suite.

## Completion criteria
- `create_eventbus_schema` has no `executescript` on any existing database and no `PRAGMA user_version = 0` reset.
- Every refusal branch leaves `sqlite_master` and `user_version` unchanged; the fresh path stamps 6 with the baseline row; the unstamped matching-shape database is stamped with zero DDL.
- The negative tests pass and `lint-imports` / `check_db_separation.py` are clean.

## Out of Scope
- The fingerprint contract extension (fingerprint row), the schema.sql version bump and FK dedup (schema.sql / migrations rows), the registered 5 -> 6 step (migrations row), and the doc corrections (doc rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the three-path `create_eventbus_schema` rewrite in `scripts/db/create_schema.py` | Completed | 20261105-223731 | 20261105-224758 | Three-path rewrite done; validation-first, no executescript on any existing database. Verification correction: path (c) needs an explicit PRAGMA stamp because _record_eventbus_baseline only inserts the ledger row. |
| 2 | Add or update tests per Validation plan | Completed | — | 20261105-224758 | test_unstamped_existing_database_is_not_stamped renamed to stamped_with_zero_ddl (now stamps current version); test_unstamped_old_shape_fails_explicitly now expects RuntimeError 'missing table'; new TestEventbusValidateFirstPaths (fresh-DDL spy, zero-DDL current path, snapshot byte-identity refusal tests). Spy correction: patch.object(wraps=...) fails on class methods (self not bound) - used an explicit wrapper function instead. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261105-224758 | ruff/mypy clean; 78 test_create_schema tests + 948 tests/db+tests/eventbus passed; lint-imports + check_db_separation clean; full suite at batch end. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261105-224758 | N/A: doc updates owned by seq 09/seq 10 per Out of Scope. |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`
- **Source issue**: issues/20261104-143443_ebschema001_separate-eventbus-schema-create-validate-migrate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-234502_ebschema001_separate-eventbus-schema-create-validate-migrate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-183956
- **Related target files**: `scripts/db/create_schema.py`, `tests/db/test_create_schema.py`