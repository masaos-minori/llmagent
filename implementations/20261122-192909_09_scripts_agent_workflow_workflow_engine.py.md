## Goal

Remove the dispatcher-TOML framing from comments/docstrings so the stale-pending timeout reads as Agent-side only (REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 3 framing-only row)

## Assumptions
- No behavior change: `_DEFAULT_PENDING_TIMEOUT_MINUTES` (line 38) and the `pending_timeout_minutes` plumbing stay.

## Design decisions
- Reword the header comment block (lines 33-38) to drop the "Mirrors shared.mcp_dedup.DEFAULT_PENDING_TIMEOUT_MINUTES ... never imports the dispatcher's dedup config" framing; reword the constructor docstring (line ~142) that says "never from the dispatcher's mcp_dedup.toml".

## Alternatives considered
- N/A: comment-only row (rewording is the requirement).

## Implementation
### Target file
`scripts/agent/workflow/workflow_engine.py`
### Procedure
1. Update the two comment sites to reference only `AgentConfig.pending_timeout_minutes` as the source; keep the value 10 default statement.
### Method
Text edits only; no code, no constant rename.
### Details
- Constant name `_DEFAULT_PENDING_TIMEOUT_MINUTES` unchanged.

### Companion test files
- `tests/agent/workflow/test_workflow_engine.py`
  - Procedure: adjust any comment-driven expectations to the new framing; no new cases.
  - Validation: `uv run pytest tests/agent/workflow/test_workflow_engine.py -q`.

## Compatibility considerations
- N/A: comments only.

## Security considerations
- N/A: comments only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_engine.py -q`.

## Completion criteria
- No comment in the module frames the timeout as dispatcher/dedup-config-derived; suite green.

## Out of Scope
- The timeout plumbing itself (unchanged); `tool_call_state_ops` framing (seq 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the framing comments | Pending | — | — | |
| 2 | Run the companion test validation | Pending | — | — | |

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
- **Requirement ID**: REQ-002; AC-005
- **Source issue**: issues/20261120-115842_mcpdl003_dedup-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-172154_mcpdl003_dedup-config-isolation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192909
- **Related target files**: `scripts/agent/workflow/workflow_engine.py`, `tests/agent/workflow/test_workflow_engine.py`
