# Implementation: H-4 — Remove ToolResultStore persistence from handle_partial_completion()

## Goal

Remove the `ctx.tool_result_store.store(...)` call and its wrapping `try/except` from
`handle_partial_completion()`. Partial-completion persistence is limited to
`session_diagnostics` (via `DiagnosticStore.save()` / `.save_partial_completion()`), which
already run unconditionally before the removed block.

## Scope

**Target**: `scripts/agent/llm_transport_errors.py`

**Out of scope**: `DiagnosticStore` implementation itself, `ctx.tool_result_store` field removal
from `AgentContext` (still used elsewhere), `stat_partial_completions` counter logic (unchanged),
`handle_non_partial_error()` (untouched — its `orjson` usage, if any, is a separate function).

## Assumptions

1. `diagnostic_store.save(...)` and `diagnostic_store.save_partial_completion(...)` (currently at
   lines 37-43) already run before the block being removed and have no dependency on it — they
   stay exactly as-is.
2. `ctx.services_required.llm.stat_partial_completions += 1` (line 59, after the removed block)
   is unaffected by removing the try/except above it.
3. `logger` (module logger) has other uses in this file (e.g. the final
   `logger.warning("Partial LLM completion saved: %s", e.kind)` call) — do not remove the import.

## Implementation

### Target file

`scripts/agent/llm_transport_errors.py`

### Procedure

#### Step 1: Read the current function in full

```python
def handle_partial_completion(
    e: LLMTransportError,
    ctx: AgentContext,
    diagnostic_store: DiagnosticStore,
) -> None:
    """Save partial text to diagnostic channel and tool_result_store."""
    incomplete_msg = f"{e.partial_text}\n[INCOMPLETE: {e.kind}]"
    diagnostic_store.save(ctx.session.session_id, "llm_transport_error", incomplete_msg)
    diagnostic_store.save_partial_completion(
        session_id=ctx.session.session_id,
        turn=ctx.stats.stat_turns,
        reason=e.kind,
        content_length=len(e.partial_text),
    )
    try:
        ctx.tool_result_store.store(
            session_id=ctx.session.session_id,
            turn=ctx.stats.stat_turns,
            tool_name="llm_partial_completion",
            args_masked="{}",
            full_text=e.detail or f"partial={len(e.partial_text)} chars",
            summary=f"[INCOMPLETE: {e.kind}]",
            is_error=True,
        )
    except (RuntimeError, OSError) as store_err:
        logger.warning(
            "ToolResultStore.store failed for partial completion: %s", store_err
        )
    ctx.services_required.llm.stat_partial_completions += 1
    logger.warning("Partial LLM completion saved: %s", e.kind)
```

(Confirm the exact `except` body wording and trailing lines with `grep -n -A 30
"def handle_partial_completion" scripts/agent/llm_transport_errors.py` before editing, since the
line numbers above are from the plan and should be re-verified against the live file.)

#### Step 2: Remove the try/except block and update the docstring

Replace the function body with:

```python
def handle_partial_completion(
    e: LLMTransportError,
    ctx: AgentContext,
    diagnostic_store: DiagnosticStore,
) -> None:
    """Save partial text to diagnostic channel only."""
    incomplete_msg = f"{e.partial_text}\n[INCOMPLETE: {e.kind}]"
    diagnostic_store.save(ctx.session.session_id, "llm_transport_error", incomplete_msg)
    diagnostic_store.save_partial_completion(
        session_id=ctx.session.session_id,
        turn=ctx.stats.stat_turns,
        reason=e.kind,
        content_length=len(e.partial_text),
    )
    ctx.services_required.llm.stat_partial_completions += 1
    logger.warning("Partial LLM completion saved: %s", e.kind)
```

### Method

- Pure deletion of the `try/except (RuntimeError, OSError)` block (7-15 lines depending on exact
  formatting); no new logic, no signature change.
- Function keeps its full signature `(e, ctx, diagnostic_store) -> None` — `ctx` stays a
  parameter since `ctx.session.session_id` and `ctx.stats.stat_turns` remain in use by the
  preserved diagnostic-store calls.

### Details

- `e.detail` (used only inside the removed `.store(...)` call as
  `e.detail or f"partial={len(e.partial_text)} chars"`) has no other reference in this function
  after the removal — confirm via grep that `LLMTransportError.detail` is not needed elsewhere in
  this file before considering any further cleanup (out of scope to touch the exception class
  itself either way).
- `ctx.tool_result_store` is not removed from `AgentContext` — only this one call site goes away.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check scripts/agent/llm_transport_errors.py` | 0 errors |
| Type check | `mypy scripts/` | no new errors |
| Grep (call removed) | `grep -n "tool_result_store" scripts/agent/llm_transport_errors.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_llm_partial_completion.py -v` | pass once the companion test doc's changes are applied (existing `test_partial_completion_writes_tool_result_store` will fail against this change until updated — see `implementations/*_test_llm_partial_completion.py.md`) |
| Tests (full) | `uv run pytest -v` | no new failures beyond the known test needing companion update |
| Pre-commit | `pre-commit run --all-files` | pass |

## Risks

- `tests/test_llm_partial_completion.py::test_partial_completion_writes_tool_result_store`
  directly asserts the removed call happened — it MUST be updated together with this change (see
  companion test doc). Implement both in the same commit to avoid a red test window.
