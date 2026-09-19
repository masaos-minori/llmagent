## Goal

Update the test assertion in `tests/rag/test_rag_pipeline_service.py::test_json_parse_error_calls_set_fallback_reason` from `assert result is None` to `assert result == ""`, reflecting the confirmed correct behavior after architect judgment favors ADR compliance. Closes REQ-004.

## Scope

- Modify the single assertion in `test_json_parse_error_calls_set_fallback_reason` from `assert result is None` to `assert result == ""`
- No changes to other assertions or test structure

## Assumptions

- The architect has determined that code should align with ADR-010 Decision #9 before this procedure is executed
- The corresponding code change in `scripts/rag/pipeline_service.py` has been implemented (returning `""` instead of `None` on parse `ValueError`)
- The test name `test_json_parse_error_calls_set_fallback_reason` remains accurate — the `_set_fallback_reason` callback is still invoked even though the result is not a fallback trigger

## Design decisions

- Change only the assertion line: `assert result is None` → `assert result == ""`
- Keep the rest of the test intact (mock setup, method calls, `_set_fallback_reason` verification)
- Do not rename the test — its purpose (verifying `_set_fallback_reason` is called on parse error) is unchanged

## Alternatives considered

- Rename the test to reflect the new behavior: rejected because the test's primary purpose (verifying `_set_fallback_reason` is called) is unchanged; renaming would add churn without benefit.
- Split into two tests (one for `""` return, one for `_set_fallback_reason`): rejected because the test is simple and splitting would add unnecessary complexity.
- Remove the test entirely: rejected because `_set_fallback_reason` invocation on parse error is an important invariant that should remain tested.

## Implementation

### Target file

`tests/rag/test_rag_pipeline_service.py`

### Procedure

#### Step 1: Modify the assertion

In `test_json_parse_error_calls_set_fallback_reason`, locate the assertion at line 255:

```python
assert result is None
```

Change to:

```python
assert result == ""
```

No other changes to the test — the mock setup (line 243-244), the method call (lines 247-254), and the `_set_fallback_reason` assertions (lines 256-257) remain unchanged.

### Details

- The key change is a single-line edit: `is None` → `== ""`
- The test's primary purpose (verifying `_set_fallback_reason` is called on parse error) is unchanged
- The test name `test_json_parse_error_calls_set_fallback_reason` remains accurate
- No changes to the mock setup or other assertions

## Compatibility considerations

- This test change must be applied together with the corresponding code change in `scripts/rag/pipeline_service.py`
- If the code change is reverted (returning `None` again), this test will fail — the test and code changes are coupled

## Security considerations

N/A: this change affects test assertions, not data access or network operations.

## Rollback considerations

- To revert: restore `assert result is None` in the test
- No database migrations or persistent state changes — rollback is straightforward

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|--------|---------|---------------------|------------------|
| `test_json_parse_error_calls_set_fallback_reason` | Unit — verify assertion passes | `pytest -k "test_json_parse_error_calls_set_fallback_reason"` | Test passes with `result == ""` assertion |
| Full test suite | Regression — all `call_rag_service` tests | `uv run pytest tests/rag/test_rag_pipeline_service.py` | All tests pass |

## Completion criteria

- [ ] `assert result is None` changed to `assert result == ""` in `test_json_parse_error_calls_set_fallback_reason`
- [ ] No other changes to the test (mock setup, method calls, `_set_fallback_reason` assertions)
- [ ] Test name unchanged
- [ ] All existing tests pass after the change

## Out of scope

- Resolving other known deviations in ADR-010
- Changing fallback policy for HTTP errors (4xx/5xx) — handled separately
- Any change to `check_duplicate_heading_numbers`'s existing purely-numeric detection behavior
- Adding cross-document content-similarity checks
- Creating a new ADR superseding Decision #9 (separate procedure if architect judgment favors ADR amendment)
- Changes to other tests in the file

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260919-094754_adr010_adr-010-decision-9-vs-rag-parse-error-handling-mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-100913_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-101830
- **Related target files**: tests/rag/test_rag_pipeline_service.py
