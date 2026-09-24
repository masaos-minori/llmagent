## Goal

Add tests asserting 401/403 errors do NOT trigger in-process fallback in `tests/rag/test_rag_pipeline_service.py`.

## Scope

- **In-Scope**: Adding a new test function `test_401_403_no_fallback()` that asserts 401/403 responses do NOT trigger in-process fallback.
- **Out-of-Scope**: Modifying existing tests, adding tests for non-auth 4xx errors (these already exist), changing the test infrastructure.

## Assumptions

- The `call_rag_service()` function will return `(None, status_code, 0.0)` for 401/403 errors (as specified in REQ-001).
- The existing test pattern uses `pytest` with `unittest.mock.patch` for mocking HTTP responses.
- The `tests/rag/` directory exists and contains related test files.

## Design decisions

- Use `pytest` with `unittest.mock.patch` to mock the HTTP response, following the existing test pattern in the same file.
- Test both 401 and 403 separately to ensure each status code is handled correctly.
- Assert that the returned result is `None` but the caller should NOT trigger in-process fallback (verified by checking that `set_fallback_reason` is called with `"http_auth_error"` instead of `"http_client_error"`).

## Alternatives considered

- Testing via integration with a real HTTP server: rejected because it adds unnecessary complexity and flakiness; unit-level mocking is sufficient for this assertion.
- Combining 401 and 403 into a single parametrized test: rejected because separate tests provide clearer failure messages when debugging.

## Implementation

### Target file

`tests/rag/test_rag_pipeline_service.py`

### Procedure

1. Find the existing `test_4xx_returns_none_no_retry` test in `tests/rag/test_rag_pipeline_service.py`
2. Add a new test function `test_401_403_no_fallback()` after the existing 4xx test
3. The new test should assert that 401/403 responses do NOT trigger in-process fallback

### Method

Use Edit tool to append the new test function after the existing 4xx test.

### Details

#### REQ-004: New test function

**After the existing `test_4xx_returns_none_no_retry` test:**

```python
@pytest.mark.asyncio
async def test_401_403_no_fallback():
    """Assert that 401/403 errors do NOT trigger in-process fallback."""
    # Arrange
    http = AsyncMock()
    rag_url = "http://localhost:8081"
    
    # Test 401 Unauthorized
    resp_401 = Mock()
    resp_401.status_code = 401
    resp_401.raise_for_status.side_effect = httpx.HTTPStatusError("Unauthorized", request=Mock(), response=resp_401)
    http.post.return_value = resp_401
    
    set_fallback_reason_calls = []
    set_fetch_result_calls = []
    
    result, status_code, latency_ms = await call_rag_service(
        http,
        rag_url,
        "test query",
        "history context",
        auth_token="token",
        set_fetch_result=lambda fr: set_fetch_result_calls.append(fr),
        set_fallback_reason=lambda reason: set_fallback_reason_calls.append(reason),
    )
    
    # Assert 401 does not trigger fallback
    assert result is None
    assert status_code == 401
    assert len(set_fallback_reason_calls) == 1
    assert set_fallback_reason_calls[0] == "http_auth_error: 401"
    
    # Test 403 Forbidden
    resp_403 = Mock()
    resp_403.status_code = 403
    resp_403.raise_for_status.side_effect = httpx.HTTPStatusError("Forbidden", request=Mock(), response=resp_403)
    http.post.return_value = resp_403
    
    set_fallback_reason_calls.clear()
    
    result, status_code, latency_ms = await call_rag_service(
        http,
        rag_url,
        "test query",
        "history context",
        auth_token="token",
        set_fetch_result=lambda fr: set_fetch_result_calls.append(fr),
        set_fallback_reason=lambda reason: set_fallback_reason_calls.append(reason),
    )
    
    # Assert 403 does not trigger fallback
    assert result is None
    assert status_code == 403
    assert len(set_fallback_reason_calls) == 1
    assert set_fallback_reason_calls[0] == "http_auth_error: 403"
```

## Compatibility considerations

- This change only affects test coverage; no runtime behavior changes.
- The test follows the existing pattern used in the same file for testing 4xx errors.

## Security considerations

- No security implications; this is a test addition.

## Rollback considerations

- Remove the new test function to restore the original state.
- No code changes to revert.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/rag/test_rag_pipeline_service.py` | Unit — verify 401/403 handling | `uv run pytest tests/rag/test_rag_pipeline_service.py::test_401_403_no_fallback -v` | New test passes |
| Full suite (regression) | N/A | `uv run pytest` | No new failures |

## Completion criteria

- [ ] New test `test_401_403_no_fallback()` exists in `tests/rag/test_rag_pipeline_service.py`
- [ ] Test asserts 401 errors do NOT trigger in-process fallback
- [ ] Test asserts 403 errors do NOT trigger in-process fallback
- [ ] All existing tests pass after changes

## Out of scope

- Changing the behavior for other 4xx errors (400, 404, etc.) — these continue to trigger fallback.
- Modifying ADR-010's stated design (4xx-triggered-fallback is intentional per Decision #4/#6).
- Any changes to `scripts/rag/pipeline_service.py` beyond what is required by REQ-001.
- Database schema changes or public/runtime interface changes.
- Adding a custom `RAGAuthError` exception class.

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `HttpResultKind` enum with `AUTH_ERROR` variant | Pending | — | — | |
| 2 | Update `_map_http_result_kind()` mapping | Pending | — | — | |
| 3 | Modify `call_rag_service()` HTTPStatusError handler for 401/403 | Pending | — | — | |
| 4 | Propagate auth error through `http_augment.py` | Pending | — | — | |
| 5 | Add `test_401_403_no_fallback()` test | Pending | — | — | |
| 6 | Update INV-015 row in `adr-index.md` | Pending | — | — | |
| 7 | Run full test suite verification | Pending | — | — | |

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
- **Source issue**: issues/20260923-100003_p004_inv015_potential_violation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-162425_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-163041
- **Related target files**: tests/rag/test_rag_pipeline_service.py
