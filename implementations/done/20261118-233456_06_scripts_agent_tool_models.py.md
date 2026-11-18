## Goal

Delete the orphan `ApprovalOutcome` dataclass as part of the DT-04 Option A removal of the orphan
approval-event cluster (REQ-007, REQ-004).

## Scope
**Release unit**: approval-event-cleanup

## Assumptions
- `ApprovalOutcome` (`scripts/agent/tool_models.py:45`) is referenced only by
  `scripts/agent/tool_audit.py:20` (removed in row 04) and by the tests rows 17/18 adjust.

## Design decisions
N/A: DT-04 Option A fixes deletion; the dataclass and its import are removed together.

## Alternatives considered
N/A: see row 04.

## Implementation
### Target file
`scripts/agent/tool_models.py`
### Procedure
Delete the `ApprovalOutcome` dataclass (`:45`); verify nothing else in the module referenced it.
### Method
Pure deletion in the same commit as row 04.
### Details
- After deletion `rg "ApprovalOutcome" scripts/` must be empty; test references disappear via rows
  17/18.

## Compatibility considerations
Generated artifacts drop the type in rows 33/34 of the same commit.

## Security considerations
N/A: unused DTO removal.

## Rollback considerations
Revert the whole unit commit (see row 04 procedure).

## Validation plan
- `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_tool_approval_preflight.py -q`
- `uv run python tools/generate_reference_table.py --check` (same commit).

## Completion criteria
`ApprovalOutcome` no longer exists; the remaining `tool_models` exports are unchanged; suites pass.

## Out of Scope
The audit module itself (row 04), test-file removal (rows 17/18).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the dataclass with the row 04 commit | Completed | 20261119-072943 | 20261119-072943 | `ApprovalOutcome` :44-61 deleted; also removed the `ApprovalDecisionType`/`RiskLevel` imports left unused by the deletion |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-072943 | 20261119-072943 | mypy pass; audit/preflight/compat-shim suites 309 passed; rg ApprovalOutcome scripts/ empty; --check no drift |

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
- **Related target files**: `scripts/agent/tool_models.py`
