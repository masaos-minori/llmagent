## Goal
- Pass the per-server effective health timeout to the startup poll and the periodic liveness check in `http_lifecycle.py` instead of the global `MCPSERVER_HEALTH_TIMEOUT` constant (REQ-001, per-server timeout applied at every request site).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the poll call site and the periodic-check call site in this file.
- Out of scope: the checker internals (seq 03); the constant itself stays for non-health request defaults unless the implementation finds it unused.

## Assumptions
- Verified in Step 3a: `MCPSERVER_HEALTH_TIMEOUT = 5.0` at `http_lifecycle.py:61`; the poll is called with `request_timeout_sec=MCPSERVER_HEALTH_TIMEOUT` at `:334`; the lifecycle deadline is computed from `cfg.startup_timeout_sec` at `:372-373`.
- The periodic check currently relies on the checker's 5.0 default (`HealthChecker.verify_running_async`); callers are `lifecycle_router.py` (`:86,135,263`, reference only).

## Design decisions
- Resolve one effective timeout per server via `get_effective_health_timeout(cfg)` (now always a positive float after seq 02) at the call site.

## Alternatives considered
- N/A: single-function change with no public-contract impact.

## Implementation
### Target file
`scripts/agent/http_lifecycle.py`

### Procedure
1. At the poll call site, pass `request_timeout_sec=get_effective_health_timeout(cfg)` instead of the global constant.
2. At the periodic-check call site, pass the effective timeout explicitly rather than relying on the checker default.

### Method
- N/A: two argument changes; the deadline cap logic itself lives in seq 03.

### Details
- Keep the global constant only if other non-health paths still use it; do not remove it speculatively.

## Compatibility considerations
- Tests pin the health-check call path in `tests/agent/test_http_lifecycle_health_check.py` (seq 20 asserts a non-default value reaches each request site).

## Security considerations
- N/A: no auth change in this file.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_health_check.py tests/agent/test_http_lifecycle_integration.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; `wc -c scripts/agent/http_lifecycle.py` below 24576 (baseline 17851 B); then the sequence in `rules/toolchain.md`.

## Completion criteria
- Both call sites use the server's effective timeout; a test shows a non-default value reaching the poll and the periodic check; all validation commands pass.

## Out of Scope
- The checker predicate and auth-path changes (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the two call-site changes | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (per-server health timeout at the poll and periodic check)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/agent/http_lifecycle.py`
