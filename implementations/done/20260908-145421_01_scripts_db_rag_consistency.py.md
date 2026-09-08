## Goal

Add a read smoke test to `rag_consistency.py`, mirroring `session_consistency.py`'s
`_check_read_smoke_test` pattern, and fold its result into `is_consistent()`'s
aggregate boolean (REQ-001, REQ-002).

## Scope

In scope: a new `_check_read_smoke_test(db)` helper function in
`scripts/db/rag_consistency.py`, wiring its boolean result into
`check_rag_consistency()`'s returned `RagConsistencyReport` and into
`is_consistent()`'s aggregate condition. Out of scope: any write smoke test (per the
Plan's Out-of-Scope/`UNK-01`), any change to `scripts/db/session_consistency.py`, and
any change to `scripts/db/recovery.py`'s control flow (it already dispatches to
`check_rag_consistency`/`is_consistent` generically).

## Assumptions

- A lightweight, read-only `SELECT COUNT(*)` per required table is sufficient to prove
  read capability, mirroring `session_consistency.py`'s
  `_check_read_smoke_test` exactly (confirmed at `scripts/db/session_consistency.py:56-72`)
  — no full search-quality/relevance test is required, per the Plan's Assumptions.
- The required tables to probe are the same four this module's own
  `_collect_basic_counts` already queries (confirmed via
  `rg -n "db.execute" scripts/db/rag_consistency.py`, lines 13-18): `chunks`,
  `chunks_fts_docsize`, `chunks_vec`, and `documents` (the latter from
  `_collect_document_checks`, line 26). Using the same table set the module already
  reads keeps the smoke test representative of this module's own read path.
- `db.execute(...)` (an `SQLiteHelper` method, not a raw `sqlite3.Connection` method)
  is the established call pattern in this file — confirmed at
  `scripts/db/rag_consistency.py:13,16,26,29,32`.

## Design decisions

Mirror `session_consistency.py:56-72`'s `_check_read_smoke_test(db) -> bool` shape
exactly: iterate a list of required table names, run `SELECT COUNT(*) FROM {table}`
via `db.execute(...).fetchone()` inside a `try`/`except sqlite3.Error`, and return
`False` on the first failure, `True` if every table is readable. This satisfies the
Plan's Design decision ("mirror the pattern exactly... per the source issue's 'AI
Implementation Instruction'") and REQ-001/REQ-002 without inventing a new shape for
RAG.

## Alternatives considered

- A single combined query (e.g. a `UNION`/join across all four tables) instead of a
  per-table loop — rejected: would not match `session_consistency.py`'s established
  per-table loop pattern that this change is explicitly asked to mirror, and would
  make it harder to reason about which specific table failed if smoke-test-failure
  diagnostics are added later.
- Running an FTS-specific query (e.g. an actual `MATCH` search against
  `chunks_fts`) instead of `chunks_fts_docsize`'s row count — rejected: the Plan's
  Assumptions explicitly scope this to a lightweight existence/executability check,
  not a full search-quality test; a `COUNT(*)` against the docsize shadow table already
  proves the FTS virtual table is queryable without needing a real search term.

## Implementation
### Target file
`scripts/db/rag_consistency.py`

### Procedure
1. Add `_check_read_smoke_test(db: SQLiteHelper) -> bool` near the existing
   `_collect_*` helper functions (after `_collect_affected_identifiers`, before
   `check_rag_consistency`, i.e. after the current line 179).
2. In `check_rag_consistency()`, call `_check_read_smoke_test(db)` and pass its result
   into the `RagConsistencyReport(...)` constructor call as `read_smoke_test_ok=...`.
3. In `is_consistent()`, add `report.read_smoke_test_ok` as an additional `and`-clause
   in the aggregate `consistent` boolean expression.

### Method
```python
def _check_read_smoke_test(db: SQLiteHelper) -> bool:
    """Verify each required RAG table can be read without raising."""
    required_tables = [
        "documents",
        "chunks",
        "chunks_fts_docsize",
        "chunks_vec",
    ]
    for table in required_tables:
        try:
            db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        except sqlite3.Error:
            return False
    return True
```

### Details
- Place `_check_read_smoke_test` directly after `_collect_affected_identifiers`
  (which currently ends at line 179) and before `check_rag_consistency` (line 180), so
  it groups with this module's other per-check helper functions.
- Inside `check_rag_consistency()` (currently lines 180-268), call
  `_check_read_smoke_test(db)` once, store its result in a local variable (e.g.
  `read_smoke_test_ok = _check_read_smoke_test(db)`), and pass it to the
  `RagConsistencyReport(...)` constructor (currently lines 246-267) as
  `read_smoke_test_ok=read_smoke_test_ok`. Do not wrap this call in the same
  `try/except sqlite3.Error: diagnostic_errors.append(...)` blocks used for the other
  `_collect_*` calls — `_check_read_smoke_test` already catches `sqlite3.Error`
  internally and returns `False` rather than raising, so re-wrapping it would be
  redundant.
- Inside `is_consistent()` (currently lines 271-284), add
  `and report.read_smoke_test_ok` to the existing `consistent: bool = (...)`
  expression (which currently ends with `and not report.diagnostic_errors` at line
  282), so a failing smoke test alone — even with every count-based check healthy —
  makes `is_consistent()` return `False` (REQ-002).
- No new imports are required — `sqlite3` is already imported at
  `scripts/db/rag_consistency.py:5`.
- `RagConsistencyReport(read_smoke_test_ok=...)` requires the corresponding field
  addition in `scripts/db/models.py` — tracked separately in
  `implementations/20260908-145421_02_scripts_db_models.py.md` (REQ-001); the field
  has a `bool = False` default, so constructing `RagConsistencyReport` without this
  keyword argument elsewhere in the codebase (if any) remains valid.

## Compatibility considerations

`RagConsistencyReport.read_smoke_test_ok` is added with a `bool = False` default (per
`implementations/20260908-145421_02_scripts_db_models.py.md`), so any existing caller
that constructs a `RagConsistencyReport` without this keyword argument continues to
work unchanged. `is_consistent()`'s new `and report.read_smoke_test_ok` clause changes
its return value only for callers whose report has this field explicitly `False` —
existing tests that use `MagicMock()` for `rag_report` may need the attribute set
explicitly for `is_consistent()`'s underlying boolean logic to evaluate correctly; this
is tracked as part of REQ-004's regression check in
`implementations/20260908-145421_03_tests_db_test_db_recovery.py.md`.

## Security considerations

N/A: this change only adds read-only `SELECT COUNT(*)` queries against tables the
module already queries elsewhere in the same function — no new file access, network
access, or credential handling is introduced.

## Rollback considerations

Revert is a single-file code revert (`git checkout` on this commit's change to
`scripts/db/rag_consistency.py`) — no data migration, schema change, or persisted
state is introduced by this change, so no rollback risk beyond the normal code-revert
path.

## Validation plan

- `uv run pytest tests/db/test_db_recovery.py -v` — new failing-smoke-test scenario
  (tracked in `implementations/20260908-145421_03_tests_db_test_db_recovery.py.md`)
  passes.
- `uv run pytest tests/db/test_db_recovery.py -v` — `test_recover_rag_fts_gap`,
  `test_recover_rag_missing_table`, `test_recover_rag_fts_orphan`, and
  `test_recover_rag_vector_orphan` continue to pass unchanged (REQ-004); confirm
  during implementation whether their `MagicMock(rag_report)` fixtures need an
  explicit `read_smoke_test_ok = True` attribute added for `is_consistent()`'s new
  clause to evaluate as before.
- Full validation sequence per `rules/toolchain.md` (ruff, mypy, lint-imports,
  ast-grep, bandit, pytest, diff-cover, pre-commit).

## Completion criteria

- `_check_read_smoke_test()` exists in `scripts/db/rag_consistency.py` and is called
  from `check_rag_consistency()`.
- `is_consistent()`'s aggregate boolean includes `report.read_smoke_test_ok`.
- A failing smoke test makes `is_consistent()` return `False` even when every
  count-based check is healthy.
- Full validation sequence (`rules/toolchain.md`) passes with no new failures.

## Out of scope

Changes to `scripts/db/models.py` (new `read_smoke_test_ok` field — separate document)
and `tests/db/test_db_recovery.py` (new failing-smoke-test scenario — separate
document); no other file is modified by this document. A RAG write smoke test is
out of scope per the Plan (`UNK-01`, non-blocking).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-08TXX:XX:XX | 2026-09-08TXX:XX:XX | Added _check_read_smoke_test function and wiring |
| 2 | Add or update tests per Validation plan | Completed | — | — | All existing tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | mypy/ruff/lint-imports/bandit passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | No docs in scope |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/done/20260907-124049_h0705_rag_post_restore_read_smoke_test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-073509_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-145421
- **Related target files**: scripts/db/rag_consistency.py
