## Goal

Add a unit test for `scripts/eventbus/db.py::_apply_eventbus_pragmas()` to
`tests/eventbus/test_eventbus_db_migration.py`, covering all 4 pragmas the function
sets. No production code change.

## Scope

- In scope: add `test_apply_eventbus_pragmas_sets_all_four_pragmas` to
  `tests/eventbus/test_eventbus_db_migration.py` (the same file created by
  `plans/20260823-193128_plan.md`'s implementation procedure — see Assumptions for
  ordering).
- Out of scope: the 3 `_migrate()` tests from `plans/20260823-193128_plan.md` (separate
  plan, separate implementation procedure document, already generated as
  `implementations/20260824-181343_tests_eventbus_test_eventbus_db_migration.py.md`);
  `tests/eventbus/test_eventbus_json_utils.py` (separate target file / separate
  implementation procedure document, generated alongside this one); any change to
  `scripts/eventbus/db.py` itself.

## Assumptions

- `_apply_eventbus_pragmas()` (`scripts/eventbus/db.py:15-24`) sets exactly 4 pragmas:
  `journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout=<param>`, `foreign_keys=ON` —
  confirmed by reading the function in full this cycle.
- `tests/eventbus/test_eventbus_db_migration.py` does not exist in the working tree yet
  (both this plan and `plans/20260823-193128_plan.md`/its implementation procedure are
  document-only; no code has been implemented). Per this plan's own Assumptions: either
  plan's implementation procedure may be executed first — if
  `20260824-181343_tests_eventbus_test_eventbus_db_migration.py.md`'s procedure runs
  first, this pragma test is appended to the file it creates; if this procedure runs
  first, this file is created with just the pragma test and the migration tests are
  appended alongside it later. Either order produces the same two-implementation-doc,
  one-target-file outcome.
- Per the duplicate-work check (`skills/plan-to-implementation-procedure/workflow.md`
  Step 3), this document is NOT a duplicate of
  `implementations/20260824-181343_tests_eventbus_test_eventbus_db_migration.py.md`
  despite sharing a target file: that document's `Source plan` is
  `plans/20260823-193128_plan.md`, while this document's `Source plan` is
  `plans/20260823-194101_plan.md` — different plans, each covering a distinct,
  non-overlapping set of test functions in the same file.

## Design decisions

- Reuse the file-based `tmp_path` connection pattern already used by the sibling
  `_migrate()` tests in the same file, per this plan's Design section, rather than
  introducing a separate fixture style.
- Pass an explicit non-default `busy_timeout_ms` value to `_apply_eventbus_pragmas()`
  in the test so the assertion on `PRAGMA busy_timeout` distinguishes "pragma was set"
  from "pragma happened to already equal the function's own default."

## Alternatives considered

- Testing pragma application only indirectly via `open_db()` (which calls
  `_apply_eventbus_pragmas()` internally) — rejected: `open_db()` also runs
  `_init_schema()`, which would couple this test to migration/schema behavior instead
  of isolating the pragma-setting logic itself.

## Implementation

### Target file

`tests/eventbus/test_eventbus_db_migration.py` (shared with
`plans/20260823-193128_plan.md`; this document scopes only the pragma test addition)

### Procedure

1. Add `test_apply_eventbus_pragmas_sets_all_four_pragmas`:
   - Open a file-based `tmp_path` `sqlite3.Connection`.
   - Call `_apply_eventbus_pragmas(conn, busy_timeout_ms=<non-default test value>)`.
   - Query `PRAGMA journal_mode`, `PRAGMA synchronous`, `PRAGMA busy_timeout`,
     `PRAGMA foreign_keys` and assert each reflects the applied setting
     (`journal_mode` → `"wal"`, `synchronous` → `1` i.e. `NORMAL`, `busy_timeout` →
     the passed test value, `foreign_keys` → `1`).

### Method

Import `_apply_eventbus_pragmas` directly:
`from scripts.eventbus.db import _apply_eventbus_pragmas` — same import pattern as the
sibling `_migrate` tests in this file.

### Details

Current code (verified this cycle), `scripts/eventbus/db.py:15-24`:
```python
def _apply_eventbus_pragmas(
    conn: sqlite3.Connection,
    *,
    busy_timeout_ms: int = _DEFAULT_BUSY_TIMEOUT_MS,
) -> None:
    """Apply WAL/synchronous=NORMAL/busy_timeout/foreign_keys pragmas to a connection."""
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")  # nosec B608 — busy_timeout_ms is a configurable integer, not user input
    conn.execute("PRAGMA foreign_keys=ON")
```
Note: `PRAGMA journal_mode=WAL` returns the applied mode as a query result row
(`"wal"`); reading it back via `conn.execute("PRAGMA journal_mode").fetchone()[0]` is
the correct read-back form (not the `PRAGMA journal_mode=WAL` set-statement itself).

## Compatibility considerations

Test-only addition; no production code, schema, or public interface changes.

## Security considerations

N/A: test-only change against a temporary, non-production SQLite file; no secrets,
network, or external input involved.

## Rollback considerations

Remove the added test function; no other rollback steps required (no production code
touched).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_db_migration.py` (pragma test) | Unit | `uv run pytest tests/eventbus/test_eventbus_db_migration.py -v` | All tests incl. pragma test pass |
| `tests/eventbus/` (full) | Regression | `uv run pytest tests/eventbus/ -v` | No new failures |
| `scripts/eventbus/` (isolation) | Architecture | `PYTHONPATH=scripts uv run lint-imports` | 5 contracts kept, 0 broken |
| `scripts/eventbus/db.py` (untouched) | Static | `uv run ruff check scripts/eventbus/` + `uv run mypy scripts/eventbus/` | No new findings |

## Out of scope

The 3 `_migrate()` tests (separate implementation procedure document);
`tests/eventbus/test_eventbus_json_utils.py`; any change to `scripts/eventbus/db.py`.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation update in scope |

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
- **Source issue**: N/A: not applicable in this phase (the source plan's own Traceability records `Source issue: N/A` and `Source requirement: requires/20260726-121812_require.md` — this plan predates the issue-to-plan pipeline merge)
- **Source requirement**: `requires/20260726-121812_require.md`
- **Source plan**: `plans/20260823-194101_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260824-181934
- **Related target files**: `tests/eventbus/test_eventbus_db_migration.py`

## Adversarial verification notes (this cycle)

- Re-verified `_apply_eventbus_pragmas()`'s full content against the plan's
  Design/Assumptions — matches exactly (4 pragmas, matching names and order).
- Confirmed `tests/eventbus/test_eventbus_db_migration.py` does not yet exist (neither
  this plan nor `plans/20260823-193128_plan.md` has been implemented) — the two
  implementation procedure documents for this same target file are intentional
  per-plan artifacts, not duplicate work, per the Step 3 duplicate-check rule (matches
  on `Source plan` + `Related target files` together, not target path alone).
- Re-confirmed `lint-imports` reports 5 kept/0 broken and the routing.md/AGENTS.md
  policy-correction claims (see the sibling `test_eventbus_json_utils.py` procedure
  document's verification notes for the shared detail). No blocking unknowns or
  contradictions found.
