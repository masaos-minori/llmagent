# Fix `TypeError: object MagicMock can't be used in 'await' expression` in 6 `test_startup.py` memory-injection tests

## Priority
Medium

## Summary
Six tests in `tests/agent/test_startup.py` (`TestStartupMemoryFailures::test_memory_injection_categorized_logging` × 3 parametrizations, and `TestStartupOrchestratorSetupPrompt` × 3) currently fail with
`TypeError: object MagicMock can't be used in 'await' expression` when `StartupOrchestrator._setup_prompt()` calls `await ctx.conv.replace_history(...)`. This was discovered while running the Workflow Engine test suite during the ADR-001 update (2026-08-31); it is unrelated to ADR-001 and was not caused by any change made in that work (no source or test files were modified).

## Background
`scripts/agent/startup.py::_setup_prompt()` at the line calling `ctx.conv.replace_history([...])` awaits the call, but the test fixtures in the two affected test classes construct `ctx.conv` (or the object standing in for it) as a plain `MagicMock` rather than an `AsyncMock` (or a mock with an async `replace_history`), so the awaited call raises `TypeError` instead of returning a coroutine.

## Problem
(Evidence: Explicit in code — full traceback below)

```
tests/agent/test_startup.py:1534 (and :561, :576, :612): await startup._setup_prompt()
scripts/agent/startup.py:670: await ctx.conv.replace_history([{"role": "system", "content": initial_prompt}])
TypeError: object MagicMock can't be used in 'await' expression
```

Failing tests:
- `TestStartupMemoryFailures::test_memory_injection_categorized_logging[ValueError-info-invalid value]`
- `TestStartupMemoryFailures::test_memory_injection_categorized_logging[Error-error-database error]`
- `TestStartupMemoryFailures::test_memory_injection_categorized_logging[ConnectionError-warning-connection refused]`
- `TestStartupOrchestratorSetupPrompt::test_memory_snippets_are_injected_when_enabled`
- `TestStartupOrchestratorSetupPrompt::test_no_memory_injection_when_disabled`
- `TestStartupOrchestratorSetupPrompt::test_memory_snippets_truncated_when_exceeds_limit`

Reproduce with: `uv run pytest tests/agent/test_startup.py -k "TestStartupMemoryFailures or TestStartupOrchestratorSetupPrompt" -q`

## Reason for Change
A failing test suite for memory-injection/prompt-setup behavior means regressions in this area (categorized logging on memory-load failure, snippet truncation, enable/disable behavior) would not be caught. Since `ctx.conv.replace_history()` is genuinely async in current code, the test fixture is out of sync with the interface it mocks.

## Implementation Intent
Update the shared fixture/mock construction in these two test classes so that `ctx.conv` (or whichever object exposes `replace_history`) uses an async-compatible mock (e.g., `unittest.mock.AsyncMock` for the `replace_history` attribute, or construct the whole `conv` mock with `spec`/`AsyncMock` where appropriate) so the `await` in `_setup_prompt()` resolves normally.

## Target Files or Areas
- `tests/agent/test_startup.py` (`TestStartupMemoryFailures`, `TestStartupOrchestratorSetupPrompt` fixture/mock setup)
- `scripts/agent/startup.py::_setup_prompt()` — read-only reference; not expected to require changes

## Required Changes
- Identify where `ctx.conv` (or the object exposing `replace_history`) is constructed in the fixtures for `TestStartupMemoryFailures` and `TestStartupOrchestratorSetupPrompt`.
- Replace the plain `MagicMock` with an async-aware mock for the `replace_history` method (or the whole object, if appropriate), consistent with how other async methods on the same object are mocked elsewhere in this test file.
- Confirm no other test in `test_startup.py` relies on `replace_history` being a synchronous mock (i.e., changing it does not break other currently-passing tests in the same file).

## Constraints
- Do not change `scripts/agent/startup.py`'s `_setup_prompt()` behavior — the `await` is correct given `replace_history` is genuinely async in current code.
- Do not broaden the fix beyond the fixtures used by the six failing tests unless a shared fixture is used more widely and needs the same correction.

## Acceptance Criteria
- All six listed tests pass.
- `uv run pytest tests/agent/test_startup.py -q` shows no new failures compared to before this fix.

## Testing Expectations
Run `uv run pytest tests/agent/test_startup.py -q` before and after the fix and confirm only the six listed tests change from failing to passing, with no other regressions. Apply the standard validation sequence in `rules/toolchain.md`.

## Documentation Impact
None — this is a test-only fix with no behavioral or architectural change.

## Out of Scope
- Any other test in `test_startup.py` not listed above.
- Changes to `scripts/agent/startup.py` or `ctx.conv`'s production implementation.

## Dependencies
Discovered during the 2026-08-31 ADR-001 update while running `tests/agent/workflow/`, `tests/agent/shared/test_startup_validation_pipeline.py`, and `tests/agent/test_startup.py` together as Verification evidence. Not caused by that update.

## Unresolved Questions
N/A: none — the fix (mock construction mismatch with an async interface) is clear from the traceback.

## AI Implementation Instruction
Read the fixture setup for `TestStartupMemoryFailures` and `TestStartupOrchestratorSetupPrompt` in full before editing. Change only the mock construction for the object exposing `replace_history`; do not modify `scripts/agent/startup.py`. Re-run the full `test_startup.py` file (not just the six failing tests) to confirm no other test depended on the prior synchronous-mock behavior.
