# Implementation Procedure Output Template (Canonical)

**SUPERSEDED (2026-08-27)**: this document's source plan
(`plans/20260826-120000_plan.md`) implemented `ToolExecutor`'s cache removal but
left this file's fields untouched (confirmed by repository re-verification);
replaced by
`implementations/20260827-134500_01_scripts_agent_config_dataclasses.py.md`
(generated from `plans/20260827-121312_plan.md`'s `REQ-001`). Do not execute.

## Goal
Remove \`tool_cache_ttl\` and \`tool_cache_max_size\` from \`ToolConfig\` in \`scripts/agent/config_dataclasses.py\`.

## Scope
- In-Scope: \`scripts/agent/config_dataclasses.py\` — delete \`tool_cache_ttl\` and \`tool_cache_max_size\` fields from \`ToolConfig\`.

## Assumptions
- Prerequisite: \`ToolExecutor\` TTL cache removal must be completed.

## Design decisions
- N/A

## Alternatives considered
- N/A

## Implementation
### Target file
\`scripts/agent/config_dataclasses.py\`
### Procedure
1. **Verify prerequisite**: Confirm \`ToolExecutor\` cache removal is complete.
2. **Modify \`ToolConfig\` definition**: Delete the following field definitions within the \`ToolConfig\` dataclass:
   - \`tool_cache_ttl: float = 300.0\`
   - \`tool_cache_max_size: int = 200\`
3. **Verification**: Run \`python -c "from agent.config_dataclasses import ToolConfig; ToolConfig()"\` to confirm successful instantiation without these fields.
### Method
Code modification and verification.
### Details
- REQ-002: Remove \`tool_cache_ttl\` and \`tool_cache_max_size\` from \`ToolConfig\`.

## Compatibility considerations
- None.

## Security considerations
- None.

## Rollback considerations
- Revert changes to \`scripts/agent/config_dataclasses.py\` via git.

## Validation plan
- Run \`python -c "from agent.config_dataclasses import ToolConfig; ToolConfig()"\`
- Verify zero matches for \`tool_cache_\` in \`scripts/agent/config_dataclasses.py\` using \`grep\`.

## Completion criteria
- \`ToolConfig\` no longer contains \`tool_cache_ttl\` or \`tool_cache_max_size\`.
- \`ToolConfig()\` instantiates without error.

## Out of scope
- Other dataclass modifications.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Superseded | — | — | See replacement doc listed at top of file |
| 2 | Add or update tests per Validation plan | Superseded | — | — | — |
| 3 | Run the validation sequence (\`rules/toolchain.md\`) | Superseded | — | — | — |
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260826_delete_tool_executor_cache_issue.md
- **Source requirement**: N/A
- **Source plan**: `plans/20260826-120000_plan.md`
- **Source implementation procedure**: N/A
- **Generated at**: 2026-08-26T12:05:00Z
- **Related target files**: `scripts/agent/config_dataclasses.py`
