## Goal
Remove the dead `self._spawned_subprocesses` attribute from `StartupOrchestrator` (declared in `__init__`, assigned in `run()`) and update the two tests that assert on its dead-state value, so the field no longer appears anywhere in the codebase.

## Priority
Low

## Scope
- **In-Scope**:
  - Remove the `self._spawned_subprocesses` declaration from `StartupOrchestrator.__init__` in `scripts/agent/startup.py`.
  - Change the assignment in `StartupOrchestrator.run()` from `self._spawned_subprocesses = await self._start_servers()` to a bare `await self._start_servers()` — keep the call (the side effect), drop only the assignment.
  - Update `tests/agent/test_startup_rollback.py`: drop the dead-state assertion in `test_rollback_no_op_when_no_subprocess_started`; delete `test_run_populates_spawned_subprocesses_on_exception_path`.
- **Out-of-Scope**:
  - Any change to rollback behavior (`lifecycle.shutdown_all()`).
  - Introducing new state to replace the field.
  - Any change to `McpServerStarter._spawned_subprocesses` — a live field on a different class, out of scope.
  - Any change to `tests/agent/test_startup_mcp_lifecycle.py` — its `test_retry_success_appends_to_spawned_subprocesses` asserts on `McpServerStarter`'s return value, not the target field.
- **Dependencies**: N/A: none.

## Background
`StartupOrchestrator.__init__` initializes `self._spawned_subprocesses` as an empty list. `run()` reassigns it from the return value of `_start_servers()` inside the `try` block. Nothing in `run()`, `_rollback_servers()`, or any caller ever reads it. Rollback is driven entirely by `lifecycle.shutdown_all()`, which terminates spawned subprocesses directly; the orchestrator never consults the tracked list.

Historically `repl.py` consumed this field — both the success-path return value and the exception-path instance attribute — to terminate orphaned subprocesses. That consumption was removed by a prior shutdown fix (`shutdown003`), after which the field became dead state at every level. The current source confirms zero readers.

## Problem
`self._spawned_subprocesses` is written in `__init__` and reassigned in `run()` but never read anywhere in the class or callers. It is dead state that implies an ownership/rollback contract — that the orchestrator tracks spawned processes for its own rollback — which does not exist. Shutdown is owned by `lifecycle.shutdown_all()`.

## Reason for Change
Remove misleading state. The field gives the false impression that the orchestrator tracks spawned processes for rollback, and is a maintenance hazard: a future reader who assumes the list drives shutdown will be wrong. The issue's escape hatch is explicit — either the field is genuinely needed (it is not) or it should be deleted rather than left implying a contract that does not exist.

## Implementation Intent
Delete the attribute declaration in `__init__` and drop the assignment in `run()` while keeping the `_start_servers()` call. Then update the two tests that introspect the field: remove the dead-state assertion from one and delete the other, whose sole purpose is asserting the field becomes populated.

## Requirements
- `REQ-001`: `StartupOrchestrator` no longer declares or assigns `self._spawned_subprocesses`; `run()` still calls `_start_servers()` and returns `(cmds, orchestrator)`.
- `REQ-002`: No test in the repo references `_spawned_subprocesses` on `StartupOrchestrator`; the affected tests are updated so the suite passes.

## Implementation Target Files
**Freeze status**: Frozen (was `Draft`; set to `Frozen` once `issue-to-plan` Step 8's Implementation Target Files Validation passed — see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/startup.py` | Modify | Remove the `self._spawned_subprocesses` declaration from `StartupOrchestrator.__init__` and change the `run()` assignment to a bare `await self._start_servers()` (keep the call, drop the assignment) | REQ-001; AC1, AC2 | Field declared in `StartupOrchestrator.__init__` and assigned in `run()` from `_start_servers()`; never read in `startup.py` or any caller; rollback uses `lifecycle.shutdown_all()` (checked in Step 2) | None — the field had no production consumer | Verified |
| `tests/agent/test_startup_rollback.py` | Modify | Drop the dead-state assertion in `test_rollback_no_op_when_no_subprocess_started` and delete `test_run_populates_spawned_subprocesses_on_exception_path` | REQ-002; AC3 | Two tests assert on the field: `test_rollback_no_op_when_no_subprocess_started` asserts `orch._spawned_subprocesses == []` and `test_run_populates_spawned_subprocesses_on_exception_path` asserts `orch._spawned_subprocesses == fake_procs` (checked in Step 2) | `test_rollback_no_op_when_no_subprocess_started`, `test_run_populates_spawned_subprocesses_on_exception_path` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

N/A: no reference files required — the change is self-contained within the two target files.

## Acceptance Criteria
- `StartupOrchestrator` no longer declares `self._spawned_subprocesses` in `__init__` (REQ-001, AC1).
- `run()` no longer assigns `self._spawned_subprocesses`; it still calls `_start_servers()` and returns exactly `(cmds, orchestrator)` (REQ-001, AC2).
- No test in the repo references `_spawned_subprocesses` on `StartupOrchestrator`; the affected tests are updated and the suite passes (REQ-002, AC3).

## Tests
- In `test_rollback_no_op_when_no_subprocess_started` (`tests/agent/test_startup_rollback.py`), remove `assert orch._spawned_subprocesses == []` while keeping `mock_lifecycle.shutdown_all.assert_awaited_once()`, which validates the real rollback behavior (REQ-002).
- Delete `test_run_populates_spawned_subprocesses_on_exception_path` entirely; its sole purpose is asserting the dead field becomes populated with the spawned procs (REQ-002).
- Run the full suite and confirm all tests pass (REQ-002).

## Documentation Impact
None beyond code comments. No external `docs/*.md` update required (REQ-001).

## Assumptions
- The field is confirmed dead: zero production readers; the only readers are the two tests in `test_startup_rollback.py`. Removing it changes no production behavior.
- The two tests are dead-state locks, not consumers of the field's value for any production behavior. Neither validates production rollback — that is covered by sibling assertions on `lifecycle.shutdown_all()`.
- `test_startup_mcp_lifecycle.py::test_retry_success_appends_to_spawned_subprocesses` targets `McpServerStarter._spawned_subprocesses` (a live field on a different class whose `_start_servers()` returns the list), not `StartupOrchestrator` — out of scope.
- The historical `repl.py` consumption was already removed by `shutdown003`; no other code reconstructs the field.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Was `_spawned_subprocesses` intended to drive per-process teardown in a past design, and is there external tooling or test that introspects it by name? (Issue Unresolved Questions) | None — resolved by evidence. | Git history and archived requirements show `repl.py` used to consume it (both the return value and the instance attribute) to terminate orphaned subprocesses; that consumption was removed by `shutdown003`. Today the only readers are the two tests in `test_startup_rollback.py`. The field is dead; deletion is safe. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/startup.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_rollback.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path A (≤3 files, no public/runtime interface change, no schema change). Analysis limited to direct verification of the two target files.

**Adversarial verification finding (contradiction with the issue).** The issue's precondition — "Confirm no test references `_spawned_subprocesses`" — is FALSE. Two tests in `tests/agent/test_startup_rollback.py` introspect the field by name:
- `test_rollback_no_op_when_no_subprocess_started` asserts `orch._spawned_subprocesses == []`.
- `test_run_populates_spawned_subprocesses_on_exception_path` asserts `orch._spawned_subprocesses == fake_procs`.

The field is nonetheless dead in production: grep across the repo shows it is declared and assigned only in `startup.py` and never read; rollback uses `lifecycle.shutdown_all()`. The issue's own escape hatch ("If used somewhere not yet found: document why and wire it into rollback deterministically") applies to a *production consumer*, not to tests that assert on dead-state invariants. The two tests are characterization locks on dead state, not consumers. Per the user's decision, the field is deleted and the two tests are updated accordingly. This satisfies AC #1 ("no longer appears anywhere in the codebase").

**Correct edit to `run()`.** The assignment line is `self._spawned_subprocesses = await self._start_servers()`. The meaningful effect is the call `await self._start_servers()`; the LHS assignment is the dead part. The fix drops only the `self._spawned_subprocesses =` prefix, leaving `await self._start_servers()`. Deleting the whole line would also delete the required spawn call.

**Scope boundary.** `McpServerStarter._spawned_subprocesses` (`scripts/agent/startup_mcp_starter.py`) is a live field on a different class; it is not touched. `test_startup_mcp_lifecycle.py` asserts on that class's return value, not the target field.

**Baseline.** radon: `run()` stays A(5); removing an assignment adds no branch. vulture and bandit report no findings on `startup.py` introduced by this change.

## Implementation steps
1. **Phase 1: Remove the dead field from `startup.py`**
   - [ ] Remove the `self._spawned_subprocesses: list[subprocess.Popen] = []` declaration from `StartupOrchestrator.__init__` (`scripts/agent/startup.py`) (REQ-001; AC1).
   - [ ] Change the `run()` assignment to a bare `await self._start_servers()`, keeping the call and dropping only the `self._spawned_subprocesses =` prefix (REQ-001; AC2).
2. **Phase 2: Update the tests that introspect the field**
   - [ ] In `test_rollback_no_op_when_no_subprocess_started` (`tests/agent/test_startup_rollback.py`), delete the `assert orch._spawned_subprocesses == []` line, keeping `mock_lifecycle.shutdown_all.assert_awaited_once()` (REQ-002; AC3).
   - [ ] Delete `test_run_populates_spawned_subprocesses_on_exception_path` entirely (REQ-002; AC3).
3. **Phase 3: Deployment & Verification**
   - [ ] Run `uv run pytest tests/agent/test_startup_rollback.py` and confirm all tests pass, including the updated `test_rollback_no_op_when_no_subprocess_started` and the remaining rollback tests (REQ-002; AC3).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup.py` (`StartupOrchestrator`) | Static: the field no longer exists and `run()` still calls `_start_servers()` | `rg -n "_spawned_subprocesses" scripts/agent/startup.py` (expect zero matches) | No reference to the field in `startup.py`; `run()` unchanged except the dropped assignment |
| `tests/agent/test_startup_rollback.py` | Regression: suite passes after removing the two dead-state assertions / deleting one test | `uv run pytest tests/agent/test_startup_rollback.py` | All tests pass; no assertion references the field |
| Repo-wide | Confirm no remaining reader of the field on `StartupOrchestrator` | `rg -n "_spawned_subprocesses" tests/ scripts/` | Only `McpServerStarter` references remain (different class) |

## Risks
- **Risk**: Deleting the whole `self._spawned_subprocesses = await self._start_servers()` line removes the required `_start_servers()` call, breaking startup. → **Mitigation**: The plan mandates dropping only the `self._spawned_subprocesses =` prefix and keeping `await self._start_servers()`; documented as an implementation-step constraint.
- **Risk**: Deleting a test that encodes a genuine production contract. → **Mitigation**: Both tests assert only on the dead field's value; neither validates production rollback (that is covered by sibling assertions on `lifecycle.shutdown_all()`). Deleting them removes dead-state locks, not behavior contracts.
- **Risk**: Missing another reader of the field elsewhere in the repo. → **Mitigation**: Repo-wide grep confirms the only readers are the two tests and the unrelated `McpServerStarter` field.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the dead field from `startup.py` | In Progress | — | — | Touches `scripts/agent/startup.py` |
| 2 | Update the tests that introspect the field | In Progress | — | — | Touches `tests/agent/test_startup_rollback.py` |
| 3 | Deployment & Verification | Pending | — | — | Runs `pytest tests/agent/test_startup_rollback.py` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261030-073124_01_scripts_agent_startup.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261030-073124_02_tests_agent_test_startup_rollback.py.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261029-220719_startorch001_dead-spawned-subprocesses.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261030-065511
- **Related target files**: scripts/agent/startup.py, tests/agent/test_startup_rollback.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem / Reason for Change / Required Changes; field written but never read (Step 2) | `scripts/agent/startup.py` | Step 1 | AC1, AC2 | Zero readers after change (Step 2) | Confirmed by repository evidence |
| REQ-002 | Testing Expectations / AI Implementation Instruction; two tests assert on the field (Step 2) | `tests/agent/test_startup_rollback.py` | Step 2 | AC3 | Updated/deleted tests; suite passes | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261030-073124 -->