## Goal

Set the side-effect flag before non-READ tool calls in `scripts/agent/tool_runner.py` by hoisting the operation classification above the gateway branch (REQ-006 / AC-6).

## Scope

- In `_execute_prepared_call` (`tool_runner.py:194-221`, re-verified 2026-11-01), move `classify_operation_type(name, ctx.services_required.runtime_tools)` (`currently at :215`) above the gateway branch (`gateway is not None` return at `:211-213`), and set `ctx.turn.attempt_side_effect = True` whenever the classification is not `OperationType.READ` — before `gateway.execute(...)` (`:212`) or `tools.execute(...)` (`:221`).
- The no-gateway preflight path (`:214-219`) consumes the same classification result (no second call); `check_preflight` behavior is unchanged.
- Unclassified tools (`OperationType.UNKNOWN`) set the flag (conservative rule, Plan Assumptions/UNK-06).

## Assumptions

- Plan `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` is Frozen; its 12-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table (re-verified 2026-11-01: all 12 paths exist on `master`, no row replaced).
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record'); drifted citations carry `(re-verified 2026-11-01)` markers.
- Canonical semantics come from the Plan REQs (Plan `:38-48`): `retry_policy.retry_on` list drawn from `exception`/`timeout`/`llm_failure` with default `["exception"]` (REQ-001); deadline-versus-inner timeout classification via the deadline's `expired()` state (REQ-002); every failed attempt consumes one budget unit and ineligible kinds are terminal at once (REQ-003); typed outward kinds `workflow_halted` / `workflow_timeout` on the `(answer, error_kind, is_partial)` tuple (REQ-004); LLM-level failure results enter the engine as stage failures of kind `llm_failure` (REQ-005); per-attempt side-effect flag on `TurnState` set by `tool_runner` (REQ-006); attempt kinds `timeout`/`exception`/`llm_failure` distinct from outward kinds (REQ-007); no turn ends with empty answer, `error_kind` `None`, and a `halted`/`failed` task (REQ-008).
- Owner decisions (Plan UNK-01, UNK-02, 2026-10-30): timeouts and LLM-failure results are not retried by default; the shipped `retry_on` pins this, and the landed engine already treats timeouts as terminal (`workflow_engine.py:208-209`, re-verified 2026-11-01).
- Landing order (Plan Assumptions 'Re-verification record'; updated by the 2026-11-02 execution verification): wftaskapi001 `20261101-140834` and wflease001 `20261101-163219` have landed on `master` (wflease001 registered migration code 4 / "1.4.0"); the wfrecovery001 `20261101-145309` procedures remain Pending and this batch lands ahead of them by owner decision, so those Pending procedure docs must be re-verified against the landed source before their own execution. Shared-file edits (`workflow_engine.py`, `models.py`, `workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `docs/23_agent/agent_03_03_...md`) rebase predictably. The wfrecovery001 Phase 4 attempt/budget contract itself is already landed on `master` (per-attempt event ids `{task_id}:{stage_id}:{attempt}`, `begin_stage_if_new` at `workflow_engine.py:264`, `finish_attempt` kinds at `:280-298`), so the Phase 2 gate is open.
- Side-effect rule (Plan Assumptions, UNK-06): every non-READ operation, including `classify_operation_type` results of `UNKNOWN`, counts as a side effect (conservative) until the owner decides a relaxation on top of the landed toolexec001 replay protocol.
- This Plan touches no schema, migration, or migration-registry file: the workflow migration ledger (`scripts/db/migrations_workflow.py`, landed HEAD code 4 / "1.4.0") is not a target row and needs no change here.
- Production always has a gateway (`factory.py:652` creates `RepositoryGateway` unconditionally; module docstring at `tool_runner.py:207-209`) — without the hoist the flag would never be set in production, which is exactly the defect REQ-006 names.
- `classify_operation_type` and `OperationType` are already imported (`tool_runner.py:37` region); `tool_policy.py` is a Reference File, not a target (no change there).

## Design decisions

- Set-before-execute (not after success): the flag records that a side effect was attempted, so a crashed or timed-out non-READ call also blocks retry (Plan Intent 'A retry never follows a completed non-READ tool call' — 'completed' means the call ran, not that it succeeded).
- One classification per call: hoisting reuses the value for both the flag and the preflight gate.

## Alternatives considered

- Set the flag inside `RepositoryGateway.execute` — rejected: the gateway is not a target row (frozen table), and the no-gateway path would miss the flag.

## Implementation
### Target file
`scripts/agent/tool_runner.py`

### Procedure
1. Hoist the classification line above the gateway branch.
2. Add the flag assignment in the non-READ case, keeping the existing preflight `try/except PolicyViolationError` block (`:216-219`).

### Method
Reordering plus one attribute write; no signature changes.

### Details
- Flag writes go through `ctx.turn` (`AgentContext.turn`, `context.py:320` region) — the same object the adapter reads per attempt (procedure 05).
- `_record_transport_failure` (`:223+`) and the recorder path above `_execute_prepared_call` (`:274`) are untouched.

## Compatibility considerations

- Blocked until procedure 06 lands (the field must exist).
- Blast radius per Plan Affected areas: `tool_runner.py` 9 commits in 30 days; behavior change is confined to setting a new flag no existing consumer reads until procedure 05 lands.

## Security considerations

- No new SQL surface: attempt persistence stays on the existing parameter-bound `finish_attempt` path; the new `error_kind` values are engine-produced literals, never caller- or user-supplied strings.
- Hoisting does not weaken the preflight gate: non-READ calls still hit `check_preflight` in the no-gateway branch, and the gateway path keeps its own enforcement (module docstring `:197-210`).

## Rollback considerations

- Restore the original branch order and delete the flag write; preflight behavior is byte-identical to today.

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py -v` (procedure 11).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports` (baseline 6 kept, 0 broken), `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-6 (setter half): after any non-READ call the flag is true; READ-only attempts leave it false; unclassified tools set it.

## Out of Scope

- Retry suppression itself (procedures 01/05).
- `tool_policy.py` classification changes (Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Hoisted classify_operation_type above the gateway branch in _execute_prepared_call; flag set (ctx.turn.attempt_side_effect = True) for every non-READ classification incl. UNKNOWN before gateway.execute or tools.execute; no-gateway preflight try/except PolicyViolationError unchanged and reuses the single classification result. |
| 2 | Add or update tests per Validation plan | Completed | — | — | No new tests in this procedure; flag-setter tests land in procedure 11. pytest tests/agent/test_tool_runner.py: 79 passed unchanged. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff format/check, mypy clean, lint-imports 6 kept, bandit clean; check-module-size initially exceeded by 31 B from added comments - fixed by shortening comments (no baseline addition); full-suite run at end of batch. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | Out of scope for this procedure; docs updated by procedure 12. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Blocked until procedure 06 adds the `TurnState.attempt_side_effect` field | Yes | 2026-11-02: procedure 06 landed immediately before this one |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 3 (Side-effect rule)
- **Requirement ID**: `REQ-006`
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-165312
- **Related target files**: `scripts/agent/tool_runner.py`, `scripts/agent/context.py`, `scripts/agent/workflow_engine_adapter.py`, `tests/agent/test_tool_runner.py`