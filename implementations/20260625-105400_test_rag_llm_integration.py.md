# tests/integration/test_rag_llm_integration.py — RAG Pipeline <-> LLM Turn Runner tests

**Plan:** `plans/20260625-095157_plan.md` (req #71)
**Target:** `tests/integration/test_rag_llm_integration.py` (new file)

## Priority: P2 (High)

## Test cases to implement

- **TC-C01**: RAG returns empty results — LLM turn runs without RAG context; no error
- **TC-C02**: RAG returns malformed text — `MemoryInjectionService` handles null bytes; LLM gets sanitized text
- **TC-C03**: RAG embedding fails during ingestion — entry stored without embedding; `stat_embed_skip += 1`; no exception
- **TC-C04**: LLM SSE stream disconnects mid-response — `PartialCompletion`; content stored to `tool_results`; `stat_partial_completions += 1`
- **TC-C05**: LLM SSE stream sends `[DONE]` immediately — empty response handled
- **TC-C06**: LLM returns invalid JSON for tool call — `ToolArgumentsDecodeError` raised
- **TC-C07**: `ToolLoopGuard` fires on repeated identical tool — `TurnResult(action="fail", reason="tool_loop_guard")`
- **TC-C08**: `ToolLoopGuard` allows different args — guard does NOT fire
- **TC-C09**: LLM rate-limited (429) — retry with exponential backoff; succeeds on 2nd attempt
- **TC-C10**: RAG pipeline MCP server unavailable — transport error in tool result; turn continues

## Key mocking approach

- LLM SSE stream: monkeypatch `LLMClient.complete()` with async generator (see plan §1c)
- RAG: mock `HybridRetriever.search()` return value
- LLM partial disconnect: raise `httpx.RemoteProtocolError` after N tokens

## Partial completion test pattern (TC-C04)

```python
async def _partial_stream(tokens):
    for t in tokens:
        yield {"type": "content", "delta": t}
    raise httpx.RemoteProtocolError("peer disconnected", request=None)
```

## Validation

```
uv run pytest tests/integration/test_rag_llm_integration.py -v --timeout=30
```
