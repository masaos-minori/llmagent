## Goal

Replace weak RAG regression assertions with meaningful checks that detect ranking, fallback, semantic cache, and diagnostics regressions in `tests/test_rag_quality_regression.py`.

## Scope

**In-Scope**:
- Replace always-true assertions (`len(result.reranked) >= 0`) with meaningful expectations
- Add tests that distinguish `use_rrf=True` from `use_rrf=False` behavior
- Verify semantic cache hit behavior through diagnostics or cache state
- Verify embed failure fallback diagnostics, not only empty results

**Out-of-Scope**:
- Building a large benchmark suite
- Replacing unit tests with full evaluation metrics

## Assumptions

1. The test fixtures (3 known documents, fixed-vector mock embedder) are deterministic and suitable for regression testing
2. `result.reranked` is a list of hit objects with properties like `chunk_id`, `url`, `title`, `rrf_score` that can be asserted on
3. `result.result_source` indicates whether the result came from cache or pipeline

## Implementation

### Target file: tests/test_rag_quality_regression.py

**Procedure**: Replace weak assertions, add RRF vs no-RRF test, strengthen semantic cache and embed failure fallback tests.

**Method**: Modify test assertions in the RAG quality regression test file.

**Details**:
1. Replace always-true assertions:
   - Line 98: Replace `assert len(result.reranked) >= 0` with meaningful assertion (e.g., `assert len(result.reranked) > 0` or check for specific hit properties like `chunk_id`, `url`)
   - Line 106: Same replacement for no-RRF test
2. Strengthen semantic cache test:
   - Line 113: Replace `assert result2.result_source == "cache" or len(result2.reranked) >= 0` with assertion that validates cache hit specifically (remove always-true fallback)
3. Add RRF vs no-RRF distinguishable test:
   - Add new test that compares results between RRF and no-RRF modes for the same query
   - Assert on `rrf_score` presence/absence or ranking differences
4. Strengthen embed failure fallback test:
   - Enhance line 125 assertion to also verify diagnostic information is present (not just empty result)

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/test_rag_quality_regression.py | Verify no always-true assertions remain | Search for `>= 0` pattern in assertions | Zero always-true assertions |
| tests/test_rag_quality_regression.py | Verify all tests pass with current fixtures | Run pytest | All tests pass (no regressions in test suite) |
| tests/test_rag_quality_regression.py | Verify RRF/no-RRF distinction is testable | Check new test | Test compares results between modes |

## Risks

- **Risk**: Stricter assertions may fail if current fixtures don't produce expected results | **Likelihood**: Medium | **Mitigation**: Run tests after each assertion change; adjust fixture data if needed to ensure deterministic outcomes | False
