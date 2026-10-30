## Goal

Make the shipped retry behavior readable from `config/workflows/default.json` by adding an explicit `retry_on` to `retry_policy` (`REQ-001`, retry policy in configuration; `REQ-003`, shipped behavior pinned; `REQ-011`, deployment compatibility).

## Scope

- Modify only `config/workflows/default.json`.

## Assumptions

- Plan Dependencies (`plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` Scope): Plan Phase 1; needs row 03 (the loader accepts the key) before the file is deployed. Already-deployed loaders ignore unknown keys, so the file may ship before or with the code. Execution order follows the Plan's phases, not `seq`.
- Owner decisions (2026-10-30): timeouts and LLM-level failure results are not retried; `execute` stays `retryable: true`, `timeout_sec: 120`; `max_attempts: 3`, `backoff_sec: 1` are unchanged.
- The pre-flight `deploy/setup_services.sh` validates the deployed copy (`/opt/llm/config/workflows/default.json`) with `python -m agent.workflow.validate`; deploying is the user's decision.

## Design decisions

- Add `"retry_on": ["exception"]` inside `retry_policy`, with no other key changed.

## Alternatives considered

- N/A: lightweight row; the policy default and the shipped value are fixed by the Plan.

## Implementation

### Target file

`config/workflows/default.json`

### Procedure

1. Add the `retry_on` key with the value `["exception"]` to the `retry_policy` object, keeping the file's existing indentation.

### Method

- One key addition; keep the JSON valid and the key order `max_attempts`, `backoff_sec`, `retry_on`.

### Details

- Do not edit the stage definitions.

## Compatibility considerations

- Backward compatible: older loaders ignore the key; the new loader treats it as the explicit form of its default.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit; the key is ignored by older loaders.

## Validation plan

- `PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json`
- `uv run pytest tests/agent/workflow/test_workflow_loader.py -v`

## Completion criteria

- The shipped file carries `retry_on: ["exception"]` and validates.

## Out of Scope

- The loader, the model, and the deployed copy under `/opt/llm/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `retry_on` to `retry_policy` | Pending | — | — | Plan Phase 1 |
| 2 | Run the validation commands | Pending | — | — | Deploy is the user's decision (Plan Phase 6) |

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
- **Requirement ID**: REQ-001 (retry policy in configuration), REQ-003 (shipped behavior), REQ-011 (deployment compatibility)
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130229
- **Related target files**: config/workflows/default.json
