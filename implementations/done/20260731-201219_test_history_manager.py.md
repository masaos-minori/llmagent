# Implementation Procedure: tests/test_history_manager.py

## Goal
Add regression tests to ensure that `HistoryManager.compress()` preserves messages when compression fails.

## Scope
- **In-Scope:**
  - Test case: `compress()` returns `None` from LLM call -> verify original messages are returned and `CompressResult.error` is set.
  - Test case: `compress()` raises `HistoryCompressionError` -> verify original messages are returned and `CompressResult.error` is set.
  - Test case: `compress()` returns `None` but `over_char` is True -> verify fallback truncation is triggered.
- **Out-of-Scope:**
  - Tests for existing functionality.

## Assumptions
1. `HistoryManager` can be instantiated with mocked HTTP client for testing.

## Design decisions
- Use `unittest.mock.AsyncMock` to simulate `httpx.AsyncClient` returning empty responses or raising errors.
- Use `unittest.mock.MagicMock` to simulate `HistorySelectionPolicy` if necessary.

## Alternatives considered
N/A

## Compatibility considerations
N/A

## Security considerations
N/A

## Rollback considerations
- Remove new test cases.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_history_manager.py` | Unit tests covering failure paths | `uv run pytest tests/test_history_manager.py` | All new tests pass |

## Out of scope
- Integration tests involving real LLM services.

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260731-085622_plan.md
- Source implementation procedure: N/A
- Generated at: 20260731-201219
- Related target files: tests/test_history_manager.py
