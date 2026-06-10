# Implementation: error_injection_service.py

## Goal

Add a module-level guard to ensure `ErrorInjectionService` is not instantiated in production paths, and document its test-only scope explicitly via a module-level warning.

## Scope

- Target: `scripts/agent/error_injection_service.py`
- `ErrorInjectionService` is currently called from `llm_turn_runner.py._handle_llm_error()` in production code — this must be documented as a deliberate design choice (it handles real `LLMTransportError` by injecting a synthetic tool message into history)
- No removal of production usage — the service IS a legitimate production pattern for mid-turn LLM failure handling, not just testing
- Add module docstring clarifying the production vs test-only scope
- Rename to avoid the "injection" naming suggesting test-only usage: no rename (out of scope per plan — plan says "policy を明示化・本番混在防止" which means document intent, not rename)

## Assumptions

1. `ErrorInjectionService.inject_mid_turn_error()` is called in production from `llm_turn_runner.py` for real `LLMTransportError` handling. This is intentional.
2. The "test-only" concern in the plan refers to any future "inject arbitrary error for testing" methods — those must not be added to this class without explicit scope control.
3. The current class has no test-only methods; the change is documentation only.

## Implementation

### Target file

`scripts/agent/error_injection_service.py`

### Procedure

1. Update module docstring to clarify: "Handles real `LLMTransportError` by converting it to a synthetic tool message in history. Not test-only — called in production by `llm_turn_runner.py`. Do not add test-specific error injection here; use a separate testing utility."
2. Add an `__all__ = ["ErrorInjectionService"]` declaration.
3. No logic changes.

### Method

Documentation-only change. No code modification.

### Details

```python
"""agent/error_injection_service.py
Converts a mid-turn LLMTransportError into a synthetic tool-result message
injected into conversation history, allowing the LLM to recover gracefully.

This is a production path called by llm_turn_runner.py, not a test utility.
Do not add test-specific error injection to this class.
"""
```

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/error_injection_service.py` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Tests | `uv run pytest tests/ -k "error_injection"` | all pass |
