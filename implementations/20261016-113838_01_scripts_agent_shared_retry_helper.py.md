## Goal

Fix `retry_once_with_delay` (`scripts/agent/shared/retry_helper.py`) so that a second failed attempt to start an HTTP subprocess MCP server re-raises a clean, catchable error instead of an `AttributeError` caused by misusing `HttpStartupError`'s constructor, so a persistently misconfigured server is routed through the required/non-required decision matrix instead of aborting startup for every remaining MCP server. (`REQ-001`, `REQ-004`)

## Scope

- **In-Scope**:
  - Rework the second-attempt re-raise at line 60 into a payload-aware, constructor-safe re-raise that preserves type semantics for standard exceptions and never raises `AttributeError` for custom-constructor exceptions.
  - Keep `fatal_prefix` + `_mask_secrets` message construction (lines 57-59) intact.
  - Narrow the module docstring if it overclaims the reconstruction guarantee.
- **Out-of-Scope**:
  - Modifying `scripts/agent/http_lifecycle_errors.py` (`HttpStartupError`) — no defensive-constructor fix.
  - Changes to command validation, subprocess launch, health polling, or process termination.
  - Changing first-attempt behavior or shutdown-event racing semantics (`_interruptible_sleep`, `StartupInterrupted`).

## Assumptions

- Exactly two callers exist (confirmed by `rg`): `start_servers` (`startup_mcp_starter.py:103`, can raise `HttpStartupError` through the command-validation path) and `verify_health` (`:173`, raises plain `RuntimeError(f"HTTP {resp.status_code}")`, which accepts a message string and is unaffected by this defect).
- `HttpStartupError.__init__(self, failure: StartupFailure)` (`http_lifecycle_errors.py:31-34`) stores `self.failure = failure` then calls `super().__init__(failure.reason)`; passing a `str` sets `self.failure = "<str>"` and evaluates `"<str>".reason`, raising `AttributeError`.
- `start_servers` catches `(OSError, RuntimeError, TimeoutError, ConnectionRefusedError, ConnectionResetError, BrokenPipeError)` (`startup_mcp_starter.py:88-95`), which excludes `AttributeError`, so the second-attempt `AttributeError` currently escapes uncaught.
- The fix must not change the first-attempt path or the shutdown-racing semantics.
- No defensive/constructor fix is applied to `HttpStartupError` itself.

## Design decisions

- Add a private synchronous helper `_rebuild_after_retry(err, message)` that (a) reconstructs the original type from a stored payload when available via a guarded `getattr(err, "failure", None)` → `type(err)(payload)`, (b) falls back to `type(err)(message)` for standard exceptions, and (c) falls back further to preserving the type plus `.args` without invoking the constructor (`cls.__new__(cls)` then assign `.args`) for any exotic constructor.
- Preserve `fatal_prefix` + `_mask_secrets` and chain `from retry_err`; do not modify `HttpStartupError`.

## Alternatives considered

Prefer payload reconstruction and standard `type(err)(message)` over generic wrapping; fall back to the `__new__`-based preserve-type+args only when `type(err)(message)` itself fails, so a caller relying on the exact exception type is not altered.

## Implementation
### Target file
`scripts/agent/shared/retry_helper.py`
### Procedure
1. Add `_rebuild_after_retry(err: Exception, message: str) -> BaseException` at module scope in `scripts/agent/shared/retry_helper.py` (below `retry_once_with_delay`).
2. Replace the re-raise at line 60 (`raise type(retry_err)(masked_msg) from retry_err`) with `raise _rebuild_after_retry(retry_err, masked_msg) from retry_err`. Leave lines 57-59 (`fatal_prefix` + `_mask_secrets`) untouched.
3. If the module docstring implies `type(err)(message)` always works, narrow it to state the constructor-safe reconstruction contract.
### Method
- Locate the second-attempt block (lines 54-60): `except Exception as retry_err:` builds `msg`/`masked_msg` then executes the line-60 re-raise.
- Insert `_rebuild_after_retry` after `retry_once_with_delay`:
  ```python
  def _rebuild_after_retry(err: Exception, message: str) -> BaseException:
      payload = getattr(err, "failure", None)
      if payload is not None:
          try:
              return type(err)(payload)
          except Exception:  # noqa: BLE001 — fall through to standard handling
              pass
      try:
          return type(err)(message)
      except Exception:  # noqa: BLE001 — exotic constructor; preserve type without invoking it
          rebuilt = type(err).__new__(type(err))
          rebuilt.args = err.args
          return rebuilt
  ```
- Substitute the helper into line 60, keeping `from retry_err`.
### Details
- Root cause: `HttpStartupError.__init__` requires a `StartupFailure` and reads `failure.reason`; the old `type(retry_err)(masked_msg)` passed a `str`, producing `"<str>".reason` → `AttributeError`, which is outside the caught tuple and escapes `start_servers` before the post-retry decision matrix (lines 110-122) runs.
- Payload reconstruction uses a guarded `getattr(err, "failure", None)` (non-coupling when the attribute is absent) rather than `isinstance`, per the plan's Design trade-off; for `HttpStartupError` the payload is a `StartupFailure`, so `type(err)(payload)` reconstructs the original type correctly.
- Standard fallback `type(err)(message)` covers `TimeoutError`/`ConnectionRefusedError`/`RuntimeError` (constructors accept a message), preserving the existing `test_*_preserved` tests.
- Exotic fallback preserves the type and `.args` without invoking the constructor (`cls.__new__(cls)` + assign `.args`); reached only when `type(err)(message)` itself raises. Documented here; the regression test (sibling document `tests/agent/test_retry_helper.py`) pins the primary custom-constructor case.
- Chaining `from retry_err` and the `fatal_prefix`/`_mask_secrets` construction above are unchanged.

## Compatibility considerations
N/A: the signature and public behavior of `retry_once_with_delay` are unchanged; only the internal second-attempt re-raise is reworked.

## Security considerations
The existing `_mask_secrets` call (lines 57-58) and `fatal_prefix` are preserved verbatim, so secret masking is unchanged; the fix removes the `AttributeError` that previously hid the real (masked) cause rather than introducing new logging.

## Rollback considerations
N/A: revert the commit (single logical change confined to one function).

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/shared/retry_helper.py` | Lint / type / arch / security | `uv run ruff format scripts/`, `ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | Clean; no new findings vs. baseline (bandit low-severity already `noqa`'d); import-linter 6 kept, 0 broken |
| `scripts/agent/shared/retry_helper.py` | Standard-type preservation + custom-constructor non-`AttributeError` + chaining (regression test authored in sibling document `tests/agent/test_retry_helper.py`) | `uv run pytest tests/agent/test_retry_helper.py -v` then full `uv run pytest` | Existing `test_timeout_error_preserved`/`test_connection_refused_error_preserved`/`test_runtime_error_preserved` pass; new custom-constructor test passes; no `AttributeError` escapes `start_servers` |

## Completion criteria

- On double failure, `retry_once_with_delay` re-raises a catchable exception for `HttpStartupError` (reconstructed from its `StartupFailure`), standard exceptions (type preserved), and exotic constructors (type preserved, chained, no `AttributeError`).
- `fatal_prefix` + `_mask_secrets` message construction is unchanged; the existing standard-type tests still pass.
- `ruff`, `mypy`, `lint-imports`, `bandit`, and full `pytest` are clean.

## Out of scope
`scripts/agent/http_lifecycle_errors.py` (`HttpStartupError`), command validation, subprocess launch, health polling, process termination, first-attempt behavior, and shutdown-event racing semantics.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details (add `_rebuild_after_retry`, replace line-60 re-raise) | In Progress | 20261016-113838 | — |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Regression test authored in sibling document `tests/agent/test_retry_helper.py` |
| 3 | Update documentation (module docstring) if in scope per Compatibility/Out of scope | Pending | — | — |  |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`
- **Source issue**: `issues/20261016-092822_mcp001_double_startup_failure_crashes_mcp_loop.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-094937_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-113838
- **Related target files**: `scripts/agent/shared/retry_helper.py`