# Implementation Procedure Output Template (Canonical)

## Goal
Update \`ConfigReloadService\` to stop attempting to apply \`cache_ttl\` during configuration reloads.

## Scope
- In-Scope: \`scripts/agent/services/config_reload.py\` — remove the code block that applies \`cache_ttl\` via \`tools.apply_config(...)`.

## Assumptions
- Prerequisite: `ToolExecutor.apply_config` has been updated to no longer accept \`cache_ttl\`.

## Design decisions
- N/A

## Alternatives considered
- N/A

## Implementation
### Target file
\`scripts/agent/services/config_reload.py\`
### Procedure
1. **Modify \`_sync_services()\`**: Locate the block where \`ctx.services_required.tools.apply_config(cache_ttl=...)\` is called and remove it.
2. **Verify result reporting**: Ensure that \`result.applied.append("tools")\` still occurs if other parameters are being applied through \`apply_config\`.
3. **Verification**: Run integration tests for config reload.
### Method
Code modification and verification.
### Details
- REQ-003: Stop applying \`cache_ttl\` in \`ConfigReloadService\`.

## Compatibility considerations
- Depends on the simultaneous removal of \`cache_ttl\` from \`ToolExecutor.apply_config\`.

## Security considerations
- None.

## Rollback considerations
- Revert changes to \`scripts/agent/services/config_reload.py\` via git.

## Validation plan
- Run \`uv run pytest\` to verify that configuration reloading works correctly without errors related to \`cache_ttl\`.

## Completion criteria
- \`scripts/agent/services/config_reload.py\` no longer contains references to \`cache_ttl\` within the \`_sync_services\` method.
- Config reload succeeds in tests.

## Out of scope
- Other parts of the configuration reload process.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-08-27 | 2026-08-27 | Adversarial verification confirmed: `rg cache_ttl scripts/agent/services/config_reload.py` returns no matches. Same REQ-003 as 20260826_01; both were independently completed by `plans/done/20260826-120000_plan.md`. No code changes needed. |
| 2 | Add or update tests per Validation plan | Completed | 2026-08-27 | 2026-08-27 | No new tests required. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-08-27 | 2026-08-27 | Validated below. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-08-27 | 2026-08-27 | N/A. |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260826_delete_tool_executor_cache_issue.md
- **Source requirement**: N/A
- **Source plan**: `plans/20260826-120000_plan.md`
- **Source implementation procedure**: N/A
- **Generated at**: 2026-08-26T12:15:00Z
- **Related target files**: `scripts/agent/services/config_reload.py`
