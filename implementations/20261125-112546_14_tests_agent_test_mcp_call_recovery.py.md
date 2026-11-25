## Goal
Update the recovery fixture's recorded-call call site for the new `args_hash` argument.

## Scope
**Release unit**: persisted directive store

## Assumptions
- One call site (line 101) inside the helper that plants a stale row; the helper's shape stays the same.

## Design decisions
N/A: call-site update only.

## Alternatives considered
N/A: test-only change.

## Implementation
### Target file
`tests/agent/test_mcp_call_recovery.py`

### Procedure
Add the hash argument to the `env.store.record_tool_call` call.

### Method
Pass a fixed canonical hash; the helper keeps its `created_at` aging step unchanged so the row is still past the
timeout window.

### Details
- Give the helper an optional hash parameter only if more than one test needs a distinct hash; otherwise use the
  fixed value.

## Compatibility considerations
Depends on the DDL column from sibling procedure seq 01.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_mcp_call_recovery.py` (REQ-007).

## Completion criteria
The recovery tests pass with the planted row carrying a hash.

## Out of Scope
No change to the recovery ownership or lease behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the call site | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (persisted hash), `REQ-007` (fake signature update)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `tests/agent/test_mcp_call_recovery.py`
