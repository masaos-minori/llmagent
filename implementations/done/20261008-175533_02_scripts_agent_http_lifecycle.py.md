## Goal
Send the Bearer header from the readiness poll and the liveness check. (REQ-002 of the Plan).

## Scope
- Only `scripts/agent/http_lifecycle.py`; no other file is modified by this procedure.

## Assumptions
- User decision (2026-10-08): keep `/health` authenticated and add the Bearer token to the Agent-side probes.

## Design decisions
- No change to `http_lifecycle_health_checker.py`: it already forwards client kwargs to `httpx.AsyncClient`.

## Alternatives considered
- Exempting `/health` in `attach_auth_middleware()`: rejected by the user decision above.

## Implementation
### Target file
scripts/agent/http_lifecycle.py

### Procedure
1. In `_health_poll_until_ready()` create the `httpx.AsyncClient` with `headers=cfg.auth_headers()`.
2. In `verify_running_async()` pass `headers=cfg.auth_headers()` through `HealthChecker.verify_running_async()`'s `**client_kwargs`.

### Method
No change to `http_lifecycle_health_checker.py`: it already forwards client kwargs to `httpx.AsyncClient`.

### Details
A 401 is still treated as not healthy, so a wrong token is detected.

## Compatibility considerations
- Servers with an empty token send no header, as before.

## Security considerations
- Do not log headers.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_health_check.py tests/agent/test_http_lifecycle.py -q --timeout=60`.

## Completion criteria
- The described change is in place and the validation commands pass (REQ-002).

## Out of scope
- Any file other than `scripts/agent/http_lifecycle.py`.

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/done/20261008-165923_mcphealthauth01_send-the-bearer-token-in-the-post-startup-mcp-health-check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-174859_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-175533
- **Related target files**: scripts/agent/http_lifecycle.py