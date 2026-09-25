# Fix logical contradiction in RAG parse error handling (ADR-010 compliance)

## Priority
Medium

## Summary
Fix a logical inconsistency in `scripts/rag/pipeline_service.py` where a fallback reason is reported even though no fallback is triggered during a JSON parse error.

## Background
According to **ADR-010 (Decision 9)**, parsing errors in the RAG service response should be treated as empty results (`""`) and must NOT trigger an in-process fallback. This design ensures that technical failures (like connection timeouts) are distinguished from valid empty search results, preventing unnecessary fallback operations.

## Problem
In `scripts/rag/pipeline_service.py`, the `call_rag_service` function handles `ValueError` (raised during JSON parsing) as follows:
```python
except ValueError as e:
    logger.warning(...)
    _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}") # <--- Logical Error
    return "", None, 0.0
```
While returning `""` correctly prevents the fallback (as seen in the return value), calling `_set_fallback_reason` is logically incorrect because no fallback actually occurred. This creates misleading observability data, where "fallback reasons" are logged for events that did not result in a fallback.

## Reason for Change
To align the implementation strictly with ADR-010 and ensure that observability metrics/logs accurately reflect system behavior. Reporting a fallback reason without a fallback is a semantic error in the logging/metrics logic.

## Implementation Intent
Remove the call to `_set_fallback_reason` within the `ValueError` exception block in `scripts/rag/pipeline_service.py`.

## Target Files or Areas
* `scripts/rag/pipeline_service.py`
* `tests/rag/test_rag_pipeline_service.py`

## Required Changes
* Remove `_set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")` from the `ValueError` handler in `scripts/rag/pipeline_service.py`.
* Update `tests/rag/test_rag_pipeline_service.py` to assert that the fallback reason callback is not called when a JSON parse error occurs.

## Constraints
Must not break existing successful response handling or other error types (4xx/5xx) that should trigger fallback.

## Acceptance Criteria
* `call_rag_service` returns `("", None, 0.0)` on JSON parse error.
* No fallback reason is passed to the `set_fallback_reason` callback on JSON parse error.
* Automated tests pass.

## Testing Expectations
Unit test in `tests/rag/test_rag_pipeline_service.py` verifying that `set_fallback_reason` is not invoked upon receiving malformed JSON.

## Documentation Impact
No changes to core documentation required, but this resolves NC-036.

## Out of Scope
Changing the actual fallback policy (which is already correct per ADR).

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
In `scripts/rag/pipeline_service.py`, find the `except ValueError as e:` block inside `call_rag_service`. Remove the line that calls `_set_fallback_reason`. Then, update `tests/rag/test_rag_pipeline_service.py` to ensure that when a mock response is invalid JSON, the `set_fallback_reason` callback is not executed.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-120000
- **Related target files**: `scripts/rag/pipeline_service.py`, `tests/rag/test_rag_pipeline_service.py`
