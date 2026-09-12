# Implementation: scripts/rag/pipeline.py

## Goal

Pass a real `set_fetch_result` callback into `AugmentRefiner(...)`'s construction in `RagPipeline.__init__` that assigns `self.last_fetch_result`; ensure the callback satisfies the `Callable[[TwoStageFetchResult], None]` type required by `AugmentRefiner.__init__`.

## Scope

- Modify `scripts/rag/pipeline.py` only.
- Add a `set_fetch_result` keyword argument to the `AugmentRefiner(...)` constructor call on lines 115-121.
- The callback must assign `self.last_fetch_result` when called with a `TwoStageFetchResult` instance.

## Assumptions

- `TwoStageFetchResult` is available via `from rag.models_data import TwoStageFetchResult` (already imported in the module — confirmed at line 45).
- `self.last_fetch_result` is typed `TwoStageFetchResult | None` (confirmed at line 85).
- The callback should be a simple assignment lambda: `lambda fr: setattr(self, "last_fetch_result", fr)` or a bound method.
- When `augment_refiner` is passed in via constructor injection (line 112-113), no additional wiring is needed — the injected instance already has its own `set_fetch_result` callback.

## Design decisions

- Use a lambda expression `lambda fr: setattr(self, "last_fetch_result", fr)` rather than a named method — keeps the change minimal and localized.
- Only wire the callback when constructing the default `AugmentRefiner` (the `else` branch at line 114); when `augment_refiner` is provided externally, the caller is responsible for their own callback wiring.

## Alternatives considered

- **Named method on `RagPipeline`**: Would make the callback more readable but adds unnecessary boilerplate for a single-line assignment.
- **Direct attribute assignment inside `augment()`**: Would require passing `last_fetch_result` through the entire augment chain, which contradicts the plan's design of using the callback mechanism.

## Implementation

### Target file

`scripts/rag/pipeline.py`

### Procedure

1. Verify `TwoStageFetchResult` is already imported (confirmed at line 45: `from rag.models_data import TwoStageFetchResult`).
2. In `RagPipeline.__init__`, add `set_fetch_result` keyword argument to the `AugmentRefiner(...)` constructor call on lines 115-121.

### Method

```python
# Step 1: Verify import exists (line 45)
# Already present: from rag.models_data import TwoStageFetchResult
# No action needed.

# Step 2: Update AugmentRefiner construction (lines 115-121)
# Before:
#     else:
#         self._augment_refiner = AugmentRefiner(
#             http=self._http,
#             cfg=self._cfg,
#             on_status=self._on_status,
#             search_diagnostics=self.last_search_diagnostics,
#             llm=self._llm,
#         )
# After:
#     else:
#         self._augment_refiner = AugmentRefiner(
#             http=self._http,
#             cfg=self._cfg,
#             on_status=self._on_status,
#             set_fetch_result=lambda fr: setattr(self, "last_fetch_result", fr),
#             search_diagnostics=self.last_search_diagnostics,
#             llm=self._llm,
#         )
```

### Details

- Line numbers are approximate — verify against current source before applying changes.
- The lambda captures `self` from the enclosing scope, so it correctly refers to the `RagPipeline` instance.
- `setattr(self, "last_fetch_result", fr)` is used instead of direct attribute access (`self.last_fetch_result = fr`) because the latter would fail if `last_fetch_result` is a property without a setter (unlikely given line 85 shows it as a plain attribute, but `setattr` is safer).
- When `augment_refiner` is injected externally (line 112-113), no callback is wired here — the external caller is responsible.

## Compatibility considerations

- **Breaking change**: The callback type changes from `Callable[[str], None]` to `Callable[[TwoStageFetchResult], None]`. All existing callers must be updated:
  - `scripts/rag/http_augment.py`: `HttpAugment.__init__`'s `set_fetch_result` parameter must be retyped to `Callable[[list[dict[str, Any]]], None] | None`.
  - `scripts/rag/augment.py`: `AugmentRefiner.__init__`'s `set_fetch_result` parameter must be retyped to `Callable[[TwoStageFetchResult], None] | None`.
  - Test files: fixtures like `_noop_fetch(r: TwoStageFetchResult)` in `tests/rag/test_rag_pipeline_service.py` already assume the corrected type.
- **No API contract change**: The HTTP endpoint (`POST /v1/call_tool`) is unchanged; only the client-side parsing of its response is modified.

## Security considerations

- No new security surface introduced. The lambda simply assigns an attribute — no I/O or side effects.
- No input validation added for `TwoStageFetchResult` content — the dataclass is constructed upstream with validated inputs.

## Rollback considerations

- Revert the callback addition and restore the original `AugmentRefiner(...)` constructor call.
- If the callback type change breaks an unexpected caller, revert to `Callable[[str], None]` and adjust the caller separately.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `RagPipeline.augment()` behavior | Unit (regression) | `uv run pytest tests/rag/test_rag_http_mode.py tests/rag/test_pipeline_http_result_kind.py -q` | All tests pass (baseline: all currently passing) |
| Full regression | Integration | `uv run pytest tests/rag/ tests/agent/commands/test_agent_rag.py -q` | 576 passed, 0 skipped (up from 573 passed, 3 skipped) |
| Type correctness | Static | `uv run mypy scripts/rag/pipeline.py` | No new errors |
| Lint | Static | `uv run ruff check scripts/rag/pipeline.py` | 0 errors |
| Security | Static | `uv run bandit -r scripts/rag/pipeline.py -c pyproject.toml` | No new findings beyond pre-existing baseline |

## Completion criteria

- [ ] `AugmentRefiner(...)` construction in `RagPipeline.__init__` includes `set_fetch_result=lambda fr: setattr(self, "last_fetch_result", fr)`.
- [ ] Callback is only wired in the default `AugmentRefiner` construction path (not when `augment_refiner` is injected).
- [ ] No lint/type/security regressions introduced.
- [ ] Full regression test suite passes with expected count (576 passed, 0 skipped).

## Out of scope

- Modifying `scripts/rag/pipeline_service.py` — handled by a separate implementation procedure document.
- Modifying `scripts/rag/http_augment.py` — handled by a separate implementation procedure document.
- Modifying `scripts/rag/augment.py` — handled by a separate implementation procedure document.
- Adding or modifying tests — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `set_fetch_result` callback to `AugmentRefiner(...)` construction | Pending | — | — | |
| 2 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Related target files**: scripts/rag/pipeline.py
