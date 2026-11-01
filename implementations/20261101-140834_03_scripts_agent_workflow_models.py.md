## Goal

Rename the `idempotency_key` field of `TaskRecord` to `task_nonce` (new) in `scripts/agent/workflow/models.py` (Plan REQ-003 rename to a name that states the real guarantee).

## Scope

- `TaskRecord.idempotency_key: str` (currently `models.py:21`) becomes `TaskRecord.task_nonce: str`; docstring/comment updated to the nonce contract.

## Assumptions

- `TaskRecord` is a plain dataclass in current HEAD (verified 2026-11-01: `models.py` is 81 lines, `TaskRecord` at `:13`); consumers construct by keyword, so the rename propagates through rows 01 (mapping) and 05/07/08 (tests).
- The 2026-10-30 Plan text referenced `models.py:21` — still exact; the Plan's earlier assumption of a TaskRequest model predates the `aa0b318c7` refactor and is not present in current HEAD (no TaskRequest to rename).

## Design decisions

- Field rename only; the value contract is unchanged (UUID4, unique, never caller-derived). No TaskStatus enum or transition validation here — that is the separate recovery Plan (`wfrecovery001`), out of this Plan's scope.

## Alternatives considered

- Keeping the field and renaming only the DDL column: rejected — the model name is what callers see; Plan REQ-003 changes model, DDL, and tests as one unit.

## Implementation
### Target file
`scripts/agent/workflow/models.py`

### Procedure
1. Rename the dataclass field at `:21` to `task_nonce` (new) and update the class's comment describing the key.

### Method
Single-field rename; rely on type-checker errors to surface every construction site (rows 01, 05, 07, 08).

### Details
- `AttemptRecord`, `ArtifactRef`, `StageDefinition`, `RetryPolicy`, `WorkflowDef` are untouched.
- `agent/workflow/__init__.py` re-exports `TaskRecord`; the export name does not change.

## Compatibility considerations

- Pairs with the DDL rename (row 04) and the migration (row 12); any positional construction of `TaskRecord` breaks — the repository constructs it by keyword only (`task_ops.py:59,84`).

## Security considerations

- N/A: name change only; uniqueness constraint semantics unchanged.

## Rollback considerations

- N/A: revert the commit together with rows 01/04/12 (one release unit).

## Validation plan

- `uv run mypy --no-namespace-packages scripts/ tests/eventbus` surfaces unfixed construction sites; `uv run pytest tests/agent/workflow/ -v`.
- `rg idempotency_key scripts/agent/workflow` shows only the `tool_call_state` transport key (out of scope) — no task-key reference (AC-3).

## Completion criteria

- `TaskRecord` exposes `task_nonce` (new) and no member named `idempotency_key` (AC-3); all keyword constructions across rows 01/05/07/08 compile and pass tests.

## Out of Scope

- `tool_call_state` models in `tool_call_state_ops.py` (their `idempotency_key` is the toolexec001 transport dedup key).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Verification Notes (2026-11-01)
- Passed. `TaskRecord.idempotency_key` at `models.py:21` (file 81 lines);
  test literals at `test_workflow_state_store.py:76-85,121-125` and
  `test_workflow_models.py:25`.
- Clarification: `workflow_engine.py:148,157` reference `idempotency_key`
  only for `ToolCallState`, which this rename does not touch. The engine's
  `create_task(..., idempotency_key=...)` keyword calls (`:96,127,144,298`)
  are renamed in the same cycle-2 commit as this row.
- Cycle: cycle 2 (rename unit with rows 01 rename part, 04, 12).

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` (rename the task key in the model)
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-140834
- **Related target files**: scripts/agent/workflow/models.py
