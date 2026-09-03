---
title: "Agent LLM and Streaming"
area: agent
tags:
  - agent
  - llm
  - streaming
related:
---
# Agent LLM and Streaming

Turn flow $\rightarrow$ [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)

## Purpose

Documenting the responsibilities of `LLMClient` and `RobustSSEParser`, the SSE streaming protocol, reconnection behavior, usage collection, partial completion processing, and runtime parameter generation.

## Design Intent

### LLMClient Objectives

`LLMClient` handles all HTTP communication with LLM endpoints. It is constructed within `AgentREPL.run()` and stored in `ctx.services.llm`.

Components are categorized as: Model, Endpoint, Authentication, and Streaming. See `shared/llm_client.py` for details.

### Hot-Reloadable Settings

`apply_config(**kwargs)` updates the following parameters without regenerating the instance: `temperature`, `max_tokens`, `max_retries`, `retry_base_delay`, `sse_heartbeat_timeout`, `sse_malformed_retry`, `sse_reconnect_max`, `stream_retry_on_heartbeat_timeout`, and `stream_retry_on_malformed_chunk`. Fields passed as `None` remain unchanged.

### Request Payload

`build_payload()` constructs a request dictionary including `messages`, `tools`, `temperature`, `max_tokens`, and `stream`. Tool definitions are retrieved from `AgentConfig.tool.tool_definitions`.

### Streaming Design Intent

`LLMClient.stream()` calls `LlmReconnectHandler.stream()`, which in turn calls `LlmSseStreamHandler.stream_once()` for each connection attempt. `stream_once()` performs the following:

1. POSTs with `stream=True`.
2. Reads byte streams via `asyncio.wait_for` (`sse_heartbeat_timeout`).
3. Passes byte streams to `RobustSSEParser.feed()`.
4. Invokes `on_token()` callback for each text delta.
5. Accumulates function call deltas in `tool_calls_map`.
6. Invokes `on_usage()` when a usage chunk is received.
7. Returns upon receiving the `[DONE]` SSE marker.

The `RobustSSEParser` implementation is in `shared/sse_parser.py`. The SSE chunk parsing logic is decoupled into `LlmSseHelpers` in `shared/llm_sse_helpers.py`.

### Partial Completion Persistence Rules

Handled by the orchestrator's transport error handler:

| Case | Action |
|---|---|
| Non-empty `partial_text` (failure during stream) | Save assistant message as `[INCOMPLETE: {kind}]` only to `session_diagnostics`. |
| Empty `partial_text` (failure before stream starts) | Pop the previous user message from history. Do not save an assistant message. |
| Tool execution failure | Append synthesized `tool` error message. Conversation continues. |

### Error Type Design

The `kind` of `LLMTransportError` is categorized as follows:

| Category | Description |
|---|---|
| `HTTP_STATUS_RETRYABLE` | HTTP 429 / 503 |
| `HTTP_STATUS_FATAL` | Other HTTP errors |
| `CONNECT_ERROR` | Connection failures |
| `READ_TIMEOUT` | Read timeouts |
| `HEARTBEAT_TIMEOUT` | No SSE event within `sse_heartbeat_timeout` seconds |
| `MALFORMED_SSE_FRAME` | Too many malformed SSE frames |
| `PREMATURE_EOF` | SSE stream ends earlier than expected content-length |

### Runtime Parameter Generation

| Parameter | Config Field | Via Hot-Reload |
|---|---|---|
| Temperature | `cfg.llm.llm_temperature` | `/set temperature <f>` or `/reload` |
| Max tokens | `cfg.llm.llm_max_tokens` | `/set max_tokens <n>` or `/reload` |
| Retry count | `cfg.llm.llm_max_retries` | `/reload` |
| Heartbeat timeout | `cfg.llm.sse_heartbeat_timeout` | `/reload` |
| Reconnect max | `cfg.llm.sse_reconnect_max` | `/reload` |

Compression uses fixed constants: `COMPRESS_TEMPERATURE=0.3`, `COMPRESS_MAX_TOKENS=300` (defined in `factory.py`; not hot-reloadable). Most other parameters are hot-reloadable via `/set` or `/reload`.

## Responsibility Boundary

### Reconnect Behavior (`LlmReconnectHandler.stream`, `shared/llm_reconnect.py`)

Retries `stream_once()` up to `sse_reconnect_max` times. Reconnection decision:

| Kind | Decision |
|---|---|
| `HEARTBEAT_TIMEOUT` | Follows `llm_stream_retry_on_heartbeat_timeout` flag |
| `MALFORMED_SSE_FRAME` | Follows `llm_stream_retry_on_malformed_chunk` flag |
| Others | Follows `LLMTransportError.retryable` |

**Boundary Condition:** If `content_parts` or `tool_calls_map` already contain partial content, or if the exception includes `partial_text`, a reconnection is NOT attempted; instead, an exception is immediately thrown. This prevents retrying a new request as a continuation of a partially generated assistant response.

Upon successful reconnection and final content delivery, `on_token("\n")` is called exactly once at the end.

### RobustSSEParser (`shared/sse_parser.py`)

A parser per connection (one instance per connection attempt).

Parser behavior:
- Blank lines and SSE comments update the last event timestamp (keepalive).
- Malformed JSON increments `stat_parse_errors`. Exceeding `sse_malformed_retry` raises `MALFORMED_SSE_FRAME`.
- `[DONE]` sets `is_done=True`.

## Key Constraints

### Partial Completion Isolation

Partially completed responses are not added to the conversation history; they are saved only to `session_diagnostics`.

### Retryable vs Fatal Semantics

HTTP status 429/503 are classified as `retryable=True` (`HTTP_STATUS_RETRYABLE`), while all other statuses are `retryable=False` (`HTTP_STATUS_FATAL`).

### Usage Statistical Limits

If the LLM endpoint returns a chunk containing a `usage` field, data is extracted from `prompt_tokens` and `completion_tokens` fields, and the `on_usage(prompt_tokens, completion_tokens)` callback is invoked. If no `usage` is returned, statistics remain `None`. `/context` displays estimates based on `chars // 4`.

## Operational Notes

- `LLMClient.call()` is used for non-streaming LLM calls (compression, title generation).
- `LLMClient.request_with_retry()` is a retry-enabled POST (only for HTTP 429/503 and `RequestError`) using exponential backoff.
- `LLMTransportError` carries `phase` (pre_stream/in_stream), `url`, `status_code`, `retryable`, `partial_text`, `detail`, and `stat_heartbeat_timeouts`.
- `UTF8_PARTIAL_DECODE_ERROR` and `PREMATURE_EOF` are clearly distinguished. `PREMATURE_EOF` is raised if the SSE stream ends before the expected `content-length`. `UTF8_PARTIAL_DECODE_ERROR` handles JSON decoding errors separately.

## Known Limitations

- Unknown

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_05_llm-and-streaming.md`

## Keywords

agent
llm
streaming
response
reconnect
transport-error
llm-client
