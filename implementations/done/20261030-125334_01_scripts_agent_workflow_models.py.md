## Goal

Define the typed status vocabulary and the explicit transition matrix in `scripts/agent/workflow/models.py` (`REQ-001`, one vocabulary for Python and SQL), and give `AttemptRecord` the persisted attempt number the other rows need (`REQ-003`, persisted numbering).

## Scope

- Modify only `scripts/agent/workflow/models.py`.
- No SQL here; the `CHECK` constraints live in the schema row and a test proves they equal these enums.

## Assumptions

- Plan Dependencies (`plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Scope): the whole Plan is ordered behind `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md` Phase 2 and its schema phase behind `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` Phase 3. This row has no schema dependency and belongs to Plan Phase 1, so it runs first.
- Execution order: follow the Plan's `Implementation steps` phases, not the table `seq` order (the schema row 10 is Phase 2 and must land before the Phase 3 and 4 rows 04-09 although it has a later `seq`).
- Plan overlap judgments (Step 8b): `models.py` is also a target of `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md` (renames `TaskRecord.idempotency_key` to `task_nonce` (new)) and `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` (`RetryPolicy` field): sequencing dependency, different dataclasses; the later change rebases.
- Python is 3.13 (`AGENTS.md` Environment), so `enum.StrEnum` is available.

## Design decisions

- `TaskStatus` (new) and `AttemptStatus` (new) are `StrEnum` classes so members compare equal to the existing plain-string values and the persisted text needs no conversion.
- The transition matrix is one module-level read-only mapping (`TaskStatus` (new) to the set of allowed next statuses) plus a terminal set for attempts; the matrix is exactly `pending -> running | halted`, `running -> completed | failed | halted`, `failed -> running`, `completed -> failed` (transitional, removed by the retry Plan), nothing else.

## Alternatives considered

- Plain string constants: rejected, no type check and no single enumeration for the `CHECK` equality test.
- A matrix per consumer: rejected, a second source of truth.

## Implementation

### Target file

`scripts/agent/workflow/models.py`

### Procedure

1. Add `TaskStatus` (new) with members `PENDING` (new), `RUNNING` (new), `COMPLETED` (new), `FAILED` (new), `HALTED` (new) and `AttemptStatus` (new) with `RUNNING` (new), `COMPLETED` (new), `FAILED` (new), valued with the existing lowercase strings.
2. Add the transition mapping `TASK_TRANSITIONS` (new) and `ATTEMPT_TERMINAL_STATUSES` (new) (completed, failed), and a small pure function `is_task_transition_allowed` (new) taking the current and next status.
3. Replace the free-text status comments on `TaskRecord.status` (`:20`) and `AttemptRecord.status` (`:34`) with the enum types in annotations only if all construction sites stay valid; otherwise keep `str` and reference the enums in the comment.
4. Add `attempt_number: int = 0` to `AttemptRecord` (after the existing required fields, before optional ones that already have defaults).

### Method

- Keep the mapping immutable (`Mapping` over `frozenset`), module level, no behavior beyond lookup.
- Existing keyword construction of `AttemptRecord` stays valid because the new field has a default.

### Details

- Do not add I/O or imports of other workflow modules; `errors.py` and `task_ops.py` import from here, not the reverse.
- Export the enums from `scripts/agent/workflow/__init__.py` only if a later row needs the package-level name; otherwise leave the package exports unchanged (that file is not a target of this Plan).

## Compatibility considerations

- `StrEnum` members equal their string values, so rows still stored or compared as plain strings keep working.
- `AttemptRecord` gains a defaulted field, so existing construction sites and tests are unaffected.

## Security considerations

- N/A: pure data definitions.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_models.py -v` (enum values, matrix, terminal set)
- `uv run ruff format scripts/agent/workflow/models.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria

- Both enums and the matrix exist; the matrix lists exactly the edges in `REQ-001`.
- `AttemptRecord` has `attempt_number`.
- No other module is changed by this document.

## Out of Scope

- SQL `CHECK` constraints and migration (schema row), transition functions (`task_ops.py` row), errors (`errors.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add enums, transition mapping, terminal set, and `attempt_number` | Completed | 20261030-144808 | 20261030-144808 | Plan Phase 1 Enums, matrix, attempt_number added |
| 2 | Add or update tests per Validation plan | Completed | 20261030-144808 | 20261030-144808 | tests/agent/workflow/test_workflow_models.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-144808 | 20261030-144808 | validators passed; full suite passed |

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
- **Requirement ID**: REQ-001 (typed vocabulary and transition matrix), REQ-003 (persisted attempt number on the record)
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125334
- **Related target files**: scripts/agent/workflow/models.py