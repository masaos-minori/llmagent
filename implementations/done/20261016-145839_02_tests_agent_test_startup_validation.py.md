## Goal

Implement `REQ-004` by adding a regression test that drives the real `check_services()` body with a programming-error exception and asserts the recorded `rag_consistency` outcome is a classified `SKIPPED` (carrying `PROGRAMMING_ERROR`), not an unclassified one.

## Scope

Modify `tests/agent/test_startup_validation.py` only: add one test method. No existing test is changed; the existing `TimeoutError` and success cases keep passing.

## Assumptions

- The programming-error exception (`KeyError`) raised inside `rag_service.consistency()` propagates through `loop.run_in_executor(...)` and `asyncio.wait_for(...)` to the broad `except Exception` branch of `check_services()`, exactly as a real `KeyError`/`AttributeError`/`TypeError` from `RagMaintenanceService().consistency()` would.
- The existing `_run_check_services()` helper already patches every other check to a clean pass, so only the RAG branch is exercised.

## Design decisions

- Drive the real `check_services()` body rather than stubbing `add_skipped()`, so the test pins the actual classification-and-message path end to end.
- Raise the programming error via `rag_service.consistency.side_effect` (through the executor/wait_for path) rather than patching `asyncio.wait_for`, so the broad `except Exception` branch — not the `except TimeoutError` branch — is exercised.

## Alternatives considered

`N/A: single test-method addition; no public contract, persistence, or security impact.`

## Implementation
### Target file
`tests/agent/test_startup_validation.py`

### Procedure
1. Add a new test method to the existing `TestRagConsistencyTimeout` class (mirroring where `test_rag_check_succeeds_within_timeout` already lives).
2. Inside it, build a `rag_service` whose `consistency()` raises a `KeyError` via `side_effect`, run it through `_run_check_services(rag_service)`, and assert the recorded outcome.

### Method

Reuse the module's existing helpers `_run_check_services()` (patches all non-RAG checks to a clean pass) and `_rag_outcomes()` (filters outcomes by `source == "rag_consistency"`).

### Details

Add this method after `test_rag_check_succeeds_within_timeout` (currently the last method in the file, ending at line 104):

```python
    @pytest.mark.asyncio
    async def test_rag_check_programming_error_classified(self) -> None:
        """REQ-004: a programming-error exception is recorded as a classified SKIPPED, not an unclassified one."""
        rag_service = MagicMock()
        rag_service.consistency.side_effect = KeyError("missing key")

        result = await _run_check_services(rag_service)

        assert _rag_outcomes(result) == [StartupCheckStatus.SKIPPED]
        skipped = [o for o in result.outcomes if o.source == "rag_consistency"]
        assert "PROGRAMMING_ERROR" in skipped[0].message
        assert "KeyError" in skipped[0].message
        assert not result.has_fatal
```

The assertion set pins both requirements: `SKIPPED` status (`REQ-003`), the `PROGRAMMING_ERROR` category and the `KeyError` type name in the message (`REQ-002`), and absence of any `FATAL` (`REQ-003`).

## Compatibility considerations

`N/A: additive test only; no change to existing test signatures, fixtures, or the module under test.`

## Security considerations

`N/A: test-only change; the `KeyError` payload is a benign literal with no secret exposure.`

## Rollback considerations

`N/A: revert the commit that adds the test.`

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_startup_validation.py` | Unit: new programming-error case plus existing timeout/success cases | `uv run pytest tests/agent/test_startup_validation.py -v` | New test passes; `test_rag_check_timeout_enforced` and `test_rag_check_succeeds_within_timeout` still pass |

## Completion criteria

- `test_rag_check_programming_error_classified` (new) passes and asserts `rag_consistency` is `SKIPPED` with `PROGRAMMING_ERROR` and `KeyError` in its message and no `FATAL`.
- The pre-existing `TimeoutError` and success tests still pass unchanged.
- `ruff format` / `ruff check` / `mypy` are clean on the test file.

## Out of scope

Any change to `scripts/agent/startup_validation.py` (that change is covered by the sibling implementation procedure), the reporter, or other pipeline checks.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261016-171028 | 20261016-171028 | changed: tests/agent/test_startup_validation.py. Added the procedure's programming-error test plus a parametrized test for the NETWORK_TRANSIENT, DATABASE_OR_IO (sqlite3 and OSError) and UNKNOWN categories (4 cases) to reach the diff-coverage gate. Red check on HEAD: the programming-error test failed; the other 2 existing tests passed. After the change 7 passed. mypy clean for the file |
| 2 | Add or update tests per Validation plan | Completed | 20261016-171028 | 20261016-171028 | changed: tests/agent/test_startup_validation.py. Added the procedure's programming-error test plus a parametrized test for the NETWORK_TRANSIENT, DATABASE_OR_IO (sqlite3 and OSError) and UNKNOWN categories (4 cases) to reach the diff-coverage gate. Red check on HEAD: the programming-error test failed; the other 2 existing tests passed. After the change 7 passed. mypy clean for the file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-171028 | 20261016-171028 | changed: tests/agent/test_startup_validation.py. Added the procedure's programming-error test plus a parametrized test for the NETWORK_TRANSIENT, DATABASE_OR_IO (sqlite3 and OSError) and UNKNOWN categories (4 cases) to reach the diff-coverage gate. Red check on HEAD: the programming-error test failed; the other 2 existing tests passed. After the change 7 passed. mypy clean for the file |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261016-171028 | 20261016-171028 | changed: tests/agent/test_startup_validation.py. Added the procedure's programming-error test plus a parametrized test for the NETWORK_TRANSIENT, DATABASE_OR_IO (sqlite3 and OSError) and UNKNOWN categories (4 cases) to reach the diff-coverage gate. Red check on HEAD: the programming-error test failed; the other 2 existing tests passed. After the change 7 passed. mypy clean for the file |

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
- **Requirement ID**: `REQ-004` (regression test asserting a programming-error exception is recorded as a classified `SKIPPED`)
- **Source issue**: issues/20261016-133921_startup001_classify-rag-consistency-startup-exceptions-instead-of-skipping-all.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-135325_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-145839
- **Related target files**: tests/agent/test_startup_validation.py