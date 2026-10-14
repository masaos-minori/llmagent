## Goal

Startup workflow-schema check: Remove `approvals` from `REQUIRED_WORKFLOW_TABLES` (REQ-004: database and deploy changes).

## Scope

- Remove `approvals` from `REQUIRED_WORKFLOW_TABLES`

## Assumptions

- Plan `plans/20261014-114443_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Apply only after the repository owner's decision (Plan Step 1) is recorded, together with every other procedure of this plan (Steps 2-11) as one commit unit.
- Line numbers come from the Plan and may shift; locate edits by symbol, test name, or section.

## Design decisions

- Remove only the gate code named in the Procedure; keep neighboring tool-level logic untouched.
- Do not remove or rename anything on the keep list: `ApprovalDecisionType`, `ApprovalDecisionEvent`, `audit_approval`, `log_approval_decision`, `require_approval_for`, `WorkflowHaltError`, `WorkflowTimeoutError`, and the halted status.

## Alternatives considered

N/A: removal is the decided direction (Plan Design)

## Implementation

### Target file

`scripts/agent/services/workflow_schema.py`

### Procedure

Remove `approvals` from `REQUIRED_WORKFLOW_TABLES`.

### Method

Evidence recorded in the Plan: `workflow_schema.py` lines 51. Locate the places with a case-sensitive search for the removed names in this file, edit by symbol or section, then format the file.

### Details

- Remove the approvals entry from REQUIRED_WORKFLOW_TABLES (line 51); the startup check then accepts both migrated and new databases.

## Compatibility considerations

The post-execution approval stage no longer exists; there is no alias or compatibility path.

## Security considerations

N/A: removal only; tool-level approval and the audit trail are untouched.

## Rollback considerations

N/A: revert the commit; the whole plan lands as one commit unit.

## Validation plan

- `uv run ruff format` and `uv run ruff check` on the file are clean.
- `uv run mypy --no-namespace-packages scripts/` shows no new error.
- The related tests listed in the Plan row pass after all procedures are applied.

## Completion criteria

- The gate code named in the Procedure is gone and the module imports cleanly.
- No item on the keep list changed.

## Out of scope

- Tool-level approval (the keep list), the MDQ and eventbus areas, and any file outside this Plan's target table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the edit | Completed | 20261014-142001 | 20261014-142001 |  |
| 2 | Run the tests that cover this file (updated by the test procedures) | Completed | 20261014-142001 | 20261014-142001 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261014-142001 | 20261014-142001 |  |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261014-112913_appr001_remove-the-post-execution-approval-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-114443_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-123722
- **Related target files**: scripts/agent/services/workflow_schema.py