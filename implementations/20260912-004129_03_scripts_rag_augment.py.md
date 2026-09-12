# Implementation: scripts/rag/augment.py

## Goal

Retype `AugmentRefiner.__init__`'s `set_fetch_result` parameter back to `Callable[[TwoStageFetchResult], None]`; add a wrapper method that builds `TwoStageFetchResult` from raw hits plus `self._cfg.rag_min_score`/`self._cfg.max_chunks_per_doc`, forwarding it to `self._set_fetch_result` only when hits are non-empty; wire this wrapper into `HttpAugment(...)` construction in `run_http_augment()`.

## Scope

- Modify `scripts/rag/augment.py` only.
- Retype `AugmentRefiner.__init__`'s `set_fetch_result` parameter from `Callable[[str], None]` to `Callable[[TwoStageFetchResult], None]`.
- Add a new wrapper method in `AugmentRefiner` that constructs `TwoStageFetchResult` from raw hit-dict list + config values.
- Update `run_http_augment()` to pass this wrapper as the `set_fetch_result` argument instead of a bare lambda.

## Assumptions

- `TwoStageFetchResult` is available via `from rag.models_data import TwoStageFetchResult` (already imported in the module? need to verify).
- `self._cfg.rag_min_score` and `self._cfg.max_chunks_per_doc` exist on the `RagConfig` object passed to `AugmentRefiner.__init__`.
- The wrapper method should only forward to `self._set_fetch_result` when `selected_hits` is truthy (non-empty), implementing "do not overwrite `last_fetch_result` when hits are empty/absent."
- The existing `on_status` lambda in `run_http_augment()` (line 74) can remain unchanged — it passes `_` which shadows the parameter name but works correctly.

## Design decisions

- Create a dedicated wrapper method `_forward_fetch_result(selected_hits: list[dict[str, Any]])` rather than using inline lambdas — improves readability and makes the logic explicit.
- The wrapper checks `if selected_hits:` before constructing `TwoStageFetchResult` and calling `self._set_fetch_result` — this single check implements both "don't overwrite when empty" and "only construct when we have data."
- Use `dataclasses.replace` pattern for constructing `TwoStageFetchResult` since it's a frozen dataclass — direct instantiation is fine per `scripts/rag/models_data.py:93`.

## Alternatives considered

- **Inline the wrapper in `run_http_augment()`**: Would work but would make the constructor call harder to read and would duplicate the `if selected_hits` check across any future callers.
- **Pass `selected_hits` through `HttpAugment` directly**: Would require changes to `http_augment.py` to expose `selected_hits`, but the plan's design routes `selected_hits` through `_set_fetch_result` in `pipeline_service.py`, so `augment.py` just needs to wrap it.

## Implementation

### Target file

`scripts/rag/augment.py`

### Procedure

1. Add import for `TwoStageFetchResult` from `rag.models_data` (verify if already present).
2. Change `AugmentRefiner.__init__`'s `set_fetch_result` parameter type from `Callable[[str], None] | None` to `Callable[[TwoStageFetchResult], None] | None`.
3. Add a new private method `_forward_fetch_result(self, selected_hits: list[dict[str, Any]]) -> None` after the existing property methods.
4. Update `run_http_augment()`'s `HttpAugment(...)` construction to pass the wrapper method instead of a bare lambda.

### Method

```python
# Step 1: Add import (around line 23, alongside existing imports)
from rag.models_data import TwoStageFetchResult

# Step 2: Change AugmentRefiner.__init__ parameter type (line 47)
# Change from:
#     set_fetch_result: Callable[[str], None] | None = None,
# To:
#     set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,

# Step 3: Add new wrapper method (after line 112, after search_diagnostics setter)
async def _forward_fetch_result(
    self, selected_hits: list[dict[str, Any]]
) -> None:
    """Construct TwoStageFetchResult from raw hits and forward to the callback."""
    if selected_hits:
        fetch_result = TwoStageFetchResult(
            hits=selected_hits,
            min_score_applied=self._cfg.rag_min_score,
            max_chunks_per_doc=self._cfg.max_chunks_per_doc,
        )
        self._set_fetch_result(fetch_result)

# Step 4: Update HttpAugment construction in run_http_augment() (lines 69-75)
# Before:
#     http_aug = HttpAugment(
#         self._http,
#         rag_url,
#         auth_token=self._cfg.rag_auth_token or "",
#         set_fetch_result=lambda r: self._set_fetch_result(r),
#         set_fallback_reason=lambda _: self._set_fallback_reason(_),
#     )
# After:
#     http_aug = HttpAugment(
#         self._http,
#         rag_url,
#         auth_token=self._cfg.rag_auth_token or "",
#         set_fetch_result=self._forward_fetch_result,
#         set_fallback_reason=lambda _: self._set_fallback_reason(_),
#     )
```

### Details

- Line numbers are approximate — verify against current source before applying changes.
- The `_forward_fetch_result` method is async-compatible (can be called synchronously since it doesn't await anything internally).
- `TwoStageFetchResult` is a frozen dataclass — direct instantiation is correct (no mutation needed).
- The `min_score_applied` value comes from `self._cfg.rag_min_score` — this matches the in-process path's construction pattern documented in `scripts/rag/stage_lifecycle.py:136-140`.
- The `max_chunks_per_doc` value comes from `self._cfg.max_chunks_per_doc` — same source as above.

## Compatibility considerations

- **Breaking change**: The callback type changes from `Callable[[str], None]` to `Callable[[TwoStageFetchResult], None]`. All existing callers must be updated:
  - `scripts/rag/http_augment.py`: `HttpAugment.__init__`'s `set_fetch_result` parameter must be retyped to `Callable[[list[dict[str, Any]]], None] | None`.
  - Test files: fixtures like `_noop_fetch(r: TwoStageFetchResult)` in `tests/rag/test_rag_pipeline_service.py` already assume the corrected type.
- **No API contract change**: The HTTP endpoint (`POST /v1/call_tool`) is unchanged; only the client-side parsing of its response is modified.

## Security considerations

- No new security surface introduced. Constructing `TwoStageFetchResult` uses the same safe dataclass pattern used elsewhere in the codebase.
- No input validation added for `selected_hits` content — the dataclass `TwoStageFetchResult.hits` is typed `list[Any]` precisely to accept HTTP-mode's `list[dict]` shape without per-hit validation.

## Rollback considerations

- Revert the type annotation change and restore the original lambda in `run_http_augment()`.
- If the callback type change breaks an unexpected caller, revert to `Callable[[str], None]` and adjust the caller separately.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `AugmentRefiner.run_http_augment()` behavior | Unit (regression) | `uv run pytest tests/rag/test_augment_refiner.py tests/rag/test_augment_integration.py -q` | All tests pass including the corrected `test_set_fetch_result_callback_called_with_result` |
| Type correctness | Static | `uv run mypy scripts/rag/augment.py` | No new errors |
| Lint | Static | `uv run ruff check scripts/rag/augment.py` | 0 errors |
| Security | Static | `uv run bandit -r scripts/rag/augment.py -c pyproject.toml` | No new findings beyond pre-existing baseline |

## Completion criteria

- [ ] `AugmentRefiner.__init__`'s `set_fetch_result` parameter type changed to `Callable[[TwoStageFetchResult], None] | None`.
- [ ] New `_forward_fetch_result` method added that constructs `TwoStageFetchResult` from raw hits + config values and forwards only when hits are non-empty.
- [ ] `run_http_augment()` passes `self._forward_fetch_result` as the `set_fetch_result` argument instead of a bare lambda.
- [ ] No lint/type/security regressions introduced.

## Out of scope

- Modifying `scripts/rag/pipeline_service.py` — handled by a separate implementation procedure document.
- Modifying `scripts/rag/http_augment.py` — handled by a separate implementation procedure document.
- Modifying `scripts/rag/pipeline.py` — handled by a separate implementation procedure document.
- Adding or modifying tests — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Retype `AugmentRefiner.__init__`'s `set_fetch_result` parameter | Pending | — | — | |
| 2 | Add `_forward_fetch_result` wrapper method | Pending | — | — | |
| 3 | Wire wrapper into `run_http_augment()` | Pending | — | — | |
| 4 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260911-132739_raghits01_http-mode-selected-hits-unparsed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-205352_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-004129
- **Related target files**: scripts/rag/augment.py
