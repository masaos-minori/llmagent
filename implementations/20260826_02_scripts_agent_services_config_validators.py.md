# Implementation Procedure Output Template (Canonical)

## Goal
Remove dead validator `validate_tool_cache_max_size` once `ToolExecutor` cache is removed.

## Scope
- In-Scope: `scripts/agent/services/config_validators.py` — delete `validate_tool_cache_max_size` function.

## Assumptions
- Prerequisite: `ToolExecutor` TTL cache removal must be completed.

## Design decisions
- N/A

## Alternatives considered
- N/A

## Implementation
### Target file
`scripts/agent/services/config_validators.py`
### Procedure
1. **Verify prerequisite**: Confirm `ToolExecutor` cache removal is complete.
2. **Remove validator**: Delete the `validate_tool_cache_max_size` function.
3. **Verification**: Run `grep -rn "tool_cache_max_size\|_v_tool_cms" scripts/` to ensure it returns no matches in this file.
### Method
Code modification and verification.
### Details
- REQ-001: Delete `validate_tool_cache_max_size` in `scripts/agent/services/config_validators.py`.

## Compatibility considerations
- None.

## Security considerations
- None.

## Rollback considerations
- Revert changes to `scripts/agent/services/config_validators.py` via git.

## Validation plan
- Run `grep -rn "tool_cache_max_size\|_v_tool_cms" scripts/` to verify zero matches.

## Completion criteria
- `validate_tool_cache_max_size` is removed from `scripts/agent/services/config_validators.py`.
- No reference to `tool_cache_max_size` remains in this file.

## Out of scope
- Other validators consolidation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | — |
| 2 | Add or update tests per Validation plan | Pending | — | — | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | — |

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
- **Requirement ID**: REQ-001
- **Source issue**: `issues/20260825_config_validators_dead_cache_validator_issue.md`
- **Source requirement**: N/A
- **Source plan**: `plans/20260825-142646_plan.md`
- **Source implementation procedure**: N/A
- **Generated at**: 2026-08-26T12:00:05Z
- **Related target files**: `scripts/agent/services/config_validators.py`
