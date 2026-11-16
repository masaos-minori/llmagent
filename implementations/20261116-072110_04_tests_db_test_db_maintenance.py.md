## Goal
- Add tests in `tests/db/test_db_maintenance.py` pinning every behavior Plan 006 changes: rollback atomicity, `DatabaseError` capture, config-error propagation in both modes, direct helper re-raise, and `pruned_ids` sourced from the delete transaction (REQ-006; AC-1..AC-5).

## Scope
**Release unit**: maintenance-error-semantics (Phases 1-3 of the plan; lands with `20261116-072110_01`..`_03`, `_05`)

- In scope: new test functions in `tests/db/test_db_maintenance.py`; one allowed test-only rename (`test_purge_best_effort_returns_partial_result_on_error` → `..._returns_failure_result_on_error`).
- Out of scope: the production changes themselves (procedures `_01`..`_03`); the `tests/agent/commands/test_memory_data_ops.py` regression run (own procedure `20261116-072110_05`); the docs update (plan Phase 3).

## Assumptions
- Plan 004 landed (verified this cycle): its rotation-invariance class `Rotation Archive Invariance (dbreview004, REQ-006)` exists at `tests/db/test_db_maintenance.py:1221+`; 006 appends to disjoint sections and must re-read the landed sections before appending (plan Overlap Scan).
- Existing mode tests at `:941-1010` are all `OperationalError`-based mock tests; no rollback/`in_transaction` assertion exists (plan row evidence, grep this cycle).
- Real-DB test pattern follows the existing purge tests at `:140-300`; mock-based purge tests at `:963-990` stay valid because `MagicMock(spec=SQLiteHelper)` exposes `begin_immediate` as a usable no-op context manager (Plan Assumptions).

## Design decisions
- AC-1 uses a real temp DB, not mocks: the assertion target is the connection's transaction state (`in_transaction is False`), which mocks cannot show (Plan Risks mitigation).
- `collect_prunable_ids` not-called check uses `patch.object(..., autospec=True)` as a spy so the AC-5 test proves the removed call, not just the resulting ids (plan Tests).

## Alternatives considered
- Mock-only rollback test: rejected — a mock connection has no transaction to inspect (plan Tests specifies the real-DB pattern).
- Pinning the rename as a separate work item: rejected — test-only rename inside the same file run, allowed by the plan Tests section.

## Implementation
### Target file
`tests/db/test_db_maintenance.py`

### Procedure
1. Rollback-atomicity test (AC-1): real temp DB seeded with 5 age-expired sessions; `patch("db.maintenance._delete_sessions_beyond_limit", side_effect=sqlite3.OperationalError(...))`; call `purge_old_sessions(..., mode=BEST_EFFORT)` → `success is False`, sessions row count unchanged, `helper._require_conn().in_transaction is False`, `data == {"age_deleted": 0, "count_deleted": 0, "kept_active_session": None}` (REQ-001).
2. Vacuum `DatabaseError` mode test (AC-2): `mock_db.vacuum.side_effect = sqlite3.DatabaseError("database disk image is malformed")` → BEST_EFFORT `success=False` / `action="vacuum_failed"`; STRICT raises (REQ-002).
3. Config-propagation characterization tests (AC-3): monkeypatch `db.maintenance.ConfigLoader.load` to raise `OSError` → `purge_old_sessions(..., mode=BEST_EFFORT)` raises; monkeypatch `db.maintenance.build_db_config` to raise `ValueError` → `purge_corrupt_archives(mode=BEST_EFFORT)` raises (REQ-003).
4. Direct re-raise test (AC-4): call `_handle_maintenance_error(ValueError("x"), "op", STRICT)` outside any `except` block → the same `ValueError` propagates (no `RuntimeError: No active exception to re-raise`) (REQ-004).
5. Pruned-ids source test (AC-5): real-DB seed of pinned + unpinned memories; run `prune_old_memories`; assert `sorted(data["pruned_ids"])` equals the ids removed from the `memories` table (post-run table state) and `data["deleted"] == len(data["pruned_ids"])`; with `collect_prunable_ids` patched via `patch.object(..., autospec=True)`, assert it is NOT called by `prune_old_memories` (REQ-005).
6. Rename `test_purge_best_effort_returns_partial_result_on_error` (`:973-987`) → `test_purge_best_effort_returns_failure_result_on_error` (new) (test-only cleanup allowed by the plan Tests section).

### Method
- Append new test functions/classes in the sections matching the entry point under test (purge / vacuum / prune / helper), disjoint from Plan 004's landed sections (`:1221+`); reuse the file's existing fixture helpers (`_make_session_db`, `_make_db_cfg`).

### Details
- Regression watch (no assertion changes expected): `test_prune_best_effort_returns_failure_on_error` (`:1000-1013`), `test_deletes_old_memories_and_fts` (`:406`; `pruned_ids` assertion `:416`), `test_purge_best_effort_returns_partial_result_on_error` (`:973-987`, rename per step 6) — see plan Tests section for why each stays green.
- Sequence context: this file is shared with Plans 004 (landed), 006 (this document), 007, 008; fixed order 004 → 006 → 007 → 008, disjoint test classes, no shared fixtures modified (plan Overlap Scan).

## Compatibility considerations
- AC-5 (plan): every pre-existing assertion in this file stays unchanged except the allowed rename; `data` keys are unchanged (`pruned_ids` stays `list[str]`).
- The new tests import nothing outside the file's existing import set plus `sqlite3` (already imported for `OperationalError`).

## Security considerations
- Test-only change; bandit does not scan `tests/` in the `-r scripts/` run; no secrets or subprocess use added.

## Rollback considerations
- `git checkout` revert of the unit commit. Part of release unit maintenance-error-semantics — revert together with `_01`..`_03`, `_05`; these tests are the regression gate for the landed behavior.

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py -v` → new tests pass; the regression watch list stays green (AC-1..AC-5).
- `uv run pytest tests/db tests/agent/commands -v` → plan Phase 3 combined run incl. the UNK-01 regression check (procedure `_05`).
- `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` → ≥ 90% on the branch diff (baseline 95%).

## Completion criteria
- All five new tests pass and assert exactly AC-1..AC-5 as specified; every pre-existing test in the file is green with unchanged assertions (rename excepted); diff-cover gate passes.

## Out of Scope
- Production edits to `maintenance.py`/`store_impl.py`/`store_protocols.py` (procedures `_01`..`_03`).
- `tests/agent/commands/test_memory_data_ops.py` (procedure `20261116-072110_05`).
- The `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` update (plan Phase 3 step).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the five REQ-006 tests + rename (plan Phase 3) | Pending | — | — | REQ-006 |
| 2 | Run `uv run pytest tests/db tests/agent/commands -v` incl. regression watch | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) + diff-cover | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006 (behavior-pinning tests for REQ-001..REQ-005)
- **Source issue**: issues/20261114-092854_dbreview006_maintenance-error-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-050112_dbreview006_maintenance-error-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-072110
- **Related target files**: tests/db/test_db_maintenance.py
