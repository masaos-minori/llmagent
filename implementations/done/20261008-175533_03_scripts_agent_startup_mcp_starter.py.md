## Goal
Send the Bearer header from the post-startup verification. (REQ-003 of the Plan).

## Scope
- Only `scripts/agent/startup_mcp_starter.py`; no other file is modified by this procedure.

## Assumptions
- User decision (2026-10-08): keep `/health` authenticated and add the Bearer token to the Agent-side probes.

## Design decisions
- Same one-argument change at both sites.

## Alternatives considered
- Exempting `/health` in `attach_auth_middleware()`: rejected by the user decision above.

## Implementation
### Target file
scripts/agent/startup_mcp_starter.py

### Procedure
1. In `verify_health()` and `_verify_single_health()` create the `httpx.AsyncClient` with `headers=cfg.auth_headers()`.

### Method
Same one-argument change at both sites.

### Details
The retry-once and FATAL behavior is unchanged.

## Compatibility considerations
- None.

## Security considerations
- Do not log headers.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_startup_mcp_starter.py -q --timeout=60`.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-003).

## Out of scope
- Any file other than `scripts/agent/startup_mcp_starter.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write or update tests first (Validation plan) | Completed | 20261008-180404 | 20261008-180404 |  |
| 2 | Implement the change in Implementation > Procedure | Completed | 20261008-180404 | 20261008-180404 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261008-180404 | 20261008-180404 |  |

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
- **Source issue**: issues/done/20261008-165923_mcphealthauth01_send-the-bearer-token-in-the-post-startup-mcp-health-check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-174859_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-175533
- **Related target files**: scripts/agent/startup_mcp_starter.py