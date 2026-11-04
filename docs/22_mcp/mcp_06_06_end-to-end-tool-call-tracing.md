---
title: "End-to-End Tool Call Tracing"
area: mcp
tags:
  - mcp
  - tracing
  - observability
related:
  - mcp_06_01_configuration-file-inventory.md
  - mcp_03_03_transport-and-health.md
  - db_03_07_mcp-dedup-and-execution-snapshot.md
---
# End-to-End Tool Call Tracing

To trace a failed tool call through agent, transport, and server logs, follow these steps:

1. Find the `mcp_request_id` in the agent-side audit log:
    ```bash
    jq 'select(.mcp_request_id == "<id>")' <log_dir>/audit.log
    ```
2. Search for the same `request_id` in the MCP server's own application log, where the `mcp_tool_exec` record is a JSON line:
    ```bash
    grep '"request_id":"<id>"' <log_dir>/<server>-mcp.log
    ```
3. Search for the `X-Request-Id` response header in the specific server logs:
    ```bash
    grep "<id>" <log_dir>/github-mcp.log  # or relevant server log
    ```
4. Check the health status of the `server_key` at that time in `<log_dir>/agent.log`.
5. If the health status has changed: check the current DEGRADED/UNAVAILABLE state and `health_reason` via `/mcp status`. Note that automatic restarts are not performed (for subprocess-mode servers, `ensure_ready()` will only attempt a restart during the next tool dispatch).

---

## Error Type Distinction in Audit Logs (Agent Side)

**Regarding cross-layer correlation:** Per-server audit logs (`github_audit.log`, `shell_audit.log`, `delete_audit.log`) do not contain correlation fields like `X-Session-Id` or `X-Request-Id`. Correlation between these logs must be established using the agent-side audit log as the reference.

The agent-side audit event includes an `error_type` field distinguishing transport
failures from tool-level failures — see `scripts/agent/tool_audit.py` for the exact
values and their assignment logic.

`error_type` is `transport` (server or network issue) or `tool` (tool-level failure); filter with `grep '"error_type":"transport"' <log_dir>/audit.log`.

## Idempotency and Dedup Fields in the Audit Trace

Every agent-side `tool_exec` record carries two additional fields (toolexec001):

| Field | Presence | Content |
|---|---|---|
| `execution_snapshot_json` | always | Canonical JSON of the deployment fingerprint captured at call start: `deployed_rev`, `git_sha`, `config_hash`, per-DB `schema_versions`. Values are hashes only — never config contents or result bodies. |
| `dedup_state` | only when non-empty | The dispatcher dedup branch taken: `duplicate_hit`, `snapshot_mismatch`, `result_truncated`, `replayed`, `unreplayable`, `store_error`. Empty for freshly executed or non-dispatch-originated calls. |

The record also carries `idempotency_key`: the workflow-scoped logical-call identity (workflow, task, turn, and call id joined by colons) that the Agent derives for the audit log. It is not the `X-Idempotency-Key` the call was dispatched under, and it is neither the durable store row's key nor the workflow `tool_call_state` row's key, so it cannot be used to match an audit line against those rows. To follow one call, join on `mcp_request_id` as described at the top of this document.

Dedup outcome tags arrive through `error_type` when the dispatcher refuses a call:
`idempotency_key_reused` (key seen with different content), `dedup_unreplayable` (interrupted
call refused for a `non_retryable` tool), and `dedup_store_error` (store unavailable,
`non_retryable` tool fails closed). Filter with, for example,
`grep '"error_type":"dedup_unreplayable"' <log_dir>/audit.log`.

Snapshot equality decides replay: a completed row is served from the store only when its stored
snapshot equals the snapshot built at the new call's start, compared per component —
`mismatching_components` names each differing component, so ops can tell a config-only change
from a code-revision change. Tolerant readers record `"unknown"` (missing revision file) or
`"absent"` (missing DB) instead of failing. Storage and replay semantics:
[db_03_07](../41_db/db_03_07_mcp-dedup-and-execution-snapshot.md); transport-side key derivation:
[mcp_03_03](mcp_03_03_transport-and-health.md).

Example line (synthetic values) — a replayed completed-hit served from the durable store:

``` text
{"event":"tool_exec","tool":"write_file","is_error":false,"error_type":"","mcp_request_id":"req-000000000000","idempotency_key":"wf-0001:task-0001:turn-0001:call-0001","dedup_state":"duplicate_hit","execution_snapshot_json":"{\"config_hash\":\"…\",\"deployed_rev\":\"…\",\"git_sha\":\"…\",\"schema_versions\":{…}}","ts":1761900000.0}
```

## Per-Server Error Counters

`ToolExecutor` maintains per-server error counters, which can be inspected via `ToolExecutor.get_error_counters()`:

Counts are split into `transport` and `tool` per server. These counters are kept in memory only (not persisted) and are reset upon agent restart.

## Detecting Repeated Failures

If a tool fails repeatedly within a sliding window, a warning is logged (threshold and window are defined in code):

``` text
WARNING: Repeated tool failures detected: shell_run failed <N> times in <W>s window
```

> **Note:** `McpServerHealthRegistry` (`shared/mcp_health.py`) only tracks transport availability. Tool-layer errors (`error_type=tool`) do not affect the McpServerHealthRegistry state — only transport failures (`error_type=transport`) affect the server's health state.

---

## Serialization of Side Effects

When a round contains tools with side effects (write operations), the scheduler groups them together to prevent concurrent modifications. This is intentional behavior for safety, though it reduces concurrency.

**Serialization Triggers:**

| Trigger | Condition | Effect |
|---|---|---|
| `requires_serial` | `requires_serial=true` is set in tool metadata | The tool is executed alone as a single-element group |
| `forced_serial` | `serial_tool_calls=true` forces serial execution | Every call runs in its own serial phase |
| `resource_read_write_conflict` / `resource_write_write_conflict` | Multiple tool calls have overlapping `resource_scopes` (exact match, or filesystem scope ancestor/descendant relationship) and at least one is a write | All tool calls in the conflicting component are executed serially |
| `global_write_scope` | Multiple writes without a specific scope (each is treated as occupying the synthetic `global:write` scope) | The scope-less writes are executed serially |

**Log Format:** `ROUND_SERIALIZATION: triggered by <tool> (<reason>) — <N> tools serialized in this round`. `/mcp` shows cumulative serialization statistics.

**Why this information is important:**
While serialization reduces concurrency, it prevents race conditions on shared resources. Before attempting to optimize concurrency, check the serialization logs to identify which tools and scopes are most frequently causing grouping.

---



## Keywords

- configuration
