## Goal

Add the `retry_on` field to `RetryPolicy` in `scripts/agent/workflow/models.py` with the shipped default that preserves today's behavior (REQ-001 / AC-1).

## Scope

- Extend `RetryPolicy` (`models.py:61-66`, fields `max_attempts`, `backoff_sec`) with `retry_on: tuple[str, ...] = ("exception",)`.
- Kind names are the literals `"exception"`, `"timeout"`, `"llm_failure"`; the field is a tuple so the dataclass stays hashable/immutable like its siblings.
- No other model changes: `StageDefinition` (`:54-56`) and `WorkflowDef` (`:69+`) are untouched; the stage-level `retryable` flag remains the outer gate.

## Assumptions

- Plan `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` is Frozen; its 12-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table (re-verified 2026-11-01: all 12 paths exist on `master`, no row replaced).
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record'); drifted citations carry `(re-verified 2026-11-01)` markers.
- Canonical semantics come from the Plan REQs (Plan `:38-48`): `retry_policy.retry_on` list drawn from `exception`/`timeout`/`llm_failure` with default `["exception"]` (REQ-001); deadline-versus-inner timeout classification via the deadline's `expired()` state (REQ-002); every failed attempt consumes one budget unit and ineligible kinds are terminal at once (REQ-003); typed outward kinds `workflow_halted` / `workflow_timeout` on the `(answer, error_kind, is_partial)` tuple (REQ-004); LLM-level failure results enter the engine as stage failures of kind `llm_failure` (REQ-005); per-attempt side-effect flag on `TurnState` set by `tool_runner` (REQ-006); attempt kinds `timeout`/`exception`/`llm_failure` distinct from outward kinds (REQ-007); no turn ends with empty answer, `error_kind` `None`, and a `halted`/`failed` task (REQ-008).
- Owner decisions (Plan UNK-01, UNK-02, 2026-10-30): timeouts and LLM-failure results are not retried by default; the shipped `retry_on` pins this, and the landed engine already treats timeouts as terminal (`workflow_engine.py:208-209`, re-verified 2026-11-01).
- Landing order (Plan Assumptions 'Re-verification record'): this batch lands after the pending procedure batches in plan order — wftaskapi001 `20261101-140834`, wfrecovery001 `20261101-145309`, wflease001 `20261101-163219` — so shared-file edits (`workflow_engine.py`, `models.py`, `workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `docs/23_agent/agent_03_03_...md`) rebase predictably. The wfrecovery001 Phase 4 attempt/budget contract itself is already landed on `master` (per-attempt event ids `{task_id}:{stage_id}:{attempt}`, `begin_stage_if_new` at `workflow_engine.py:264`, `finish_attempt` kinds at `:280-298`), so the Phase 2 gate is open.
- Side-effect rule (Plan Assumptions, UNK-06): every non-READ operation, including `classify_operation_type` results of `UNKNOWN`, counts as a side effect (conservative) until the owner decides a relaxation on top of the landed toolexec001 replay protocol.
- This Plan touches no schema, migration, or migration-registry file: the workflow migration ledger (`scripts/db/migrations_workflow.py`, HEAD code 2 / "1.2.0") is not a target row and needs no change here.
- Default `("exception",)` reproduces the owner-decided behavior (Plan UNK-01/UNK-02); `RetryPolicy` is constructed only by `workflow_loader.py` (`:128-131`) and test fixtures (`tests/agent/workflow/*`), so a defaulted field breaks nothing.

## Design decisions

- Per-kind list instead of a boolean `retry_timeouts` (Plan Design 'Retry policy' alternative (a)): it also covers `llm_failure` and future kinds without more booleans.

## Alternatives considered

- `list[str]` field — rejected: mutable default is illegal on a dataclass and the value is read-only after load.
- A new `RetryKind` enum — rejected by Plan scope: the loader validates literal strings against a module-level set; no shared enum file is a target row.

## Implementation
### Target file
`scripts/agent/workflow/models.py`

### Procedure
1. Add the field after `backoff_sec` (`models.py:65`).
2. Note the allowed kinds in the class docstring (`exception`, `timeout`, `llm_failure`) so the contract is visible at the dataclass.

### Method
One dataclass field addition.

### Details
- HEAD anchor (re-verified 2026-11-01): `class RetryPolicy` at `models.py:61-66`.
- `lint-imports` unaffected: `models.py` imports nothing new.

## Compatibility considerations

- The pending wftaskapi001 (`20261101-140834_03`) and wfrecovery001 (`20261101-145309_01`) procedures edit the same file earlier in plan order; Plan Assumptions record the overlap as non-contradicting (distinct dataclasses/fields).

## Security considerations

- No new SQL surface: attempt persistence stays on the existing parameter-bound `finish_attempt` path; the new `error_kind` values are engine-produced literals, never caller- or user-supplied strings.

## Rollback considerations

- Delete the field; loader and config rows revert with it.

## Validation plan

- `uv run pytest tests/agent/workflow/ -v` (procedures 08, 09 exercise the field).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports` (baseline 6 kept, 0 broken), `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-1 (model half): `RetryPolicy` carries `retry_on` with default `["exception"]` semantics.

## Out of Scope

- Validation and parsing of the key (procedure 03); the shipped config (procedure 04).

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
- **Workflow phase**: Phase 1 (Policy schema and loader; independent)
- **Requirement ID**: `REQ-001`
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-165312
- **Related target files**: `scripts/agent/workflow/models.py`, `scripts/agent/workflow/workflow_loader.py`, `config/workflows/default.json`, `tests/agent/workflow/test_workflow_loader.py`, `scripts/agent/workflow/workflow_engine.py`
