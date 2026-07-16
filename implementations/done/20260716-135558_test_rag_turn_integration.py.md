# Implementation: tests/integration/test_rag_turn_integration.py (new — real `LLMTurnRunner` + RAG tool round-trip tests, F01–F05)

Source plan: `plans/20260716-135105_plan.md`

## Goal

Add the first tests in the repository to drive `LLMTurnRunner.run()`
through a real tool-call → tool-result → `ctx.conv.history` → next
`_stream_llm()` round-trip using a `respx`-mocked RAG tool HTTP response —
closing the gap left by `tests/integration/test_rag_llm_integration.py`'s
TC-C01–C10, none of which actually exercise `RagPipeline.augment()` or
`LLMTurnRunner.run()` together (confirmed by direct read during planning:
C01 mocks `HybridRetriever.search()` in isolation, C02 tests a bare
`str.replace()`, C04 only checks `hasattr(llm, "stat_retries")`, C05 wraps
its assertion in `except Exception: pass`).

## Scope

**In:**
- Create `tests/integration/test_rag_turn_integration.py` with 5 test
  functions (F01–F05, per the source plan's Design §2 table):
  1. `test_f01_rag_empty_result_turn_continues` — RAG tool returns
     `{"result": "", "is_error": false}`; `ctx.conv.history` gains a
     `role: "tool"` message with empty content; the turn loop continues
     (next `_stream_llm()` call is invoked, no abort, no exception).
  2. `test_f02_rag_tool_error_increments_error_count` — RAG tool returns
     `{"result": "DB open failed (RAG unavailable): ...", "is_error": true}`;
     `result.error_type == "tool"`; the error text lands in the tool
     message content; `ToolLoopGuard`'s consecutive-error counter
     increments per `llm_turn_runner.py:117-118`.
  3. `test_f03_sse_disconnect_after_rag_result_not_persisted_as_assistant` —
     an `LLMTransportError` (`httpx.RemoteProtocolError`) on the *second*
     `_stream_llm()` call (the one following a RAG tool result already in
     history) is raised, not retried (per `LlmReconnectHandler`'s
     documented "no reconnect on partial output" rule); `_handle_llm_error()`
     converts it to a `TurnResult` with `persist_as_assistant=False`; the
     already-appended RAG tool message is not rolled back.
  4. `test_f04_rag_injection_pattern_sanitization_boundary` —
     documents/confirms whether `sanitize_document()` is invoked inside
     `RagPipeline.augment()` (before the MCP tool response is formed) as
     opposed to anywhere in the `tool_runner.py` → `ctx.conv.history` path.
  5. `test_f05_mixed_success_and_timeout_in_same_round` — two RAG tool
     calls in one round, one times out (`httpx.TimeoutException`) and one
     succeeds; both results land in `ctx.conv.history` via
     `_collect_tool_result_msgs()`; the next loop iteration proceeds with
     the mixed-result history intact.

**Out:**
- Any modification to `tests/integration/test_rag_llm_integration.py`
  (TC-C01–C10) — read-only reference, not edited (per the source plan's
  Scope, the existing 4 files are not modified).
- Any modification to `tests/test_llm_turn_runner.py` — its `runner`
  fixture construction pattern is reused/mirrored, not imported directly
  unless it is trivially importable; if not, replicate the same
  construction approach in this new file.
- Any production code change (`scripts/agent/llm_turn_runner.py`,
  `scripts/rag/pipeline.py`, `scripts/rag/utils.py`) — test-only plan; F04
  is explicitly a documentation test (see Details), not a trigger for a
  sanitization-boundary code change.

## Assumptions

1. `tests/test_llm_turn_runner.py`'s existing `runner` fixture (per the
   Explore sub-agent's excerpt: `runner._ctx.services_required.llm.stream
   = AsyncMock(...)`) demonstrates the correct `MagicMock`-based
   `AgentContext` construction pattern for `LLMTurnRunner` — this new
   file's tests should follow the same construction style (a `MagicMock()`
   `ctx` with `services_required.llm.stream` and `services_required.tools`
   /`gateway` set up as needed), not a from-scratch `AgentContext`.
2. The tool-call round-trip path is: `LLMTurnRunner.run()` (lines 91-118
   per the Explore report) → `execute_all_tool_calls()`
   (`scripts/agent/tool_runner.py`) → `_collect_tool_result_msgs()`
   (`tool_runner.py:166-192`) appends `{"role": "tool", "tool_call_id":
   tc_id, "content": llm_text}` to `ctx.conv.history` → next loop
   iteration's `_stream_llm()` call sends the updated history. This exact
   chain (confirmed by the RAG-LLM Explore sub-agent's report) is what
   F01–F03/F05 must drive through, not a shortcut that skips
   `execute_all_tool_calls()`.
3. To make `execute_all_tool_calls()` route to a RAG-shaped tool response
   without a real `rag_pipeline` MCP server, `respx.mock()` must intercept
   at the same `httpx.AsyncClient` / `ToolExecutor` boundary already
   proven in `tests/integration/test_agent_mcp_integration.py` — reuse
   that file's `_make_http_executor` pattern (constructing a
   `McpServerConfig` + `ToolExecutor` with a pinned resolver), adapted so
   `ctx.services_required.tools` (or `.gateway`) is the constructed
   `ToolExecutor` instance, matching how `tool_runner.py`'s
   `execute_one_tool_call()` actually dispatches (per the MCP Explore
   report: `ctx.services_required.gateway.execute()` or
   `ctx.services_required.tools.execute()`).
4. For F03, the `respx` side-effect must be sequenced by call count
   (`nonlocal call_count`) exactly as already proven correct in
   `test_agent_mcp_integration.py`'s `test_a04_http_503_retry_then_success`
   /`test_a17_http_503_retry_then_success` — the *first* `_stream_llm()`
   call (initial user turn) must succeed and produce a tool_call for the
   RAG tool; the *second* call (after the tool result is appended) must
   raise the transport error. This requires the mocked LLM endpoint and
   the mocked RAG tool endpoint to be tracked with independent call
   counters if `respx.mock()` is scoped per-URL (verify `respx`'s
   multi-route behavior within one `with respx.mock(...)` block during
   implementation).
5. F04 is explicitly a documentation/discovery test per the source plan's
   Design §2 — its purpose is to state clearly, in its own assertion and
   docstring, which boundary sanitization actually occurs at (inside
   `RagPipeline.augment()`, per the RAG-LLM Explore report's finding that
   `sanitize_document()` is called only from `rag/stages/augment.py`'s
   `_format_chunks()`), not to assert that `tool_runner.py` sanitizes
   anything — if this test's premise turns out to be wrong upon direct
   read of `rag/stages/augment.py` and `tool_runner.py`, correct the
   assertion to match reality, not the plan's assumption.

## Implementation

### Target file

`tests/integration/test_rag_turn_integration.py` (new file)

### Procedure

1. Before writing any test, read `tests/test_llm_turn_runner.py`'s
   `runner` fixture construction in full, and
   `tests/integration/test_agent_mcp_integration.py`'s
   `_make_http_executor()` helper in full, to confirm the exact
   `MagicMock`/`ToolExecutor` wiring needed to combine both patterns in one
   test.
2. Create the file with a module docstring:
   ```python
   """tests/integration/test_rag_turn_integration.py

   Integration tests: RAG Pipeline <-> LLM Turn Runner, real round-trip
   (TC-F01 through TC-F05).

   Companion to test_rag_llm_integration.py (TC-C01-C10, which mocks
   HybridRetriever/LLMClient internals in isolation and never drives
   LLMTurnRunner.run() through an actual tool-call round-trip). These
   tests construct a real LLMTurnRunner with a MagicMock-based
   AgentContext (mirroring tests/test_llm_turn_runner.py's fixture style)
   and a respx-mocked RAG tool HTTP response (mirroring
   test_agent_mcp_integration.py's _make_http_executor pattern), so the
   full tool-call -> tool-result -> ctx.conv.history -> next LLM stream
   round-trip is exercised in one test process.
   """

   from __future__ import annotations

   import httpx
   import pytest
   import respx
   from unittest.mock import AsyncMock, MagicMock
   ```
3. Add a shared helper (module-level, not a fixture, matching
   `test_agent_mcp_integration.py`'s own non-fixture helper style) to
   construct a `ToolExecutor` pinned to a single RAG tool name, following
   `_make_http_executor()`'s exact pattern from that file (import
   `ToolExecutor`, `McpServerConfig`, `TransportType`; construct with a
   monkeypatched `_resolver.resolve`).
4. Add a shared helper to construct a `MagicMock`-based `ctx` for
   `LLMTurnRunner`, mirroring `tests/test_llm_turn_runner.py`'s `runner`
   fixture: `ctx.services_required.llm.stream = AsyncMock(...)`,
   `ctx.services_required.tools = <constructed ToolExecutor>`,
   `ctx.conv.history = [...]`, `ctx.cfg.tool.max_tool_turns = N`, and
   whatever else `LLMTurnRunner.run()` reads (confirm the full attribute
   set by re-reading `llm_turn_runner.py`'s `run()` method, lines 57-125
   per the Explore report, before finalizing).
5. Add `test_f01_rag_empty_result_turn_continues`:
   ```python
   @pytest.mark.asyncio
   async def test_f01_rag_empty_result_turn_continues() -> None:
       # respx-mock the RAG tool HTTP endpoint to return {"result": "", "is_error": false}
       # Construct ctx with services_required.llm.stream returning a tool_call
       #   for the RAG tool on round 1, then a plain-text answer on round 2.
       # Run runner.run() and assert:
       #   - a role="tool" message with content="" is in ctx.conv.history
       #   - runner.run() completes without raising
       #   - services_required.llm.stream was called twice (2 rounds)
       ...
   ```
   (Full body to be written against the confirmed `LLMTurnRunner.run()`
   contract from Implementation Step 1 — this is a structural placeholder
   showing the required assertions, not final code.)
6. Add `test_f02_rag_tool_error_increments_error_count` — same
   construction, RAG tool HTTP response is
   `{"result": "DB open failed (RAG unavailable): boom", "is_error": true}`;
   assert the tool message's content includes the error text and that
   whatever error-counting mechanism `llm_turn_runner.py` uses (confirm
   exact attribute/counter name by re-reading lines 91-118) reflects one
   error.
7. Add `test_f03_sse_disconnect_after_rag_result_not_persisted_as_assistant` —
   per Assumption 4's sequencing requirement: mock the LLM stream call to
   return a tool_call on the first invocation and raise
   `LLMTransportError`/`httpx.RemoteProtocolError` on the second; assert
   the resulting `TurnResult` (or equivalent return value of `run()`) has
   `persist_as_assistant=False` and that the RAG tool message added before
   the disconnect remains in `ctx.conv.history` (not popped/rolled back).
8. Add `test_f04_rag_injection_pattern_sanitization_boundary` — read
   `scripts/rag/stages/augment.py` and `scripts/mcp_servers/rag_pipeline/service.py`
   (or wherever the RAG MCP server formats its tool response) directly
   before writing this test; assert on whichever boundary is confirmed by
   that read (e.g. "an unsanitized injection string placed directly into
   the mocked HTTP response body is *not* further sanitized by
   `tool_runner.py`'s `_collect_tool_result_msgs()`" — i.e. sanitization,
   if any, already happened upstream inside the RAG pipeline itself before
   the HTTP response was formed, and this test's mock bypasses that layer
   entirely by construction, which the test's docstring must state
   explicitly to avoid misleading a future reader).
9. Add `test_f05_mixed_success_and_timeout_in_same_round` — two RAG tool
   calls in one assistant turn's `tool_calls` list; `respx` side-effect
   keyed on request body's tool name (matching
   `test_robustness_chaos.py`'s `test_3b2_multiple_error_types_in_same_turn`
   pattern for keying side-effects on `request.content`'s JSON `name`
   field); assert both results appear in `ctx.conv.history` and the next
   round proceeds.

### Method

Five async test functions combining `respx` HTTP mocking (RAG tool
endpoint) with a `MagicMock`-based `AgentContext` and a real
`LLMTurnRunner` instance — reusing two already-proven patterns
(`test_llm_turn_runner.py`'s ctx-mocking style,
`test_agent_mcp_integration.py`'s `respx`+`ToolExecutor` style) combined
for the first time in one test, rather than inventing a new mocking
approach.

### Details

- This file's tests are the highest-complexity new tests in the overall
  plan (per the source plan's Risk R-3) — budget extra review time for
  F03 specifically, and add an explicit `assert call_count == 2` (or
  equivalent visible sequencing assertion) rather than relying on
  implicit mock-call-order correctness.
- F04's docstring must state plainly what boundary it confirms — do not
  let it read as "proves tool_runner sanitizes RAG content" if the actual
  finding (per Assumption 5) is the opposite.
- Do not attempt to spin up a real `rag_pipeline` MCP server subprocess —
  all RAG-tool responses in this file are `respx`-mocked HTTP, consistent
  with the rest of the integration suite's HTTP-mocking convention.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New tests pass | `uv run pytest tests/integration/test_rag_turn_integration.py -v` | 5 passed |
| F03 sequencing verified | inspect test assertion for explicit `call_count == 2` (or equivalent) | present, not implicit |
| Flakiness check | `for i in {1..5}; do uv run pytest tests/integration/test_rag_turn_integration.py -v --timeout=30; done` | 5/5 clean runs |
| Lint | `uv run ruff check tests/integration/test_rag_turn_integration.py` | 0 errors |
| Type check | `uv run mypy tests/integration/test_rag_turn_integration.py` | no new errors |
| Existing suite unaffected | `uv run pytest tests/integration/test_rag_llm_integration.py tests/test_llm_turn_runner.py -v` | all existing tests still pass unchanged |
| Full integration suite | `uv run pytest tests/integration/ -v` | all 44 existing + all new tests (this file + companion 3 files) pass together |
