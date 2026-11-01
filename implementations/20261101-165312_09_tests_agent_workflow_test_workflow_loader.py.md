## Goal

Add `retry_on` loader tests to `tests/agent/workflow/test_workflow_loader.py` (REQ-001, REQ-009, REQ-011 / AC-1, AC-9).

## Scope

- New cases: valid `retry_on` list parses to the tuple; absent key loads the default `("exception",)`; unknown kind (`"halt"`) raises `WorkflowLoadError`; non-list or non-string values raise `WorkflowLoadError`; a definition without `retry_on` (older format) still loads (AC-9 compatibility).
- Shipped-file case: `WorkflowLoader().load("default")` produces `retry_on == ("exception",)` from `config/workflows/default.json` (pins procedure 04).
- Pre-flight parity: one case runs the same validation `python -m agent.workflow.validate` performs (REQ-011 / AC-9).

## Assumptions

- Plan `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` is Frozen; its 12-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table (re-verified 2026-11-01: all 12 paths exist on `master`, no row replaced).
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record'); drifted citations carry `(re-verified 2026-11-01)` markers.
- Canonical semantics come from the Plan REQs (Plan `:38-48`): `retry_policy.retry_on` list drawn from `exception`/`timeout`/`llm_failure` with default `["exception"]` (REQ-001); deadline-versus-inner timeout classification via the deadline's `expired()` state (REQ-002); every failed attempt consumes one budget unit and ineligible kinds are terminal at once (REQ-003); typed outward kinds `workflow_halted` / `workflow_timeout` on the `(answer, error_kind, is_partial)` tuple (REQ-004); LLM-level failure results enter the engine as stage failures of kind `llm_failure` (REQ-005); per-attempt side-effect flag on `TurnState` set by `tool_runner` (REQ-006); attempt kinds `timeout`/`exception`/`llm_failure` distinct from outward kinds (REQ-007); no turn ends with empty answer, `error_kind` `None`, and a `halted`/`failed` task (REQ-008).
- Owner decisions (Plan UNK-01, UNK-02, 2026-10-30): timeouts and LLM-failure results are not retried by default; the shipped `retry_on` pins this, and the landed engine already treats timeouts as terminal (`workflow_engine.py:208-209`, re-verified 2026-11-01).
- Landing order (Plan Assumptions 'Re-verification record'): this batch lands after the pending procedure batches in plan order — wftaskapi001 `20261101-140834`, wfrecovery001 `20261101-145309`, wflease001 `20261101-163219` — so shared-file edits (`workflow_engine.py`, `models.py`, `workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `docs/23_agent/agent_03_03_...md`) rebase predictably. The wfrecovery001 Phase 4 attempt/budget contract itself is already landed on `master` (per-attempt event ids `{task_id}:{stage_id}:{attempt}`, `begin_stage_if_new` at `workflow_engine.py:264`, `finish_attempt` kinds at `:280-298`), so the Phase 2 gate is open.
- Side-effect rule (Plan Assumptions, UNK-06): every non-READ operation, including `classify_operation_type` results of `UNKNOWN`, counts as a side effect (conservative) until the owner decides a relaxation on top of the landed toolexec001 replay protocol.
- This Plan touches no schema, migration, or migration-registry file: the workflow migration ledger (`scripts/db/migrations_workflow.py`, HEAD code 2 / "1.2.0") is not a target row and needs no change here.
- The file's existing tmp-path definition fixtures (file is 248 lines, required-keys coverage only, re-verified 2026-11-01) are reused for each variant.

## Design decisions

- Each AC-1 clause (present/absent/unknown) gets its own case so failures localize to the loader helper.

## Alternatives considered

- Parametrized single test — rejected: the file's existing style is explicit named cases.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_loader.py`

### Procedure
1. Append `TestRetryOn` with the cases above.

### Method
Test-only additions in the existing class-per-topic layout.

### Details
- `WorkflowLoadError` import already used in this file for the existing key tests.

## Compatibility considerations

- No changes to the existing required-keys tests.

## Security considerations

- No new SQL surface: attempt persistence stays on the existing parameter-bound `finish_attempt` path; the new `error_kind` values are engine-produced literals, never caller- or user-supplied strings.

## Rollback considerations

- Delete the class.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_loader.py -v` — new cases fail against pre-change `master`.

## Completion criteria

- AC-1 and AC-9 fully covered in this file.

## Out of Scope

- Engine consumption tests (procedure 08).

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
- **Workflow phase**: Phase 1 (Policy schema and loader)
- **Requirement ID**: `REQ-001`, `REQ-009`, `REQ-011`
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-165312
- **Related target files**: `tests/agent/workflow/test_workflow_loader.py`, `scripts/agent/workflow/workflow_loader.py`, `scripts/agent/workflow/models.py`, `config/workflows/default.json`
