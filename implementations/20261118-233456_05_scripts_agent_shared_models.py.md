## Goal

Delete the orphan `ApprovalDecisionEvent` dataclass together with the DT-04 Option A removal of the
orphan approval-event path (REQ-007, REQ-004).

## Scope
**Release unit**: approval-event-cleanup

## Assumptions
- `ApprovalDecisionEvent` (`scripts/agent/shared/models.py:30`) is constructed only by
  `log_approval_decision()` (Plan row 04), verified by consumer scan in the Plan `Problem` section.
- `ToolApprovalEvent` (`:13`) is the live event and must not be touched.

## Design decisions
- Full dataclass deletion (Option A) rather than keeping the type for a future gate (Options B/C rejected).

## Alternatives considered
N/A: DT-04 Option A already fixes the choice; keeping an unused event type contradicts REQ-007.

## Implementation
### Target file
`scripts/agent/shared/models.py`
### Procedure
Delete the `ApprovalDecisionEvent` dataclass (`:30`) and any import or export that exists only for it.
### Method
Pure deletion; no field or docstring changes on the remaining models.
### Details
- Land in the same commit as Plan row 04 (`tool_audit.py`); after deletion `rg "ApprovalDecisionEvent" scripts/`
  must be empty.

## Compatibility considerations
The generated API reference/manifest drop the type in rows 33/4 (rows 33/34) of the same commit.

## Security considerations
N/A: type removal on an unused event model.

## Rollback considerations
Revert the whole unit commit (see row 04 procedure).

## Validation plan
- `uv run pytest tests/agent/test_tool_audit.py -q`
- `uv run python tools/generate_reference_table.py --check` (same commit).

## Completion criteria
`ApprovalDecisionEvent` no longer exists; `ToolApprovalEvent` is unchanged; the audit suite passes.

## Out of Scope
`audit_approval()` itself (row 04), ADR wording (row 29).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the dataclass with the row 04 commit | Pending | — | — | DT-04 approved Option A 2026-11-18 |
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
- **Requirement ID**: `REQ-007` (orphan cluster removal), `REQ-004` (DT-04 decision)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `scripts/agent/shared/models.py`
