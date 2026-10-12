# Startup prompt setup swallows all memory-injection errors as a generic disabled flag

## Priority
Low

## Summary
In `PromptSetup.setup_prompt()`, the memory-injection call is wrapped in `except Exception`,
and any exception sets `ctx.conv.memory_disabled = True` regardless of cause. The classifier
only distinguishes `NETWORK_TRANSIENT` (ConnectionError/TimeoutError) from `DATABASE_OR_IO`
(sqlite3.Error/OSError) from `UNKNOWN`. A genuine programming error (e.g. `AttributeError`,
`TypeError`, `KeyError`) in the memory service is logged as `UNKNOWN` and downgraded to
"continue without memory", which masks root causes and makes memory-subsystem bugs look like a
benign network/DB condition. Narrow the catch to the expected failure domains and let
unexpected exceptions propagate (or be reported distinctly) so they are not silently classified
as benign.

## Background
`startup_prompt_setup.py` injects semantic memories into the initial system prompt. On failure
it must not abort startup, so it catches broadly, classifies the cause, sets a global
`memory_disabled` flag, and continues. This is a deliberate fail-safe for runtime conditions
(network flakiness, DB unavailability).

## Problem
`except Exception` also catches programming errors (`AttributeError`, `TypeError`,
`IndexError`, etc.) that indicate a real bug in the memory service or in `setup_prompt` itself.
`_classify_memory_failure` maps everything that is not a network/DB error to `UNKNOWN`, which is
logged at `info` level and produces only a single non-fatal view warning. The net effect: a
memory-service defect is indistinguishable from a transient network blip, and the root cause is
unlikely to be investigated because it is buried in an `UNKNOWN` info log plus one warning.

## Reason for Change
Fail-safe-on-runtime-error is correct; fail-safe-on-programming-error hides defects. Startup
memory injection should tolerate the documented runtime failure modes but surface unexpected
exceptions so they are visible during development and in logs, rather than being normalized into
a generic "disabled" state.

## Implementation Intent
- Keep the fail-safe behavior for the documented runtime domains: `ConnectionError`,
  `TimeoutError`, `sqlite3.Error`, `OSError`.
- For any other exception, do not silently normalize it. Options (pick one and document it):
  - Re-raise after logging at `error` so the failure is visible (accepting that startup may
    abort — coordinate with the caller's error handling), or
  - Record it under a distinct, high-priority category that is surfaced prominently (not
    collapsed into the benign `UNKNOWN` path), and/or escalate via the existing fatal/warning
    pipeline if one is available at this call site.
- Extend `_classify_memory_failure` to distinguish `PROGRAMMING_ERROR` from `UNKNOWN`.

## Target Files or Areas
- `scripts/agent/startup_prompt_setup.py` (`setup_prompt()`, `_classify_memory_failure()`)
- `scripts/agent/startup.py` — read only, to see how a memory-setup failure is handled upstream

## Required Changes
- Narrow the `except Exception` around `on_session_start(...)` to the runtime failure domains
  that justify silent continue.
- Route unexpected exceptions to a distinct, visible category instead of collapsing them into
  `UNKNOWN`.
- Update `_classify_memory_failure` to add a `PROGRAMMING_ERROR` category.

## Constraints
- Startup must still proceed for the documented runtime failures (network/DB) — do not make
  those fatal.
- Coordinate with the caller so that surfacing an unexpected exception does not break the
  startup contract (startup should complete; the question is visibility, not necessarily abort).

## Acceptance Criteria
- A `ConnectionError`/`TimeoutError`/`sqlite3.Error`/`OSError` during memory injection still
  results in graceful continue with the correct category.
- An unexpected exception (e.g. `AttributeError`) is no longer normalized into the benign
  `UNKNOWN` continue path without distinct visibility.
- Existing memory-failure tests still pass; add a test for a non-runtime exception.

## Testing Expectations
- Add a test that raises a non-runtime exception from `on_session_start` and asserts the
  category/classification differs from the benign path (and is surfaced, per the chosen policy).
- Re-run `tests/agent/test_startup_memory_failures.py` and `test_startup_prompt_setup.py`.
- `ruff check`, `mypy`, full suite green.

## Documentation Impact
Update `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` if it
documents the memory-failure classification categories.

## Out of Scope
- Any change to the memory service itself (`on_session_start`).
- Changes to unrelated startup checks.

## Dependencies
N/A: none

## Unresolved Questions
- Whether the caller (`startup.py`) can tolerate an unexpected exception propagating, or whether
  the fix must keep startup completing while merely improving visibility.
- Whether `UNKNOWN` currently carries any downstream behavior beyond logging.

## AI Implementation Instruction
Confirm the runtime failure domains that justify silent continue, narrow the catch accordingly,
and add a distinct `PROGRAMMING_ERROR` category for unexpected exceptions. Decide with the
caller whether such exceptions may propagate or must be surfaced without aborting startup. Do
not change the memory service or other startup checks.

## Traceability
- **Workflow phase**: `python-code-review` + `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `N/A: not filed from a Plan`
- **Source implementation procedure**: `N/A: not filed from an implementation procedure`
- **Generated at**: 20261012-124838
- **Related target files**: `scripts/agent/startup_prompt_setup.py`
