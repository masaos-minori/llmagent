## Goal
Add the Bearer header helper to `McpServerConfig`. (REQ-001 of the Plan).

## Scope
- Only `scripts/shared/mcp_config.py`; no other file is modified by this procedure.

## Assumptions
- User decision (2026-10-08): keep `/health` authenticated and add the Bearer token to the Agent-side probes.

## Design decisions
- Mirror the header built in `scripts/shared/http_transport.py`.

## Alternatives considered
- Exempting `/health` in `attach_auth_middleware()`: rejected by the user decision above.

## Implementation
### Target file
scripts/shared/mcp_config.py

### Procedure
1. Add `auth_headers(self) -> dict[str, str]` returning `{"Authorization": f"Bearer {self.auth_token}"}` or `{}` for an empty token.

### Method
Mirror the header built in `scripts/shared/http_transport.py`.

### Details
The method is a plain instance method, not a property, so call sites read `cfg.auth_headers()`.

## Compatibility considerations
- Additive; no existing field changes.

## Security considerations
- The token is placed only in the returned dict; the method never logs.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/shared/test_mcp_config.py -q --timeout=60`; ruff; mypy.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-001).

## Out of scope
- Any file other than `scripts/shared/mcp_config.py`.

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20261008-165923_mcphealthauth01_send-the-bearer-token-in-the-post-startup-mcp-health-check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-174859_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-175533
- **Related target files**: scripts/shared/mcp_config.py