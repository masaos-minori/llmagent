## Goal

Modify `call_rag_service()` in `scripts/rag/pipeline_service.py` to return `""` instead of `None` on parse `ValueError`, aligning the code with ADR-010 Decision #9 ("parse errors should be logged and treated as empty result, `""`, not a fallback trigger"). Closes REQ-002, REQ-005.

## Scope

- Modify the `except ValueError` branch in `call_rag_service()` to return `""` instead of `None`
- Update the docstring to reflect the new return contract
- No changes to other error handling paths (HTTP errors, transport errors, retry logic)

## Assumptions

- The architect will determine whether code or ADR should be corrected before this procedure is executed
- If architect judgment favors ADR compliance, this procedure applies
- The change is limited to the single `except ValueError` branch — no other code paths affected

## Design decisions

- Return `""` (empty string) from the `except ValueError` branch instead of `None`
- Update the docstring's return contract table to reflect that JSON parse errors now produce `""` rather than `None`
- Keep the logging statement (`logger.warning`) unchanged — the log message remains valid regardless of return value
- Keep `_set_fallback_reason` call unchanged — the fallback reason is still recorded even though the caller won't trigger in-process fallback

## Alternatives considered

- Raise the `ValueError` instead of catching it: rejected because it would break the existing error classification contract and require callers to handle a different exception type.
- Return `None` but suppress the fallback trigger: rejected because there is no mechanism in the caller to distinguish between "fallback triggered" and "no fallback needed" without changing the return type.
- Create a sentinel value like `NoFallback`: rejected because it introduces a new type and breaks the existing `str | None` return contract.

## Implementation

### Target file

`scripts/rag/pipeline_service.py`

### Procedure

1. Modify the `except ValueError` branch to return `""` instead of `None`
2. Update the docstring's return contract table

### Method

#### Step 1: Modify `except ValueError` branch

In `call_rag_service()`, locate the `except ValueError` block (currently at lines 163-170):

```python
except ValueError as e:
    logger.warning(
        "RAG service parse error (%s), falling back to in-process: %s",
        rag_url,
        e,
    )
    _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
    return None, None, 0.0
```

Change the return statement from `return None, None, 0.0` to `return "", None, 0.0`.

The rest of the block (logging + `_set_fallback_reason` call) remains unchanged — the fallback reason is still recorded for observability even though the caller won't trigger in-process fallback.

#### Step 2: Update docstring

Update the docstring's return contract table (lines 70-87) to reflect the new contract:

Change:
```
         | ``None``       | One of:                                           |
         |                | - HTTP 4xx (client error, no retry)               |
         |                | - HTTP 5xx with all retries exhausted             |
         |                | - Transport error (connection refused, timeout)   |
         |                | - JSON parse error on response body               |
         |                | None triggers in-process fallback in the caller.  |
```

To:
```
         | ``None``       | One of:                                           |
         |                | - HTTP 4xx (client error, no retry)               |
         |                | - HTTP 5xx with all retries exhausted             |
         |                | - Transport error (connection refused, timeout)   |
         |                | None triggers in-process fallback in the caller.  |
         | ``""``         | JSON parse error on response body                 |
         |                | Empty result — not a failure, no fallback.        |
```

Also update the summary paragraph below the table (line 111):

Change:
```
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
```

To:
```
        Augmented context string, empty string for valid empty results
        or JSON parse errors, or None to signal failure and trigger
        in-process fallback.
```

### Details

- The key change is a single-character edit: `None` → `""` in the return statement
- The `_set_fallback_reason` call remains because it serves observability purposes (tracking why the RAG service was called) even when the result is not a fallback trigger
- The docstring update ensures the public contract matches the new behavior — this is important for callers who may rely on the documented return values
- No changes to the retry loop, HTTP error handling, or transport error handling

## Compatibility considerations

- The return type contract changes: callers expecting `None` on parse error must now check for `""` instead
- However, `""` is already used for valid empty results (HTTP 200 with no `"result"` field), so the semantic distinction between "valid empty" and "parse error" is lost — callers should not rely on distinguishing these cases
- This is a behavioral change that could affect systems depending on parse errors triggering in-process fallback

## Security considerations

N/A: this change affects error handling behavior, not data access or network operations.

## Rollback considerations

- To revert: restore `return None, None, 0.0` in the `except ValueError` branch
- Restore the original docstring return contract table
- No database migrations or persistent state changes — rollback is straightforward

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|--------|---------|---------------------|------------------|
| `call_rag_service()` (parse error) | Unit — verify return value | `pytest -k "test_json_parse_error_calls_set_fallback_reason"` | Returns `""` on parse error |
| `call_rag_service()` (other errors) | Regression — HTTP errors, timeouts | `pytest -k "test_4xx\|test_timeout\|test_transport"` | Other error paths unchanged |
| Full test suite | Regression — all `call_rag_service` tests | `uv run pytest tests/rag/test_rag_pipeline_service.py` | All tests pass |

## Completion criteria

- [ ] `call_rag_service()` returns `""` on parse `ValueError` instead of `None`
- [ ] Docstring return contract table updated to reflect new behavior
- [ ] Docstring summary paragraph updated to reflect new behavior
- [ ] `_set_fallback_reason` call preserved in `except ValueError` branch
- [ ] Logging statement preserved in `except ValueError` branch
- [ ] No changes to other error handling paths (HTTP errors, transport errors, retry logic)
- [ ] All existing tests pass after the change

## Out of scope

- Resolving other known deviations in ADR-010
- Changing fallback policy for HTTP errors (4xx/5xx) — handled separately
- Any change to `check_duplicate_heading_numbers`'s existing purely-numeric detection behavior
- Adding cross-document content-similarity checks
- Creating a new ADR superseding Decision #9 (separate procedure if architect judgment favors ADR amendment)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-005
- **Source issue**: issues/20260919-094754_adr010_adr-010-decision-9-vs-rag-parse-error-handling-mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-100913_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-101830
- **Related target files**: scripts/rag/pipeline_service.py
