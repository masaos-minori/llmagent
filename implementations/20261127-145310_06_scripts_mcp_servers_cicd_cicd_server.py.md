# Implementation Procedure — scripts/mcp_servers/cicd/cicd_server.py

## Goal

Add the FastAPI lifespan that owns the shared HTTP client, make health report the effective credential and the probe outcome, and keep the pre-bind gate fail-closed for a missing credential.

## Scope
**Release unit**: shared client and probe

Requirements implemented: REQ-001 (health reads the same effective credential), REQ-002 (write-capable startup refuses to bind without a credential), REQ-003 (probe runs in the lifespan and feeds health), REQ-008 (lifespan creates and closes the client). Acceptance criteria: AC-1, AC-2, AC-4, AC-6, AC-7.

## Assumptions
- The probe runs in the lifespan after bind because the startup stage is synchronous and `validate_cicd_security()` is documented as a pure function (Plan D3, UNK-04); the pre-bind stage keeps the config-only credential check from the guards row.
- `make_health_response()` (`scripts/mcp_servers/health_response.py:38`) derives `ready` from `deps` plus `security.validated`; this document does not invent its own ready rule.
- The module currently builds the service at import time; moving construction into the lifespan changes when `build_service()` runs, which the companion lifecycle tests cover through the sibling row.

## Design decisions
- Follow the existing FastAPI `lifespan` precedent in `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (reference only): create the client on startup, close it on shutdown.
- Health reports the effective credential through `resolve_effective_credential()` and the probe outcome as a dependency entry, so service, posture, and health cannot disagree (AC-1).

## Alternatives considered
- Keeping import-time service construction: rejected per REQ-008 — a client created at import has no shutdown path.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_server.py`

### Procedure
- Add a FastAPI `lifespan` (new) that creates the shared `httpx.AsyncClient`, injects it into `build_service()`, runs the side-effect-free read-permission probe (`GET /repos/{owner}/{repo}/actions/workflows`) against the effective credential, stores the probe outcome, and closes the client on shutdown.
- Change `health()` to read the effective credential through `resolve_effective_credential()` instead of `os.environ.get("GITHUB_TOKEN", "")` only, and include the probe outcome (permission, reachability, rate-limit status, dispatch `not_applicable`) without exposing the token.
- Keep `_enforce_posture_gate()` (lines 238-254) refusing bind on an unvalidated posture; the new credential check makes a tokenless write-capable start unvalidated (REQ-002).

### Method
- `health()` at lines 195-212 currently reads only the environment variable (verified in Step 3a); the module has no lifespan and builds the service at import time (verified).
- The probe uses the lifespan client, not a new client, so the composite and job backends reach the same path (`scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py`, reference only).

### Details
- The bandit `B105` finding at `cicd_server.py:202` (`deps["github_token"] = "not_set"`) stays; if the literal moves, re-check the finding rather than suppress it (Plan Validation quality baseline).

### Companion test files
- `tests/mcp_servers/cicd/test_cicd_health_posture.py`
  - Procedure: assert health uses the effective credential and carries the probe outcome; correct the stale empty-token docstring at line 36 (`require_auth_token()` at `scripts/mcp_servers/server.py:250-260` no longer keeps an accept-all path; `attach_auth_middleware()` is fail-closed on an empty token).
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_cicd_health_posture.py`.
- `tests/mcp_servers/cicd/test_mcp_server_health_status.py`
  - Procedure: update the 503-when-token-not-set case (lines 60-80) to the fail-closed startup rule and the effective-credential source.
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_mcp_server_health_status.py`.
- `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`
  - Procedure: update the health endpoint characterization (lines 268-285) to the effective credential and the probe block.
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_cicd_server_endpoints.py`.

## Compatibility considerations
- A tokenless deployment that currently binds successfully will refuse to bind (Plan Risk, stated intent); the documentation rows record the new rule.

## Security considerations
- The probe is side-effect-free and reports status without exposing the token (AC-7); the gate reports only the failed check id and reason code (AC-2).

## Rollback considerations
- N/A: revert the commit; the phase is covered by its own tests.

## Validation plan
- Integration: lifespan startup/shutdown and health parity — `uv run pytest tests/mcp_servers/cicd/test_cicd_lifecycle.py tests/mcp_servers/cicd/test_cicd_health_posture.py tests/mcp_servers/cicd/test_mcp_server_health_status.py tests/mcp_servers/cicd/test_cicd_server_endpoints.py`.
- Full sequence per `rules/toolchain.md`, including bandit re-check of the `B105` literal.

## Completion criteria
- Shutdown closes the lifespan-owned client and tests can still inject their own client (AC-6); health reports the effective credential and the probe outcome (AC-1, AC-4); a write-capable start without a credential refuses to bind (AC-2).

## Out of Scope
- The probe policy function and the credential check (guards row); error and audit mapping (mcpci004, out of this Plan's scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion test files) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | documentation is covered by the Plan's docs rows |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-008 (effective credential, fail-closed startup, probe, lifespan)
- **Source issue**: issues/20261119-141106_mcpci001_cicd-credential-config-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-152931_mcpci001_cicd-credential-config-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-145310
- **Related target files**: `scripts/mcp_servers/cicd/cicd_server.py`, `tests/mcp_servers/cicd/test_cicd_health_posture.py`, `tests/mcp_servers/cicd/test_mcp_server_health_status.py`, `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`
