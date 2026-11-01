## Goal

Add the per-attempt side-effect flag to `TurnState` in `scripts/agent/context.py` (REQ-006 / AC-6).

## Scope

- Extend `TurnState` (`context.py:213-226`, fields `current_turn_id`, `background_tasks`, `persistence_boundary`) with `attempt_side_effect: bool = False` (name chosen here; the Plan calls it 'a per-attempt side-effect flag' and freezes no field name).
- The flag is transient process state: no DB column, no persistence boundary write, no cross-process visibility.
- Reset is owned by the adapter's attempt start (procedure 05), not by this dataclass.

## Assumptions

- Plan `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` is Frozen; its 12-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table (re-verified 2026-11-01: all 12 paths exist on `master`, no row replaced).
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record'); drifted citations carry `(re-verified 2026-11-01)` markers.
- Canonical semantics come from the Plan REQs (Plan `:38-48`): `retry_policy.retry_on` list drawn from `exception`/`timeout`/`llm_failure` with default `["exception"]` (REQ-001); deadline-versus-inner timeout classification via the deadline's `expired()` state (REQ-002); every failed attempt consumes one budget unit and ineligible kinds are terminal at once (REQ-003); typed outward kinds `workflow_halted` / `workflow_timeout` on the `(answer, error_kind, is_partial)` tuple (REQ-004); LLM-level failure results enter the engine as stage failures of kind `llm_failure` (REQ-005); per-attempt side-effect flag on `TurnState` set by `tool_runner` (REQ-006); attempt kinds `timeout`/`exception`/`llm_failure` distinct from outward kinds (REQ-007); no turn ends with empty answer, `error_kind` `None`, and a `halted`/`failed` task (REQ-008).
- Owner decisions (Plan UNK-01, UNK-02, 2026-10-30): timeouts and LLM-failure results are not retried by default; the shipped `retry_on` pins this, and the landed engine already treats timeouts as terminal (`workflow_engine.py:208-209`, re-verified 2026-11-01).
- Landing order (Plan Assumptions 'Re-verification record'; updated by the 2026-11-02 execution verification): wftaskapi001 `20261101-140834` and wflease001 `20261101-163219` have landed on `master` (wflease001 registered migration code 4 / "1.4.0"); the wfrecovery001 `20261101-145309` procedures remain Pending and this batch lands ahead of them by owner decision, so those Pending procedure docs must be re-verified against the landed source before their own execution. Shared-file edits (`workflow_engine.py`, `models.py`, `workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `docs/23_agent/agent_03_03_...md`) rebase predictably. The wfrecovery001 Phase 4 attempt/budget contract itself is already landed on `master` (per-attempt event ids `{task_id}:{stage_id}:{attempt}`, `begin_stage_if_new` at `workflow_engine.py:264`, `finish_attempt` kinds at `:280-298`), so the Phase 2 gate is open.
- Side-effect rule (Plan Assumptions, UNK-06): every non-READ operation, including `classify_operation_type` results of `UNKNOWN`, counts as a side effect (conservative) until the owner decides a relaxation on top of the landed toolexec001 replay protocol.
- This Plan touches no schema, migration, or migration-registry file: the workflow migration ledger (`scripts/db/migrations_workflow.py`, landed HEAD code 4 / "1.4.0") is not a target row and needs no change here.
- `TurnState` is constructed once with `AgentContext` (`context.py:320` region, re-verified 2026-11-01 per the file's own comment at `:218-220`) and is not recreated per turn — so 'cleared at each attempt start' must be an explicit write at attempt start (procedure 05), which is why the default alone is not the reset mechanism.

## Design decisions

- Boolean flag instead of a per-attempt tool-call id set (Plan Design 'Side effects': the heavier tracking is unnecessary for a yes/no rule).

## Alternatives considered

- Reuse `ctx.workflow` state instead of `TurnState` — rejected (REQ-006 names `TurnState`, the per-turn transient owner).

## Implementation
### Target file
`scripts/agent/context.py`

### Procedure
1. Add the field after `persistence_boundary` (`:226`) with a comment stating: set by `tool_runner` before a non-READ call (procedure 07), cleared at each attempt start by the adapter (procedure 05), read by the adapter's failure wrap.

### Method
One dataclass field addition.

### Details
- HEAD anchor (re-verified 2026-11-01): `class TurnState` at `context.py:213-226`.
- Blast radius per Plan Affected areas: `context.py` 12 commits in 30 days; the additive defaulted field breaks no construction site.

## Compatibility considerations

- No serialization: `TurnState` is not persisted, so no schema or migration interaction exists for this Plan.

## Security considerations

- No new SQL surface: attempt persistence stays on the existing parameter-bound `finish_attempt` path; the new `error_kind` values are engine-produced literals, never caller- or user-supplied strings.

## Rollback considerations

- Delete the field; procedures 05 and 07 revert with it.

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_orchestrator.py -v` (procedures 11, 10).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports` (baseline 6 kept, 0 broken), `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-6 (state half): a defaulted boolean exists on `TurnState` that procedures 05/07 write and read.

## Out of Scope

- Who sets/clears the flag (procedures 05, 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Added attempt_side_effect: bool = False to TurnState after persistence_boundary, with ownership comment (set by tool_runner, cleared at attempt start by adapter, read by adapter failure wrap). Transient only: no DB column, no boundary write. |
| 2 | Add or update tests per Validation plan | Completed | — | — | No new tests in this procedure; flag behavior tests land in procedures 10/11. pytest tests/agent/test_context.py tests/agent/test_tool_runner.py: 96 passed, 1 skipped. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff format/check, mypy clean, lint-imports 6 kept, bandit, check-module-size OK; full-suite run at end of batch. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | Out of scope for this procedure; docs updated by procedure 12. |

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
- **Requirement ID**: `REQ-006`
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-165312
- **Related target files**: `scripts/agent/context.py`, `scripts/agent/tool_runner.py`, `scripts/agent/workflow_engine_adapter.py`, `tests/agent/test_tool_runner.py`