## Goal

Read the server's own `[dedup]` table at bootstrap and inject it into the dispatcher before serving, failing fast on invalid or missing configuration (REQ-001, REQ-006).

## Scope
**Release unit**: dedup-config-isolation-core (shared-store config isolation, store-identity gate, and operational reference removal)

## Assumptions
- `load_dedup_section()` (seq 01), `configure_dedup()` (seq 03), and the ten per-server `[dedup]` tables (seqs 13-22) land in the same delivery unit.
- `ConfigLoader.restrict_to(self.own_config_file)` (lines 340-348) already allows loading exactly the own file.

## Design decisions
- Injection point: in `run_http()` immediately after the `restrict_to()`/fail-closed block and before `_enforce_startup_posture_gate()` — the store must be configured before any request reaches `dispatch_tool`.
- Fail fast: a missing or invalid `[dedup]` table raises the `ConfigParseError`/`ConfigMissingError` (message names the server file) before any socket is created, matching the existing startup-gate posture.

## Alternatives considered
- Lazy first-request injection: rejected — REQ-006 requires startup fail-fast, and lazy injection re-opens the discovery window.
- Reading `[dedup]` directly with `tomllib` instead of `ConfigLoader`: rejected — bypasses the isolation audit trail of `restrict_to()`.

## Implementation
### Target file
`scripts/mcp_servers/server.py`
### Procedure
1. After `ConfigLoader.restrict_to(self.own_config_file)` (line 343), load the own config file through `ConfigLoader` and pass its `["dedup"]` mapping to `load_dedup_section()`; let its typed errors propagate.
2. Call `configure_dedup(store_config)` (sibling seq 03) on `mcp_servers.dispatch` before the startup posture gate and before uvicorn construction.
3. Keep the falsy-`own_config_file` fail-closed branch unchanged (lines 345-348).
### Method
Small straight-line addition; no new class or hook — the bootstrap sequence already exists, this appends two calls in order.
### Details
- Module is 17,612 B: ample headroom.
- Import `load_dedup_section()` from `shared.mcp_dedup` (facade re-export, seq 02) rather than the config submodule directly.

### Companion test files
- `tests/mcp_servers/test_server_idempotency_boundary.py`
  - Procedure: add a bootstrap-injection case — a server whose own config lacks `[dedup]` raises `ConfigMissingError` before binding, and a valid config results in the dispatcher globals being configured.
  - Validation: `uv run pytest tests/mcp_servers/test_server_idempotency_boundary.py tests/mcp_servers/test_config_isolation_fail_closed.py -q`.

## Compatibility considerations
- Subclass servers must all have a `[dedup]` table (seqs 13-22) or they fail startup — intended (REQ-006); `_NoConfigFileServer`-style test doubles that never call `run_http()` are unaffected.

## Security considerations
- Config Isolation posture unchanged: the injection reads only the own file already whitelisted by `restrict_to()`; loopback binding and posture gates untouched.

## Rollback considerations
- Revert the commit; without injection the dispatcher falls back to its own degraded contract (overlay-only), so a reverted server still serves safely.

## Validation plan
- `uv run pytest tests/mcp_servers/ -q`; integration check per the plan's Validation plan row (store opens only via injected config); `uv run mypy scripts/mcp_servers/server.py`.

## Completion criteria
- A server process opens the store only through its own `[dedup]` table; invalid/missing `[dedup]` prevents socket creation; overlay-only path unreachable when configured.

## Out of Scope
- The `[dedup]` tables themselves (seqs 13-22); dispatcher internals (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the bootstrap injection per Implementation | Pending | — | — | |
| 2 | Add or update companion tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-006; AC-002
- **Source issue**: issues/20261120-115842_mcpdl003_dedup-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-172154_mcpdl003_dedup-config-isolation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192909
- **Related target files**: `scripts/mcp_servers/server.py`, `tests/mcp_servers/test_server_idempotency_boundary.py`
