## Goal

Correct the docstring framing that states the stale-pending timeout comes from dispatcher-side config (REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 3 framing-only row)

## Assumptions
- Timeout wiring stays Agent-side (`recover_stale_*` callers pass the Agent value); no behavior change.

## Design decisions
- Update the docstring near line 142 to name `AgentConfig.pending_timeout_minutes` as the timeout source instead of the dispatcher-side config.

## Alternatives considered
- N/A: comment-only row.

## Implementation
### Target file
`scripts/agent/workflow/tool_call_state_ops.py`
### Procedure
1. Reword the timeout-source docstring sentence (near line 142); nothing else.
### Method
Text edit only.
### Details
- The state-transition/WHERE-guard logic is untouched.

### Companion test files
- `tests/agent/workflow/test_stale_recovery_lease.py`
  - Procedure: regression run only; adjust expectations if any assert on the old framing.
  - Validation: `uv run pytest tests/agent/workflow/test_stale_recovery_lease.py -q`.

## Compatibility considerations
- N/A: docstring only.

## Security considerations
- N/A: docstring only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_stale_recovery_lease.py -q`.

## Completion criteria
- No remaining statement in the module attributes the timeout to dispatcher-side config; suite green.

## Out of Scope
- Lease/recovery behavior (unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the framing docstring | Pending | — | — | |
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
- **Related target files**: `scripts/agent/workflow/tool_call_state_ops.py`, `tests/agent/workflow/test_stale_recovery_lease.py`
