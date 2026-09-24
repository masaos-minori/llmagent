## Goal

Update `scripts/rag/http_augment.py` to handle the new auth error signal from `call_rag_service()` and propagate it without triggering in-process fallback.

## Scope

- **In-Scope**: Updating `_HTTP_RESULT_KIND_MAP` to include `AUTH_ERROR` → `HttpResultKind.ERROR` mapping; modifying the `run()` method to check `status_code` before deciding whether to trigger fallback.
- **Out-of-Scope**: Changing behavior for non-auth 4xx errors, adding new exception classes, modifying public/runtime interfaces beyond what is required by REQ-002.

## Assumptions

- The `HttpResultKind.AUTH_ERROR` enum value will be added to `scripts/rag/models_result.py` by the preceding procedure document.
- The `_HTTP_RESULT_KIND_MAP` will be extended with `"auth_error": HttpResultKind.AUTH_ERROR` by the preceding procedure document.
- `call_rag_service()` returns `(None, status_code, 0.0)` for 401/403 errors (as specified in REQ-001).

## Design decisions

- Check `status_code` directly in `http_augment.py` rather than relying solely on `http_result_kind` because:
  1. The `status_code` field is already available on `HttpAugmentResult` and provides a clear, explicit signal.
  2. This avoids requiring callers to also check `http_result_kind`, keeping the logic simple and localized.
  3. Consistent with the pattern used elsewhere in the codebase where `status_code` is checked for error classification.

## Alternatives considered

- Relying only on `http_result_kind == HttpResultKind.AUTH_ERROR`: rejected because it would require propagating the kind through the entire pipeline, which is more invasive than checking `status_code` directly.
- Returning a tuple `(result, status_code, latency_ms, is_auth_error)` from `call_rag_service()`: rejected because it would change the return type contract, breaking backward compatibility.

## Implementation

### Target file

`scripts/rag/http_augment.py`

### Procedure

1. Update `_HTTP_RESULT_KIND_MAP` to include `"auth_error": HttpResultKind.AUTH_ERROR`
2. Modify the `run()` method to check `status_code` before deciding whether to trigger fallback
3. For 401/403 errors, do NOT call `_set_fallback_reason()` and do NOT trigger in-process fallback

### Method

Use Edit tool to replace the exact string in the specified lines.

### Details

#### REQ-002: Line 135-136 — Fallback decision in `run()` method

**Before:**
```python
        if result is None:
            self._set_fallback_reason(http_fallback_reason)
```

**After:**
```python
        if result is None:
            if status_code in (401, 403):
                # Auth error — do NOT fall back to in-process; surface the error
                logger.warning(
                    "RAG service authentication error (%s), NOT falling back to in-process",
                    self._rag_url,
                )
            else:
                self._set_fallback_reason(http_fallback_reason)
```

#### REQ-002: `_HTTP_RESULT_KIND_MAP` extension

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

- This change modifies the fallback decision logic in `http_augment.py` — callers that previously relied on silent fallback for all failures will now see auth errors surfaced.
- The `HttpResultKind.AUTH_ERROR` enum value is additive and does not break existing code that matches on specific values.
- No changes to the public API or runtime interface.

## Security considerations

- This change IMPROVES security posture by surfacing authentication errors instead of hiding them behind fallback.
- No new secrets, credentials, or sensitive data are exposed — only HTTP status codes (401/403) are logged, which are standard HTTP status codes.

## Rollback considerations

- Revert the string replacement in `http_augment.py` to restore the original uniform fallback behavior.
- Remove the `"auth_error"` entry from `_HTTP_RESULT_KIND_MAP`.
- No code changes to revert beyond these two changes.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/http_augment.py` | Integration — verify augment stage behavior | `uv run pytest tests/rag/test_rag_http_mode.py -v` | Existing tests pass |
| Full suite (regression) | N/A | `uv run pytest` | No new failures |

## Completion criteria

- [ ] `http_augment.py` does NOT trigger in-process fallback when receiving a 401/403 error signal
- [ ] `http_augment.py` continues to trigger fallback for non-auth 4xx errors
- [ ] `_HTTP_RESULT_KIND_MAP` includes `"auth_error": HttpResultKind.AUTH_ERROR`
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260923-100003_p004_inv015_potential_violation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-162425_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-163041
- **Related target files**: scripts/rag/http_augment.py
