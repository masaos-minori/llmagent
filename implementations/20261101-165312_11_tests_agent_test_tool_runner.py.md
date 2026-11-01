## Goal

Add side-effect-flag tests to `tests/agent/test_tool_runner.py` (REQ-006, REQ-009 / AC-6).

## Scope

- New cases through the file's existing `_execute_prepared_call` test pattern (file is 2265 lines, re-verified 2026-11-01): a non-READ call through a mocked gateway sets `ctx.turn.attempt_side_effect` true before the gateway executes; a READ call leaves it false; an unclassified (UNKNOWN) tool sets it; the no-gateway branch sets it and still runs `check_preflight` unchanged.
- Flag ordering: a case where the mocked gateway raises asserts the flag was already set before the exception (set-before-execute contract).

## Assumptions

- Plan `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` is Frozen; its 12-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table (re-verified 2026-11-01: all 12 paths exist on `master`, no row replaced).
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record'); drifted citations carry `(re-verified 2026-11-01)` markers.
- Canonical semantics come from the Plan REQs (Plan `:38-48`): `retry_policy.retry_on` list drawn from `exception`/`timeout`/`llm_failure` with default `["exception"]` (REQ-001); deadline-versus-inner timeout classification via the deadline's `expired()` state (REQ-002); every failed attempt consumes one budget unit and ineligible kinds are terminal at once (REQ-003); typed outward kinds `workflow_halted` / `workflow_timeout` on the `(answer, error_kind, is_partial)` tuple (REQ-004); LLM-level failure results enter the engine as stage failures of kind `llm_failure` (REQ-005); per-attempt side-effect flag on `TurnState` set by `tool_runner` (REQ-006); attempt kinds `timeout`/`exception`/`llm_failure` distinct from outward kinds (REQ-007); no turn ends with empty answer, `error_kind` `None`, and a `halted`/`failed` task (REQ-008).
- Owner decisions (Plan UNK-01, UNK-02, 2026-10-30): timeouts and LLM-failure results are not retried by default; the shipped `retry_on` pins this, and the landed engine already treats timeouts as terminal (`workflow_engine.py:208-209`, re-verified 2026-11-01).
- Landing order (Plan Assumptions 'Re-verification record'): this batch lands after the pending procedure batches in plan order — wftaskapi001 `20261101-140834`, wfrecovery001 `20261101-145309`, wflease001 `20261101-163219` — so shared-file edits (`workflow_engine.py`, `models.py`, `workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `docs/23_agent/agent_03_03_...md`) rebase predictably. The wfrecovery001 Phase 4 attempt/budget contract itself is already landed on `master` (per-attempt event ids `{task_id}:{stage_id}:{attempt}`, `begin_stage_if_new` at `workflow_engine.py:264`, `finish_attempt` kinds at `:280-298`), so the Phase 2 gate is open.
- Side-effect rule (Plan Assumptions, UNK-06): every non-READ operation, including `classify_operation_type` results of `UNKNOWN`, counts as a side effect (conservative) until the owner decides a relaxation on top of the landed toolexec001 replay protocol.
- This Plan touches no schema, migration, or migration-registry file: the workflow migration ledger (`scripts/db/migrations_workflow.py`, HEAD code 2 / "1.2.0") is not a target row and needs no change here.
- `TurnState` in test fixtures is the real dataclass (the file's `_make_ctx`-style helpers construct it); no new fixture layer.

## Design decisions

- Read the flag on the context object (the adapter-visible contract), not the classification call log.

## Alternatives considered

- Assert classification hoisting via call-order mocks only — rejected: AC-6 is about the flag state.

## Implementation
### Target file
`tests/agent/test_tool_runner.py`

### Procedure
1. Append `TestAttemptSideEffectFlag` with the four ordering/state cases.

### Method
Test-only additions.

### Details
- Gateway mocks: reuse the file's existing fake-gateway fixtures so both branches are exercised.

## Compatibility considerations

- Existing 2265-line file's cases stay untouched.

## Security considerations

- No new SQL surface: attempt persistence stays on the existing parameter-bound `finish_attempt` path; the new `error_kind` values are engine-produced literals, never caller- or user-supplied strings.

## Rollback considerations

- Delete the class.

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py -v` — new cases fail against pre-change `master`.

## Completion criteria

- AC-6 (flag half) covered by this file.

## Out of Scope

- Retry suppression behavior (procedure 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 3 (Side-effect rule)
- **Requirement ID**: `REQ-006`, `REQ-009`
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-165312
- **Related target files**: `tests/agent/test_tool_runner.py`, `scripts/agent/tool_runner.py`, `scripts/agent/context.py`
