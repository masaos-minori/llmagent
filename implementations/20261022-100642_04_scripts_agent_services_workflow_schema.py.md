## Goal
Reword the version-mismatch hint of `check_workflow_schema()` so it no longer tells the operator to "migrate", leaving the check's logic unchanged (REQ-006: startup check keeps its behavior).

## Scope
- Change the hint text in the version-mismatch result only.

## Assumptions
- No test pins the hint text: tests only assert the substring "schema version mismatch" in the error (verified in `tests/agent/test_repl_health.py`).
- The mismatch error still names both versions.

## Design decisions
- New hint: recreate the workflow database (archive the file, then run `deploy/init_db.sh`), consistent with the documented recreate procedure.

## Alternatives considered
N/A: one-string change.

## Implementation
### Target file
`scripts/agent/services/workflow_schema.py`

### Procedure
1. In the `SchemaCheckResult` returned on a version mismatch, replace the trailing sentence "Run create_workflow_schema() to migrate." with the recreate hint.

### Method
- Keep the f-string prefix `Workflow schema version mismatch: expected ...` byte-identical.

### Details
- Do not change `REQUIRED_WORKFLOW_TABLES`, the other messages, or the comparison logic.

## Compatibility considerations
Callers and tests rely on the `valid=False` result and the "schema version mismatch" substring, both preserved.

## Security considerations
N/A: text change only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_startup_workflow_preflight.py tests/agent/test_repl_health.py -q`.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria
- The hint no longer says "migrate" and the mismatch tests pass.

## Out of Scope
- Check logic, required columns, and other messages.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the mismatch hint | Pending | — | — | |
| 2 | Run the startup and health tests | Pending | — | — | |
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
- **Requirement ID**: `REQ-006` (startup check unchanged except the hint text)
- **Source issue**: `issues/20261021-102049_rmwfmig_remove-the-workflow.sqlite-incremental-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093726_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100642
- **Related target files**: scripts/agent/services/workflow_schema.py
