## Goal

Extend the EventBus schema-identity contract and publish its canonical-validation entry point (REQ-004 / AC-004): add views and partial-index predicate text to `build_fingerprint`, and add `validate_canonical(conn)` that composes the `PRAGMA user_version` gate (against the `schema.sql` stamp, kept outside the fingerprint tuple) with `assert_matches` (REQ-002 pre-mutation version + shape check).

## Scope
**Release unit**: canonical-version-6

## Assumptions
- The module must keep `shared-is-leaf` (imports only the standard library), so it CANNOT import `eventbus_schema_version()` from `scripts/db/schema_sql.py` (a `db`-layer module). The version stamp is therefore read directly from `scripts/eventbus/schema.sql` via the existing `_schema_sql()`, parsing the last `PRAGMA user_version = N;`.
- `assert_matches` compares the structural fingerprint only (not `user_version`); `validate_canonical` adds the version half so the combined entry enforces canonical identity (version + shape).
- `build_fingerprint` stays purely structural (version excluded), so existing callers — the startup gate and the migration step postconditions — keep their current version handling unchanged.
- `validate_canonical` (new) is declared by this Plan's fingerprint row and referenced by the `create_schema.py` row (seq 01); both live under the same Plan, so the stale detector resolves the cross-reference.

## Design decisions
- Include `view` objects alongside `table` objects in `build_fingerprint`'s scan so an added/removed/changed view is a fingerprint deviation; canonical `schema.sql` defines no views, so any view present in a target database is rejected (AC-004). Each object reuses the existing per-object extractors (`_columns`, `_indexes`, `_table_level_constraints`, `_foreign_keys`, `_triggers`).
- Add the partial-index predicate text (the normalized `WHERE` clause from the index's own `sqlite_master` SQL) as a fifth element of each index tuple, so altering a partial-index predicate (e.g. `idx_events_redelivered_from`) is detected. Non-partial indexes carry `None`.
- Keep `PRAGMA user_version` out of the fingerprint tuple (formatting/version-fragile); the per-object comparison already covers semantics, and the version is enforced by `validate_canonical`.

## Alternatives considered
- Adding a full normalized-DDL hash to the contract: rejected — formatting-fragile and redundant with the per-object comparison (Design decision 2).
- Reading the version from `db.schema_sql.eventbus_schema_version()`: rejected — violates `shared-is-leaf`; parse `schema.sql` directly instead.

## Implementation
### Target file
`scripts/shared/eventbus_schema_fingerprint.py`

### Procedure
1. Add the version-stamp regex constant after the existing regex constants (after `_CONSTRAINT_RE`, L19): `_VERSION_STAMP_RE` (new) = `re.compile(r"PRAGMA\s+user_version\s*=\s*(\d+)")`.
2. Add `_canonical_schema_version` (new) after `_schema_sql()`: read `_schema_sql()`, `findall(_VERSION_STAMP_RE)`, return `int(stamps[-1])` (last stamp wins), raising `RuntimeError` if no stamp exists.
3. Extend `_indexes` to append the partial-index predicate: after computing `keys`, fetch the index's own DDL via `SELECT sql FROM sqlite_master WHERE type='index' AND name=?`, and if present extract the trailing `WHERE ...` with `re.search(r"\bWHERE\s+(.*)$", ddl, re.IGNORECASE | re.DOTALL)`, normalize it with `_normalize_ddl`, and store `None` when absent; append a **5-element** tuple `(name, unique, partial, keys, predicate)` instead of the current 4-element tuple.
4. Extend `build_fingerprint` to scan views: change the object scan from `WHERE type='table'` to `WHERE type IN ('table', 'view')` (selecting `(name, type)`), and iterate that list building the same 6-tuple per object (tables and views alike).
5. Add `validate_canonical` (new) after `assert_matches`: read `PRAGMA user_version`, compare to `_canonical_schema_version()`; on mismatch raise `RuntimeError` naming the version and directing to recreate or migrate through the registered forward-only path; on match call `assert_matches(conn, label=label)`.

### Method
- The fingerprint extension is additive: adding a view class and one index tuple element changes nothing for the current canonical shape (no views, and the existing partial index `idx_events_redelivered_from` gains a deterministic predicate that both expected and actual compute identically), so already-deployed canonical shapes show no false positive (UNK-03 resolution).
- `validate_canonical` composes two independent checks; the version gate runs first so a version mismatch never reaches the (more verbose) fingerprint diff.

### Details
- Pre-change anchors: L17-L19 (regex constants), L70-L80 (`_indexes`, 4-element tuples), L111-L136 (`build_fingerprint`, `type='table'` scan), L177-L183 (`assert_matches`).
- `_canonical_schema_version` (new) reads the file fresh on every call, so after `schema.sql` stamps 6 (seq 02) it returns 6 with no code change.
- The refusal message may carry the numeric version (schema, not data) and must not carry row content.
- Layering unchanged: still imports only the standard library; no `db.*` or `eventbus.*` import is introduced.

### Companion test files
- None: the REQ-004 fingerprint-deviation tests (added view, altered partial-index predicate, version mismatch via validate_canonical, no false positive on the current canonical shape) live in the eventbus schema equivalence test (its own Plan row), which this row's validation references. No companion section is emitted for this row.

## Compatibility considerations
- Existing fingerprint callers (`scripts/eventbus/schema.py` `_init_schema`, the migration step postconditions) call `assert_matches` / `build_fingerprint`, which now include views and the predicate element; since the canonical shape has no views and the predicate is computed identically for both sides, their behavior is unchanged. Re-run the startup-path tests in Phase 6.
- The `_indexes` tuple arity changes from 4 to 5 elements; any test that constructs or asserts a raw `_indexes` tuple literal (rather than going through `build_fingerprint`) would need updating — verify none exists in Phase 6.

## Security considerations
- Fail-closed preserved: `validate_canonical` refuses a version-mismatched database before any write; the extended fingerprint rejects an unexpected view, so a hostile schema cannot introduce objects through the validate path.

## Rollback considerations
- Revert the `_VERSION_STAMP_RE` (new) / `_canonical_schema_version` (new) additions, the `_indexes` 5-element change, the `build_fingerprint` view scan, and `validate_canonical`; the reverted functions restore the prior structural-only fingerprint and there is no separate entry point to undo.

## Validation plan
- Unit (`tests/db/test_eventbus_schema_equivalence.py`): assert `build_fingerprint` differs when a view is added, differs when a partial-index predicate is altered, is unchanged for the current canonical shape (no false positive); assert `validate_canonical` passes a version-6 canonical connection and raises on a version mismatch.
- Static + layer: `lint-imports` (no new cross-layer import), `tools/check_db_separation.py`, full suite.
- This row has no companion test file; the deviation tests are owned by the `test_eventbus_schema_equivalence.py` row.

## Completion criteria
- `build_fingerprint` includes views and partial-index predicate text; `validate_canonical` enforces version + shape.
- The REQ-004 deviation tests pass and the canonical shape shows no false positive.
- `lint-imports` / `check_db_separation.py` are clean (still stdlib-only).

## Out of Scope
- The `schema.sql` version bump and FK removal (seq 02), the 5 -> 6 rebuild step (seq 03), the `create_eventbus_schema` three-path rewrite using `validate_canonical` (seq 01), the equivalence/convergence tests (the test row), and the doc corrections (seq 09, seq 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `build_fingerprint` (views + partial predicate) and add `validate_canonical` in `scripts/shared/eventbus_schema_fingerprint.py` | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`, `REQ-002`
- **Source issue**: issues/20261104-143443_ebschema001_separate-eventbus-schema-create-validate-migrate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-234502_ebschema001_separate-eventbus-schema-create-validate-migrate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-183956
- **Related target files**: `scripts/shared/eventbus_schema_fingerprint.py`
