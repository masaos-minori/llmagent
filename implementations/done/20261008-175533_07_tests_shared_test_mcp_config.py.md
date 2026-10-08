## Goal
Cover `auth_headers()`. (REQ-001, REQ-005 of the Plan).

## Scope
- Only `tests/shared/test_mcp_config.py`; no other file is modified by this procedure.

## Assumptions
- User decision (2026-10-08): keep `/health` authenticated and add the Bearer token to the Agent-side probes.

## Design decisions
- The empty-token case sets `auth_token = ""` after construction because `__post_init__` rejects it.

## Alternatives considered
- Exempting `/health` in `attach_auth_middleware()`: rejected by the user decision above.

## Implementation
### Target file
tests/shared/test_mcp_config.py

### Procedure
1. Add a test for a non-empty token and a test for an empty token.

### Method
The empty-token case sets `auth_token = ""` after construction because `__post_init__` rejects it.

### Details
Plain unit tests.

## Compatibility considerations
- Test-only change.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/shared/test_mcp_config.py -q --timeout=60`.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-001, REQ-005).

## Out of scope
- Any file other than `tests/shared/test_mcp_config.py`.

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
- **Requirement ID**: REQ-001, REQ-005
- **Source issue**: issues/done/20261008-165923_mcphealthauth01_send-the-bearer-token-in-the-post-startup-mcp-health-check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-174859_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-175533
- **Related target files**: tests/shared/test_mcp_config.py