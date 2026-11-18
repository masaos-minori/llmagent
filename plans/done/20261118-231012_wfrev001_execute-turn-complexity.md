## Goal
- Split `WorkflowEngineAdapter.execute_turn` (`scripts/agent/workflow_engine_adapter.py`, ~112 lines, radon complexity C(13)) into small named methods by responsibility — turn-entry preparation, per-attempt execute closure, and exit-status bookkeeping — without changing any behavior, so each concern is independently reviewable and testable.

## Priority
Medium

## Scope
- **In-Scope**: Refactor `execute_turn` only, extracting its four mixed responsibilities into named helpers while preserving the public adapter surface and every task-status write on every exit path.
- **Out-of-Scope**: Changing the execute-stage retry/halt semantics (AC-5/AC-6); changing the workflow engine, `state_store.py`, or `orchestrator.py`; renaming public adapter methods or changing `execute_turn`'s signature; adding new behavior beyond the current exit paths.
- **Dependencies**: Related (same adapter, prior cleanup) — `issues/done/20261107-203227_wfaudit014_retry-loop-dead-parameters.md` (removed a dead exit-path parameter; this addresses the remaining structural complexity) and `issues/done/20261107-203228_wfaudit015_state-store-facade-bypass.md` (facade routing in the same class pair; avoid conflicting refactors in the same pass). Both are closed (`issues/done/`); neither gates this Plan.
  - **Depends on**: N/A: none

## Background
`execute_turn` is the single entry point that runs one LLM turn through the workflow engine. It was shaped by repeated wiring changes (ADR-014 adapter, the AC-5/AC-6 execute-stage failure contract, the turn-entry replay-control message, and the `_owns_state_store` close-on-exit lifecycle). Each added concern appended another branch or closure rather than extracting a helper. The adjacent retry-path cleanup in `issues/done/20261107-203227_wfaudit014_retry-loop-dead-parameters.md` removed one dead parameter but left the overall method structure intact.

## Problem
`execute_turn` is ~112 lines (L115-226) and mixes four unrelated responsibilities in one control-flow graph:

- Task init and workflow activation (L130-142), already delegated to `_init_workflow_task` / `_activate_workflow`.
- Three nested async closures (`plan_fn`, `execute_fn`, `verify_fn`) that mutate three `nonlocal` values (`answer`, `error_kind`, `is_partial`) and read `self._ctx.turn.attempt_side_effect` (L144-184). `plan_fn` (L144-145) and `verify_fn` (L180-183) are currently trivial `return None` no-ops; only `execute_fn` performs work.
- Turn-entry preparation inside the same `with self._tool_override(...)` scope as `engine.run` (L185-201).
- A six-branch `try/except/finally` whose `exit_reason` variable is resolved by `_status_for_exit` + `_record_exit_status` into a status the adapter may or may not write (L202-226).

The `exit_reason` threading is the fragile part: `execute_turn` sets `exit_reason` in six places, `_status_for_exit` returns `None` for every branch except `"cancelled"`, and `_record_exit_status` writes nothing when the engine already recorded the terminal status. A change that adds a new exit path (a new exception type, a new early return) can silently leave a task status unwritten because the author assumed the engine covered it. The per-attempt side-effect guard (`self._ctx.turn.attempt_side_effect = False` reset inside `execute_fn`) is also easy to misread as turn-scoped when it is actually attempt-scoped, which is what makes retries safe.

## Reason for Change
The execute-stage retry/halt contract (AC-5/AC-6) and the turn-entry replay path are both subtle; burying them in a ~112-line method with a shared `exit_reason` state machine raises the cost of the next correct change. Extracting the three responsibilities into small, named methods makes each independently reviewable and testable without loading the whole turn lifecycle. Current baseline: `execute_turn` is the most complex method in the file (radon C(13)); vulture and bandit report no findings.

## Implementation Intent
Extract by responsibility, preserving behavior byte-for-byte:

- Move turn-entry preparation (the `_prepare_turn_input` call plus its `WorkflowHaltError`/`WorkflowTimeoutError` re-route and the generic-exception "mark task halted then raise `WorkflowHaltError`" branch, L185-201) into a `_run_turn_entry(line, ctx)` async method that raises `WorkflowHaltError` on failure, matching the current halt-handler routing. `_prepare_turn_input` already exists as an independent method (L318-332); this wrapper owns the tool-override scope and the exception mapping.
- Narrow `execute_fn` so the per-attempt `attempt_side_effect` reset and the `WorkflowStageFailure` conversion (AC-5/AC-6) are visually grouped, delegating the attempt body to a small helper rather than holding it inline. Keep the nonlocal mutation of `answer`/`error_kind`/`is_partial` exactly as today.
- Replace the inline `exit_reason` string threaded through six branches with a single small function that maps an engine outcome directly to the status the adapter writes. The adapter already owns only the `"cancelled"` -> `"halted"` write (`_status_for_exit`); make that the sole adapter-owned branch explicit rather than a `None`-return convention.
- Preserve the `_owns_state_store` close-on-exit behavior in the `finally` (L220-224) unchanged.
- Consider whether `verify_fn`'s no-op needs to exist as a closure at all, or can be a module-level no-op callback passed to `engine.run` — a design choice left open (see Unknown UNK-01).

Describe the extraction in terms of responsibility boundaries, not line numbers, unless a boundary itself is the decision.

## Requirements
- `REQ-001`: Extract turn-entry preparation into its own async method with the existing halt-routes (`WorkflowHaltError`/`WorkflowTimeoutError` passthrough, generic-exception -> mark halted -> raise `WorkflowHaltError`) preserved.
- `REQ-002`: Narrow `execute_fn` so the per-attempt `attempt_side_effect` reset and the `WorkflowStageFailure` conversion are visually grouped, and confirm the reset is attempt-scoped, not turn-scoped.
- `REQ-003`: Replace the `exit_reason` string + `_status_for_exit`/`_record_exit_status` `None`-return convention with one explicit adapter-owned status write; keep the engine's own terminal writes as the only other writer.
- `REQ-004`: Preserve the `_owns_state_store` close-on-exit behavior in the `finally`.
- `REQ-005`: Behavior must be byte-for-byte identical: same task statuses written on every exit path, same `answer`/`error_kind`/`is_partial` tuple, same `on_error`/`_handle_workflow_halt` routing.

## Implementation Target Files
**Freeze status**: Frozen (set from `Draft` after `issue-to-plan` Step 8b's
Implementation Target Files Validation passed — `audit_plan_target_paths.py` reports
0 findings; both rows `Verified`).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Modify — refactor `execute_turn` into named responsibility methods; add `_run_turn_entry`; narrow `execute_fn`; collapse the `exit_reason` state machine | Structural complexity of `execute_turn` (radon C(13)); fragile six-way `exit_reason` threading | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005; Acceptance Criteria 1, 3 | `execute_turn` L115-226 (112 lines); `_status_for_exit` L56-68 returns `None` except `"cancelled"`; `_prepare_turn_input` L318-332 already independent; `execute_fn` closures L144-178 (checked in Step 3) | `test_adapter_guards.py`, `test_adapter_store_ownership.py` | Verified |
| `tests/agent/workflow/test_adapter_guards.py` | Modify — add the early-exit regression test (REQ-005 testing expectation) | New regression test that a fresh early-exit path after `engine.run` starts still produces the correct task status | REQ-005; Testing Expectations 2 | Drives `execute_turn` directly and asserts task status + returned tuple (REQ-002); fails on HEAD until the state machine cannot drop a write (checked in Step 3) | `test_adapter_guards.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tests/agent/workflow/test_adapter_store_ownership.py` | Confirm the `_owns_state_store` close-on-exit contract (REQ-004) is preserved; drives `execute_turn` and asserts the injected store survives. No change needed because `execute_turn`'s store-close path is unchanged. | REQ-004 |
| `scripts/agent/orchestrator.py` | Confirm the only external caller uses only the public `WorkflowEngineAdapter` surface (`execute_turn`/`deactivate_workflow`), which this Plan does not change. | REQ-005 |

## Acceptance Criteria
- **AC-1 (REQ-001, REQ-002, REQ-003)**: `execute_turn` no longer exceeds ~60 lines of control flow; the four responsibilities each live in a named method.
- **AC-2 (REQ-005)**: Every existing exit-path test (`test_adapter_guards.py`, `test_adapter_store_ownership.py`) passes unchanged, asserting the same task statuses and returned tuples.
- **AC-3 (REQ-005)**: No exit path leaves a task status unwritten that the current code writes; the new early-exit regression test covers a fresh exception type raised after `engine.run` starts.

## Tests
- **T-1 (REQ-005)**: Retarget/extend the existing adapter tests against the extracted methods; suites green. Existing `execute_turn`-level assertions pass unchanged (AC-2).
- **T-2 (REQ-005)**: Add a regression test (`test_adapter_guards.py`) that a new early-exit path (a fresh exception type raised after `engine.run` starts) still produces the correct task status, so the state machine cannot silently drop a write again (AC-3).
- **T-3 (REQ-001..REQ-004)**: Ruff format/check and mypy clean on `scripts/agent/workflow_engine_adapter.py`.

## Documentation Impact
N/A: no `docs/*.md` describes the adapter's turn-execution flow or task-status ownership in a way this refactor changes. If the implementation phase finds such a doc via `docs/00_index.md`'s "Document References by Task" table, confirm the extracted methods match and compress any per-branch description into the responsibility boundary rather than adding implementation-step detail.

## Assumptions
- The public adapter surface (`execute_turn`, `deactivate_workflow`) signatures and return contract stay fixed, so `orchestrator.py` needs no change.
- The three `nonlocal` values (`answer`, `error_kind`, `is_partial`) and their mutation sites are preserved exactly; extracting closures passes these as parameters rather than relying on closure capture.
- `engine.run(task, plan_fn, execute_fn, verify_fn)` still receives three awaitable/callable callbacks; if `verify_fn` becomes a module-level no-op it must remain awaitable to satisfy the same call contract.
- Each extraction step preserves behavior, so the suite stays green after every step and each step is independently revertable.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Should `verify_fn` remain a closure, or become a module-level no-op callback? The verify stage is required by `workflow_loader.py`, but the turn-end work now lives in the Orchestrator bracket, so the closure does nothing today. Both options preserve behavior. | None missing; this is an owner preference, not a repository gap. | Owner confirms during `plan-to-implementation-procedure`; either choice is acceptable. | False |
| UNK-02 | Whether to make the adapter's sole status write (`"cancelled"` -> `"halted"`) explicit via an outcome enum, or keep the current `_status_for_exit`/`_record_exit_status` `None`-return convention. Both preserve behavior. | None missing; owner preference. | Owner confirms during `plan-to-implementation-procedure`; either choice is acceptable. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/workflow/test_adapter_guards.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

Blast Radius is judged qualitatively (Path A): the only external caller is `orchestrator.py`, which uses only the public surface this Plan does not change. `Churn (30d)` and `Bus Factor` are `N/A` because Path A skips the historical analysis.

## Design
Classification: **Path A** (see `skills/issue-to-plan/SKILL.md` Routing). Modification scope is ≤3 files (`scripts/agent/workflow_engine_adapter.py` + one test file), the public adapter surface is unchanged, and there is no DB-schema change. The import inspection (Step 3) confirms `workflow_engine_adapter.py` is imported only by `scripts/agent/orchestrator.py` (public `WorkflowEngineAdapter`), and the two test files are standalone.

Responsibility boundaries for the extraction:

- **Turn-entry preparation** → `_run_turn_entry(line, ctx)`: owns the `with self._tool_override(self._allowed_tools)` scope, calls the existing `_prepare_turn_input(line, ctx)`, and maps exceptions: `WorkflowHaltError`/`WorkflowTimeoutError` re-raise, any other exception -> mark the task `"halted"` via `self._state_store.update_task_status` then raise `WorkflowHaltError`. This reproduces L185-201's routing exactly.
- **Per-attempt execute** → `execute_fn` narrowed to reset `attempt_side_effect`, call an attempt helper, and convert `error_kind` to `WorkflowStageFailure` (AC-5/AC-6); the attempt body (`_run_execute_stage` call + side-effect terminal check) moves into a small named helper. `plan_fn`/`verify_fn` stay as the three callbacks passed to `engine.run` until UNK-01 is resolved.
- **Exit-status bookkeeping** → the six-branch `try/except/finally` keeps its structure; the `exit_reason` string is replaced by a direct mapping from the engine outcome to the status the adapter writes, with `_status_for_exit`'s single `"cancelled"` -> `"halted"` branch made explicit. `_record_exit_status` and the `_owns_state_store` close-on-exit in `finally` are unchanged (REQ-004).

No release unit: every extraction step preserves behavior, so the suite stays green after each step and all phases land together in one commit (each independently revertable).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Extract turn-entry preparation** (`scripts/agent/workflow_engine_adapter.py`, REQ-001)
   - [ ] Add async `_run_turn_entry(line, ctx)` that owns the `self._tool_override` scope, calls `_prepare_turn_input`, and reproduces the L185-201 exception routing (passthrough of `WorkflowHaltError`/`WorkflowTimeoutError`; generic exception -> mark task `"halted"` -> raise `WorkflowHaltError`).
   - [ ] Replace the inline L185-201 block in `execute_turn` with a call to `_run_turn_entry`; confirm behavior unchanged by the existing adapter tests.
2. **Phase 2: Narrow the per-attempt execute closure** (`scripts/agent/workflow_engine_adapter.py`, REQ-002)
   - [ ] Move the attempt body (`_run_execute_stage` call + `attempt_side_effect` terminal check) into a small named helper; keep `execute_fn` as a thin wrapper that resets `attempt_side_effect`, calls the helper, and converts `error_kind` to `WorkflowStageFailure` (AC-5/AC-6).
   - [ ] Preserve the nonlocal mutation of `answer`/`error_kind`/`is_partial` exactly.
3. **Phase 3: Collapse the `exit_reason` state machine and verify** (`scripts/agent/workflow_engine_adapter.py`, `tests/agent/workflow/test_adapter_guards.py`, REQ-003, REQ-004, REQ-005)
   - [ ] Replace the inline `exit_reason` string threading with a direct outcome-to-status mapping; make the `"cancelled"` -> `"halted"` branch explicit; leave `_record_exit_status` and the `_owns_state_store` close-on-exit in `finally` unchanged.
   - [ ] Add the early-exit regression test to `tests/agent/workflow/test_adapter_guards.py` (fresh exception type raised after `engine.run` starts still yields the correct task status).
   - [ ] Run ruff, mypy, the adapter test suite, and radon (expect complexity reduced, behavior unchanged).

### Release units
N/A: no release unit — every phase passes validation alone because each extraction preserves behavior and the suite stays green after each step.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Static: format, lint, types, architecture, security, complexity | `uv run ruff format --check scripts/agent/workflow_engine_adapter.py`; `uv run ruff check scripts/agent/workflow_engine_adapter.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports`; `uv run bandit scripts/agent/workflow_engine_adapter.py`; `uv run radon cc scripts/agent/workflow_engine_adapter.py -s` | ruff/mypy/lint-imports/bandit clean; radon shows `execute_turn` complexity below C(13) |
| `tests/agent/workflow/test_adapter_guards.py`, `tests/agent/workflow/test_adapter_store_ownership.py` | Unit: existing exit-path assertions pass unchanged; new early-exit regression test passes | `uv run pytest tests/agent/workflow/test_adapter_guards.py tests/agent/workflow/test_adapter_store_ownership.py -v` | All pass, asserting the same task statuses and returned tuples |
| `scripts/` changed lines (all) | Diff-scoped coverage across the refactor diff | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"` → `uv run coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥90% on changed lines (`rules/toolchain.md` completion checklist). Document-only phase records the baseline (no changed lines yet); the threshold gates the refactor diff in the implementation phase.

## Risks
- **Risk**: The refactor changes internal control flow; a subtle difference (e.g. the ordering of the `_record_exit_status` write vs. the engine's terminal write, or the `attempt_side_effect` reset timing) could silently change a task-status write. → **Mitigation**: REQ-005's byte-for-byte contract enforced by the existing exit-path tests passing unchanged (AC-2) plus the new early-exit regression test (AC-3); radon comparison confirms complexity reduced, not behavior altered.
- **Risk**: Extracting closures that capture `workflow_id` and mutate three `nonlocal` values could introduce a scoping bug. → **Mitigation**: pass values explicitly as parameters instead of relying on closure capture; the returned tuple is asserted by existing tests.
- **Risk**: Making `verify_fn` a module-level no-op (UNK-01) could break `engine.run`'s expectation that it receives three awaitable callbacks. → **Mitigation**: keep the module-level no-op awaitable, or retain the closure until UNK-01 is resolved; do not change the callback contract.
- **Risk**: Replacing the `exit_reason` state machine could drop a status write on a newly added exit path. → **Mitigation**: AC-3 requires that no exit path leaves a task status unwritten; the regression test covers a fresh post-`engine.run` exception.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Extract turn-entry preparation into `_run_turn_entry` (`scripts/agent/workflow_engine_adapter.py`, REQ-001) | In Progress | — | — |  |
| 2 | Phase 2: Narrow the per-attempt execute closure (`scripts/agent/workflow_engine_adapter.py`, REQ-002) | In Progress | — | — |  |
| 3 | Phase 3: Collapse the `exit_reason` state machine and verify (`scripts/agent/workflow_engine_adapter.py`, `tests/agent/workflow/test_adapter_guards.py`, REQ-003/004/005) | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261119-070552_01_scripts_agent_workflow_engine_adapter.py.md | 1, 2, 3 | Procedure | Pending | — | — |
| implementations/20261119-070552_02_tests_agent_workflow_test_adapter_guards.py.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261118-221314_wfrev001_execute-turn-complexity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261118-231012
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`, `tests/agent/workflow/test_adapter_guards.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; `_prepare_turn_input` exists independent (L318-332) | `scripts/agent/workflow_engine_adapter.py` | Step 1 | AC-1 | T-3 | Confirmed by repository evidence |
| REQ-002 | Required Changes bullet 2; `execute_fn` closure body (L147-178) | `scripts/agent/workflow_engine_adapter.py` | Step 2 | AC-1 | T-1 | Confirmed by repository evidence |
| REQ-003 | Required Changes bullet 3; `_status_for_exit` returns `None` except `"cancelled"` (L56-68) | `scripts/agent/workflow_engine_adapter.py` | Step 3 | AC-1, AC-3 | T-2 | Confirmed by repository evidence |
| REQ-004 | Constraints bullet 4; `_owns_state_store` close-on-exit in `finally` (L220-224) | `scripts/agent/workflow_engine_adapter.py` | Step 3 | AC-2 | T-1 | Confirmed by repository evidence |
| REQ-005 | Constraints (byte-for-byte identical); Testing Expectations | `scripts/agent/workflow_engine_adapter.py`, `tests/agent/workflow/test_adapter_guards.py` | Step 3 | AC-2, AC-3 | T-1, T-2 | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261119-070552 -->