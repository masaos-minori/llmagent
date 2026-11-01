## Goal

Parse and validate `retry_policy.retry_on` in `scripts/agent/workflow/workflow_loader.py` inside a separate helper, rejecting unknown kinds with `WorkflowLoadError` and defaulting an absent key (REQ-001, REQ-011 / AC-1, AC-9).

## Scope

- Add `_validate_retry_on(policy: dict) -> tuple[str, ...]` (module level, next to `_validate` at `workflow_loader.py:56`): absent key returns the default `("exception",)`; present key must be a list of strings drawn from `{"exception", "timeout", "llm_failure"}`, otherwise `WorkflowLoadError` naming the offending kind.
- Call it from `_validate` (`:56-96`, after the `max_attempts`/`backoff_sec` checks at `:86-91`) and pass the result into the `RetryPolicy(...)` construction (`:128-131`).
- `_REQUIRED_POLICY_KEYS` (`:48`) stays `{max_attempts, backoff_sec}` — `retry_on` is optional by REQ-001 and must NOT be added to it.

## Assumptions

- Plan `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` is Frozen; its 12-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table (re-verified 2026-11-01: all 12 paths exist on `master`, no row replaced).
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record'); drifted citations carry `(re-verified 2026-11-01)` markers.
- Canonical semantics come from the Plan REQs (Plan `:38-48`): `retry_policy.retry_on` list drawn from `exception`/`timeout`/`llm_failure` with default `["exception"]` (REQ-001); deadline-versus-inner timeout classification via the deadline's `expired()` state (REQ-002); every failed attempt consumes one budget unit and ineligible kinds are terminal at once (REQ-003); typed outward kinds `workflow_halted` / `workflow_timeout` on the `(answer, error_kind, is_partial)` tuple (REQ-004); LLM-level failure results enter the engine as stage failures of kind `llm_failure` (REQ-005); per-attempt side-effect flag on `TurnState` set by `tool_runner` (REQ-006); attempt kinds `timeout`/`exception`/`llm_failure` distinct from outward kinds (REQ-007); no turn ends with empty answer, `error_kind` `None`, and a `halted`/`failed` task (REQ-008).
- Owner decisions (Plan UNK-01, UNK-02, 2026-10-30): timeouts and LLM-failure results are not retried by default; the shipped `retry_on` pins this, and the landed engine already treats timeouts as terminal (`workflow_engine.py:208-209`, re-verified 2026-11-01).
- Landing order (Plan Assumptions 'Re-verification record'; updated by the 2026-11-02 execution verification): wftaskapi001 `20261101-140834` and wflease001 `20261101-163219` have landed on `master` (wflease001 registered migration code 4 / "1.4.0"); the wfrecovery001 `20261101-145309` procedures remain Pending and this batch lands ahead of them by owner decision, so those Pending procedure docs must be re-verified against the landed source before their own execution. Shared-file edits (`workflow_engine.py`, `models.py`, `workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `docs/23_agent/agent_03_03_...md`) rebase predictably. The wfrecovery001 Phase 4 attempt/budget contract itself is already landed on `master` (per-attempt event ids `{task_id}:{stage_id}:{attempt}`, `begin_stage_if_new` at `workflow_engine.py:264`, `finish_attempt` kinds at `:280-298`), so the Phase 2 gate is open.
- Side-effect rule (Plan Assumptions, UNK-06): every non-READ operation, including `classify_operation_type` results of `UNKNOWN`, counts as a side effect (conservative) until the owner decides a relaxation on top of the landed toolexec001 replay protocol.
- This Plan touches no schema, migration, or migration-registry file: the workflow migration ledger (`scripts/db/migrations_workflow.py`, landed HEAD code 4 / "1.4.0") is not a target row and needs no change here.
- Complexity guard (Plan Risks): `_validate` is radon grade C (18) at the recorded baseline (2026-10-30); keeping the new validation in a separate helper keeps `_validate` at or below C (18). The Validation plan re-runs `uv run radon cc scripts/agent/workflow/workflow_loader.py -s -n C`.
- Older deployed loaders ignore unknown policy keys (Plan Assumptions verification record: `_validate` ignores unknown keys), so the config may ship before or with the code (Plan Design 'Compatibility').

## Design decisions

- Validation lives in a dedicated helper rather than inline (Plan REQ-001 explicit wording: 'validation in a separate helper').
- The allowed-kind set is a module-level frozenset `_RETRY_KINDS` so the engine doc (procedure 01) and tests share one vocabulary; the helper returns a tuple (procedure 02 field type).

## Alternatives considered

- Reject the key entirely on unknown kinds only at engine start — rejected: AC-1 requires a `WorkflowLoadError` at load time, and the deploy pre-flight (`python -m agent.workflow.validate`) is the earliest gate.

## Implementation
### Target file
`scripts/agent/workflow/workflow_loader.py`

### Procedure
1. Add `_RETRY_KINDS` and `_validate_retry_on`.
2. Wire the call in `_validate` and thread the parsed tuple into `RetryPolicy(...)` at `:128-131`.
3. Confirm `validate.py` (`scripts/agent/workflow/validate.py`) needs no change: it calls the loader, which now validates (Plan Reference Files).

### Method
One helper function plus two call-site edits.

### Details
- Error message shape: `retry_policy.retry_on contains unknown kind 'X' (allowed: exception, timeout, llm_failure)` — matches the existing message style (`:87-91`, `:92-96`).
- `require_approval` rejection (`:92-96`) stays as is.

## Compatibility considerations

- Deploy pre-flight: `deploy/setup_services.sh` runs `python -m agent.workflow.validate` before start (Plan Reference Files); an invalid shipped `retry_on` therefore blocks startup, which is the intended gate (AC-9).

## Security considerations

- No new SQL surface: attempt persistence stays on the existing parameter-bound `finish_attempt` path; the new `error_kind` values are engine-produced literals, never caller- or user-supplied strings.

## Rollback considerations

- Remove the helper and the call; the config key from procedure 04 is ignored by the reverted loader (forward-compatible), so config and code can be reverted independently.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_loader.py -v` (procedure 09).
- `PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json` (AC-9).
- `uv run radon cc scripts/agent/workflow/workflow_loader.py -s -n C` — grade not above the recorded C (18).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports` (baseline 6 kept, 0 broken), `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-1: a definition without `retry_on` loads with the default; an unknown kind raises `WorkflowLoadError`.
- AC-9: the pre-flight passes on the shipped file and on an older-format file without the key.

## Out of Scope

- Engine consumption of the parsed value (procedure 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Added _RETRY_KINDS + _validate_retry_on helper; wired into _validate after backoff check; threaded retry_on into RetryPolicy(...). _RetryPolicyJson made total=False (runtime required-key check stays in _validate) to keep TypedDict .get widening assignable; validate.py needs no change (calls the loader). |
| 2 | Add or update tests per Validation plan | Completed | — | — | No new tests in this procedure per its Validation plan (loader tests land in procedure 09); existing 26 loader tests pass; AC-1 helper behavior smoke-checked inline (default tuple, unknown-kind and non-list WorkflowLoadError messages). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff format/check, mypy (loader+models clean), lint-imports 6 kept, radon cc _validate C(18) unchanged, bandit, check-module-size, preflight 'python -m agent.workflow.validate config/workflows/default.json' OK, pytest test_workflow_loader.py 26 passed. |
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
- **Workflow phase**: Phase 1 (Policy schema and loader)
- **Requirement ID**: `REQ-001`, `REQ-011`
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-165312
- **Related target files**: `scripts/agent/workflow/workflow_loader.py`, `scripts/agent/workflow/models.py`, `config/workflows/default.json`, `tests/agent/workflow/test_workflow_loader.py`