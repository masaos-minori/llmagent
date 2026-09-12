# Implementation: scripts/rag/http_augment.py

## Goal

Retype `HttpAugment.__init__`'s `set_fetch_result` parameter from `Callable[[str], None]` to `Callable[[list[dict[str, Any]]], None]`; remove the incorrect direct `self._set_fetch_result(result)` call at the end of `run()` that passes the augmented context string.

## Scope

- Modify `scripts/rag/http_augment.py` only.
- Retype `HttpAugment.__init__`'s `set_fetch_result` parameter annotation.
- Remove lines 120-121 in `HttpAugment.run()` that call `self._set_fetch_result(result)` with the augmented context string.

## Assumptions

- The callback type change from `Callable[[str], None]` to `Callable[[list[dict[str, Any]]], None]` does not break any other callers (confirmed via repo-wide `rg` search — only the 7 test files enumerated in the plan reference these symbols).
- Removing the `self._set_fetch_result(result)` call will not cause any side effects because the callback should receive `selected_hits` (raw hit-dict list), not the augmented context string.
- The `_set_fetch_result` attribute is set in `__init__` and used only within `run()` — no other method references it.

## Design decisions

- Simply delete the two lines (120-121) rather than replacing them with a corrected call — the callback should receive `selected_hits`, which is passed through from `pipeline_service.py` via the chain, not the context string.
- Retype only the `set_fetch_result` parameter in `__init__`; the internal `_set_fetch_result` attribute gets its type inferred from the constructor parameter.

## Alternatives considered

- **Replace the string call with a `selected_hits` call**: Would require passing `selected_hits` through `HttpAugment` explicitly, but the plan's design routes `selected_hits` through `_set_fetch_result` in `pipeline_service.py`, so `HttpAugment` just needs to pass it through unchanged.
- **Keep the string call and add both callbacks**: Would complicate `HttpAugment` unnecessarily — the plan's design separates concerns: `pipeline_service.py` handles `selected_hits`, `augment.py` handles `TwoStageFetchResult` construction.

## Implementation

### Target file

`scripts/rag/http_augment.py`

### Procedure

1. Add import for `Any` from `typing` (needed for the new type annotation).
2. Change `HttpAugment.__init__`'s `set_fetch_result` parameter type from `Callable[[str], None] | None` to `Callable[[list[dict[str, Any]]], None] | None`.
3. Delete lines 120-121 in `HttpAugment.run()`:
   ```python
   # Call user-provided callbacks after determining result
   if result is not None:
       self._set_fetch_result(result)
   elif result is None:
       self._set_fallback_reason(http_fallback_reason)
   ```
   Keep only the `elif result is None` branch (the fallback reason callback).

### Method

```python
# Step 1: Add import (around line 8, alongside existing imports)
from typing import Any

# Step 2: Change HttpAugment.__init__ parameter type (line 66)
# Change from:
#     set_fetch_result: Callable[[str], None] | None = None,
# To:
#     set_fetch_result: Callable[[list[dict[str, Any]]], None] | None = None,

# Step 3: Delete lines 120-121 in HttpAugment.run()
# Before (lines 119-123):
#     # Call user-provided callbacks after determining result
#     if result is not None:
#         self._set_fetch_result(result)
#     elif result is None:
#         self._set_fallback_reason(http_fallback_reason)
# After:
#     if result is None:
#         self._set_fallback_reason(http_fallback_reason)
```

### Details

- Line numbers are approximate — verify against current source before applying changes.
- The `self._set_fallback_reason(http_fallback_reason)` call on the `elif result is None` branch must be preserved — it serves a different purpose (recording why the fallback occurred).
- The `if result is not None` branch that called `self._set_fetch_result(result)` must be removed entirely — the context string is not what the callback expects.

## Compatibility considerations

- **Breaking change**: The callback type changes from `Callable[[str], None]` to `Callable[[list[dict[str, Any]]], None]`. All existing callers must be updated:
  - `scripts/rag/pipeline_service.py`: `call_rag_service`'s `set_fetch_result` parameter must be retyped to `Callable[[list[dict[str, Any]]], None] | None`.
  - Test files: fixtures like `_noop_fetch(r: TwoStageFetchResult)` in `tests/rag/test_rag_pipeline_service.py` already assume the corrected type.
- **No API contract change**: The HTTP endpoint (`POST /v1/call_tool`) is unchanged; only the client-side parsing of its response is modified.

## Security considerations

- No new security surface introduced. Removing the erroneous callback invocation eliminates a potential `AttributeError` in downstream code that accesses `fetch.hits`/`fetch.min_score_applied` on `last_fetch_result` (as documented in `scripts/rag/diagnostics.py:99-106`).

## Rollback considerations

- Revert the type annotation change and restore the deleted `self._set_fetch_result(result)` call.
- If the callback type change breaks an unexpected caller, revert to `Callable[[str], None]` and adjust the caller separately.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `HttpAugment.run()` behavior | Unit (regression) | `uv run pytest tests/rag/test_augment_refiner.py tests/rag/test_augment_integration.py -q` | All tests pass including the corrected `test_set_fetch_result_callback_called_with_result` |
| Type correctness | Static | `uv run mypy scripts/rag/http_augment.py` | No new errors |
| Lint | Static | `uv run ruff check scripts/rag/http_augment.py` | 0 errors |
| Security | Static | `uv run bandit -r scripts/rag/http_augment.py -c pyproject.toml` | No new findings beyond pre-existing baseline (B107 on `auth_token: str = ""` default) |

## Completion criteria

- [ ] `HttpAugment.__init__`'s `set_fetch_result` parameter type changed to `Callable[[list[dict[str, Any]]], None] | None`.
- [ ] Lines 120-121 (`self._set_fetch_result(result)` call) removed from `HttpAugment.run()`.
- [ ] `self._set_fallback_reason(http_fallback_reason)` call preserved on the `result is None` branch.
- [ ] No lint/type/security regressions introduced.

## Out of scope

- Modifying `scripts/rag/pipeline_service.py` — handled by a separate implementation procedure document.
- Modifying `scripts/rag/augment.py` — handled by a separate implementation procedure document.
- Modifying `scripts/rag/pipeline.py` — handled by a separate implementation procedure document.
- Adding or modifying tests — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Retype `HttpAugment.__init__`'s `set_fetch_result` parameter | Pending | — | — | |
| 2 | Remove incorrect `self._set_fetch_result(result)` call in `run()` | Pending | — | — | |
| 3 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260911-132739_raghits01_http-mode-selected-hits-unparsed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-205352_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-004129
- **Related target files**: scripts/rag/http_augment.py
