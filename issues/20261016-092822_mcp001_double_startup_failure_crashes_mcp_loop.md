# Double startup failure of an HTTP subprocess MCP server raises AttributeError instead of a fatal error, crashing the whole MCP startup loop

## Priority
High

## Summary
Fix `retry_once_with_delay` so that a second failed attempt to start an HTTP subprocess MCP server re-raises a clean, catchable error instead of an `AttributeError` caused by misusing `HttpStartupError`'s constructor. A persistently misconfigured server must either be disabled (required=false) or raise a fatal `RuntimeError` (required=true); today it raises `AttributeError`, which aborts startup for every remaining MCP server.

## Background
`scripts/agent/startup_mcp_starter.py::McpServerStarter.start_servers` starts each HTTP/subprocess MCP server once, then wraps a second attempt in `retry_once_with_delay` (`scripts/agent/shared/retry_helper.py`). On the second failure the helper executes `raise type(retry_err)(masked_msg)`, where `masked_msg` is a plain `str`. `HttpStartupError` (`scripts/agent/http_lifecycle_errors.py`) is a `RuntimeError` whose `__init__(self, failure: StartupFailure)` stores `failure` and reads `failure.reason`. The command-validation path raises `HttpStartupError(StartupFailure(...))` (`scripts/agent/http_lifecycle.py::_create_and_validate_proc`).

## Problem
Verified against the code on 2026-10-16:
- `HttpStartupError.__init__` requires a `StartupFailure` and accesses `failure.reason`. Passing a `str` (what `retry_once_with_delay` does on line 60) sets `self.failure = "<str>"` and then evaluates `"<str>".reason`, which raises `AttributeError`.
- `start_servers` catches `(OSError, RuntimeError, TimeoutError, ConnectionRefusedError, ConnectionResetError, BrokenPipeError)`. `HttpStartupError` is a `RuntimeError` and is caught on the first attempt, but the `AttributeError` raised on the second attempt is NOT in that tuple, so it propagates uncaught out of `start_servers`.
- Consequence: a server that fails both attempts crashes the entire startup loop before any later server is started. The two post-retry branches in `start_servers` (disable non-required servers via `disable_server`, or raise a fatal `RuntimeError` for required servers) are never reached, so neither the required nor the non-required decision matrix is applied.

## Reason for Change
A single server with a permanent misconfiguration (bad command, missing dependency, etc.) currently takes down startup of all other MCP servers with an unrelated `AttributeError`, hiding the real cause and breaking the required/non-required failure policy.

## Implementation Intent
Make the retry helper re-raise in a way that is safe for every exception type raised by the subprocess-start path, including custom exceptions whose constructor does not accept a message string. Prefer reconstructing the original exception from its stored payload (e.g. re-raise `HttpStartupError(failure)` using the captured `StartupFailure`) over `type(err)(str_message)`, or fall back to chaining a new exception without calling the original constructor. Keep the fatal prefix and secret masking.

## Target Files or Areas
- `scripts/agent/shared/retry_helper.py` (Phase 4 primary)
- `scripts/agent/http_lifecycle_errors.py` (evidence; possible defensive fix)
- `scripts/agent/startup_mcp_starter.py` (verify both failure branches are reached)
- `tests/agent/test_retry_helper.py`

## Required Changes
- Ensure a second failed attempt re-raises a catchable exception that preserves the original type semantics; never call `type(original_error)(str)` when that constructor has a non-standard signature.
- Confirm `HttpStartupError` raised twice still resolves through the required/non-required decision matrix in `start_servers` (disable vs. fatal `RuntimeError`).
- Preserve secret masking (`_mask_secrets`) and the fatal prefix on the re-raised message.
- Add a regression test: a helper whose function raises a custom `RuntimeError` subclass with a non-string constructor on both attempts must not raise `AttributeError`.

## Constraints
- Do not change the first-attempt behavior or the shutdown-event racing semantics.
- Preserve exception chaining (`from retry_err`) so the original traceback is retained.
- No changes to the allowed-command or subprocess-launch logic; this is a retry-helper defect only.

## Acceptance Criteria
- A subprocess MCP server that fails both attempts raises either a fatal `RuntimeError` (required) or returns control so `disable_server` runs (non-required); no `AttributeError` escapes `start_servers`.
- The re-raised exception carries the masked fatal message and chains the original error.
- Existing `retry_once_with_delay` tests still pass and a new regression test covers the custom-constructor case.

## Testing Expectations
- Unit tests for `retry_once_with_delay` covering: standard exception, custom `RuntimeError` subclass with a non-string constructor, and shutdown-during-retry.
- Integration-style test that a double-failing `HttpStartupError` reaches the correct `start_servers` branch.
- `ruff`, `mypy --no-namespace-packages scripts/`, bandit, full `pytest` with sandbox config.

## Documentation Impact
None required. Document the retry helper's re-raise contract in a docstring comment if the current one implies `type(err)(message)` always works.

## Out of Scope
- Changes to command validation, subprocess launch, health polling, or process termination.
- Reworking the broader startup retry/discovery flow beyond this defect.

## Dependencies
- `N/A: none`

## Unresolved Questions
- Whether other callers of `retry_once_with_delay` (health-check retry in `startup_mcp_starter.py`) also raise custom-constructor exceptions that would hit the same bug. Evidence suggests the health-check retry raises plain `RuntimeError`, but this should be confirmed during implementation.

## AI Implementation Instruction
Implement only the retry-helper re-raise defect. Do not touch subprocess launch, command validation, health polling, or termination. Confirm every caller of `retry_once_with_delay` passes an exception whose constructor accepts the masked string or handle the general case. Add a regression test for the custom-constructor failure. No compatibility shims.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261016-092822
- **Related target files**: scripts/agent/shared/retry_helper.py, scripts/agent/http_lifecycle_errors.py, scripts/agent/startup_mcp_starter.py
