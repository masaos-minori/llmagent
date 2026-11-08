## Goal
Retarget every test in `test_workflow_state_store.py` from the four helpers scheduled for deletion (`start_attempt`, `count_attempts`, `StateStore.find_stale_running_attempts`, `StateStore.pending_tool_calls`) onto the production paths (`begin_stage_if_new`, `recover_stale_attempts`, `tool_call_state_ops.pending_tool_calls`, inline COUNT query), and add the lease-stamping regression test that the deleted `start_attempt` branch never had (`REQ-001`-`REQ-004`).

## Scope
**Release unit**: wfaudit009-full

- Covers Plan `plans/20261108-084010_wfaudit009_test-only-state-helpers.md` row 4 only: `tests/agent/workflow/test_workflow_state_store.py`.
- This is a Phase 1 (plan step 1) document: all edits land while the helpers still exist; the suite must be green with helpers present before documents 01-03 delete them (equivalence gate).

## Assumptions
- Call sites re-verified at HEAD `ad48bfa28`: import L20 (`count_attempts`, `finish_attempt`, `start_attempt` from `agent.workflow.attempt_ops`); `TestAttempts` L150-187; diagnostic seeds L252-254; `test_find_stale_returns_only_old_attempts` L517-534 (class `TestRecoverStaleAttempts`, helper `_insert_task_and_attempt` L282, `_open_store` L312); nine `store.pending_tool_calls` sites L719, L725, L749, L753, L763, L770, L775, L789, L812 (class `TestToolCallStateOps`).
- `begin_stage_if_new` is already imported (L21) and `tool_call_state_ops` as a module (L19); no new import lines are needed. `finish_attempt` stays imported from `agent.workflow.attempt_ops`.
- The `workflow_db`/`store` fixtures are per-test (`tmp_path`), so a `processed_events.event_id` used in one test never collides with another; within one test the event ids below are distinct.
- `wfaudit001`/`wfaudit007` land before this plan (plan Notes), so the recovery-shape assertions here must not pin internals of `recover_stale_attempts` beyond its return count, row status outcomes and `last_recovery_report` — the assertions below use only that surface.

## Design decisions
- Attempt creation in tests moves to the single production writer `begin_stage_if_new` (same insert columns; `REQ-002`), with distinct literal event ids (`evt-ta-*`, `evt-diag-*`) because its key is the event id, not the (task, stage) pair `start_attempt` used.
- Counting stays test-local via an inline `SELECT COUNT(*) as cnt FROM attempts` query (plan Assumptions: production counts attempts via the engine retry range, so no counter helper is kept).
- Stale-detection tests assert `recover_stale_attempts` outcomes (recovered count, row statuses, report counts) instead of the deleted finder's returned dicts (`REQ-003`).
- Pending-listing assertions keep their exact shape and call `tool_call_state_ops.pending_tool_calls(store._db, task_id)` directly (`REQ-004`; `UNK-01`: if `wfaudit015` adds a facade before implementation, the call can target the facade instead — assertion-equivalent).

## Alternatives considered
- Seeding attempts with raw INSERTs in tests: rejected — it bypasses the production writer and re-creates the "tests exercise a surface production never runs" problem the plan removes.
- Keeping a shared `conftest.py` attempt-seed helper: rejected — only this plan's files need it, and `begin_stage_if_new` calls with literal event ids are already the seed.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_state_store.py`

### Procedure
Six ordered edits: import line, `TestAttempts` block, diagnostic seeds, recovery finder test, pending-listing sites; then run the equivalence gate.

### Method
1. Import (L20): `from agent.workflow.attempt_ops import count_attempts, finish_attempt, start_attempt` -> `from agent.workflow.attempt_ops import finish_attempt`.
2. `TestAttempts`:
   - Rename `test_start_attempt_returns_record` (L151) to `test_begin_stage_returns_record` (new): seed `begin_stage_if_new(store._db, "evt-ta-1", task.task_id, "plan")`, `assert attempt is not None`, then keep the identical assertions (`attempt.task_id`, `attempt.stage_id`, `attempt.status == "running"`).
   - Rename `test_count_attempts` (L158) to `test_attempt_count_via_inline_query` (new): seed two attempts with event ids `evt-ta-2`/`evt-ta-3` at stage `execute`, then assert `int(rows[0]["cnt"]) == 2` from `store._db.fetchall("SELECT COUNT(*) as cnt FROM attempts WHERE task_id=? AND stage_id='execute'", (task.task_id,))`.
   - Seed swaps only: `test_finish_attempt_completed` L166 -> `begin_stage_if_new(store._db, "evt-ta-4", task.task_id, "plan")`; `test_finish_attempt_with_error` L182 -> `begin_stage_if_new(store._db, "evt-ta-5", task.task_id, "execute")`; each followed by `assert attempt is not None` before `finish_attempt(store._db, attempt.attempt_id, ...)`. All `finish_attempt`/vocabulary-guard assertions stay unchanged.
   - Add `test_begin_stage_if_new_stamps_lease_columns` (new) at the end of the class: seed with `lease_duration_sec=900` (event id `evt-ta-lease`, stage `execute`), read the row's `owner_id`/`lease_expires_at` via `store._db.fetchall` by `attempt_id`, and assert both are not NULL and `lease_expires_at > started_at` (both in the fixed `Z` format, so string comparison is safe); then seed one lease-less attempt (`evt-ta-nolease`) and assert both lease columns are NULL — covering both docstring branches of `begin_stage_if_new` that `start_attempt` duplicated untested (plan Tests section: this coverage is added, not "kept").
3. `TestDiagnosticQueries`: in `test_get_execute_attempt_count_filters_by_stage` (seeds L252-254) replace the three `start_attempt` seeds with `begin_stage_if_new` calls using event ids `evt-diag-1`/`evt-diag-2` (stage `execute`) and `evt-diag-3` (stage `plan`); the `get_execute_attempt_count` assertions stay identical.
4. `TestRecoverStaleAttempts`: rename `test_find_stale_returns_only_old_attempts` (L517-534) to `test_recovery_marks_only_old_attempts` (new) and rewrite its docstring to reference `recover_stale_attempts`. Keep both seeds unchanged (`att-1` lease-less at `2026-01-01T00:00:00Z`, `att-2` fresh via `_iso(5)`, both through `_insert_task_and_attempt`); replace the `s.find_stale_running_attempts(s._db)` call and dict-key assertions with `count = s.recover_stale_attempts(s._db)`, `assert count == 1`, status-row lookups (`att-1` `failed`, `att-2` `running`, same `s._db.fetchall` style already used in sibling tests of the class), and `assert s.last_recovery_report.legacy_recovered == 1`.
5. `TestToolCallStateOps`: swap all nine `store.pending_tool_calls(<task_id>)` call sites (L719-812) to `tool_call_state_ops.pending_tool_calls(store._db, <task_id>)`; every surrounding assertion (`idempotency_key` lists, `state`, `retry_class`, ordering, finalize/duplicate semantics) stays byte-equivalent. `store.record_tool_call` and `store.finalize_tool_call` facades survive and are not retargeted.

### Details
- After this document the file contains zero occurrences of the tokens `start_attempt`, `count_attempts` (as the helper name) and `find_stale_running_attempts` — including the old docstring at L518 — so the `REQ-001` grep is satisfied by test-side changes alone before deletion lands.
- `begin_stage_if_new` returns `AttemptRecord | None`; the `assert attempt is not None` lines keep type-checkers happy and assert the insert actually happened.

## Compatibility considerations
- Behavior-preserving: fixture setup (tasks, stages, statuses, timestamps) is unchanged; only creation calls and call targets swap (plan Risks mitigation: Phase 1 runs before deletion).
- `tests/agent/workflow/test_state_store.py` and `test_workflow_engine.py` are covered by documents 05-06; no cross-file helpers are shared with them.

## Security considerations
- None.

## Rollback considerations
- Revert this document alone: the file returns to HEAD calls, which still work because the helpers are only deleted in plan step 2 (documents 01-03).

## Validation plan
- Phase 1 equivalence gate (plan Validation plan): after these edits, `uv run pytest tests/agent/workflow/ -q` is green with all four helpers still present.
- Mutation guard (plan Risks): temporarily stub the lease-stamping branch in `begin_stage_if_new` and confirm `test_begin_stage_if_new_stamps_lease_columns` (new) fails; restore.
- New renamed/added tests must fail against HEAD if they were run before their seed swaps (they are behavior-locked to `begin_stage_if_new`). Full `uv run pytest tests/ -q` per `rules/toolchain.md`.

## Completion criteria
- Suite green with helpers present; every assertion of the HEAD file preserved with identical observable meaning; lease-stamping branch covered for the first time; zero references to the deleted helper names remain in the file.

## Out of Scope
- Deleting the helpers themselves (documents 01-03).
- `wfaudit015` facade routing for pending listing (`UNK-01`; either target is assertion-equivalent).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | the test edits are the implementation; lands before documents 01-03 |
| 2 | Add or update tests per Validation plan | Pending | — | — | merged into step 1: renames, seed swaps and `test_begin_stage_if_new_stamps_lease_columns` (new) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Phase 1 equivalence gate runs here with helpers still present |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | docs grep verified zero matches; verification-only |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261107-203222_wfaudit009_test-only-state-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084010_wfaudit009_test-only-state-helpers.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-170505
- **Related target files**: `tests/agent/workflow/test_workflow_state_store.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-170505 -->
