# orchestrator.py — save partial completions to DiagnosticStore

**Plan:** `plans/20260625-094407_plan.md` (req #65)
**Target:** `scripts/agent/orchestrator.py`

## What to change

`_handle_partial_completion()` at lines 483-510. Currently saves to `self._diagnostic_store`
via generic `save()` (for `"llm_transport_error"` kind) and to `tool_result_store`.

Add a call to `save_partial_completion()` using the canonical kind `"partial_completion"`:

**After the existing `self._diagnostic_store.save(...)` call (line 490-492):**

```python
    def _handle_partial_completion(
        self,
        e: LLMTransportError,
        ctx: AgentContext,
    ) -> None:
        """Save partial text to diagnostic channel and tool_result_store."""
        incomplete_msg = f"{e.partial_text}\n[INCOMPLETE: {e.kind}]"
        self._diagnostic_store.save(
            ctx.session.session_id, "llm_transport_error", incomplete_msg
        )
        # NEW: also save as canonical partial_completion diagnostic
        self._diagnostic_store.save_partial_completion(
            session_id=ctx.session.session_id,
            turn=ctx.stats.stat_turns,
            reason=e.kind,
            content_length=len(e.partial_text),
        )
        try:
            ctx.tool_result_store.store(...)
        ...
```

Note: `self._diagnostic_store` is already a `DiagnosticStore` instance on `Orchestrator`.
The new method call follows immediately after the existing `save()` call.

## Validation

```
ruff check scripts/agent/orchestrator.py
mypy scripts/agent/orchestrator.py
```
