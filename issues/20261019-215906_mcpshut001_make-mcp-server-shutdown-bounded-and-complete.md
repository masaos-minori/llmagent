# Make MCP server shutdown bounded and complete

## Priority
Medium

## Summary
Agent shutdown stops the MCP server subprocesses one at a time, waiting up to 30 seconds each. When the session is cut off part-way (or simply takes long), the servers not yet reached keep running as orphans and hold their ports. The intended outcome is a shutdown that finishes in bounded time and never leaves MCP server processes behind.

## Background
- Observed on 2026-10-19 after deploying rebuilt binaries: the agent was started twice with piped input (`/mcp`, then `/exit`) under a `timeout 100` wrapper. After the second run, 14 processes (7 servers, two processes each) remained, re-parented to PID 611, and ports 8004, 8005, 8007, 8008, 8010, 8012, 8013 stayed in LISTEN.
- The log of that run shows `Escalated to SIGKILL for process group` for only the first two servers (`shell`, `git`); the remaining seven servers were never signalled.
- The same orphaning happened after the first run, and an older `mcp_mdq` (PID 74050) from an earlier session was also still holding port 8013, so the condition is not specific to one run.

## Problem
- Evidence (confirmed from source): `ShutdownCoordinator.shutdown_all` iterates the managed servers sequentially and awaits `terminate_with_timeout` for each with `_SHUTDOWN_TIMEOUT_SEC = 30.0`. Worst case for 10 servers is about 300 seconds; any outer deadline or interruption leaves every server not yet reached running.
- Evidence (confirmed from log): `shell` and `git` did not exit within 30 seconds of SIGTERM and were escalated to SIGKILL.
- Hypothesis (not verified): the MCP server's `uvicorn.Config` sets no `timeout_graceful_shutdown`, so on SIGTERM uvicorn waits for open connections (for example the agent's keep-alive connection) and does not exit until the 30 second escalation.
- Orphaned servers keep the loopback ports, so the next agent start can fail the port check or talk to a stale (older binary) server.

## Reason for Change
- Operational reliability: leftover servers can silently serve old code after a redeploy, which defeats the deploy verification (`/mcp` showed healthy while stale processes could still own the ports).
- Shutdown time grows linearly with the number of servers and is unpredictable.

## Implementation Intent
- Keep the existing responsibility split: the coordinator decides order and bounds, the terminator performs the signalling, and each server owns its own graceful exit.
- First verify the hypothesis, then fix the cause with the smallest change: give the server a bounded graceful-shutdown period, and make the coordinator signal all servers before waiting (concurrent termination) so total time is bounded by one timeout rather than the sum.
- Preserve the SIGTERM then SIGKILL escalation and the process-group signalling.

## Target Files or Areas
- `scripts/agent/http_lifecycle_shutdown_coordinator.py` (sequential loop, `_SHUTDOWN_TIMEOUT_SEC`)
- `scripts/agent/http_lifecycle_process_terminator.py` (`terminate_with_timeout`)
- `scripts/mcp_servers/server.py` (`run_http`, `uvicorn.Config`)
- `tests/agent/` tests for the coordinator and terminator (exact files Unknown)

## Required Changes
- Reproduce and record the cause: run one MCP server with the agent connected, send SIGTERM, and record how long it takes to exit and whether open connections delay it.
- Set a bounded graceful-shutdown timeout for the MCP server's uvicorn instance (value chosen from the measurement above).
- Change `shutdown_all` so termination of all servers is started together and then awaited with one overall bound.
- Ensure that if the agent is interrupted during shutdown, every already-spawned server process group still receives a termination signal.

## Constraints
- Do not run MCP servers outside loopback; the existing loopback checks stay as they are.
- Process-group signalling (`start_new_session=True` plus `killpg`) stays the mechanism, so onefile launcher and child are both covered.
- The SIGINT absorption during shutdown stays.

## Acceptance Criteria
- Shutting down an agent with 10 MCP servers completes within one termination timeout plus a small margin, not the sum of per-server timeouts.
- After a normal `/exit` and after an interrupted shutdown, no `/opt/llm/bin/mcp_*` process remains and ports 8004 to 8014 are free.
- A server that ignores SIGTERM is still removed by SIGKILL within the bound.
- The cause (graceful-shutdown wait or another cause) is stated in the change with its measurement.

## Testing Expectations
- Unit tests for the coordinator with fake processes: all servers receive a signal before the first wait completes; a stuck server does not delay the others beyond the bound; an exception or cancellation mid-shutdown still signals the rest.
- Regression test that the escalation to SIGKILL still happens.
- Manual verification on the deployed binaries: start the agent, `/exit`, then confirm with `pgrep -af /opt/llm/bin/mcp_` and `ss -ltn` that nothing is left.
- `ruff`, `mypy`, `lint-imports`, and the full suite per `rules/toolchain.md`.

## Documentation Impact
- Yes, if the timeout values or shutdown order change: update the lifecycle and operations documents that describe shutdown behavior (failure behavior and operational notes). Exact files Unknown; locate through `docs/00_index.md`.

## Out of Scope
- The `cicd` `http_error` display (caused by an unset `GITHUB_TOKEN`; GitHub integration is intentionally unused).
- The unreachable `embed-llm` at the remote host.
- Changing the startup order, the health-check logic, or binary build and deploy procedures.
- Cleaning up the currently orphaned processes (an operator action, not part of this change).

## Dependencies
- N/A: none. Open issues under `issues/` (`memcfg001`) do not touch these files.

## Unresolved Questions
- Is the uvicorn graceful-shutdown wait the actual cause of the `shell` and `git` delay? Unverified; the first Required Change resolves it.
- Is a shorter default than 30 seconds acceptable for servers that run long tool calls (for example `shell`) at shutdown?

## AI Implementation Instruction
- Verify the cause before changing code, and record the measurement in the change.
- Keep the change minimal and limited to the target areas; do not refactor unrelated lifecycle code.
- Do not kill or modify running production processes while investigating; reproduce with a separately started server.
- Stop and report if the measurement contradicts the hypothesis.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261019-215906
- **Related target files**: scripts/agent/http_lifecycle_shutdown_coordinator.py, scripts/agent/http_lifecycle_process_terminator.py, scripts/mcp_servers/server.py
