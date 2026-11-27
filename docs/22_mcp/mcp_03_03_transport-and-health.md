---
title: "HttpTransport, McpServerHealthRegistry, and Tracing Correlation Keys"
area: mcp
tags:
  - mcp
  - transport
  - health-registry
related:
  - mcp_00_document-guide.md
  - mcp_03_01_dispatch-and-routing.md
  - mcp_03_02_tool-registry.md
  - mcp_03_04_tool-call-tracing-and-lifecycle.md
  - mcp_03_05_lifecycle-and-new-server.md
  - db_09_mcp_dedup_and_execution_snapshot.md
---

# HttpTransport, McpServerHealthRegistry, and Tracing Correlation Keys

## HttpTransport (`shared/http_transport.py`)

### HttpTransport

`HttpTransport` provides POST `/v1/call_tool` over httpx. `ToolTransportInvoker` instantiates and retains it; `ToolExecutor` only imports the `TransportError` type.

- If `cfg.auth_token` is not empty, `Authorization: Bearer <token>` is added.
- All transport-level failures (timeouts, non-2xx HTTP outside the tool-level set, malformed responses, exhaustion of retries) raise a `TransportError`; it never directly returns `is_error=True`.
- Transport error handlers catch `TransportError` and convert it to `ToolCallResult(error_type="transport")`.
- `set_session_id(session_id)` injects an `X-Session-Id` header into every request (via `ToolTransportInvoker`).
- **Retries:** Retries are performed on HTTP 429/502/503/504 and on non-timeout `httpx.RequestError` (e.g. connection errors). For side-effecting tools (`_WRITE_TOOLS`), the ambiguous classes — post-send `httpx.RequestError` and the statuses `502`/`503`/`504` — raise `TransportError` immediately (fail-closed, ADR-004); pre-send connection errors and `429` stay retryable. The number of attempts is bounded, the delay between attempts for retryable HTTP statuses increases exponentially, and no sleep follows the last attempt. Only the final result (success or `TransportError` after all retries exhausted) is recorded in the McpServerHealthRegistry. The `TransportError` message (`"[Retry exhausted] ..."`) includes the tool name, the last retryable HTTP status (if any), the last request-error cause (`last_error=<class>: <message>`, when a non-timeout `httpx.RequestError` was retried), and the attempt count, in that order; raw response bodies are not included.
- **Status classification:** `/v1/call_tool` responses with tool-level statuses `400/403/404/409/422` do NOT raise `TransportError`; they return `ToolCallResult(is_error=True, error_type="tool")` with the server's reason (`detail` or `result` body field, raw-text fallback for any other body) and count as health-registry successes (`record_success`), so repeated tool errors never cool the server down — tool-level outcomes are server-domain results, not transport faults. `401`, all `5xx`, timeouts, malformed bodies and retry exhaustion remain `TransportError` and record health failures; `401` deliberately stays transport so auth faults remain visible. The write-tool fail-closed gate on `502/503/504` (ADR-004) is unchanged.
- **Non-retryable errors:** HTTP timeouts (`httpx.TimeoutException`) and `HTTPStatusError` for status codes other than 429/502/503/504 and the tool-level set are propagated immediately without retries.
- **Tool-level vs. Transport-level errors:** Tool-level errors (`error_type == "tool"`) are treated as successful transport calls, triggering `record_success()` and incrementing the `stat_tool_errors` counter. Transport-level errors trigger `record_failure()` and increment the `stat_transport_errors` counter. Both counters are tracked independently.

### Idempotency Key Contract and Durable Dedup

`HttpTransport` carries one logical call id per logical tool call and sends it as the
`X-Idempotency-Key` header on every attempt (retries reuse the same key; they do not
re-issue it). The caller owns key generation: the agent assigns one stable id per logical
call (`context.call_id`, surfaced by `scripts/agent/tool_runner.py::_logical_call_id`) and the
transport forwards it verbatim — nothing is derived, because the old hash derivations collided
across callers. A side-effecting call dispatched without a logical call id is refused before
leaving the transport. The same byte-identical key reaches the dispatcher for that call across
retries, processes, and restarts, so a retried or re-sent side-effecting call is recognized by
server-side dedup.

Server side (`scripts/mcp_servers/dispatch.py`), a caller-supplied non-empty key drives the
dedup layers. For side-effecting tools the key feeds two layers:

- A bounded in-process fast-path overlay (`_duplicate_cache`, TTL/eviction: see
  [mcp_03_01](mcp_03_01_dispatch-and-routing.md)) that now serves as a cache in front of the
  durable store, not the durability mechanism itself.
- The durable dedup store in `mcp_dedup.sqlite` (`shared/mcp_dedup.py`), whose lease-held row
  states (`pending` / `completed` / `failed` / `interrupted`), acquisition vocabulary
  (`acquired`, `replay_completed`, `in_progress`, `contract_mismatch`,
  `reconciliation_required`, `outcome_unknown`, `replay_unavailable`), store start states
  (`first_initialization`, `healthy`, `lost`, `replaced`, `legacy_or_unverified`,
  `schema_mismatch`), replay decision table, retry classification, retention, and concurrency
  contract are documented in [db_09](../41_db/db_09_mcp_dedup_and_execution_snapshot.md).

Failure semantics at the dispatcher boundary: a key reused with different content (different
tool or arguments) is rejected as `error_type="idempotency_key_reused"` before dispatch, on both
the overlay and the durable row. A live lease held by another caller is refused as
`error_type="dedup_in_progress"`. An expired-lease or `interrupted` call is replayed only for
tools whose declared `retry_policy` is retryable (`same_logical_call_only` or
`reconcile_then_retry`; an expired `pending` lease goes through
the audited reconciliation step first); `non_retryable` tools, and terminal rows that cannot be
safely replayed (`replay_unavailable`, `outcome_unknown`), are refused with
`error_type="dedup_unreplayable"`. Store unavailability — including a store whose identity is
lost, replaced, legacy, or drifted and whose open is refused — never stalls retryable tools (the
call proceeds with an audited `dedup_state="store_error"` marker) but fails closed for
`non_retryable` tools (`error_type="dedup_store_error"`). Only real, successful, non-dry-run
results are cached; dry-run outcomes clear the key.
---

## McpServerHealthRegistry (`shared/mcp_health.py`)

The canonical and only import path is `shared/mcp_health.py`.

**State Transitions:**

``` text
HEALTHY ──(failure < threshold)──→ DEGRADED ──(failure × threshold)──→ UNAVAILABLE
   ▲                │                                                      │
   │            (record_success)                                (cooldown elapsed)
   │                │                                                      ↓
   └──(record_success)────────── HALF_OPEN (trial probe) ──────────────────┘
                                     │
                                   (failure)
                                     │
                                     ↓
                          UNAVAILABLE (cooldown reset)
```

| State | Condition |
|---|---|
| `HEALTHY` | No failures, or after a successful call |
| `DEGRADED` | number of failures < threshold |
| `UNAVAILABLE` | number of failures ≥ threshold; dispatch is blocked |
| `HALF_OPEN` | After the cooldown; allows one trial dispatch |

Semantics: `record_failure` increments the failure count (`HALF_OPEN` goes straight back to `UNAVAILABLE` with the cooldown reset); `record_success` resets the failure count and unavailable timestamp (`HALF_OPEN` goes to `HEALTHY`); `get_state` returns `HEALTHY` for unknown keys; `is_unavailable` returns `True` only while `UNAVAILABLE` and the cooldown has not elapsed, and transitions to `HALF_OPEN` as a side effect when the cooldown expires. Constructor parameters are `failure_threshold` and `half_open_cooldown_sec`; the cooldown is a fixed value, not exponential backoff.

**Shared Wiring (invariant):** one registry instance is created while the tool executor is built (`factory.py`) and shared by the writer (`ToolTransportInvoker`, holding the registry injected at construction via its `health_registry=` parameter and calling `record_failure`/`record_success`) and the readers (`AppServices.health_registry`, used by `McpStatusService.probe_all()` and dispatch gating through `is_unavailable()`). Because they hold the same object, transport failures are visible to dispatch gating and `/mcp status` without synchronization lag. Replacing or rebuilding the registry object (for example creating a second `McpServerHealthRegistry()`) would desynchronize writers and readers and break dispatch gating, so changes must keep a single shared instance.

---

## End-to-End Tool Call Tracing

Correlation keys (`X-Session-Id`, `X-Request-Id`, `server_key`, `tool_name`) are defined in [mcp_02_01](mcp_02_01_endpoints-and-transport.md#correlation-keys). To trace a single tool call, combine `X-Request-Id` (unique per call) and `X-Session-Id` (spans the entire session). The Agent audit record stores the server request id as `mcp_request_id`.

### Example Success Path

1. The LLM emits a tool call; `ToolRouteResolver` resolves `server_key` (for example `file_read`).
2. The Agent POSTs `/v1/call_tool` with `X-Session-Id`.
3. The server answers with an `X-Request-Id` and `is_error=false`.
4. The Agent builds `ToolCallResult(output, is_error=False, request_id, server_key)`.
5. `audit_tool_exec()` writes a `tool_exec` JSON-lines entry carrying `mcp_request_id`.
6. `McpServerHealthRegistry.record_success(server_key)` keeps the state `HEALTHY`.

The failure path is in [mcp_03_04](mcp_03_04_tool-call-tracing-and-lifecycle.md).

## Keywords

- mcp
- HttpTransport
- McpServerHealthRegistry
- health state
- retry
- correlation keys
- tool call tracing
- end-to-end tracing
- transport
- health-registry
