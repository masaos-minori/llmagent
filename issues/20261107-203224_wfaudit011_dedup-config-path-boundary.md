# Route mcp_dedup config through the shared resolver and cache its load

## Priority
Medium

## Summary
The dedup config loader bypasses the project's config-directory resolver (CWD-relative default path) and is re-read from disk, uncached and synchronously, inside an async hot path every turn. Move the file to the resolver-managed config directory and resolve the config once per process.

## Background
Code review evidence (Verified):
- `shared/mcp_dedup.py` defaults its config path to a CWD-relative `config/mcp_dedup.toml`; it does not consult `resolve_config_dir()` / `LLMAGENT_CONFIG_DIR`, unlike every other config consumer in the project (workflow loader, agent.toml, eventbus).
- The same module hardcodes a fallback database path under the production root, while every other database path flows from the `[paths]` config section.
- `WorkflowEngine.build_turn_control_message` calls the config loader on every turn-execution attempt; the loader performs a blocking file read (TOML parse) inside an `async def`. It works today only because services start with the production root as their working directory.
- The dispatcher side caches store+config at module level with a disabled-fallback; the agent side has no equivalent caching.

## Problem
- Running any entry point from a different working directory silently changes which config file is read (or disables dedup policy) — an ambiguous configuration behavior with no error.
- A synchronous file read inside the per-attempt async path is exactly the pattern this project already retired elsewhere (the blocking-IO issue for sync SQLite writes).

## Reason for Change
Configuration boundary consistency is a project rule; this is the last config consumer outside the resolver. The per-turn re-read is a small but real event-loop stall and a drift risk against the resolver fix.

## Implementation Intent
Make the dedup config path resolver-derived (config directory from the shared resolver), and load+cache it once at the consumer boundary (agent startup / engine construction), keeping the existing validation semantics and the graceful disable-on-missing behavior. The fallback DB path should come from the paths configuration like other databases.

## Target Files or Areas
- scripts/shared/mcp_dedup.py (defaults and loader)
- scripts/agent/workflow/workflow_engine.py (per-turn config consumption)
- scripts/mcp_servers/dispatch.py (module-level cache, keep semantics aligned)
- config/mcp_dedup.toml (location under the resolver-managed directory)
- deploy sync/init scripts that copy config files

## Required Changes
- Default config path via `resolve_config_dir()` (honoring the config-dir override env var).
- Cache the loaded config at the agent-side consumer; remove the per-turn reload.
- Source the fallback DB path from the paths configuration.
- Confirm deploy config-sync copies the file to the resolver-managed location.

## Constraints
- Missing-config behavior (defaults + disabled-dedup fallback) must not change.
- Existing deployments pass config via the production config directory; the change must find the same file there.
- Keep the dispatcher-side and agent-side views of one config file consistent — a single parse per process per side is acceptable; divergence is not.

## Acceptance Criteria
- Starting the agent from an arbitrary working directory reads the same config file (override env var honored).
- No per-turn TOML read remains on the turn path (observable via call-count test or loader spy).
- Fallback DB path derives from the paths config section.

## Testing Expectations
- Unit test: config resolution via the override env var (mirroring existing resolver tests).
- Test that repeated control-message builds do not re-read the file.
- Deploy tests around config sync remain green; manual start from a non-production CWD as verification.

## Documentation Impact
Deployment docs referencing the dedup config location and the config-file list must reflect the resolver-managed path. Note the caching decision (config fixed at process start; restart to change it) as an operational statement.

## Out of Scope
- Changing dedup policy values.
- Dedup store lifecycle.
- Async-ifying other blocking paths (already handled by the earlier blocking-IO work).

## Dependencies
- Context: `plans/done/20261101-143807_blockio001_sync-sqlite-writes-block-event-loop.md` (resolved precedent for the async-boundary rule).
- Deploy sync coordination with the deploy scripts' config-copy step (no sibling issue open).

## Unresolved Questions
- Should a config change require a process restart for the agent side (cache-at-start) or support reload? Assume cache-at-start here; confirm with the owner.

## AI Implementation Instruction
Do not fork a second config-resolution path for dedup — reuse the shared resolver used by the workflow loader. Keep validation and error wording identical. Remove the per-turn loader call in the engine by resolving once at construction or first use.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203224
- **Related target files**: scripts/shared/mcp_dedup.py, scripts/agent/workflow/workflow_engine.py, scripts/mcp_servers/dispatch.py, config/mcp_dedup.toml
