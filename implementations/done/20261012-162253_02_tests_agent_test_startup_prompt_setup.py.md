## Goal
- Add tests that pin the new classification and the error log and warning for a programming error, without changing what the existing tests pin (`REQ-004`).

## Scope
- Only `tests/agent/test_startup_prompt_setup.py`: new tests in the existing classification class and the existing memory-failure class.

## Assumptions
- The helper `_make_prompt_setup` and the pattern of patching `shared.logger.Logger` are reused as they are.
- The existing tests keep passing because ValueError and RuntimeError stay UNKNOWN and the other categories are untouched.

## Design decisions
- Parametrize the classification over the five types plus KeyError and IndexError as members of the lookup family.
- Assert on the logger's error call and keyword arguments rather than on rendered text alone.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/agent/test_startup_prompt_setup.py`

### Procedure
1. In the classification class add test_programming_errors_classified_as_programming_error, parametrized over AttributeError, NameError, TypeError, KeyError, IndexError and AssertionError; each classified exception must return the category string PROGRAMMING_ERROR.
2. In the same class add test_runtime_error_stays_unknown: RuntimeError returns UNKNOWN.
3. In the memory-failure class add test_programming_error_logs_error_with_traceback_and_distinct_warning: memory service whose session-start call raises AttributeError with the message boom; patch the module logger as the neighbouring test does; run setup_prompt; assert the memory-disabled flag is true, the logger's error method was called once with exc_info true and a message containing internal error, the info method was not called, and the view warning was called once with text containing Memory injection failed, AttributeError, boom and the NON_FATAL tag.
4. Run the new tests against the unmodified production code and confirm the six classification cases and the logging test fail while test_runtime_error_stays_unknown passes.

### Method
- Follow the existing style: plain test functions in the classes, pytest.mark.asyncio for the async one, pytest.mark.parametrize for the classification.
- Do not edit the existing parametrized logging test or any helper.

### Details
- The existing classification tests already cover ConnectionError, TimeoutError, sqlite3.Error, OSError and ValueError, so only RuntimeError is added for the unchanged side.
- Use only plain names for the new tests; no helper is needed.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_startup_prompt_setup.py -v`; before procedure 01 seven of the eight new test cases fail, after it all pass and the existing tests still pass.
- `uv run ruff format --check tests/agent/test_startup_prompt_setup.py`, `uv run ruff check tests/agent/test_startup_prompt_setup.py`.
- Execution order for the whole plan: procedure 02 (tests) first, then 01 (code), then 03 (docs); the new tests must be seen failing before the code is edited.

## Completion criteria
- The new tests exist; the classification and logging cases fail on the old code and pass after procedure 01; existing tests are unchanged and pass.

## Out of scope
- Production code, other test files, and any change to what the existing tests assert.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the classification and logging tests and confirm the new cases fail on the unmodified code | Completed | 20261012-163451 | 20261012-163516 | stale_detector clean; applied first (mutation precondition) changed: tests/agent/test_startup_prompt_setup.py (+8 test cases); 7 of 8 fail on the unmodified code as predicted (mutation precondition met) |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-163545 | 20261012-163545 | ruff format/check pass; all 8 new cases pass after procedure 01 (7 failed before); existing tests unchanged |

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
- **Requirement ID**: `REQ-004` (tests for the new category and its reporting)
- **Source issue**: issues/20261012-124838_start004_startup-prompt-setup-swallows-all-memory-injection-errors-as-a-generic-disabled-flag.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-154332_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-162253
- **Related target files**: tests/agent/test_startup_prompt_setup.py