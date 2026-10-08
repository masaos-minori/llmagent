## Goal
Let the status probe forward headers. (REQ-004 of the Plan).

## Scope
- Only `scripts/agent/services/mcp_health.py`; no other file is modified by this procedure.

## Assumptions
- User decision (2026-10-08): keep `/health` authenticated and add the Bearer token to the Agent-side probes.

## Design decisions
- Keeping the original call shape avoids breaking tests and fakes that assert the exact `get` arguments.

## Alternatives considered
- Exempting `/health` in `attach_auth_middleware()`: rejected by the user decision above.

## Implementation
### Target file
scripts/agent/services/mcp_health.py

### Procedure
1. Add `headers: dict[str, str] | None = None` to `_probe_mcp_health_detail()`.
2. Pass `headers=` to `http.get` only when it is non-empty, so the call shape is unchanged for callers without a token.

### Method
Keeping the original call shape avoids breaking tests and fakes that assert the exact `get` arguments.

### Details
Optional argument keeps all existing callers valid.

## Compatibility considerations
- Backward compatible.

## Security considerations
- Do not log headers.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_repl_health.py tests/agent/commands/test_cmd_mcp.py -q --timeout=60`.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-004).

## Out of scope
- Any file other than `scripts/agent/services/mcp_health.py`.

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/done/20261008-165923_mcphealthauth01_send-the-bearer-token-in-the-post-startup-mcp-health-check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-174859_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-175533
- **Related target files**: scripts/agent/services/mcp_health.py