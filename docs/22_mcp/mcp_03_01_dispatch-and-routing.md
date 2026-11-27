---
title: "Tool Call Dispatch Flow and Routing Resolution"
area: mcp
tags:
  - mcp
  - routing
  - lifecycle
related:
  - mcp_00_document-guide.md
  - mcp_03_02_tool-registry.md
  - mcp_03_03_transport-and-health.md
  - mcp_03_04_tool-call-tracing-and-lifecycle.md
  - mcp_03_05_lifecycle-and-new-server.md
  - mcp_01_system_overview.md
  - mcp_03_06_tool-runtime-availability-metadata.md
  - adr_02_02_003_agent-runtime-tool-registry-routing-authority.md
  - mcp_06_07_mcp-failure-diagnosis.md
  - agent_12_reference-api.md
  - governance_03_issue-and-uncertainty-management.md
---

# MCP Tool Call Dispatch Flow and Routing Resolution

- System Overview → [mcp_01_system_overview.md](mcp_01_system_overview.md)

## Purpose

To document tool routing, server startup/shutdown lifecycles, the internal structure of `ToolExecutor`, on-demand restart behavior (there is no background watchdog), idle timeouts, and procedures for adding new servers.

---

## Tool Call Dispatch Flow

The agent sets the `server_key` and `tool_name` in the dispatch log context. The `X-Request-Id` (returned in the HTTP response header of the MCP server) correlates the agent's dispatch logs with transport and server audit logs.

``` text
LLM returns tool_call
   → ToolRouteResolver.resolve(tool_name) → server_key
   → ToolExecutor.execute(tool_name, args)
         1. MCP server dispatch (internal dispatch)
             → startup_mode==none gate → immediate error ("disabled (startup_mode=none)")
             → McpServerHealthRegistry: is_unavailable? → return error immediately (no attempt made)
               (if HALF_OPEN, allow as a trial dispatch)
             → LifecycleProtocol.ensure_ready(server_key)
             → concurrency semaphore acquire (if configured)
             → HttpTransport.call()
             → McpServerHealthRegistry.record_success() on success / record_failure() on transport error
             → return ToolCallResult(output, is_error, request_id, server_key)
```

### Dispatch Gate Behavior

- Tool calls to a server with `startup_mode=none` return an error immediately before attempting health checks or lifecycle activation.
- If the health registry returns a `HALF_OPEN` state, the block by `is_unavailable` is skipped to allow exactly one in-flight trial dispatch (circuit breaker half-open attempt). While that trial is in flight, further concurrent calls are rejected with an `"unavailable"` error result; the trial flag is released on success, failure, or cancellation so the slot never leaks. (`McpServerHealthRegistry.acquire_trial` in `scripts/shared/mcp_health.py`)
- `ToolTransportInvoker.invoke()` exists as a separate general-purpose method providing health checks, lifecycle activation, and semaphore control similar to internal dispatch, and runs the same pre-call gates as `ToolExecutor.execute()`, including the `startup_mode=none` check.

### Idempotency and retry

The `X-Idempotency-Key` request header gives a logical call a stable identity on the server: it drives server-side de-duplication of state-mutating calls and lets the Agent reuse one key across that call's retries.

In addition to this transport key, the Agent also records a separate audit-side key in the `tool_exec` event's `idempotency_key` field — the workflow-scoped logical-call identity (`workflow_id:task_id:turn_id:call_id`) — which identifies the logical call for the audit log and is **not** used for server-side de-duplication.

Replay is Agent-managed: a reissued call's identity comes from a `ReplayDirective` built at turn entry from a persisted `interrupted` replayable `tool_call_state` row (`scripts/agent/tool_preparation.py`) and held on `TurnState.replay_directives`, so the LLM never sees the id it carries. The definitions of the ids named here are the single id table in [mcp_06_06_end-to-end-tool-call-tracing.md](mcp_06_06_end-to-end-tool-call-tracing.md).

- **Key ownership:** the caller/Agent generates one idempotency key per logical call. `HttpTransport.call()` emits it as the `X-Idempotency-Key` header and reuses the same value on every retry of that call, so a re-sent write keeps a single identity.
- **Audit key (separate):** the Agent's `tool_exec` audit event records its own workflow-scoped logical-call identity (workflow, task, turn, and call id joined by colons) in its `idempotency_key` field. This value is never sent to a server, is not the `X-Idempotency-Key`, and no de-duplication keys on it; to follow one call across the Agent and a server, join on the request id (see [mcp_02_03](mcp_02_03_audit-logging-and-errors.md)).
- **Key requirement:** every side-effecting dispatch, HTTP or programmatic, needs a key. A keyless side-effecting call is refused before the handler runs with `error_type=idempotency_key_required`; a read-only call executes without a key and is never stored. Proven by `tests/mcp_servers/test_mcp_dispatch.py::test_keyless_side_effecting_call_is_rejected`.
- **Cache keying:** a successful result is stored keyed by the idempotency key plus the resolved tool name plus a normalized hash of the arguments. Reusing a key with different tool or argument content is rejected as an error rather than served. Proven by `tests/mcp_servers/test_mcp_dispatch.py::test_same_key_served_from_cache` and `test_durable_args_hash_mismatch_rejected`.
- **TTL and eviction:** cached results carry a fixed time-to-live; the cache is bounded to a maximum entry count and evicts oldest-first past that bound, dropping expired entries first. Proven by `tests/mcp_servers/test_mcp_dispatch.py::test_ttl_expiry_reexecutes` and `test_eviction_reexecutes_oldest`.
- **Errors are never cached**, so a failed call always re-executes. A preview performs no dedup acquisition at all: it runs the handler and writes neither a durable ledger row nor an overlay entry, so the same key can still execute for real afterwards. Proven by `tests/mcp_servers/test_mcp_dispatch.py::test_error_result_not_cached`, `test_preview_result_is_not_cached`, and `test_preview_leaves_no_row`.
- **Write-tool retry:** side-effecting tools (the transport's `_WRITE_TOOLS`, mirroring the
  dispatch layer's write set) are retried only on pre-send connection failures
  (`httpx.ConnectError`, `httpx.ProxyError`) and on `429`; post-send ambiguous request errors
  and ambiguous statuses `502`/`503`/`504` raise `TransportError` immediately
  (fail-closed, ADR-004) because the server may already have executed the write. Read-tool
  retry is unchanged. Timeouts are never retried for any tool. `call()` always emits a
  per-call key, so retried writes keep a stable identity.

Enforcement points: `dispatch_tool()` in `scripts/mcp_servers/dispatch.py` (server-side dedup) and `HttpTransport.call()` (key generation and retry).

The store behind the dispatch-side claim is `scripts/shared/mcp_dedup.py`: each acquisition is held under a renewable owner lease and terminal rows are immutable evidence. A store acquisition failure is audited as `store_error` and the call proceeds for a retryable tool, while a non-retryable tool fails closed with `error_type=dedup_store_error` (`tests/mcp_servers/test_mcp_dispatch.py::test_store_error_retryable_proceeds_non_retryable_fails_closed`); terminal-row immutability is proven by `tests/shared/test_mcp_dedup.py::test_terminal_rows_are_immutable`. Lease behavior is proven by `tests/mcp_servers/test_mcp_dispatch_concurrency.py::test_lease_renewed_while_the_handler_runs` (renewal while the handler is in flight) and `test_lost_lease_surfaces_without_redispatch` (a refused renewal reports `lease_conflict` once and leaves the row for reconciliation without re-running the handler).

### Execution modes

`scripts/shared/execution_mode.py` is the closed vocabulary a dispatch reports on `DispatchResult.execution_mode`:

- `preview` — the handler ran as a preview. Returned only when the tool declares `preview_capability=dry_run` and its `dry_run` argument is exactly `True`. A preview takes no dedup acquisition: no lease, no heartbeat, no ledger row, no overlay write.
- `applied` — the handler ran for real.
- `no_op` — the handler did not run: a served replay, a dedup refusal, a key rejection, or an unknown tool.
- `""` — no dispatcher outcome was attached.

`side_effect_applied` is `True` only for an applied success on a side-effecting tool. Both fields are written by the dispatcher, never derived from `error_type` or `dedup_state`.

The mode is resolved from the validated arguments plus the tool's declared `preview_capability`, never read from the request. A tool without the capability treats `dry_run` as an ordinary argument handled by argument validation. A `dry_run` that is present on a capable tool but is not a `bool` raises `ValueError` naming the tool and the offending type only — the value is never echoed because arguments can carry secrets.

`X-Execution-Mode` is a cross-check only. The caller may claim `preview` or `applied`; `no_op` is a dispatcher outcome and is never an accepted claim. A claim outside the input-derived modes, or one that disagrees with the resolver's answer, is an `ExecutionContextError` rather than a silent override, and an empty claim lets the resolved mode stand.

Enforcement points: `resolve_execution_mode()` in `scripts/shared/execution_mode.py`, `build_execution_context()` and `extract_execution_context()` in `scripts/mcp_servers/execution_context.py`, `HttpTransport.call()` (emits the claim), and `dispatch_tool()` (reports the outcome).

---

## Tool resolution and LLM visibility

A single stage does the real filtering: `RuntimeToolRegistry.llm_tool_definitions()` returns only tools with `enabled_for_llm=True`, and that is the set of function definitions actually sent to the LLM. Disabled tools (per the owning server's `enabled`/`disabled_reason`) are excluded here, before the LLM ever sees them — not at a later "runtime routability" stage.

`LLMTurnRunner._stream_llm()` is the only LLM-call path in the loop and calls `registry.llm_tool_definitions()` directly (falling back to `ctx.cfg.tool.tool_definitions` only when no registry is available), so Stage 1 above is the sole filtering stage — see ADR-003 for the distinction between static availability, dynamic health, and approval, and `mcp_03_06_tool-runtime-availability-metadata.md` for the availability metadata.

Once a tool call reaches `ToolRouteResolver.resolve()`/`RuntimeToolRegistry`, routing succeeds as long as the tool is *owned* by a server — `enabled_for_llm`/`disabled_reason` are not re-checked at this layer. A disabled tool that somehow reaches this point (e.g., a stale LLM response referencing a tool disabled after the definitions were generated) is not rejected by the agent-side router; enforcement of "disabled tools must not execute" then depends on the owning MCP server's own `/v1/call_tool` gate, which every server except `mdq` implements (`git`, `file_read`/`file_write`/`file_delete`, `github`, `web_search`, `shell`, `cicd`, `rag_pipeline` — see `mcp_03_06_tool-runtime-availability-metadata.md`).

**Critical failure mode:** If `RuntimeToolRegistry` is missing entirely, the LLM sees no tools at all, resulting in "Unknown tool" errors even when tools exist in the system. At execution time, if the registry is not wired into `ToolExecutor` (discovery has not completed), `execute()` cannot resolve any tool and returns a `routing:not_ready` result without running any tool.

## Data source for DAG scheduling

The DAG scheduler reads its metadata from `RuntimeToolRegistry`, the same registry that backs routing and LLM visibility. For each approved call, `agent/tool_runner.py::_execute_with_dag()` builds a call-id-keyed `ToolSpec` via `RuntimeToolRegistry.tool_spec_for_call(call_id, name, args)` (`shared/runtime_tool_registry.py`), which resolves per-call resource scopes from the tool's declared `resource_scope_kind`/`resource_scope_keys` and the call's actual arguments (`shared/resource_scope.py::resolve_resource_scopes()`). `agent/tool_scheduler.py::build_execution_groups()` consumes this `dict[str, ToolSpec]` keyed by `call_id` (not tool name) and raises `MissingToolSpecError` if a call's `call_id` has no entry, instead of silently defaulting.

### Fields used by the DAG scheduler

The following `ToolSpec` fields (resolved per call from the tool's `/v1/tools` schema-2.0 declaration) drive scheduling:

- `requires_serial`: Controls whether the tool requires serialized execution (forms a solo serial-barrier group)
- `resource_scopes`: Tuple of kind-prefixed resource-scope strings (e.g. `"filesystem:/a/b.txt"`) the call occupies; conflicting scopes across calls form a serialized conflict-graph group (`shared/resource_scope.py::_scopes_conflict()` — exact match, or ancestor/descendant for `"filesystem:"` scopes)
- `is_write`: Indicates whether the tool performs write operations (a write tool with no resolved scope is treated as occupying the synthetic `"global:write"` scope, so it still participates in — and can conflict within — the same resource-scope conflict graph as scoped writes; there is no separate `write_first` bucket)

### Key distinction

- **RuntimeToolRegistry**: Sole authority for both routing/LLM visibility (`/v1/tools`) AND DAG scheduling metadata (`ToolSpec` via `tool_spec_for_call()`).
- **config/agent.toml `[[tool_definitions]]`**: Only the LLM-facing function-calling schema (name/description/parameters) exposed to the model; carries no scheduling metadata of its own.

There is a single data source for scheduling metadata today: a tool's `/v1/tools` schema-2.0 declaration (`is_write`, `requires_serial`, `resource_scope_kind`, `resource_scope_keys`). Updating `config/agent.toml`'s tool definitions does not affect DAG scheduling.

---

## ToolRouteResolver (`shared/route_resolver.py`)

Resolves `tool_name → server_key` using `RuntimeToolRegistry`. See [ADR-003](../10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md) for rationale and invariants.

**Wiring order:** the `McpServerHealthRegistry` is passed at `ToolExecutor` construction, and the `RuntimeToolRegistry` is attached afterward with `set_runtime_registry()` once `/v1/tools` discovery completes. Passing `None` raises `TypeError` — an unwired resolver must never be re-established as unwired. Until the registry is wired, `resolve()` reports the `not_ready` kind.

**Routing error contract:** a routing failure never reaches the transport. `ToolExecutor.execute()` catches `ToolRoutingError` and returns a `ToolCallResult` with `is_error=True` and `error_type="routing"`; the output begins with `routing:<kind>:` where `<kind>` is one of `not_ready`, `unknown_tool`, `posture_excluded`, `server_unavailable`. Dynamic circuit-breaker results (`UNAVAILABLE` / `HALF_OPEN`) are produced by the health gate and keep their existing result form; they are not routing failures.

Tool names are grouped by owning server in the static frozensets of `shared/tool_constants.py`; these groups seed drift detection and operation-type classification, not routing. A tool name that `RuntimeToolRegistry` cannot resolve raises `ValueError`. For diagnosis guidance, see [MCP Failure Diagnosis](mcp_06_07_mcp-failure-diagnosis.md#llm-sees-a-tool-but-execution-fails-with-unknown-tool).

**Not to be confused with `ToolExecutor.server_configs`:** `ToolRouteResolver` has no `server_configs` parameter (see [Agent Reference API](../23_agent/agent_12_reference-api.md) for its parameters). `ToolExecutor.server_configs` (`shared/tool_executor.py`) is a separate, current, active configuration: a `dict[str, McpServerConfig]` used for MCP server transport and — via the inherited `ToolTransportInvoker` boundary — startup-mode checks (`ToolTransportInvoker._run_precall_gates()` calls `self._server_configs.get(server_key)`), unrelated to tool-name routing.

**Per-server tool definition layers:** every MCP server spreads one tool's definition across four independently owned places: the schema (`TOOL_LIST`, what the LLM sees), the runtime dispatch table (name to handler), the registry registration (`shared/tool_constants.py` frozensets, for drift detection), and the deployment allowlist (`tool_names` in `config/agent.toml`). Changing any one requires updating the other three in the same change. `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` verifies this for all MCP servers (`tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` for mdq).

---

## Tool Lifecycle Overview (schema → dispatch → registry → side-effect → risk → audit)

Every MCP tool passes through these layers consistently from invocation to audit logging. Updating only one layer while leaving others unchanged causes drift (inconsistency between layers).

``` text
① Schema Definition        Each server's `tools.py::TOOL_LIST` — Names and input schemas exposed to LLM
② Runtime Dispatch        `mdq_server.py`'s `_DISPATCH_TABLE`, `web_search/formatters.py`'s `_WEB_DISPATCH`, or `service.get_dispatch_table()`
③ Registry Registration    `shared/tool_constants.py`'s frozenset → `shared/tool_registry.py` (for drift detection); routing relies solely on `RuntimeToolRegistry` in `shared/runtime_tool_registry.py`
④ Side-effect Detection     Only execution path `agent/tool_runner.py::_execute_with_dag()` delegates to `agent/tool_scheduler.py::build_execution_groups()` and references `RuntimeToolRegistry`-registered `is_write` (PreparedToolCall.spec) to determine parallel/serial execution (unregistered tools are rejected in the preparation phase via fail-closed)
⑤ Risk Classification & Approval `agent/tool_policy.py::classify_operation_type()` / `classify_risk()` — Priority: `approval_risk_rules` → `tool_safety_tiers` → operation-type classification (`tool_constants.py` frozensets first, then `RuntimeToolRegistry` for READ vs UNKNOWN)
⑥ Audit Logging           `agent/tool_audit.py` — Records `classify_operation_type()` result as `operation_type`
```

**Layers ③–⑤ reference different sources.** ③ is registry registration (ownership; drift detection only), ④ is batch execution parallel/serial control (`RuntimeToolRegistry` `is_write`), and ⑤ is approval risk assessment and audit classification. Missing a reference can cause each layer to drift individually. `agent/tool_policy.py::classify_operation_type()` evaluates in this order: (1) the `shared/tool_constants.py` frozensets `WRITE_TOOLS`, `MDQ_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, `CICD_WRITE_TOOLS`, `GIT_WRITE_TOOLS` give WRITE; (2) `DELETE_TOOLS` gives DELETE; (3) the shell execution tool set gives EXECUTE; (4) `GITHUB_WRITE_TOOLS` and `GITHUB_DANGEROUS_TOOLS` give API_WRITE; (5) any other tool is looked up in `RuntimeToolRegistry`: a registered tool whose `RuntimeTool` is a write tool gives WRITE, any other registered tool gives READ, and an unregistered tool or a missing registry gives UNKNOWN (fail closed, no static-registry fallback; ADR-003 Decision Detail #6/#8). Startup validation reports any tool whose `RuntimeTool` write attribute disagrees with the static sets (ADR-003 INV-03).

### Serialization mechanism integrated into a single scheduler

`agent/tool_runner.py::_execute_with_dag()` is the sole execution path, and all serialization decisions (tool-specific mandatory serialization via `ToolSpec.requires_serial`, resource-scope conflicts, and the batch-level `serial_tool_calls` setting) are made in `agent/tool_scheduler.py::build_execution_groups()` (phase construction + conflict graph + `force_serial` input):

| Source | Behavior |
|---|---|
| `ToolSpec.requires_serial` (individual tools. e.g., MDQ's `index_paths`/`refresh_index`, shell's `shell_run`) | Forms a solo serial phase as an in-place barrier |
| Overlapping `resource_scopes` (where at least one is `is_write=True`; unscoped writes use synthetic `"global:write"` scope) | Grouped as connected components in the conflict graph and serialized within the group |
| `ctx.cfg.tool.serial_tool_calls=True` → `force_serial=True` (batch-level input) | Bypasses all the above and forces individual serial phases for each call in order |

Parallel/serial determination relies solely on `PreparedToolCall.spec.is_write`.

---

## Reliable Sources for Routing

See [ADR-003](../10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md) for rationale and invariants.

---

## Tool Registry (`shared/tool_registry.py`)

Drift detection only; not used for routing. See [ADR-003](../10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md) for the distinction between routing authority and drift detection.

## Keywords

- mcp
- routing
- lifecycle
- ToolRouteResolver
- ToolRegistry
- tool dispatch
- routing drift
- startup_mode gate
- HALF_OPEN trial dispatch
