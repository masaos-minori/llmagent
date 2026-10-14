## Goal

Tool audit tests: Add the INV-11 regression test (the `tool_approval` event carries `workflow_id` and the turn-ID `task_id` for approved and denied decisions) (REQ-005: tests).

## Scope

- Add the INV-11 regression test (the `tool_approval` event carries `workflow_id` and the turn-ID `task_id` for approved and denied decisions)

## Assumptions

- Plan `plans/20261014-114443_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Apply only after the repository owner's decision (Plan Step 1) is recorded, together with every other procedure of this plan (Steps 2-11) as one commit unit.
- Line numbers come from the Plan and may shift; locate edits by symbol, test name, or section.

## Design decisions

- Edit by test name; compare `pytest --collect-only -q` counts before and after and confirm only the intended tests changed.
- New test text must not contain registered removed names (the allowlisted test files excepted); use unregistered terms such as require_approval, approvals, or pending_approval where needed.

## Alternatives considered

N/A: test-only change

## Implementation

### Target file

`tests/agent/test_tool_audit.py`

### Procedure

Add the INV-11 regression test (the `tool_approval` event carries `workflow_id` and the turn-ID `task_id` for approved and denied decisions).

### Method

Evidence recorded in the Plan: `tool_audit.py:33-49` `audit_approval` writes the `tool_approval` event with `task_id=ctx.turn.current_turn_id`; no INV-11 regression test exists yet. Locate the places with a case-sensitive search for the removed names in this file, edit by symbol or section, then format the file.

### Details

- Add a class TestAuditApprovalInv11 (new) that builds a context with a workflow_id and a current turn ID, calls audit_approval for an approved and a denied decision, and asserts the logged tool_approval event carries workflow_id and a task_id equal to the turn ID. This is the regression test for INV-11; the behavior itself is unchanged.

## Compatibility considerations

N/A: test-only change

## Security considerations

N/A: test-only change

## Rollback considerations

N/A: revert the commit; the whole plan lands as one commit unit.

## Validation plan

- `uv run pytest` on this file passes after the code procedures are applied.
- `uv run ruff format` and `uv run ruff check` on the file are clean.

## Completion criteria

- The file contains no removed gate name outside what the Procedure keeps.
- Remaining tests still pass and the collected-count change matches the Procedure.

## Out of scope

- Tool-level approval (the keep list), the MDQ and eventbus areas, and any file outside this Plan's target table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the edit | Completed | 20261014-142001 | 20261014-142001 |  |
| 2 | Run the affected tests | Completed | 20261014-142001 | 20261014-142001 |  |
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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261014-112913_appr001_remove-the-post-execution-approval-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-114443_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-123722
- **Related target files**: tests/agent/test_tool_audit.py