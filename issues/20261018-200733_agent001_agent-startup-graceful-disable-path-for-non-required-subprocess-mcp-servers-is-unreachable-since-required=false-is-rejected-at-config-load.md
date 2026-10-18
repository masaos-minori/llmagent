# Agent startup graceful-disable path for non-required subprocess MCP servers is unreachable since required=false is rejected at config load

## Priority
Low

## Summary
`McpServerStarter.start_servers` and its helper `disable_server` implement a graceful-degradation path for non-required (`required=false`) subprocess MCP servers: on a failed start they disable the server and continue. That path is unreachable in production, because `McpServerConfig` construction rejects `required=false` for `startup_mode=subprocess` at config-load time. The branches are dead code, and the guard comment that justifies the config rejection contradicts the actual `start_servers` implementation.

## Background
`scripts/agent/startup_mcp_starter.py` `McpServerStarter.start_servers` iterates the configured subprocess HTTP MCP servers and, for each, attempts a single start, then a single retry via `retry_once_with_delay`. On the second failure it branches on `cfg.required`:

- `required=true` -> raise a fatal `RuntimeError` (correct, and reachable for every real server).
- `required=false` -> call `disable_server` (set `startup_mode=NONE`, clear `tool_names`) and continue.

`disable_server` is defined in the same module and is called only from that `required=false` branch.

Meanwhile `scripts/shared/mcp_config.py` `McpServerConfig.__post_init__` runs `_validate_cross_fields` -> `_validate_startup_requirements`, which raises `ValueError` when `startup_mode==SUBPROCESS` and `required` is falsy. `_build_mcp_servers` builds every server through this constructor, so no valid runtime `McpServerConfig` can carry `required=false` on a subprocess server. Every subprocess server therefore has `required=true`.

The rejection is intentional and correct (documented in the guard comment next to the check): a subprocess server that fails to spawn cannot degrade gracefully, so it must fail closed. The problem is not the rejection; it is that the startup module still contains the now-impossible graceful path alongside it.

## Problem
Two related defects:

1. Dead code. The `if not cfg.required:` branch in `start_servers` and the entire `disable_server` method can never execute against a real configuration. They exist as if non-required subprocess servers were supported, but the config layer forbids them.
2. Contradictory documentation. The guard comment in `mcp_config.py` states that "the spawn path ignores `required`, so a non-required subprocess server would still abort startup on a spawn failure." The actual spawn path (`start_servers`) does NOT ignore `required` — it branches on it and disables-and-continues for non-required servers. A maintainer reading either side would form an incorrect mental model: the comment suggests the startup code does not honor `required`, while the startup code suggests non-required subprocess servers are handled.

Neither defect causes a runtime fault today. Both are maintenance hazards: a future author who trusts `start_servers` may add logic that depends on the graceful-disable path, and one who trusts the comment may assume the spawn path fails open.

## Reason for Change
The divergence is latent now but will surface on the next edit to this path. Removing the dead path and reconciling the comment eliminates a trap and makes the code agree with the documented constraint.

## Implementation Intent
Treat this as a cleanup that removes unreachable code and fixes the contradictory comment. Do not change any startup runtime behavior: all subprocess servers remain `required=true` and fail closed on spawn failure. First confirm (via a targeted `rg`/grep) that `disable_server` and the `required=false` branch have no other callers (production or test) before deleting.

## Target Files or Areas
- `scripts/agent/startup_mcp_starter.py` — `start_servers` `required=false` branch and `disable_server`
- `scripts/shared/mcp_config.py` — `_validate_startup_requirements` guard comment

## Required Changes
- Remove the `if not cfg.required:` graceful-disable branch in `start_servers` (and the now-redundant `else`), leaving only the `required=true` fatal-raise path, since every subprocess server is required.
- Delete the `disable_server` method if it has no remaining callers.
- Rewrite the guard comment in `_validate_startup_requirements` so it no longer claims the spawn path ignores `required`; state instead that non-required subprocess servers are disallowed because spawn failures must fail closed.

## Constraints
- Do not change startup runtime behavior. Subprocess servers must stay `required=true` and fail closed on spawn failure.
- Do not relax the `mcp_config.py` rejection; the intent (fail closed) is correct.
- Preserve the retry-once semantics for the reachable `required=true` path.

## Acceptance Criteria
- `start_servers` no longer branches on `cfg.required`; the only post-retry action is the fatal raise.
- `disable_server` is removed, or, if retained for a confirmed external caller, is documented as such.
- The `mcp_config.py` guard comment no longer asserts that the spawn path ignores `required`.
- No subprocess-server startup behavior changes.

## Testing Expectations
- Confirm via grep that `disable_server` and the removed branch have no other callers before deletion.
- Run the affected MCP lifecycle / startup test targets plus `ruff` / `mypy` before closing.

## Documentation Impact
This issue is partly a documentation correction: reconcile the guard comment with the implementation. No separate `docs/*.md` change required.

## Out of Scope
- Do not change the `required=false` rejection for subprocess servers.
- Do not alter the `required=true` fail-closed spawn behavior.
- Do not refactor the retry helper or health-check flow in this issue.

## Dependencies
N/A: none

## Unresolved Questions
- Is `disable_server` referenced by any test or reload path that constructs a `required=false` subprocess server directly (bypassing `_build_mcp_servers`)? If so, that caller must be accounted for before deletion.

## AI Implementation Instruction
Confirm `disable_server` has no other callers, then delete the unreachable `required=false` branch in `start_servers` and the `disable_server` method, and rewrite the `mcp_config.py` guard comment to stop claiming the spawn path ignores `required`. Do not change any startup runtime behavior.

## Traceability
- **Workflow phase**: python-code-review (produced via issue-creator)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261018-200733
- **Related target files**: scripts/agent/startup_mcp_starter.py, scripts/shared/mcp_config.py
