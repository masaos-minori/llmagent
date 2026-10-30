## Goal

Parse and validate the optional `retry_policy.retry_on` list in `scripts/agent/workflow/workflow_loader.py`, rejecting unknown kinds with a clear error and defaulting an absent key (`REQ-001`, retry policy in configuration; `REQ-011`, deployment compatibility).

## Scope

- Modify only `scripts/agent/workflow/workflow_loader.py`.

## Assumptions

- Plan Dependencies (`plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` Scope): Plan Phase 1; needs row 02 (`RETRY_ON_KINDS`, `RetryPolicy.retry_on`); independent of the wfrecovery001 Plan. Execution order follows the Plan's phases, not `seq`.
- Verified in Step 3 of the Plan: `_validate` (`:56-96`) checks required keys only and ignores unknown keys (it rejects only `require_approval`), so older deployed loaders accept a config that carries `retry_on`; `_validate` is radon grade C (18), so the new validation goes into a separate helper.
- `WorkflowLoader.load` builds `RetryPolicy` from `retry_policy` at `:128-131` region with `int(...)` coercions for the existing keys; the existing pattern is kept for those keys.
- `deploy/setup_services.sh` validates the deployed definition with `python -m agent.workflow.validate`, which uses this loader.
- Names created by earlier rows of this Plan, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `RETRY_ON_KINDS` and `retry_on` (row 02 document).

## Design decisions

- Add `_validate_retry_on` (new) as a separate function: absent key means the default, a non-list or a list containing a value outside `RETRY_ON_KINDS` raises `WorkflowLoadError` naming the offending value.
- Call it from `_validate` once, adding one call and no new branches to that function.

## Alternatives considered

- Inline checks in `_validate`: rejected, it would raise the grade-C complexity of 18 further.

## Implementation

### Target file

`scripts/agent/workflow/workflow_loader.py`

### Procedure

1. Add `_validate_retry_on` (new) beside `_validate` (`:56`).
2. Call it from `_validate` after the existing `retry_policy` key checks (`:86-91` region).
3. In `WorkflowLoader.load`, build `RetryPolicy` with `retry_on` set from the parsed list (as a tuple) when present, else leave the model default.

### Method

- Reject duplicates silently by keeping the tuple as given after validation; do not reorder.
- The error message lists the allowed kinds.

### Details

- Do not change `_REQUIRED_STAGE_KEYS` or `_REQUIRED_POLICY_KEYS`: the key stays optional (older configs load).
- Run `uv run radon cc scripts/agent/workflow/workflow_loader.py -s -n C` after the change; `_validate` must not exceed grade C (18).

## Compatibility considerations

- A config without `retry_on` loads as before; a config with it loads on older loaders (unknown keys ignored); a config with an unknown kind now fails with `WorkflowLoadError`.

## Security considerations

- N/A: configuration validation only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_loader.py -v`
- `PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json`
- `uv run ruff format scripts/agent/workflow/workflow_loader.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run radon cc scripts/agent/workflow/workflow_loader.py -s -n C`

## Completion criteria

- A definition without `retry_on` loads with the default; a valid list loads as a tuple; an unknown kind or a non-list raises `WorkflowLoadError`.
- `_validate` complexity is not above grade C (18).

## Out of Scope

- The model field (row 02), the shipped file (row 04), engine behavior (row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_validate_retry_on` (new), call it, and build `RetryPolicy` with `retry_on` | Pending | — | — | Plan Phase 1 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Row 09 document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (validated retry policy), REQ-011 (deployment compatibility)
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130229
- **Related target files**: scripts/agent/workflow/workflow_loader.py
