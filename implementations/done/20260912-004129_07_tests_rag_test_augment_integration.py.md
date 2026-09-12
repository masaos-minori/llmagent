# Implementation: tests/rag/test_augment_integration.py

## Goal

Correct `test_set_fetch_result_callback_called_with_result` (currently asserts the callback receives the string `"context"`) to mock `call_rag_service` with a `side_effect` that invokes `set_fetch_result` with a raw hit-dict list (matching `test_set_fallback_reason_callback_called`'s existing side-effect pattern in the same file), and assert `captured_results[0]` is the expected `TwoStageFetchResult`.

## Scope

- Modify `tests/rag/test_augment_integration.py` only.
- Correct the `test_set_fetch_result_callback_called_with_result` test's mock setup and assertion.
- This file is byte-identical to `tests/rag/test_augment_refiner.py` per the plan's Assumptions section — apply identical corrections.

## Assumptions

- `TwoStageFetchResult` is available via `from rag.models_data import TwoStageFetchResult` (already imported in the module? need to verify).
- The existing `test_set_fallback_reason_callback_called` test in the same file uses a `side_effect` pattern to invoke callbacks — use it as a reference.
- The current test mocks `call_rag_service` as a bare `MagicMock` returning a 3-tuple `(result, status_code, latency_ms)`.
- The test's `captured_results` list captures callback invocations — currently populated by the erroneous direct string call in `http_augment.py`'s `run()`.

## Design decisions

- Replace the bare `MagicMock` return value with a `side_effect` that constructs a `TwoStageFetchResult` and passes it to the captured callback — matches the existing `test_set_fallback_reason_callback_called` pattern.
- Use the same raw hit-dict structure that the RAG service would emit (confirmed in `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py:215`).

## Alternatives considered

- **Assert on the raw hit-dict list directly**: Would require changing the callback capture mechanism; more complex than needed since `TwoStageFetchResult` is the correct intermediate representation.
- **Remove the test entirely**: Not appropriate — the test validates a real behavior (callback invocation) that must be preserved, just with the correct argument type.

## Implementation

### Target file

`tests/rag/test_augment_integration.py`

### Procedure

1. Read the full test file to identify the exact location and current content of `test_set_fetch_result_callback_called_with_result`.
2. Modify the test's mock setup to use a `side_effect` that invokes `set_fetch_result` with a raw hit-dict list.
3. Change the assertion from `captured_results[0] == "context"` to `captured_results[0] == TwoStageFetchResult(...)`.

### Method

```python
# Step 1: Read the test file to find the exact test method

# Step 2: Modify the test's mock setup
# Current pattern (approximate):
#     with patch("rag.augment.call_rag_service") as mock_call:
#         mock_call.return_value = ("context", 200, 10.0)
#         # ... run augment ...
#         self.assertEqual(captured_results[0], "context")

# Corrected pattern:
#     mock_selected_hits = [{"id": "hit1", "score": 0.9}]
#     with patch("rag.augment.call_rag_service") as mock_call:
#         def set_side_effect(*args, **kwargs):
#             # Extract the set_fetch_result callback from kwargs or args
#             set_fetch_result = kwargs.get("set_fetch_result") or args[5] if len(args) > 5 else None
#             if set_fetch_result:
#                 set_fetch_result(mock_selected_hits)
#             return ("context", 200, 10.0)
#         mock_call.side_effect = set_side_effect
#         # ... run augment ...
#         expected = TwoStageFetchResult(
#             hits=mock_selected_hits,
#             min_score_applied=self.cfg.rag_min_score,
#             max_chunks_per_doc=self.cfg.max_chunks_per_doc,
#         )
#         self.assertEqual(captured_results[0], expected)
```

### Details

- Line numbers are approximate — verify against current source before applying changes.
- Need to read the actual test file to determine the exact mock setup for `call_rag_service` and how `set_fetch_result` is passed through the chain.
- The `side_effect` approach mirrors the existing `test_set_fallback_reason_callback_called` test's pattern in the same file.
- After editing this file, run `diff tests/rag/test_augment_integration.py tests/rag/test_augment_refiner.py` to confirm they remain byte-identical (per the plan's Assumptions section).

## Compatibility considerations

- **No breaking change for production code** — only test assertions are modified.
- The corrected assertions now match the actual type contract enforced by the production code changes.

## Security considerations

- No new security surface introduced. Only test assertions are modified.

## Rollback considerations

- Revert the mock setup and restore the original string-based assertion.
- If any test fails after correction, investigate whether the mock setup needs adjustment rather than reverting the assertion correction.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `test_set_fetch_result_callback_called_with_result` | Unit (corrected assertion) | `uv run pytest tests/rag/test_augment_integration.py::test_set_fetch_result_callback_called_with_result -q` | Test passes |
| Both duplicate test files | Unit (corrected assertion) | `uv run pytest tests/rag/test_augment_refiner.py tests/rag/test_augment_integration.py -q` | All tests pass including the corrected test in both files |
| Full regression | Integration | `uv run pytest tests/rag/ tests/agent/commands/test_agent_rag.py -q` | 576 passed, 0 skipped (baseline was 573 passed, 3 skipped) |

## Completion criteria

- [ ] `test_set_fetch_result_callback_called_with_result` mocks `call_rag_service` with a `side_effect` that invokes `set_fetch_result` with a raw hit-dict list.
- [ ] Assertion changed from `captured_results[0] == "context"` to `captured_results[0] == TwoStageFetchResult(hits=<raw hits>, ...)`.
- [ ] File remains byte-identical to `tests/rag/test_augment_refiner.py` after edits (verified via `diff`).
- [ ] All tests pass when executed individually and as part of the full suite.

## Out of scope

- Modifying `scripts/rag/pipeline_service.py` — handled by a separate implementation procedure document.
- Modifying `scripts/rag/http_augment.py` — handled by a separate implementation procedure document.
- Modifying `scripts/rag/augment.py` — handled by a separate implementation procedure document.
- Modifying `scripts/rag/pipeline.py` — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read test file to identify exact locations | Completed | — | — | Already applied
| 2 | Correct mock setup in test | Completed | — | — | Already applied
| 3 | Correct assertion in test | Completed | — | — | Already applied
| 4 | Run validation sequence (`rules/toolchain.md`) | Completed | — | — | Tests passed

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260911-132739_raghits01_http-mode-selected-hits-unparsed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-205352_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-004129
- **Related target files**: tests/rag/test_augment_integration.py
