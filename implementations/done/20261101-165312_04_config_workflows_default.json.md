## Goal

Add the explicit shipped `retry_on` to `config/workflows/default.json` so shipped behavior is readable from configuration (REQ-001, REQ-003, REQ-011 / AC-1, AC-3, AC-9).

## Scope

- Extend the `retry_policy` block (`default.json:19-22`, currently `max_attempts: 3`, `backoff_sec: 1`) with `"retry_on": ["exception"]`.
- No stage changes: `plan`/`verify` stay `retryable: false`, `execute` stays `retryable: true` with 30/120/10 s timeouts (`:4-18`).
- `config/defaults/default_settings.json` is NOT a target — it no longer exists on `master` (re-verified 2026-11-01); workflow configuration lives only in `config/workflows/*.json`.

## Assumptions

- Plan `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` is Frozen; its 12-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table (re-verified 2026-11-01: all 12 paths exist on `master`, no row replaced).
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record'); drifted citations carry `(re-verified 2026-11-01)` markers.
- Canonical semantics come from the Plan REQs (Plan `:38-48`): `retry_policy.retry_on` list drawn from `exception`/`timeout`/`llm_failure` with default `["exception"]` (REQ-001); deadline-versus-inner timeout classification via the deadline's `expired()` state (REQ-002); every failed attempt consumes one budget unit and ineligible kinds are terminal at once (REQ-003); typed outward kinds `workflow_halted` / `workflow_timeout` on the `(answer, error_kind, is_partial)` tuple (REQ-004); LLM-level failure results enter the engine as stage failures of kind `llm_failure` (REQ-005); per-attempt side-effect flag on `TurnState` set by `tool_runner` (REQ-006); attempt kinds `timeout`/`exception`/`llm_failure` distinct from outward kinds (REQ-007); no turn ends with empty answer, `error_kind` `None`, and a `halted`/`failed` task (REQ-008).
- Owner decisions (Plan UNK-01, UNK-02, 2026-10-30): timeouts and LLM-failure results are not retried by default; the shipped `retry_on` pins this, and the landed engine already treats timeouts as terminal (`workflow_engine.py:208-209`, re-verified 2026-11-01).
- Landing order (Plan Assumptions 'Re-verification record'; updated by the 2026-11-02 execution verification): wftaskapi001 `20261101-140834` and wflease001 `20261101-163219` have landed on `master` (wflease001 registered migration code 4 / "1.4.0"); the wfrecovery001 `20261101-145309` procedures remain Pending and this batch lands ahead of them by owner decision, so those Pending procedure docs must be re-verified against the landed source before their own execution. Shared-file edits (`workflow_engine.py`, `models.py`, `workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `docs/23_agent/agent_03_03_...md`) rebase predictably. The wfrecovery001 Phase 4 attempt/budget contract itself is already landed on `master` (per-attempt event ids `{task_id}:{stage_id}:{attempt}`, `begin_stage_if_new` at `workflow_engine.py:264`, `finish_attempt` kinds at `:280-298`), so the Phase 2 gate is open.
- Side-effect rule (Plan Assumptions, UNK-06): every non-READ operation, including `classify_operation_type` results of `UNKNOWN`, counts as a side effect (conservative) until the owner decides a relaxation on top of the landed toolexec001 replay protocol.
- This Plan touches no schema, migration, or migration-registry file: the workflow migration ledger (`scripts/db/migrations_workflow.py`, landed HEAD code 4 / "1.4.0") is not a target row and needs no change here.
- The explicit value pins the owner decisions (Plan UNK-01/UNK-02): timeout and LLM failure are terminal under the shipped config.

## Design decisions

- Explicit-in-config instead of relying on the loader default (Plan row 4 'Shipped behavior must be readable from configuration').

## Alternatives considered

- Leave the key absent (loader default) — rejected by the frozen table row: AC-1 asserts the shipped file carries the key.

## Implementation
### Target file
`config/workflows/default.json`

### Procedure
1. Add the key to the `retry_policy` object.
2. Run the pre-flight validation on the edited file.

### Method
One JSON key addition.

### Details
- Rolling-deploy safety (Plan Risks): an older deployed loader ignores the unknown key (Plan Assumptions verification record), so config and code order does not matter for startup.
- Deployment sync: the deployed `/opt/llm/config/workflows/default.json` updates through the normal config sync in the deploy skill (REQ-011); deploying is the user's decision (Plan Phase 6 approval gate).

## Compatibility considerations

- `tests/agent/workflow/test_workflow_loader.py` gains a shipped-file assertion (procedure 09) so the pinned value cannot drift.

## Security considerations

- No new SQL surface: attempt persistence stays on the existing parameter-bound `finish_attempt` path; the new `error_kind` values are engine-produced literals, never caller- or user-supplied strings.

## Rollback considerations

- Remove the key; the loader default reproduces the same behavior (AC-1).

## Validation plan

- `PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json` (AC-9).
- `uv run pytest tests/agent/workflow/test_workflow_loader.py -v` (procedure 09).

## Completion criteria

- AC-1: the shipped `default.json` carries `retry_on`. AC-3 is pinned by procedure 08/09 tests against this file.

## Out of Scope

- Any stage timeout or `retryable` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Added "retry_on": ["exception"] to the retry_policy block; no stage changes. Existing file indentation style preserved. |
| 2 | Add or update tests per Validation plan | Completed | — | — | No new tests in this procedure; shipped-file assertion lands in procedure 09. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Preflight 'python -m agent.workflow.validate config/workflows/default.json' OK with the new key; pytest test_workflow_loader.py 26 passed; parsed retry_policy == {max_attempts:3, backoff_sec:1, retry_on:[exception]}. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | Out of scope for this procedure; docs updated by procedure 12. Deployed /opt/llm config sync deferred to the deploy decision (Plan Phase 6 gate). |

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
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-011`
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-165312
- **Related target files**: `config/workflows/default.json`, `scripts/agent/workflow/workflow_loader.py`, `scripts/agent/workflow/models.py`, `tests/agent/workflow/test_workflow_loader.py`