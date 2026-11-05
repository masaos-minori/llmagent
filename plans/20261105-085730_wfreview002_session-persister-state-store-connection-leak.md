## Goal
- Close the `StateStore` that `SessionPersister.persist_session_diagnostics()` opens, on every exit path, without changing the reported diagnostics values or the non-fatal failure posture.

## Priority
Medium

## Scope
- **In-Scope**: ownership and `finally`-based close of the persister-created `StateStore`; a close-spy test for the success and DB-error paths.
- **Out-of-Scope**: closing `Orchestrator`'s process-lifetime `self._state_store`; the session id semantics of the counts (wfreview001); `StateStore` ownership semantics on the engine/adapter path; adding a context-manager protocol to `StateStore`.
- **Dependencies**: `N/A: none`. The related Issue wfreview001 (`plans/20261105-085618_wfreview001_workflow-diagnostics-empty-session-id.md`) edits the same function's inputs but not this file, so the two are independent.

## Background
Adversarial review (2026-11-03) found that the diagnostics block builds `StateStore()` and never calls `close()`. `StateStore.__init__` opens `workflow.sqlite` in write mode; `close()` is the teardown.

## Problem
Verified in Step 2: `scripts/agent/session_persister.py` imports and builds `StateStore()` inside `try`, runs four queries, and has no `finally` and no `close()` (`rg` finds no `close`/`closing` in the file). `scripts/agent/workflow_engine_adapter.py` closes the stores it owns, so the persister is the outlier. Each persisted session leaks one write-mode connection.

## Reason for Change
The fix is local, and "the opener closes" is the codebase's resource rule. An idle write connection can also contend with the engine's `begin_immediate()` transactions.

## Implementation Intent
Bind the store to a local before the queries, and close it in a `finally` that cannot raise: a failing `close()` is logged as a warning and swallowed, so the method keeps its log-and-continue posture. A constructor failure leaves nothing to close. No `StateStore` change.

## Requirements
- `REQ-001`: The `StateStore` created in `persist_session_diagnostics()` is closed exactly once on the success path, the `sqlite3.Error`/`RuntimeError` query-failure path, and the `execute_attempts is None` guard path.
- `REQ-002`: A failure inside `close()` does not escape `persist_session_diagnostics()` and is logged, not silently swallowed.
- `REQ-003`: A test asserts exactly-once `close()` on the success path and on the DB-error path, and the `close()`-raises case of REQ-002.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/session_persister.py` | Session diagnostics persistence | Add `finally`-based, non-raising close of the local `StateStore` | REQ-001, REQ-002 / AC-1, AC-2 | `store = StateStore()` in `persist_session_diagnostics`, no close on any path (checked in Step 2) | `tests/agent/test_session_persister.py` | Verified |
| `tests/agent/test_session_persister.py` | Persister tests | Add close-spy cases; the `db` fixture patches `StateStore` with `RuntimeError`, so the new cases patch it with a mock store | REQ-003 / AC-3 | `db` fixture at the top of the file patches `agent.workflow.state_store.StateStore` (checked in Step 2) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/state_store.py` | `StateStore.__init__` opens the DB; `close()` delegates to `SQLiteHelper.close()` | REQ-001 |
| `scripts/db/helper.py` | `SQLiteHelper.close()` catches only `OSError`, so a `sqlite3.Error` from `conn.close()` can propagate | REQ-002 |
| `scripts/agent/workflow_engine_adapter.py` | Pattern for closing an owned store | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001): no unclosed `StateStore()` construction remains in `scripts/agent/session_persister.py`; `close()` is called once on each path listed in REQ-001.
- AC-2 (REQ-002): a `close()` that raises `sqlite3.Error` leaves `persist_session_diagnostics()` returning normally and logs a warning.
- AC-3 (REQ-003): the new tests pass, and the existing `tests/agent/test_session_persister.py` cases pass unchanged.
- AC-4: `uv run pytest tests/agent/test_session_persister.py tests/agent/workflow`, ruff, mypy pass.

## Tests
- `REQ-001`: mock store, success path: `close` called once.
- `REQ-001`: mock store whose getter raises `sqlite3.Error`: `close` called once, no exception.
- `REQ-001`: mock store returning `None` from `get_execute_attempt_count`: `close` called once, `retry_count` stays 0.
- `REQ-002`, `REQ-003`: mock store whose `close` raises `sqlite3.Error`: no exception, warning logged.

## Documentation Impact
N/A: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` describes `StateStore` responsibility, not connection lifecycle (checked in Step 2), so the Issue's optional note is not needed.

## Assumptions
- Overlap with `plans/20261104-114342_memlogleak001_memory-persist-logs-messages.md` (same two files) judged compatible: that Plan edits `persist_session_memories` and adds `caplog` tests next to `TestPersistSessionMemoriesGate`; this Plan edits `persist_session_diagnostics` and adds separate test cases (Step 8b).
- The persister keeps its own short-lived store rather than sharing the orchestrator's `self._state_store`; sharing would change ownership and is outside the Issue.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a real-DB close test is cheap | Fixture cost of a real `workflow.sqlite` not measured | Mock spy suffices per the Issue; wfreview001's real-DB fixture may be reused later | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/session_persister.py` | Modify | Low | N/A | N/A | Runtime code under `scripts/`; copied by deploy, no schema or config change |
| `tests/agent/test_session_persister.py` | Modify | Low | N/A | N/A | None (tests are not deployed) |

## Design
Path A (2 files, no interface or schema change). The `finally` close catches `(sqlite3.Error, OSError)` and logs a warning with the session id, matching the module's existing log-and-continue style. `get_*` calls are unchanged, so reported values are identical. Consumer scan not required: no persisted schema, public API, or shared constant changes.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Add the close-spy tests and confirm the success-path and error-path cases fail on current code (REQ-001, REQ-002, REQ-003; `tests/agent/test_session_persister.py`)
2. **Phase 2: Close the store**
   - [ ] Add the non-raising `finally` close (REQ-001, REQ-002; `scripts/agent/session_persister.py`)
3. **Phase 3: Deployment & Verification**
   - [ ] Hand-off to `skills/deploy/SKILL.md`: the change must be committed and pushed first; deploying is the user's decision (approval gate). Run the Validation plan commands (REQ-001; `scripts/agent/session_persister.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_session_persister.py` | Unit, mock spy | `uv run pytest tests/agent/test_session_persister.py tests/agent/workflow` | New cases fail before Phase 2, all pass after |
| `scripts/agent/session_persister.py` | Lint, type, security, size | `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run python tools/check_module_size.py` | No new findings (radon and vulture not installed: Not available; bandit run recorded in the wfreview001 Plan) |

## Risks
- **Risk**: A close that raises replaces the original exception → **Mitigation**: close is wrapped to log and swallow `sqlite3.Error`/`OSError`, tested by REQ-002.
- **Risk**: The new mock-store tests diverge from the real `StateStore` surface → **Mitigation**: `MagicMock(spec=StateStore)` so a renamed getter fails the test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add close-spy tests, confirm they fail | Pending | — | — | |
| 2 | Add non-raising finally close | Pending | — | — | |
| 3 | Deploy hand-off and verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261103-134147_wfreview002_session-persister-state-store-connection-leak.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-085730
- **Related target files**: `scripts/agent/session_persister.py`, `tests/agent/test_session_persister.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes 1; `session_persister.py` diagnostics block | `scripts/agent/session_persister.py` | Phase 2 | AC-1 | close-spy tests | Confirmed by repository evidence |
| REQ-002 | Issue Constraints (non-fatal), AI Implementation Instruction; `SQLiteHelper.close` catches only `OSError` | `scripts/agent/session_persister.py` | Phase 2 | AC-2 | close-raises test | Derived from confirmed evidence |
| REQ-003 | Issue Required Changes 2, Testing Expectations | `tests/agent/test_session_persister.py` | Phase 1 | AC-3 | pytest command in Validation plan | Explicit in issue |
