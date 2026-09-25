## Goal

Rename and update the unit test `test_json_parse_error_calls_set_fallback_reason` in `tests/rag/test_rag_pipeline_service.py` to assert that the fallback reason callback is NOT invoked upon receiving malformed JSON, consistent with the source code fix in `scripts/rag/pipeline_service.py`.

## Scope

- Rename test function from `test_json_parse_error_calls_set_fallback_reason` to `test_json_parse_error_does_not_call_set_fallback_reason`
- Change assertion `assert len(reasons) == 1` to `assert len(reasons) == 0`
- Remove assertion `assert reasons[0].startswith("http_parse_error:")` (index out of range after the change)
- Preserve all other test logic: mock setup, HTTP response body, client initialization

## Assumptions

- The test class `TestFallbackReasonCallback` and its decorator structure (`@pytest.mark.asyncio`, `@respx.mock`) remain unchanged
- No other test or code references this test function name directly (e.g., via `--collect-only` filters or parametrized fixtures)

## Design decisions

- Rename the test function rather than creating a new one: preserves test history in git blame and avoids duplicate test collection
- Keep the same test body structure: only assertions change; mock setup and invocation remain identical

## Alternatives considered

- **Create a new test and delete the old one**: rejected — loses git blame continuity; rename is cleaner
- **Keep the old name and invert assertions**: rejected — name `test_json_parse_error_calls_set_fallback_reason` would contradict the assertion `len(reasons) == 0`; name must reflect behavior

## Implementation

### Target file

`tests/rag/test_rag_pipeline_service.py`

### Procedure

1. Open `tests/rag/test_rag_pipeline_service.py`
2. Locate the `test_json_parse_error_calls_set_fallback_reason` method (lines 240-256)
3. Rename the function: `def test_json_parse_error_calls_set_fallback_reason` → `def test_json_parse_error_does_not_call_set_fallback_reason`
4. Change line 255: `assert len(reasons) == 1` → `assert len(reasons) == 0`
5. Delete line 256: `assert reasons[0].startswith("http_parse_error:")`
6. Verify no trailing blank line artifacts remain between this test and the next class definition

### Method

Direct edit: rename function, modify one assertion, delete one assertion. No imports or structural changes.

### Details

Current code (lines 240-256):
```python
    @pytest.mark.asyncio
    @respx.mock
    async def test_json_parse_error_calls_set_fallback_reason(self) -> None:
        reasons: list[str] = []
        respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(200, content=b"not-json")
        )
        async with httpx.AsyncClient() as client:
            result, status, _ = await call_rag_service(
                client,
                RAG_URL,
                "q",
                "",
                set_fetch_result=_noop_fetch,
                set_fallback_reason=reasons.append,
            )
        assert result == ""
        assert len(reasons) == 1
        assert reasons[0].startswith("http_parse_error:")
```

After change:
```python
    @pytest.mark.asyncio
    @respx.mock
    async def test_json_parse_error_does_not_call_set_fallback_reason(self) -> None:
        reasons: list[str] = []
        respx.post(f"{RAG_URL}/v1/call_tool").mock(
            return_value=httpx.Response(200, content=b"not-json")
        )
        async with httpx.AsyncClient() as client:
            result, status, _ = await call_rag_service(
                client,
                RAG_URL,
                "q",
                "",
                set_fetch_result=_noop_fetch,
                set_fallback_reason=reasons.append,
            )
        assert result == ""
        assert len(reasons) == 0
```

Note: `assert result == ""` is preserved — the return value contract is unchanged by this fix. The test still verifies that parse errors produce an empty string result; only the fallback reason assertion changes.

## Compatibility considerations

- Test name change affects test selection via `-k` flag: callers using `-k test_json_parse_error_calls_set_fallback_reason` must update to `-k test_json_parse_error_does_not_call_set_fallback_reason`
- No API or behavioral changes to production code from the test perspective — the test now correctly validates the fixed behavior

## Security considerations

No security impact. This is a test-only change that modifies assertions to match corrected source behavior.

## Rollback considerations

Rollback is trivial: revert the three edits (rename + two assertion changes). No database migrations, config changes, or dependency updates required.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/rag/test_rag_pipeline_service.py | Verify renamed test passes | `uv run pytest tests/rag/test_rag_pipeline_service.py -k test_json_parse_error_does_not_call_set_fallback_reason` | Test passes with `assert len(reasons) == 0` |
| tests/rag/test_rag_pipeline_service.py | Verify old test name no longer matches | `uv run pytest tests/rag/test_rag_pipeline_service.py -k test_json_parse_error_calls_set_fallback_reason --collect-only` | Zero tests collected |
| tests/rag/test_rag_pipeline_service.py | Full suite regression | `uv run pytest tests/rag/test_rag_pipeline_service.py` | All 16 tests pass |

## Completion criteria

- [ ] Test function renamed to `test_json_parse_error_does_not_call_set_fallback_reason`
- [ ] `assert len(reasons) == 1` changed to `assert len(reasons) == 0`
- [ ] `assert reasons[0].startswith("http_parse_error:")` removed
- [ ] `assert result == ""` preserved unchanged
- [ ] No other lines in the file modified
- [ ] All tests in `tests/rag/test_rag_pipeline_service.py` pass

## Out of scope

- Modifying any other test in this file
- Modifying `scripts/rag/pipeline_service.py` (covered by separate implementation procedure)
- Adding new tests for other error paths
- Updating CI configuration or test infrastructure

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260925-113735 | 20260925-113735 | REQ-002 |
| 2 | Add or update tests per Validation plan | Completed | 20260925-113735 | 20260925-113735 | REQ-003 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260925-113735 | 20260925-113735 | REQ-003 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260925-113735 | 20260925-113735 | N/A: no docs to update |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20260925-120000_nc036_fix-rag-parse-error-logic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-104405_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260925-111351
- **Related target files**: tests/rag/test_rag_pipeline_service.py