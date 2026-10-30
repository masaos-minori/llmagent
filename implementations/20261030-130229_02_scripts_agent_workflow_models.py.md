## Goal

Add an optional `retry_on` list of error kinds to `RetryPolicy` in `scripts/agent/workflow/models.py` (`REQ-001`, per-kind retry eligibility in workflow policy).

## Scope

- Modify only `scripts/agent/workflow/models.py` (`RetryPolicy` and its kind vocabulary).

## Assumptions

- Plan Dependencies (`plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` Scope): Plan Phase 1; independent of the wfrecovery001 Plan and the schema. Execution order follows the Plan's phases, not `seq`.
- Plan overlap judgments (Step 8b): `models.py` is also a target of `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md` (task key rename) and `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` (status enums): sequencing dependency, different dataclasses.
- Owner decision (2026-10-30): defaults keep today's behavior, so `retry_on` defaults to exception only.
- `RetryPolicy` is a plain dataclass built by the loader and defaulted inside `WorkflowDef` (`RetryPolicy(max_attempts=3, backoff_sec=1)`); adding a defaulted field keeps both valid.

## Design decisions

- Add `retry_on: tuple[str, ...] = ("exception",)` as the last field, and a module-level constant `RETRY_ON_KINDS` (new) with the allowed values `exception`, `timeout`, llm_failure, so the loader and the engine share one vocabulary.

## Alternatives considered

- A boolean retry_timeouts: rejected, it cannot cover llm_failure or later kinds (Plan Design).

## Implementation

### Target file

`scripts/agent/workflow/models.py`

### Procedure

1. Add `RETRY_ON_KINDS` (new) above `RetryPolicy` (`:61`).
2. Add the `retry_on` field with the tuple default to `RetryPolicy`.

### Method

- Use a tuple (immutable) so the dataclass default is safe without `default_factory`.

### Details

- Do not change `StageDefinition` or `WorkflowDef`; `WorkflowDef`'s default policy constructs `RetryPolicy` positionally by keyword and stays valid.

## Compatibility considerations

- Additive, defaulted field; older callers and tests that build `RetryPolicy(max_attempts=..., backoff_sec=...)` are unaffected.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_loader.py tests/agent/workflow/test_workflow_models.py -v`
- `uv run ruff format scripts/agent/workflow/models.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`

## Completion criteria

- `RetryPolicy().retry_on`-style construction without the argument yields `("exception",)`; `RETRY_ON_KINDS` (new) lists the three kinds.

## Out of Scope

- Loader parsing and validation (row 03), engine use (row 01), the shipped configuration (row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `RETRY_ON_KINDS` (new) and the `retry_on` field | Pending | — | — | Plan Phase 1 |
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
- **Requirement ID**: REQ-001 (retry eligibility in policy)
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130229
- **Related target files**: scripts/agent/workflow/models.py
