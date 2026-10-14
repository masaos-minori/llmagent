## Goal

Workflow Engine: Remove `_gate_approval`, the approval imports, the `workflow.approval` span, the `WorkflowPendingApprovalError` clause in `run()`, and the stale docstring (REQ-002: remove the gate code).

## Scope

- Remove `_gate_approval`, the approval imports, the `workflow.approval` span, the `WorkflowPendingApprovalError` clause in `run()`, and the stale docstring; keep `WorkflowHaltError`, `WorkflowTimeoutError`, and retry handling

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

`scripts/agent/workflow/workflow_engine.py`

### Procedure

Remove `_gate_approval`, the approval imports, the `workflow.approval` span, the `WorkflowPendingApprovalError` clause in `run()`, and the stale docstring; keep `WorkflowHaltError`, `WorkflowTimeoutError`, and retry handling.

### Method

Evidence recorded in the Plan: `workflow_engine.py` lines 19, 20, 21, 22, 89, 103 (plus 27 more). Locate the places with a case-sensitive search for the removed names in this file, edit by symbol or section, then format the file.

### Details

- Remove the gate call in run() (about line 147), the _gate_approval method with its approval span and rejection branch (about line 216), the imports of the approval operations (lines 19-23), the approval TTL constant and expiry use (about line 184), the clause that re-raises WorkflowPendingApprovalError, and the docstrings that describe the gate (lines 4, 8, 102-108, 137).
- Keep _span_ctx (the retry, stage, and run spans use it), the WorkflowHaltError raise for retry exhaustion (about line 262), and WorkflowTimeoutError handling.

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261014-112913_appr001_remove-the-post-execution-approval-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-114443_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-123722
- **Related target files**: scripts/agent/workflow/workflow_engine.py