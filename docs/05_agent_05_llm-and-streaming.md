---
title: "Agent LLM and Streaming"
category: agent
tags:
  - agent
  - agent
  - llm
  - streaming
  - response
related:
  - 05_agent_00_document-guide.md
---

# Agent LLM and Streaming

- Turn flow → [05_agent_03_turn-processing-flow.md](05_agent_03_turn-processing-flow.md)

## Purpose

Document the `LLMClient` and `RobustSSEParser` responsibilities, the SSE streaming
protocol, reconnect behavior, usage collection, and partial completion handling.

---

## LLMClient (`shared/llm_client.py`)

`LLMClient` owns all HTTP communication with the LLM endpoint. It is constructed in
`AgentREPL.run()` and stored in `ctx.services.llm`.

### Constructor

```python
LLMClient(
    http: httpx.AsyncClient,
    max_retries: int = 3,
    retry_base_delay: float = 1.0,
    temperature: float = 0.2,
    max_tokens: int = 1024,
    on_token: Callable[[str], None] | None = None,     # called per SSE token
    on_usage: Callable[[int, int], None] | None = None, # (prompt_tokens, completion_tokens)
    sse_heartbeat_timeout: float = 30.0,
    sse_malformed_retry: int = 2,
    sse_reconnect_max: int = 1,
    llm_stream_retry_on_heartbeat_timeout: bool = True,
    llm_stream_retry_on_malformed_chunk: bool = False,
)
```

### Key methods

| Method | Description |
|---|---|
| `build_payload(history, tool_defs, stream=False)` | Build request dict with messages/tools/temperature/max_tokens |
| `async request_with_retry(url, payload)` | POST with exponential backoff retry (HTTP 429/503 + RequestError only) |
| `async call(url, history, tool_defs)` | Non-streaming LLM call (used for compression, title generation) |
| `async stream(url, history, tool_defs)` | SSE streaming with reconnect support; raises `LLMTransportError` on failure |

### Statistics attributes

| Attribute | Description |
|---|---|
| `stat_retries` | `request_with_retry` retry count |
| `stat_reconnects` | SSE reconnect count |
| `stat_heartbeat_timeouts` | HEARTBEAT_TIMEOUT event count |
| `stat_partial_completions` | Partial completion saved count |
| `stat_parse_errors` | Malformed SSE frame count (including skipped) |

---

## Payload Construction

`build_payload()` produces:

```json
{
  "messages": [...],
  "tools": [...],
  "tool_choice": "auto",
  "temperature": 0.2,
  "max_tokens": 1024,
  "stream": true
}
```

OpenAI-compatible format. Tool definitions come from `AgentConfig.tool.tool_definitions`
(loaded from `config/tools_definitions.toml`).

---

## SSE Streaming

`LLMClient.stream()` calls `LlmSseStreamHandler.stream_once()` which:
1. POSTs with `stream=True`
2. Reads bytes via `asyncio.wait_for` (`sse_heartbeat_timeout` timeout)
3. Feeds bytes to `RobustSSEParser.feed()`
4. Calls `on_token()` callback for each text delta
5. Accumulates `tool_calls_map` for function call deltas
6. Calls `on_usage()` when usage chunk arrives
7. Returns on `[DONE]` SSE marker

### RobustSSEParser (`shared/llm_client.py`)

Per-connection parser (1 instance per connection attempt).

| Method | Description |
|---|---|
| `feed(raw: bytes) -> (list[str], bool)` | Decode bytes; return payload strings + is_done flag |
| `check_heartbeat(url: str) -> None` | Raise `HEARTBEAT_TIMEOUT` if idle too long |

Parser behavior:
- Blank lines and SSE comments (`:`) update last event timestamp (keepalive)
- Malformed JSON increments `stat_parse_errors`; exceeding `sse_malformed_retry` raises `MALFORMED_SSE_FRAME`
- `[DONE]` sets `is_done=True`

---

## Reconnect Behavior

`stream()` wraps `LlmSseStreamHandler.stream_once()` in a retry loop:

```
LlmSseStreamHandler.stream_once() attempt 1
  → if LLMTransportError.retryable and reconnect count < sse_reconnect_max:
       reconnect (new RobustSSEParser, new HTTP request)
       append partial_text to content_parts (preserve accumulated output)
   → else: raise LLMTransportError with full partial_text
```

Reconnect conditions (controlled by config flags):
- `HEARTBEAT_TIMEOUT` → reconnect if `llm_stream_retry_on_heartbeat_timeout=True`
- `MALFORMED_SSE_FRAME` → reconnect if `llm_stream_retry_on_malformed_chunk=True`
- `HTTP_STATUS_RETRYABLE` (429/503) → always reconnect
- `HTTP_STATUS_FATAL` / `CONNECT_ERROR` → no reconnect

---

## LLMTransportError

```python
class LLMTransportError(Exception):
    kind: LLMErrorKind
    phase: Literal["pre_stream", "in_stream"]
    url: str
    status_code: int | None
    retryable: bool
    partial_text: str    # non-empty = partial completion occurred
    detail: str
```

`kind` values:

| Kind | Cause |
|---|---|
| `HTTP_STATUS_RETRYABLE` | HTTP 429 / 503 |
| `HTTP_STATUS_FATAL` | Other HTTP error |
| `CONNECT_ERROR` | Connection failure |
| `READ_TIMEOUT` | Read timeout |
| `HEARTBEAT_TIMEOUT` | No SSE event for `sse_heartbeat_timeout` seconds |
| `MALFORMED_SSE_FRAME` | Too many malformed frames |
| `PREMATURE_EOF` | Stream ended unexpectedly |

---

## Usage Collection

When the LLM endpoint returns a chunk with `usage` field:
- Usage data extracted from `prompt_tokens` and `completion_tokens` fields
- Calls `on_usage(prompt_tokens, completion_tokens)` callback
- Callback updates `ctx.stats.stat_input_tokens` and `ctx.stats.stat_output_tokens`
- Displayed in `/stats` output

If endpoint omits `usage`: stats remain `None`; `/context` shows `chars // 4` estimate.

---

## Partial Completion Persistence

Handled by orchestrator transport error handler:

| Case | Action |
|---|---|
| `partial_text` non-empty (in-stream fail) | Save `[INCOMPLETE: {kind}]` assistant message to `session_diagnostics` only |
| `partial_text` empty (pre-stream fail) | Pop last user message from history; no assistant message saved |
| Tool continuation fail | Add synthetic `tool` error message; conversation continues |

---

## LLM Generation Parameters at Runtime

| Parameter | Config field | Hot-reload via |
|---|---|---|
| Temperature | `cfg.llm.llm_temperature` | `/set temperature <f>` or `/reload` |
| Max tokens | `cfg.llm.llm_max_tokens` | `/set max_tokens <n>` or `/reload` |
| Retry count | `cfg.llm.llm_max_retries` | `/reload` |
| Heartbeat timeout | `cfg.llm.sse_heartbeat_timeout` | `/reload` |
| Reconnect max | `cfg.llm.sse_reconnect_max` | `/reload` |

Compression uses fixed constants: `COMPRESS_TEMPERATURE=0.3`, `COMPRESS_MAX_TOKENS=300`
(defined in `factory.py`; not hot-reloadable).

### Per-Use-Case LLM Generation Constants

| Use case | Location | Temperature | Max tokens |
|---|---|---|---|
| Normal LLM call | `cfg.llm.llm_temperature` / `cfg.llm.llm_max_tokens` | 0.2 (default) | 1024 (default) |
| History compression | `factory.py: COMPRESS_TEMPERATURE` / `COMPRESS_MAX_TOKENS` | 0.3 | 300 |
| Session title generation | `cfg.llm.title_llm_temperature` / `cfg.llm.title_llm_max_tokens` | 0.1 | 20 |
| MQE query expansion | `scripts/rag/pipeline.py: MQE_TEMPERATURE` / `MQE_MAX_TOKENS` | 0.6 | 300 |
| Cross-encoder rerank | `scripts/rag/pipeline.py: RERANK_TEMPERATURE` / `RERANK_MAX_TOKENS` | 0.0 | 256 |

Normal call parameters are hot-reloadable via `/set temperature` or `/reload`.
All other constants are compile-time fixed.

## Related Documents

- `agent`
- `llm`
- `streaming`

## Keywords

agent
llm
streaming
response
