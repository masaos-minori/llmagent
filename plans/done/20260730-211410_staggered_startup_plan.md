# Work Plan: Staggered Startup for MCP Server Health Checks

## Goal

Add configurable startup stagger delay between consecutive HTTP subprocess MCP server starts to reduce burst load on health endpoints.

## Scope

**In-Scope:**
- Add `startup_stagger_delay_sec` configuration parameter to `McpServerConfig`
- Track last successful startup time in `_start_servers()` and apply stagger delay before starting next server
- Log the stagger delay applied for observability

**Out-of-Scope:**
- Staggering stdio-mode server startups (out of scope per requirement)
- Changing the health check polling interval within a single server's startup
- Adding jitter to the stagger delay

## Assumptions

1. Default stagger delay of 1.0 seconds is reasonable for most deployments
2. The stagger delay should be zero by default to maintain backward compatibility
3. Operators may want to disable staggering entirely for fast-starting servers

## Unknowns

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any deployment currently relies on concurrent server startups for performance | Configuration audit | Review config files for multi-server setups | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `scripts/shared/mcp_config.py` — add `startup_stagger_delay_sec` field to `McpServerConfig`
  - `scripts/agent/startup.py` — track last startup time and apply stagger in `_start_servers()`
- **Blast Radius:** Startup timing changes; no functional behavior changes
- **Risk Metrics:** Moderate — affects startup sequence which is critical path
- **Deploy Impact:** No deploy.sh changes required

## Implementation Steps

1. **Phase 1: Preparation**
   - [ ] Audit TOML config files to understand current multi-server configurations

2. **Phase 2: Core Logic Implementation**
   - [ ] In `McpServerConfig.__post_init__()`, add validation for `startup_stagger_delay_sec >= 0`
   - [ ] In `McpServerConfig`, add field: `startup_stagger_delay_sec: float = 0.0`
   - [ ] In `_build_single_server()`, read `startup_stagger_delay_sec` from TOML with default 0.0
   - [ ] In `_start_servers()`, add tracking variable `last_startup_time = 0.0`
   - [ ] Before starting each server, compute elapsed time since last startup and sleep for `max(0, cfg.startup_stagger_delay_sec - elapsed)`
   - [ ] Update `last_startup_time` after each successful start
   - [ ] Log stagger delay when non-zero: `logger.info("Staggering startup by %.1fs", stagger_delay)`

3. **Phase 3: Deployment & Verification**
   - [ ] Run `ruff check scripts/shared/mcp_config.py scripts/agent/startup.py` to verify lint passes
   - [ ] Run `pytest tests/ -k startup --no-header -q` to verify existing tests pass
   - [ ] Verify no new mypy errors introduced

## Validation Plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/mcp_config.py` | Unit test verifying stagger delay is parsed from config | `pytest tests/test_mcp_config*.py -v` | Tests pass |
| `scripts/agent/startup.py` | Integration test verifying stagger delay is applied between consecutive server startups | Manual verification via code review | Correct stagger behavior |
| `scripts/agent/startup.py` | Integration test verifying no stagger when only one server exists | Manual verification via code review | No unnecessary delay |

## Risks & Mitigations

- **Risk:** Default of 0.0 maintains backward compatibility but doesn't solve the burst problem → **Mitigation:** Document recommended value (1.0s) in config comments or docs
- **Risk:** Stagger adds latency to multi-server startup → **Mitigation:** Allow operators to set to 0.0 if they prefer faster startup
- **Risk:** Stagger delay calculation could have floating-point precision issues → **Mitigation:** Use `max(0.0, ...)` to ensure non-negative sleep duration

## Traceability

- Workflow phase: requirement-to-plan
- Source issue: N/A
- Source requirement: requires/20260730-204131_require.md
- Source plan: N/A
- Source implementation procedure: N/A
- Generated at: 20260730-211410
- Related target files: scripts/shared/mcp_config.py, scripts/agent/startup.py
