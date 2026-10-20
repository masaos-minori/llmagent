# Clock-boundary assertions in shared json_utils tests make CI flaky

## Priority
Medium

## Summary
Make the `now_iso` and `now_iso_raw` tests in `tests/shared/test_json_utils.py` independent of the wall clock, so that a second or midnight boundary falling inside a test can no longer fail CI.

## Background
CI run `39406860045` (commit `df00f7e2b`) failed in the `test` job with a single failure and 9661 passed:

- `tests/shared/test_json_utils.py::TestNowIso::test_now_iso_consistent_across_calls_same_second` failed with `assert '2026-10-20T10:22:49Z' == '2026-10-20T10:22:50Z'`.
- The next run on `e8d7d96b9`, whose change did not touch this area, passed in full, and a local full-suite run of the same tests passed repeatedly before it.
- The change in `df00f7e2b` and `e8d7d96b9` only touched `deploy/` shell scripts and a CI workflow, so it cannot influence this test.

Related history: `issues/done/20260927-075303_test002_flaky-tests-observed-in-full-suite-run.md` handled other flaky tests; it does not mention `json_utils`. No open issue under `issues/` covers this file.

## Problem
`test_now_iso_consistent_across_calls_same_second` calls `now_iso()`, sleeps 10 ms, calls `now_iso()` again, and asserts the two strings are equal. `now_iso()` has one-second resolution, so the assertion fails whenever a second boundary falls inside that 10 ms window, which is roughly 1 in 100 runs by construction (derived from the 10 ms sleep against a 1 s resolution, not measured).

Two sibling tests in the same file have the same structure and are exposed to the same class of failure, though only the first has been observed failing:

- `test_now_iso_raw_consistent_across_calls_same_second` sleeps 10 ms and compares the first 19 characters of two `now_iso_raw()` results.
- `test_now_iso_date_changes_at_midnight` calls `now_iso()` and then compares its date to a date read from a separate clock call, so it fails if UTC midnight falls between the two calls.

The assertions describe a property of `now_iso`'s format and clock source, not a property that needs real elapsed time to verify.

## Reason for Change
A red CI run costs a re-run and obscures real failures, and each unrelated failure erodes trust in the suite. The tests can be made deterministic at small cost, and the repository already declares a time-freezing library as a dev dependency (`freezegun` in `pyproject.toml`), so no new dependency is needed.

## Implementation Intent
Verify the intended properties against a controlled clock instead of the real one:

- For the "same second" tests, freeze time so two calls within one frozen instant must return the same value, and advance the frozen clock across a boundary to show the value changes. This tests the formatting and truncation contract directly.
- For the midnight test, freeze time at a known instant (including one just before midnight) and assert the date part from that instant rather than from a second clock read.
- Keep the tests that assert only format (suffix, length, absence of an offset) unchanged, since they do not depend on the clock value.
- Do not change `now_iso`, `now_iso_raw`, or their documented behavior.

## Target Files or Areas
- `tests/shared/test_json_utils.py` (classes `TestNowIso` and `TestNowIsoRaw`)

## Required Changes
- Rewrite `test_now_iso_consistent_across_calls_same_second` so it no longer depends on real elapsed time or a second boundary.
- Rewrite `test_now_iso_raw_consistent_across_calls_same_second` the same way.
- Rewrite `test_now_iso_date_changes_at_midnight` so it compares against the frozen instant, not a separate clock read.
- Decide for `test_now_iso_time_changes_over_time` and `test_now_iso_raw_time_changes_over_time` (each sleeps 1.1 s): replace the real sleep with a frozen-clock advance if that keeps the intent, since the two sleeps add about 2.2 s to every run.

## Constraints
- Use the dev dependency already declared; do not add a new one.
- The tests must not touch `/opt/llm` or any production path (see the isolation done in `tests/conftest.py`).
- Behavior of `shared.json_utils` must stay identical.

## Acceptance Criteria
- None of the rewritten tests reads the real clock for its assertion, so none can fail at a second or midnight boundary.
- A boundary case is covered explicitly: two frozen instants one second apart produce different `now_iso()` values, and instants within one second produce the same value.
- `uv run pytest tests/shared/test_json_utils.py` passes and runs no slower than before.
- The full suite still passes, and `uv run python tools/check_mock_patch_targets.py` and the repository's lint and type checks stay clean for the changed file.

## Testing Expectations
- Unit tests only. Run the changed file repeatedly (for example a loop of 20 runs or `pytest --count` if available) to confirm stability, and run the full suite once.
- Optionally demonstrate the old failure deterministically by freezing time at `...:49.995` and showing the old assertion fails while the new one passes; this is evidence, not a test to commit.

## Documentation Impact
No documentation change is expected. No file under `docs/` describes these tests.

## Out of Scope
- Changing `now_iso`, `now_iso_raw`, `scripts/eventbus/json_utils.py`, or any caller.
- Auditing the whole suite for other time-dependent tests. If other sleep-based or clock-comparing tests are found, file a separate issue.
- Changing CI configuration, retries, or quarantining tests.

## Dependencies
N/A: none. No open issue under `issues/` touches `tests/shared/test_json_utils.py`.

## Unresolved Questions
- Whether `test_now_iso_raw_consistent_across_calls_same_second` and `test_now_iso_date_changes_at_midnight` have ever failed in CI is not confirmed; only the first test is evidenced. They are included because they share the cause by construction.
- The roughly 1 in 100 failure rate per run is derived from the sleep length and the one-second resolution, not measured from CI history.

## AI Implementation Instruction
Edit only `tests/shared/test_json_utils.py`. Keep the tests that only check format as they are. Do not modify production code or add dependencies. Prefer the smallest rewrite that removes the real-clock dependency from each flagged test, and keep the test names so history stays traceable unless the name states a now-false property. If a test cannot be made deterministic without changing the intended property, stop and report it rather than weakening the assertion.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261020-194610
- **Related target files**: tests/shared/test_json_utils.py
