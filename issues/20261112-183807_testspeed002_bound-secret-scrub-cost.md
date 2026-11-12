# Bound the cost of secret scrubbing on long string arguments

## Priority
Medium

## Summary
Scrubbing a single 100,000-character string with the content-pattern secrets masker takes about 67 s, which makes one test the longest item of the suite and sets a floor on parallel test time. Identify why the cost is so high and bring it down to a bounded, near-linear cost without changing what the masker detects.

## Background
- `tests/agent/test_tool_result_formatter.py::TestMaskArgsContentScrub::test_large_string_terminates` builds `{"payload": "x" * 100_000}` and calls `mask_args`.
- Measured on 2026-11-12: 67.4 s when run alone (`uv run pytest -p no:randomly -o addopts=""` on that node id), and 97.6 s inside an 8-way parallel run of the whole suite. It is the slowest test of the suite and, being one test, it is also the lower bound of the parallel wall time.
- `scripts/agent/tool_result_formatter.py::_mask_value` calls `_mask_secrets` (from `scripts/agent/secrets_masker.py`) on every string leaf. The `mask_args` docstring says masking is applied before logging and audit writes.
- `scripts/agent/secrets_masker.py` holds a list of case-insensitive regular expressions, several ending in `(\S+)` and one starting with `[a-z][a-z0-9+.-]*://`. `rg` shows six other modules under `scripts/agent/` reference the masker (`startup_mcp_starter.py`, `shared/retry_helper.py`, `http_lifecycle_health_checker.py`, `http_lifecycle_errors.py`, `diagnostic_store.py`, and the formatter), so a slow scrub can affect more than this one call site.
- The test name says "terminates", so the original intent was a guard against a non-terminating scrub; today it terminates but slowly.

## Problem
A 100 KB string argument costs about a minute of CPU in a function that sits on the logging and audit path. Whether a real tool call can carry such a string (for example a large file body) and block on this cost is not established, but the measured cost is far above what a linear scan of 100,000 characters would take.

## Reason for Change
The cost is both a test-suite bottleneck (the largest single entry in the duration profile) and a possible latency risk in production code. The root cause is not yet known; removing it also removes the need to exclude the test from fast loops.

## Implementation Intent
First find the cause by timing each pattern in the masker against the input (a profile, not a guess). The working hypothesis, not confirmed, is superlinear backtracking or repeated start-position scanning for at least one pattern on a long run of letters. Then fix the responsible pattern or add a bounded pre-check so cost grows linearly with input length, keeping the set of secrets that get masked identical. Keep the responsibility boundary: `secrets_masker.py` owns detection; `tool_result_formatter.py` only applies it.

## Target Files or Areas
- `scripts/agent/secrets_masker.py`
- `scripts/agent/tool_result_formatter.py` (only if a bound belongs at the call site)
- `tests/agent/test_tool_result_formatter.py`
- `tests/agent/test_secrets_masker.py`

## Required Changes
- Measure the time each masker pattern takes on the 100,000-character input and record which ones are superlinear.
- Rewrite or guard the responsible pattern(s) so scrub time is near-linear in input length.
- Keep `test_large_string_terminates` and add a regression check that fails if cost becomes superlinear again (for example a bounded run with `pytest-timeout`, or comparing 100,000 and 200,000 characters), without depending on machine speed.
- Add cases to `test_secrets_masker.py` proving the detection results are unchanged for the existing secret forms on short strings.

## Constraints
- Security: no secret form currently masked may become unmasked; the change must be behavior-preserving for detection.
- The masker is shared by several modules; do not change its public function signature.
- Python 3.13 `re` only (no new dependency without justification).

## Acceptance Criteria
- Scrubbing `"x" * 100_000` through `mask_args` completes in under 1 s on the development machine (the 1 s threshold is a proposal; confirm at planning time).
- The root cause is identified and written in the change record.
- Every existing test in `tests/agent/test_secrets_masker.py` and `tests/agent/test_tool_result_formatter.py` passes unchanged.
- A new regression check guards against superlinear scaling.

## Testing Expectations
- Unit tests for detection parity (before and after) on representative secret strings.
- The regression check above.
- `uv run pytest tests/agent/test_secrets_masker.py tests/agent/test_tool_result_formatter.py`, then the full suite once.
- `uv run ruff check`, `uv run mypy`, `uv run bandit` on the touched files.

## Documentation Impact
None expected (no `docs/` behavior change). If a docs page states performance characteristics of masking, it must be updated; 不明 whether one does (not searched).

## Out of Scope
- Changing which secret patterns exist or adding new patterns.
- Changing where masking is invoked.
- Excluding the test from runs instead of fixing the cost (that only hides the problem).

## Dependencies
N/A: none

## Unresolved Questions
- Root cause: 不明. Only the timing was measured; the patterns were not profiled individually.
- Whether `mask_args` runs synchronously before a tool executes, so that a large argument delays the call: 不明. Not traced through `scripts/agent/`.
- Realistic maximum size of a string argument in production: 不明.

## AI Implementation Instruction
Profile before changing anything and report the per-pattern timings. Keep detection behavior identical and add parity tests first. Do not edit unrelated modules that import the masker. If a pattern cannot be made linear without changing what it detects, stop and report the trade-off instead of changing detection.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261112-183807
- **Related target files**: `scripts/agent/secrets_masker.py`, `scripts/agent/tool_result_formatter.py`, `tests/agent/test_tool_result_formatter.py`, `tests/agent/test_secrets_masker.py`
