# Implementation Procedure Output Template (Canonical)

**SUPERSEDED (2026-08-27)**: source plan `plans/20260825-142646_plan.md` marked
Superseded; replaced by
`implementations/20260827-134500_01_scripts_agent_config_dataclasses.py.md`
(generated from `plans/20260827-121312_plan.md`'s `REQ-001`). Do not execute.

## Goal
Remove `_v_tool_cms` import/call and `tool_cache_ttl`/`tool_cache_max_size` fields from `ToolConfig` once `ToolExecutor` cache is removed.

## Scope
- In-Scope: `scripts/agent/config_dataclasses.py` — remove `_v_tool_cms` import and `__post_init__` call, and delete `tool_cache_ttl`/`tool_cache_max_size` fields from `ToolConfig`.

## Assumptions
- Prerequisite: `ToolExecutor` TTL cache removal must be completed.

## Design decisions
- N/A

## Alternatives considered
- N/A

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`
### Procedure
1. **Verify prerequisite**: Confirm `ToolExecutor` cache removal is complete.
2. **Modify imports**: Remove `validate_tool_cache_max_size as _v_tool_cms` from imports.
3. **Modify `ToolConfig.__post_init__`**: Remove the `_v_tool_cms(self)` call.
4. **Modify `ToolConfig` definition**: Remove `tool_cache_ttl` and `tool_cache_max_size` field definitions.
5. **Verification**: Run `python -c "from agent.config_dataclasses import ToolConfig; ToolConfig()"` and verify zero matches for `tool_cache_max_size` or `_v_tool_cms` using `grep`.
### Method
Code modification and verification.
### Details
- REQ-002: Modify `scripts/agent/config_dataclasses.py` to remove `_v_tool_cms` usage.
- REQ-003: Modify `scripts/agent/config_dataclasses.py` to remove `tool_cache_ttl` and `tool_cache_max_size` fields.

## Compatibility considerations
- None.

## Security considerations
- None.

## Rollback considerations
- Revert changes to `scripts/agent/config_dataclasses.py` via git.

## Validation plan
- Run `grep -rn "tool_cache_max_size\|_v_tool_cms" scripts/` to ensure zero matches.
- Run `python -c "from agent.config_dataclasses import ToolConfig; ToolConfig()"` to confirm successful instantiation.

## Completion criteria
- `_v_tool_cms` is removed from `scripts/agent/config_dataclasses.py`.
- `tool_cache_ttl` and `tool_cache_max_size` are removed from `ToolConfig`.
- `ToolConfig()` instantiates without error.

## Out of scope
- Other dataclass changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Superseded | — | — | See replacement doc listed at top of file |
| 2 | Add or update tests per Validation plan | Superseded | — | — | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Superseded | — | — | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Superseded | — | — | — |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: `issues/20260825_config_validators_dead_cache_validator_issue.md`
- **Source requirement**: N/A
- **Source plan**: `plans/20260825-142646_plan.md`
- **Source implementation procedure**: N/A
- **Generated at**: 2026-08-26T12:00:05Z
- **Related target files**: `scripts/agent/config_dataclasses.py`
