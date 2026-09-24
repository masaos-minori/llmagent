## Goal

Modify `call_rag_service()` in `scripts/rag/pipeline_service.py` to distinguish 401/403 errors from other 4xx errors when deciding whether to trigger fallback.

## Scope

- **In-Scope**: Modifying the `except httpx.HTTPStatusError as e:` block (line 152-161) to handle 401/403 differently from other 4xx errors.
- **Out-of-Scope**: Changing behavior for non-auth 4xx errors (400, 404, etc.), adding new exception classes, modifying public/runtime interfaces beyond what is required by REQ-001.

## Assumptions

- The ADR-010 Design team intends 401/403 to bypass fallback — confirmed by INV-015's explicit statement ("No local fallback on RAG 401/403").
- Extending `HttpResultKind` with an `AUTH_ERROR` variant is preferred over raising exceptions (see Plan's Design section).
- `scripts/rag/models_result.py` already exists and contains the `HttpResultKind` enum definition.

## Design decisions

- Prefer sentinel value approach (extending `HttpResultKind` with `AUTH_ERROR`) over raising a custom exception because:
  1. Minimal caller impact — callers already check `result is None`; adding an extra `kind == AUTH_ERROR` check is additive, not breaking.
  2. Consistent with existing pattern — `HttpAugmentResult.http_result_kind` already carries classification information.
  3. Observable — metrics/logging can distinguish auth errors from other failures.

## Alternatives considered

- Raising a custom `RAGAuthError` exception for 401/403: rejected because it requires try/except changes in all callers and breaks backward compatibility.
- Returning a special tuple `(None, status_code, latency_ms)` with a flag indicating auth error: rejected because it would require changing the return type contract of `call_rag_service()`, which is used by multiple callers.

## Implementation

### Target file

`scripts/rag/pipeline_service.py`

### Procedure

1. Extend `HttpResultKind` enum in `scripts/rag/models_result.py` with `AUTH_ERROR = "auth_error"`
2. Modify `call_rag_service()` in `scripts/rag/pipeline_service.py` line 152-161 to check for 401/403 before the generic 4xx handler
3. Return `(None, status_code, 0.0)` for 401/403 but set a flag/marker so callers know it's an auth error (not a general failure)
4. Update `_map_http_result_kind()` mapping in `http_augment.py` to include `AUTH_ERROR` → `HttpResultKind.ERROR`

### Method

Use Edit tool to replace the exact string in the specified lines. For the enum extension, append a new line after the existing enum members.

### Details

#### REQ-001: Line 152-161 — HTTPStatusError handler

**Before:**
```python
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
```

**After:**
```python
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                logger.warning(
                    "RAG service authentication error (%s) %s, NOT falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_auth_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
```

**Note:** The key change is that 401/403 now returns `(None, status_code, 0.0)` WITHOUT triggering in-process fallback in the caller. The caller (`http_augment.py`) must check `status_code` to determine if this is an auth error vs. a general failure.

#### REQ-001: `scripts/rag/models_result.py` — HttpResultKind enum extension

**Before:**
```python
class HttpResultKind(StrEnum):
    """Outcome classification for HTTP responses in RAG pipeline stages."""

    SUCCESS = "success"
    EMPTY = "empty"
    ERROR = "error"
    NOT_USED = "not_used"
```

**After:**
```python
class HttpResultKind(StrEnum):
    """Outcome classification for HTTP responses in RAG pipeline stages."""

    SUCCESS = "success"
    EMPTY = "empty"
    ERROR = "error"
    NOT_USED = "not_used"
    AUTH_ERROR = "auth_error"
```

#### REQ-002: `scripts/rag/http_augment.py` — _HTTP_RESULT_KIND_MAP extension

**Before:**
```python
_HTTP_RESULT_KIND_MAP: dict[str, HttpResultKind] = {
    "remote_nonempty": HttpResultKind.SUCCESS,
    "remote_empty": HttpResultKind.EMPTY,
    "in_process_fallback": HttpResultKind.ERROR,
}
```

**After:**
```python
_HTTP_RESULT_KIND_MAP: dict[str, HttpResultKind] = {
    "remote_nonempty": HttpResultKind.SUCCESS,
    "remote_empty": HttpResultKind.EMPTY,
    "in_process_fallback": HttpResultKind.ERROR,
    "auth_error": HttpResultKind.AUTH_ERROR,
}
```

## Compatibility considerations

- This change modifies the error handling behavior for 401/403 errors — callers that previously relied on silent fallback will now see the auth error signal.
- The `HttpResultKind.AUTH_ERROR` enum value is additive and does not break existing code that matches on specific values (e.g., `if kind == HttpResultKind.SUCCESS`).
- The return type of `call_rag_service()` remains unchanged — still returns `(str | None, int | None, float)`.

## Security considerations

- This change IMPROVES security posture by surfacing authentication errors instead of hiding them behind fallback.
- No new secrets, credentials, or sensitive data are exposed — only HTTP status codes (401/403) are logged, which are standard HTTP status codes.

## Rollback considerations

- Revert the string replacement in `pipeline_service.py` to restore the original uniform 4xx handling.
- Remove the `AUTH_ERROR` enum value from `models_result.py`.
- Remove the `"auth_error"` entry from `_HTTP_RESULT_KIND_MAP` in `http_augment.py`.
- No code changes to revert beyond these three files.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/pipeline_service.py` | Unit — verify 401/403 handling | `uv run pytest tests/rag/test_rag_pipeline_service.py::test_401_403_no_fallback -v` | New test passes |
| `scripts/rag/http_augment.py` | Integration — verify augment stage behavior | `uv run pytest tests/rag/test_rag_http_mode.py -v` | Existing tests pass |
| Full suite (regression) | N/A | `uv run pytest` | No new failures |

## Completion criteria

- [ ] `call_rag_service()` returns `(None, status_code, 0.0)` for 401/403 errors WITHOUT triggering in-process fallback in the caller
- [ ] `call_rag_service()` continues to return `(None, status_code, 0.0)` for non-auth 4xx errors (preserving existing fallback behavior)
- [ ] `HttpResultKind.AUTH_ERROR` enum value exists in `scripts/rag/models_result.py`
- [ ] `_HTTP_RESULT_KIND_MAP` includes `"auth_error": HttpResultKind.AUTH_ERROR`
- [ ] New test(s) exist asserting 401/403 errors do NOT trigger in-process fallback
- [ ] All existing tests pass after changes

## Out of scope

- Changing the behavior for other 4xx errors (400, 404, etc.) — these continue to trigger fallback.
- Modifying ADR-010's stated design (4xx-triggered-fallback is intentional per Decision #4/#6).
- Any changes to `scripts/rag/http_augment.py` beyond updating `_HTTP_RESULT_KIND_MAP`.
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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260923-100003_p004_inv015_potential_violation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-162425_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-163041
- **Related target files**: scripts/rag/pipeline_service.py
