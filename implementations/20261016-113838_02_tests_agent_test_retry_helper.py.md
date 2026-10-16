## Goal

Add a regression test to `tests/agent/test_retry_helper.py` covering a custom `RuntimeError` subclass with a non-string constructor raised on both attempts, which must not raise `AttributeError` and must propagate as the custom type (chaining the original error). (`REQ-006`)

## Scope

- **In-Scope**:
  - Add `test_custom_runtime_error_non_string_constructor_preserved` to `TestRetryHelperExceptionPreservation` in `tests/agent/test_retry_helper.py`.
  - The test exercises a `RuntimeError` subclass whose `__init__` rejects a plain message string, raised on both attempts, asserting the propagated exception keeps its type, chains the original error, and never surfaces an `AttributeError`.
- **Out-of-Scope**:
  - Any change to `scripts/agent/shared/retry_helper.py` (owned by sibling document `implementations/20261016-113838_01_scripts_agent_shared_retry_helper.py.md`).
  - Modifying the existing `test_timeout_error_preserved`/`test_connection_refused_error_preserved`/`test_runtime_error_preserved` tests.

## Assumptions

- The sibling document reworks `retry_once_with_delay`'s line-60 re-raise into `_rebuild_after_retry`, which reconstructs the original type from a stored payload, falls back to `type(err)(message)` for standard exceptions, and falls back to preserving type + `.args` (via `cls.__new__(cls)`) for exotic constructors.
- The existing `TestRetryHelperExceptionPreservation` class (lines 5-72) covers standard types only; this test extends it with the custom-constructor case.
- Tests are async (`@pytest.mark.asyncio`) and call `retry_once_with_delay` with `shutdown_event=None`.

## Design decisions

- Define a local `class _CustomRuntimeError(RuntimeError)` whose `__init__(self, code: int)` raises `TypeError` for a non-int argument, so `type(err)(masked_msg)` fails and forces the fix's exotic-constructor fallback path.
- Assert on double failure that the caught exception is a `_CustomRuntimeError` instance, that its `__cause__` is a `_CustomRuntimeError` (confirming `from retry_err` chaining), and that no `AttributeError`/`TypeError` escapes.

## Alternatives considered

Could reuse `HttpStartupError` for the custom case, but a minimal custom `RuntimeError` subclass that rejects a string argument more directly exercises the generic exotic-constructor fallback the fix targets (and keeps the unit test independent of `StartupFailure` construction).

## Implementation
### Target file
`tests/agent/test_retry_helper.py`
### Procedure
1. Add `test_custom_runtime_error_non_string_constructor_preserved` to `TestRetryHelperExceptionPreservation`.
2. Run the validation sequence.
### Method
- Inside the test, define the custom exception and a two-call `failing_func`:
  ```python
  class _CustomRuntimeError(RuntimeError):
      def __init__(self, code: int) -> None:
          if not isinstance(code, int):
              raise TypeError("code must be an int, not a str")
          self.code = code

  call_count = 0

  async def failing_func():
      nonlocal call_count
      call_count += 1
      if call_count == 1:
          raise _CustomRuntimeError(1)
      raise _CustomRuntimeError(2)
  ```
- Wrap the call in `pytest.raises(_CustomRuntimeError) as exc_info`.
- After the call, assert `isinstance(exc_info.value, _CustomRuntimeError)` and `isinstance(exc_info.value.__cause__, _CustomRuntimeError)`.
### Details
- The constructor's `isinstance(code, int)` guard makes `_CustomRuntimeError(masked_msg)` raise `TypeError`, so the fix's standard fallback (`type(err)(message)`) fails and the exotic `cls.__new__(cls)` + `.args` path is exercised — the exact scenario that previously produced an uncaught `AttributeError` for `HttpStartupError`.
- Chaining assertion (`__cause__` is a `_CustomRuntimeError`) confirms `from retry_err` is preserved through the exotic fallback.
- Do not assert on `exc.code`: the `__new__`-based fallback preserves type + `.args` but not custom attributes, so `self.code` is unset on the rebuilt instance.
- Keep `_CustomRuntimeError` scoped inside the test function to avoid polluting the module namespace or clashing with other test modules.

## Compatibility considerations
N/A: adds a new test method only; existing test methods and the module import surface are unchanged.

## Security considerations
N/A: test-only addition; no runtime code path or secret handling is touched.

## Rollback considerations
N/A: revert the commit (single test-method addition).

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_retry_helper.py` | Regression: custom non-string-constructor `RuntimeError` propagates as its own type, chains, no `AttributeError` | `uv run pytest tests/agent/test_retry_helper.py -v` | New `test_custom_runtime_error_non_string_constructor_preserved` passes; existing `test_*_preserved` still pass |

## Completion criteria

- `test_custom_runtime_error_non_string_constructor_preserved` exists in `TestRetryHelperExceptionPreservation` and passes.
- The test asserts type preservation, `__cause`_ chaining, and the absence of an `AttributeError`/`TypeError` on double failure.
- Existing standard-type tests still pass; `ruff`, `mypy`, `bandit`, and full `pytest` are clean.

## Out of scope
Any change to `scripts/agent/shared/retry_helper.py`, modification of existing `test_*_preserved` tests, and changes outside the retry-helper test module.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the custom-constructor regression test to `tests/agent/test_retry_helper.py` | In Progress | 20261016-113838 | — |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: `REQ-006`
- **Source issue**: `issues/20261016-092822_mcp001_double_startup_failure_crashes_mcp_loop.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-094937_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-113838
- **Related target files**: `tests/agent/test_retry_helper.py`