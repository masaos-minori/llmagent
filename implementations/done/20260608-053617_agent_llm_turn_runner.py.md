# Implementation: agent/llm_turn_runner.py — callback removal

## Goal

Remove `on_turn_start` / `on_turn_end` callbacks from `LLMTurnRunner.__init__()` and `run()`. These callbacks are now managed directly by `Orchestrator._handle_llm_turn()`.

## Scope

- `scripts/agent/llm_turn_runner.py`
- Remove constructor parameters `on_turn_start` and `on_turn_end`.
- Remove internal storage `self._on_turn_start`, `self._on_turn_end`.
- Remove any invocations of these callbacks in `run()`.
- Keep `tracer` parameter (it's used for internal span instrumentation in `_span_ctx`).

## Assumptions

- No other callers pass `on_turn_start` / `on_turn_end` to `LLMTurnRunner` besides `Orchestrator` (grep to confirm).
- The callbacks are invoked in `run()` — need to check where and remove those calls.

## Implementation

### Target file

`scripts/agent/llm_turn_runner.py`

### Procedure

1. Remove `on_turn_start` and `on_turn_end` from `__init__` signature.
2. Remove `self._on_turn_start = on_turn_start` and `self._on_turn_end = on_turn_end`.
3. Read the `run()` method to find where callbacks are invoked and remove those lines.
4. Update the class docstring.
5. Run `ruff format`.
6. Run `mypy`.
7. Run `uv run pytest tests/test_llm_turn_runner.py`.

### Method

Dead parameter removal.

## Validation plan

1. `uv run pytest tests/test_llm_turn_runner.py` — pass.
2. `uv run ruff check scripts/agent/llm_turn_runner.py` — no errors.
3. `uv run mypy scripts/agent/llm_turn_runner.py` — no errors.
