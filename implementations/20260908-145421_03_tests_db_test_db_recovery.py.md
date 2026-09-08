## Goal

Add a test proving a failing RAG read smoke test causes `recover_corruption()` to
return `action="logical_verify_failed"` even when every count-based check is healthy,
and confirm the four existing RAG consistency tests still pass unchanged (REQ-003,
REQ-004).

## Scope

In scope: one new test case in `tests/db/test_db_recovery.py`, plus running the four
existing RAG consistency tests named by REQ-004 to confirm no regression. Out of
scope: any change to `scripts/db/rag_consistency.py` or `scripts/db/models.py`
themselves (tracked in the other two documents from this same Plan).

## Assumptions

- Existing fixtures `mock_db_cfg`, `mock_sqlite_helper`, and the shared
  `_mock_restore_side_effect()` helper (`tests/db/test_db_recovery.py:215-221`) are
  reused as-is, following the exact pattern already used by `test_recover_rag_fts_gap`
  (lines 224-251), `test_recover_rag_missing_table` (254-281),
  `test_recover_rag_fts_orphan` (284-...), and `test_recover_rag_vector_orphan`
  (314-341): a `MagicMock()` `rag_report` with every field set explicitly, patched in
  via `patch("scripts.db.recovery.check_rag_consistency", return_value=rag_report)`.
- Verified by reading all four existing tests: each sets exactly one field to an
  unhealthy value (`fts_gap=5`, `diagnostic_errors=("Missing table: chunks",)`,
  `fts_orphan_count=3`, `orphan_vec_count=2` respectively) while every other field is
  healthy — `is_consistent()`'s `and`-chained boolean expression short-circuits at
  that first unhealthy field in each case (confirmed via
  `scripts/db/rag_consistency.py:271-284`), so none of the four ever reaches the new
  `and report.read_smoke_test_ok` clause (Row 1) during evaluation. This means no
  existing test requires an explicit `read_smoke_test_ok` attribute added to keep
  passing — the Plan's Risk entry about `MagicMock()` interference does not apply once
  the new clause is placed last in the `and`-chain (confirmed as Row 1's Design
  decision).
- No existing test in this file exercises the RAG success path (`is_consistent()`
  returning `True`) through `check_rag_consistency` — confirmed via `rg -n
  "check_rag_consistency|RagConsistencyReport" tests/db/test_db_recovery.py`, which
  finds only the four `check_rag_consistency` patches above; `test_recover_healthy`
  and `test_recover_corrupt_rag_restores` never construct a `rag_report` (the latter
  patches `_run_logical_verification` directly, bypassing `check_rag_consistency`
  entirely). No existing test therefore needs `read_smoke_test_ok=True` added for a
  "should still succeed" assertion.

## Design decisions

Add one new test, `test_recover_rag_read_smoke_test_failed`, following the exact same
`MagicMock()` structure as the four existing RAG tests: every count-based field set to
a healthy value, and `read_smoke_test_ok=False` as the sole unhealthy field — proving
REQ-002/REQ-003 (a smoke-test-only failure, with all counts healthy, still fails
verification).

## Alternatives considered

- Exercising `_check_read_smoke_test()` (Row 1) directly against a real/mocked
  `SQLiteHelper` instead of mocking `check_rag_consistency` at the
  `recover_corruption()` boundary — rejected: every other test in this file's RAG
  section mocks at the `check_rag_consistency` boundary rather than the underlying
  SQLite connection, and this Plan's Row 1 procedure already covers the internal
  `_check_read_smoke_test()` helper's own correctness at the module level; this test's
  job is to prove the field is wired into `recover_corruption()`'s outcome, consistent
  with what the other three RAG tests each prove for their own field.

## Implementation
### Target file
`tests/db/test_db_recovery.py`

### Procedure
1. Add `test_recover_rag_read_smoke_test_failed` immediately after
   `test_recover_rag_vector_orphan` (currently ending at line 341), following the
   same `MagicMock()`/`_mock_restore_side_effect()` structure.
2. Run `uv run pytest tests/db/test_db_recovery.py::test_recover_rag_fts_gap
   tests/db/test_db_recovery.py::test_recover_rag_missing_table
   tests/db/test_db_recovery.py::test_recover_rag_fts_orphan
   tests/db/test_db_recovery.py::test_recover_rag_vector_orphan -v` to confirm no
   regression (REQ-004) — per the Assumptions above, no fixture change is expected to
   be needed for these four to keep passing.

### Method
```python
def test_recover_rag_read_smoke_test_failed(mock_db_cfg, mock_sqlite_helper):
    """RAG read smoke test failure should cause logical verification failure,
    even when every count-based check is healthy."""
    with patch("scripts.db.recovery._run_integrity_check") as mock_integrity:
        mock_integrity.side_effect = _mock_restore_side_effect()

        rag_report = MagicMock()
        rag_report.chunks = 10
        rag_report.vec = 10
        rag_report.fts_gap = 0
        rag_report.fts_orphan_count = 0
        rag_report.orphan_vec_count = 0
        rag_report.documents_without_chunks_count = 0
        rag_report.chunks_without_vec_count = 0
        rag_report.duplicate_chunk_index_count = 0
        rag_report.url_level_mismatches = {}
        rag_report.diagnostic_errors = None
        rag_report.read_smoke_test_ok = False

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("shutil.copy2"),
            patch("os.replace"),
            patch("scripts.db.recovery.check_rag_consistency", return_value=rag_report),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "logical_verify_failed"
            assert result.logical_ok is not True
```

### Details
- Place the new test immediately after `test_recover_rag_vector_orphan` (currently
  ending at line 341), keeping the file's existing grouping of RAG consistency
  scenarios together.
- Every field except `read_smoke_test_ok` is set to the same healthy values the other
  four tests use for their own non-triggering fields, so the only unhealthy signal in
  this test is the smoke-test result — this is what proves REQ-002 (smoke test alone
  can fail verification) and REQ-003 (the failure surfaces as
  `action="logical_verify_failed"`).
- No new fixtures or imports are needed — `MagicMock`, `patch`, `DbCondition`,
  `recover_corruption`, and `_mock_restore_side_effect` are all already imported/defined
  in this file.

## Compatibility considerations

N/A: test-only addition; no production code or public test fixture signature changes.

## Security considerations

N/A: no real filesystem, network, or credential access — mocks `_run_integrity_check`,
`check_rag_consistency`, `pathlib.Path.exists`, `shutil.copy2`, and `os.replace`,
consistent with the rest of this file's RAG test group.

## Rollback considerations

Revert is a single-file test revert; no fixture or production code is shared
exclusively with this test, so reverting it has no effect beyond removing its own
coverage.

## Validation plan

- `uv run pytest tests/db/test_db_recovery.py -v` — the new test passes.
- `uv run pytest tests/db/test_db_recovery.py::test_recover_rag_fts_gap
  tests/db/test_db_recovery.py::test_recover_rag_missing_table
  tests/db/test_db_recovery.py::test_recover_rag_fts_orphan
  tests/db/test_db_recovery.py::test_recover_rag_vector_orphan -v` — all four pass
  unchanged (REQ-004).
- Full validation sequence per `rules/toolchain.md`, including
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` on the
  changed lines across all three implementation-procedure documents from this Plan.

## Completion criteria

- `test_recover_rag_read_smoke_test_failed` exists and passes.
- `test_recover_rag_fts_gap`, `test_recover_rag_missing_table`,
  `test_recover_rag_fts_orphan`, and `test_recover_rag_vector_orphan` pass unchanged.
- No new failures in `uv run pytest tests/db/test_db_recovery.py -v`.

## Out of scope

Any change to `scripts/db/rag_consistency.py` (Row 1) or `scripts/db/models.py`
(Row 2) themselves. If Procedure step 2's regression run reveals that any of the four
existing RAG tests unexpectedly requires an explicit `read_smoke_test_ok` attribute,
that is a Plan Gap to report during implementation (per
`skills/plan-to-implementation-procedure/workflow.md` Step 3c), not a change to make
silently in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-08TXX:XX:XX | 2026-09-08TXX:XX:XX | Added test_recover_rag_read_smoke_test_failed |
| 2 | Add or update tests per Validation plan | Completed | — | — | All 21 tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | mypy/ruff passed |
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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/done/20260907-124049_h0705_rag_post_restore_read_smoke_test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-073509_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-145421
- **Related target files**: tests/db/test_db_recovery.py
