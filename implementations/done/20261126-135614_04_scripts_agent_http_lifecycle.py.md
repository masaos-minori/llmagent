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
- Corrected in Step 3b: the caller also resolves the server's `required_capability` from `config/tool_catalog.toml` and passes it to `poll_until_ready`; the checker itself does not read the catalog (owner decision, 2026-11-26). The loader is the new shared leaf `scripts/shared/tool_catalog.py` (`load_tool_catalog()`, `required_capability_for()`), shared with seq 09. This path is not in the Plan's frozen target table and the Plan is archived (`plans/done/`), so `amend_plan.py` refuses it; recorded as a deviation in the Final Report rather than as a new Plan row.
- Corrected in Step 3b: a missing or unreadable catalog resolves to `None` here with a warning, and the poll then reads the body through the legacy `ready` fallback; the fail-closed FATAL for a missing catalog stays at discovery (REQ-005), which is the enforcement point.
- Corrected in Step 3b: the periodic-check call site stops passing `headers=cfg.auth_headers()` (seq 03 makes `auth_headers()` the only header path inside the checker); passing it would collide with the checker's own headers.

## Alternatives considered
- N/A: single-function change with no public-contract impact.

## Implementation
### Target file
`scripts/agent/http_lifecycle.py`

### Procedure
1. At the poll call site, pass `request_timeout_sec=get_effective_health_timeout(cfg)` instead of the global constant, and `required_capability=required_capability_for(catalog, server_key)` resolved from the catalog.
2. At the periodic-check call site, pass the effective timeout explicitly rather than relying on the checker default, and drop the `headers=` argument.
3. Add `scripts/shared/tool_catalog.py` (new shared leaf): `load_tool_catalog(config_dir=None)` reads `config/tool_catalog.toml` through `resolve_config_dir()`; `required_capability_for(catalog, server_key)` returns the declared identifier or `None`. Seq 09's `_load_tool_catalog()` is expected to call this loader when its cycle runs.

### Method
- N/A: two argument changes; the deadline cap logic itself lives in seq 03.

### Details
- Keep the global constant only if other non-health paths still use it; do not remove it speculatively.
- Corrected in Step 3b: `MCPSERVER_HEALTH_TIMEOUT` has no remaining consumer after this change (`rg` over `scripts/`, `tests/`, `docs/`), so it is removed and the module docstring bullet that named it is replaced.

## Compatibility considerations
- Tests pin the health-check call path in `tests/agent/test_http_lifecycle_health_check.py` (seq 20 asserts a non-default value reaches each request site).

## Security considerations
- N/A: no auth change in this file.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_health_check.py tests/agent/test_http_lifecycle_integration.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; `wc -c scripts/agent/http_lifecycle.py` below 24576 (current size 17851 B); then the sequence in `rules/toolchain.md`.

## Completion criteria
- Both call sites use the server's effective timeout; a test shows a non-default value reaching the poll and the periodic check; all validation commands pass.

## Out of Scope
- The checker predicate and auth-path changes (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the two call-site changes | Completed | 20261126-170920 | 20261126-170920 | Changed: _resolve_required_capability() added, poll call site passes request_timeout_sec=get_effective_health_timeout(cfg) and required_capability, periodic call site passes the effective timeout and no longer passes headers=; MCPSERVER_HEALTH_TIMEOUT removed and the docstring bullet naming it replaced. Step 3b deviation: the catalog lookup moved to the new shared leaf scripts/shared/tool_catalog.py (load_tool_catalog/required_capability_for), shared with seq 05 and seq 09; not a row of the Plan's frozen target table, approved by the user 2026-11-26. File size 1940 B. |
| 2 | Tests are covered by the test-file procedure (seq 20) | Completed | 20261126-170920 | 20261126-170920 | Tests are in seq 20: TestCallerResolvesRequiredCapability covers the catalog entry, missing entry, and missing-catalog warning paths. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-170920 | 20261126-170920 | ruff format/check, mypy, lint-imports, bandit pass; targeted tests 26 passed. Full suite pending at end of batch. Docs: N/A, docs update is seq 33's target row. |

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