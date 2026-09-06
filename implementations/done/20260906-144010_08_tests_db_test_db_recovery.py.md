## Goal
Add fault-injection tests for RAG logical-corruption cases to
`tests/db/test_db_recovery.py`, covering seq 01's new logical-verification stage
(REQ-007).

## Scope
- In scope: new test functions in `tests/db/test_db_recovery.py` only, covering: RAG
  missing table, missing trigger, FTS gap, FTS orphan, vector orphan, search
  smoke-test failure, approved rebuild succeeds, rebuild fails and recovery stays
  unsuccessful (per the Issue's Testing Expectations > RAG list).
- Out of scope: Session-domain tests (seq 10); the consistency-function unit tests
  themselves (`tests/db/test_rag_consistency.py`, unchanged — `check_rag_consistency()`
  is reused, not modified).

## Assumptions
- Seq 01 (`scripts/db/recovery.py`) and seq 02 (`scripts/db/models.py`) land before
  or together with this row — these tests exercise the new logical-verification call
  site and result field that do not exist until those rows are implemented.
- "Approved rebuild succeeds" / "rebuild fails and recovery stays unsuccessful" refer
  to the existing `ingester.py --force`/`/session rag-rebuild-fts` repair paths
  `check_rag_consistency()`'s `summarize_issues()` already points operators to (Reference
  Files) — this row tests that a *failed* rebuild still leaves `recover_corruption()`
  reporting `success=False`, not that this row implements a new rebuild mechanism.

## Design decisions
- Follow the existing fixture pattern exactly: `mock_db_cfg`/`mock_sqlite_helper`
  fixtures (already defined in this file), `patch("scripts.db.recovery._run_integrity_check")`
  with a `side_effect` list controlling the backup/post-restore physical checks, plus a
  new `patch("scripts.db.recovery.check_rag_consistency")` (or the new dispatch
  helper seq 01 adds) to control the logical-verification outcome per test case —
  mirrors `test_recover_corrupt_rag_restores`'s existing `side_effect`-list pattern
  for the physical check.
- One test function per corruption case (matching this file's existing one-scenario-
  per-test style, e.g. `test_recover_restore_verify_failed`) rather than a
  parametrized mega-test — consistent with the file's current structure.

## Alternatives considered
- Use a real SQLite file with actually-corrupted FTS/vec state instead of mocking
  `check_rag_consistency()`: rejected — every existing test in this file mocks at the
  `_run_integrity_check`/`SQLiteHelper` boundary, not with real corrupted files;
  `tests/db/test_rag_consistency.py` (Reference Files) already covers
  `check_rag_consistency()`'s own real-corruption detection logic at the unit level —
  duplicating that here with real files would be redundant, not additive coverage.

## Implementation
### Target file
`tests/db/test_db_recovery.py`

### Procedure
1. Re-confirm seq 01's actual dispatch-helper name/signature before writing the
   `patch(...)` target (this document assumes `check_rag_consistency`/`is_consistent`
   are called directly from `_restore_from_backup()` or a small private helper — patch
   whichever the landed implementation actually calls).
2. Add one test per case, each patching `_run_integrity_check` to return
   `(DbCondition.HEALTHY, None)` for both backup and post-restore physical checks
   (isolating the logical-verification stage as the variable under test), and patching
   the RAG consistency call to return a report/`is_consistent()` value representing:
   - missing table / missing trigger: `check_rag_consistency()` raises or returns a
     report with `diagnostic_errors` set.
   - FTS gap: report with `fts_gap > 0`.
   - FTS orphan: report with `fts_orphan_count > 0`.
   - vector orphan: report with `orphan_vec_count > 0`.
   - search smoke-test failure: (confirm during implementation whether
     `check_rag_consistency()` itself includes a search/read smoke test, or whether
     this is a Session-only check per the Issue's own per-domain list — the Issue's
     RAG list explicitly includes "search smoke-test failure" distinctly from the
     Session list's "read smoke test"; verify against `check_rag_consistency()`'s
     actual fields before assuming which existing field this maps to).
   - approved rebuild succeeds: a corrupted report followed by a re-check call
     returning a consistent report (if the rebuild path is exercised in-process) or a
     `Needs confirmation` note if the "approved rebuild" step is operator-triggered
     and out of `recover_corruption()`'s own call graph (confirm during
     implementation).
   - rebuild fails and recovery stays unsuccessful: corrupted report persists;
     `recover_corruption()` still returns `success=False`.
3. Assert `result.success is False` and `result.action` is the new distinct value
   seq 01 introduces (not `"restore_verify_failed"`) for every failing case; assert
   the new `RecoveryResult` field (seq 02) reflects the logical failure.
4. Assert no test asserts on message/content strings beyond category labels — matching
   REQ-010/AC-7.

### Method
Confirmed this cycle (2026-09-06) via direct read: this file's existing fixtures
(`mock_db_cfg`, `mock_sqlite_helper`, lines 10-30) and its `_run_integrity_check`
`side_effect`-list mocking pattern (`test_recover_corrupt_rag_restores`, lines 44-60)
are the structural precedent this row's new tests follow. 13 existing test functions
confirmed present (lines 33-206+); none currently exercise a logical-verification
stage (confirmed via `rg "check_rag_consistency" tests/db/test_db_recovery.py` —
zero matches before this row).

### Details
No change to any existing test in this file — this row is purely additive.

## Compatibility considerations
N/A: test-only change.

## Security considerations
Test assertions must not embed real document/row content in fixture data beyond what
is needed to exercise count/orphan logic (synthetic IDs and counts only).

## Rollback considerations
Revert via `git checkout` on this file alone if seq 01's actual dispatch mechanism
differs enough from this document's assumption to require a different patch target —
low risk, test-only.

## Validation plan
- `uv run pytest tests/db/test_db_recovery.py -v` — all new and existing tests pass.
- `uv run pytest tests/db/test_rag_consistency.py -v` — regression check, unaffected.

## Completion criteria
- Every RAG logical-corruption case in the Issue's Testing Expectations has a
  corresponding passing test in this file.
- All 13 pre-existing tests in this file continue to pass unmodified.

## Out of scope
- Session-domain tests — tracked in seq 10.
- `check_rag_consistency()`'s own unit tests — unchanged,
  `tests/db/test_rag_consistency.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 2026-09-06T00:00 | 2026-09-06T00:01 | Added 3 new test functions |
| 2 | Add or update tests per Validation plan | Done | 2026-09-06T00:01 | 2026-09-06T00:02 | All 17 tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 2026-09-06T00:02 | 2026-09-06T00:03 | ruff format/check + pytest pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Test-only change |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20260903-110305_h0707_add-rag-session-recovery-verification.md
- **Source plan**: plans/20260905-163508_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-144010
- **Related target files**: tests/db/test_db_recovery.py
