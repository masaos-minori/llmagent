# Implementation Procedure Output Template (Canonical)

## Goal
Remove caching logic and the \`cache_ttl\` parameter from \`ToolExecutor\` in \`scripts/shared/tool_executor.py\`.

## Scope
- In-Scope: \`scripts/shared/tool_executor.py\` — remove \`_cache\`, \`_execute_with_cache\`, \`stat_cache_hits\`, and the \`cache_ttl\` parameter from \`apply_config\`.

## Assumptions
- The system will no longer support TTL-based caching for tools.

## Design decisions
- N/A

## Alternatives considered
- N/A

## Implementation
### Target file
\`scripts/shared/tool_executor.py\`
### Procedure
1. **Remove internal members**: Delete the following attributes from the \`__init__\` method or class level:
   - \`self._cache\` (or equivalent initialization)
   - \`self.stat_cache_hits\` (or equivalent initialization)
2. **Remove \`_execute_with_cache\` method**: Delete the entire \`_execute_with_cache\` method definition.
3. **Update \`execute()` method**: Modify the \`execute()` method to call the underlying execution mechanism directly instead of calling \`_execute_with_cache()\`.
4. **Update \`apply_config()` signature**: Change \`def apply_config(self, *, cache_ttl: float | None = None) -> None:\` to \`def apply_config(self) -> None:\` (or remove it if no other parameters exist).
5. **Cleanup imports**: Remove any unused imports like \`OrderedDict\` that were used for the cache.
6. **Verification**: Run existing unit tests for \`ToolExecutor\`.
### Method
Code modification and testing.
### Details
- REQ-001: Remove all caching-related members and the \`cache_ttl\` parameter.

## Compatibility considerations
- Breaking change: Any caller of \`apply_config(cache_ttl=...)` will break. This is expected as part of this refactor.

## Security considerations
- None.

## Rollback considerations
- Revert changes to \`scripts/shared/tool_executor.py\` via git.

## Validation plan
- Run \`uv run pytest tests/shared/test_tool_executor.py\` to ensure core functionality remains intact.
- Verify that \`stat_cache_hits\` is no longer accessible.

## Completion criteria
- \`ToolExecutor\` has no mention of \`_cache\`, \`_execute_with_cache\`, or \`stat_cache_hits\`.
- \`apply_config\` does not accept \`cache_ttl\`.
- All unit tests pass.

## Out of scope
- Adding new caching mechanisms.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | — |
| 2 | Add or update tests per Validation plan | Pending | — | — | — |
| 3 | Run the validation sequence (\`rules/toolchain.md\`) | Pending | — | — | — |
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
- **Source issue**: issues/20260826_delete_tool_executor_cache_issue.md
- **Source requirement**: N/A
- **Source plan**: `plans/20260826-120000_plan.md`
- **Source implementation procedure**: N/A
- **Generated at**: 2026-08-26T12:10:00Z
- **Related target files**: `scripts/shared/tool_executor.py`
