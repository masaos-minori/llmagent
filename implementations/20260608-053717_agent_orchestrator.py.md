# Implementation: agent/orchestrator.py — duplicate error handling reduction

## Goal

Remove the duplicate `LLMTransportError` catch in `_process_turn()` (lines 178–182). After the callback design change (Phase 3 step 12), the error is already handled in `_handle_llm_turn()` and `_process_turn` no longer needs its own catch.

## Scope

- `scripts/agent/orchestrator.py`
- Remove `except LLMTransportError` block in `_process_turn()` (lines 178–182).
- `_handle_llm_turn()` already catches `LLMTransportError` and returns `TurnResult(success=False, ..., error_kind=str(e))`.
- `_process_turn()` already handles `result.success == False` and extracts `error_kind`.

## Assumptions

- `_handle_llm_turn()` always catches `LLMTransportError` and returns a `TurnResult` (never raises it after the refactor).
- The `finally` block that restores `ctx.cfg.tool.allowed_tools` still executes correctly.
- Removing the catch does not change error propagation to `repl.py`.

## Implementation

### Target file

`scripts/agent/orchestrator.py`

### Procedure

1. Remove `from shared.llm_client import LLMTransportError` if it becomes unused after removal.
2. Remove the `except LLMTransportError as e:` block in `_process_turn()` (lines 178–182) — the try-finally structure remains:
   ```python
   try:
       # ... (no LLMTransportError catch)
   finally:
       ctx.cfg.tool.allowed_tools = original_allowed
   ```
3. Verify that `result.error_kind` from `_handle_llm_turn()` is already handled correctly on lines 175–176.
4. Run `ruff format`.
5. Run `mypy`.
6. Run `uv run pytest tests/test_orchestrator.py`.

### Method

Dead code removal from the except block.

## Validation plan

1. `uv run pytest tests/test_orchestrator.py` — pass.
2. `uv run pytest` full suite — no regressions.
3. `uv run ruff check scripts/agent/orchestrator.py` — no errors.
4. `uv run mypy scripts/agent/orchestrator.py` — no errors.
