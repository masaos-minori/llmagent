# Implementation: tests/test_agent_factory.py — mock reference update

## Goal

Update `ServerLifecycleManager` mock references in `tests/test_agent_factory.py` to use `LifecycleManagerProtocol` or concrete manager mocks.

## Scope

- `tests/test_agent_factory.py`
- Mock setup and assertions related to lifecycle manager.

## Assumptions

- The factory's `_build_tool_executor()` now returns `LifecycleManagerProtocol` instead of `ServerLifecycleManager`.
- Test assertions on the return type may need updating.

## Implementation

### Target file

`tests/test_agent_factory.py`

### Procedure

1. Search for `ServerLifecycleManager` references in the test file.
2. Replace mock targets and assertions to align with the new `LifecycleManagerProtocol` return type.
3. If the tests verify `build_agent_context` result contains a lifecycle manager, update the type assertion.
4. Run `ruff format`.
5. Run `uv run pytest tests/test_agent_factory.py` — all pass.

### Method

Mock target update with minimal changes.

## Validation plan

1. `uv run pytest tests/test_agent_factory.py -v` — all tests pass.
2. `uv run ruff check tests/test_agent_factory.py` — no errors.
3. `uv run mypy tests/test_agent_factory.py` — no errors.
