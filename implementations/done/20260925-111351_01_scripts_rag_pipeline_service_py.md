## Goal

Remove the spurious `_set_fallback_reason` call in the `ValueError` handler of `call_rag_service()` in `scripts/rag/pipeline_service.py`, aligning observability with actual system behavior per ADR-010 INV-07.

## Scope

- Remove line 181: `_set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")` from the `except ValueError` block
- Preserve all other behavior: return value `("", None, 0.0)`, logging, retry logic for other error types

## Assumptions

- The `set_fallback_reason` callback parameter is optional (`None` by default)
- No caller depends on the fallback reason being set for JSON parse errors
- The sole caller (`scripts/rag/http_augment.py`) does not propagate parse-error fallback reasons externally (confirmed: `result=""` causes `fallback_reason=None` at line 128 and outer `_set_fallback_reason` guard at line 139)

## Design decisions

- Minimal surgical fix: remove only the single `_set_fallback_reason` call; do not refactor the callback mechanism
- Return value contract unchanged: `""` still signals valid empty result, `None` still triggers fallback
- Logging (`logger.warning` at line 176-180) preserved — parse errors should still be observable via logs

## Alternatives considered

- **Add a separate callback for parse-only events**: rejected — adds complexity without user benefit; log entries suffice for observability
- **Change return value to `None` on parse error**: rejected — contradicts ADR-010 INV-07 ("解析エラーは空結果として扱う"); would trigger unnecessary in-process fallback

## Implementation

### Target file

`scripts/rag/pipeline_service.py`

### Procedure

1. Open `scripts/rag/pipeline_service.py`
2. Locate the `except ValueError as e:` block (lines 175-182)
3. Delete line 181: `_set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")`
4. Verify no trailing blank line artifacts remain
5. Verify indentation of line 182 (`return "", None, 0.0`) is unchanged

### Method

Direct edit: delete the single line. No imports, function signatures, or control flow changes.

### Details

Current code (lines 175-182):
```python
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return "", None, 0.0
```

After change:
```python
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            return "", None, 0.0
```

Note: The log message text "falling back to in-process" is technically inaccurate for the same reason as the `_set_fallback_reason` call (no fallback occurs). However, fixing the log message wording is out of scope for this task — it would require a separate Plan. This task only addresses the `_set_fallback_reason` call.

## Compatibility considerations

- Callers that provide `set_fallback_reason` will receive one fewer callback invocation specifically for JSON parse errors
- All other error paths (4xx, 401/403 auth errors, 5xx retries exhausted, transport errors) are unaffected
- The docstring at lines 85-87 already states JSON parse errors return `""` (empty string, no fallback) — the implementation now matches the documented contract

## Security considerations

No security impact. This change removes an observability side effect; it does not alter authentication, authorization, input handling, or data flow.

## Rollback considerations

Rollback is trivial: re-add the deleted line 181. No database migrations, config changes, or dependency updates required.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/pipeline_service.py | Unit — verify parse error path returns correct values without calling callback | `uv run pytest tests/rag/test_rag_pipeline_service.py -k test_json_parse_error_does_not_call_set_fallback_reason` | Test passes with `assert result == ""` and `assert len(reasons) == 0` |
| scripts/rag/pipeline_service.py | Regression — verify 4xx handler still calls fallback reason | `uv run pytest tests/rag/test_rag_pipeline_service.py -k "test_4xx_calls"` | Test passes with `assert len(reasons) == 1` |
| scripts/rag/pipeline_service.py | Regression — verify 5xx exhausted handler still calls fallback reason | `uv run pytest tests/rag/test_rag_pipeline_service.py -k "test_5xx_exhausted"` | Test passes with `assert len(reasons) == 1` |
| scripts/rag/pipeline_service.py | Regression — verify auth error handlers still call fallback reason | `uv run pytest tests/rag/test_rag_pipeline_service.py -k "auth"` | Auth tests pass with `assert len(reasons) == 1` |
| scripts/rag/pipeline_service.py | Full suite regression | `uv run pytest tests/rag/test_rag_pipeline_service.py` | All 16 tests pass |

## Completion criteria

- [ ] Line 181 (`_set_fallback_reason` call) removed from `scripts/rag/pipeline_service.py`
- [ ] Return value `("", None, 0.0)` at line 182 preserved unchanged
- [ ] Log statement at lines 176-180 preserved unchanged
- [ ] No other lines in the file modified
- [ ] All existing tests in `tests/rag/test_rag_pipeline_service.py` pass after corresponding test updates

## Out of scope

- Changing the log message text "falling back to in-process" (technically inaccurate but separate concern)
- Modifying any other error handler (4xx, 5xx, transport error, auth error)
- Adding new callbacks or observability mechanisms
- Updating documentation beyond what test changes necessitate
- Modifying `scripts/rag/http_augment.py` or any other caller

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260925-113720 | 20260925-113720 | REQ-001, REQ-002 |
| 2 | Add or update tests per Validation plan | Completed | 20260925-113720 | 20260925-113720 | REQ-002, REQ-003 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260925-113720 | 20260925-113720 | REQ-003 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260925-113720 | 20260925-113720 | N/A: no docs to update |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260925-120000_nc036_fix-rag-parse-error-logic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-104405_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260925-111351
- **Related target files**: scripts/rag/pipeline_service.py