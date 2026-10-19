# test_failed_reindex_does_not_record_the_new_mtime is intermittently red

## Priority
Low

## Summary
Make `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py::TestRefreshIncrementalBranches::test_failed_reindex_does_not_record_the_new_mtime` deterministic by guaranteeing that the second write changes the file's modification time, as its sibling tests already do, and capture the failure details if it still occurs.

## Background
- The test failed once in a full-suite run on 2026-10-19 (9360 passed, 1 failed after a rebase) and passed on the following single-file, related-directory, and whole-directory reruns; the failure output was not captured.
- Reproduction attempt on 2026-10-19: 40 consecutive isolated runs of this test all passed, so the failure is rare and load- or timing-dependent.
- The service decides whether a file changed from its modification time only (`st_mtime_ns` recorded as `mtime:<path>` in `index_state`); the production path is `_refresh_changed_file` in `scripts/mcp_servers/mdq/indexer.py`.

## Problem
- Hypothesis (not proven): the test writes `"# A\n\nOne"`, runs a refresh, then writes `"# A\n\nTwo"` (same size, 3 bytes) and runs a refresh again expecting a failed re-index (`(0, 0, 1)`). If the two writes receive the same `st_mtime_ns` (coarse filesystem timestamp granularity on this WSL2 host, and a fast first refresh), the second refresh sees an unchanged file and counts a skip (`(0, 1, 0)`), failing the assertion.
- Supporting evidence (Explicit in code): sibling tests in the same file call `time.sleep(0.05)` between writes at four places to force a new modification time; this test does not.
- Confirmed: the assertion `_counters(result) == (0, 0, 1)` and `_index_state_keys(service) == recorded_before` are the two lines that can fail; the actual failure output is unknown.

## Reason for Change
- An intermittently red test wastes investigation time (it was investigated as a possible regression after an unrelated rebase) and can fail CI at random.
- The fix is small and mirrors an existing pattern in the same file.

## Implementation Intent
- Make the modification time change deterministic instead of relying on elapsed time: after the second `write_text`, set a later mtime explicitly with `os.utime(target, ns=(...))` (preferred), or add the same `time.sleep(0.05)` the sibling tests use.
- Do not change the production change-detection logic here; whether mtime-only detection should also consider the file size (a same-tick, same-size edit would be missed in production too) is a separate design question.
- Keep the assertions as they are.

## Target Files or Areas
- `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`
- `scripts/mcp_servers/mdq/indexer.py` (read only; no change expected)

## Required Changes
- In `test_failed_reindex_does_not_record_the_new_mtime`, ensure the file's mtime after the second write is strictly greater than the first, using `os.utime` with an explicit later timestamp (or the sibling tests' `time.sleep(0.05)`).
- Check the other tests in the file that rewrite a file after an initial refresh (for example the `"World Changed"` and `"Changed Content"` cases) and apply the same guarantee where one is missing.
- If the test still fails intermittently, add the actual counters to the assertion message so the next failure is diagnosable.

## Constraints
- Do not change `_refresh_changed_file` or the `index_state` format.
- Keep the test fast and free of long sleeps.

## Acceptance Criteria
- The test passes in repeated runs under load (for example 200 consecutive runs while the machine is busy) with no failure.
- Every test in the file that rewrites a file after an initial refresh guarantees a changed modification time.
- The rest of the file's tests are unchanged in behavior.

## Testing Expectations
- `uv run pytest tests/mcp_servers/mdq/test_mdq_incremental_refresh.py -q`, then a repeated loop of the single test (for example 200 runs, optionally with CPU load).
- The `rules/toolchain.md` sequence for the changed file.

## Documentation Impact
Not required (test-only change).

## Out of Scope
- Changing production change detection to include size or content hashing (a separate decision, to be filed only if the owner wants it).
- The failing GitHub tool definitions test (filed separately as testfix001).

## Dependencies
- N/A: none. No open issue under `issues/` overlaps; sibling check recorded 2026-10-19.
- Related: testfix001 (separate test problem; independent).

## Unresolved Questions
- The exact failure output of the single observed failure (not captured); the mtime-tie hypothesis is unconfirmed.
- Whether the mtime-only detection in production deserves a follow-up for same-size edits within one timestamp tick.

## AI Implementation Instruction
- Keep the diff to the test file; do not change the indexer.
- Use `os.utime` or the existing sleep pattern; do not add long sleeps.
- Stop and report if the test still fails after the mtime is guaranteed to differ (the hypothesis would then be wrong).

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261019-143959
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`
