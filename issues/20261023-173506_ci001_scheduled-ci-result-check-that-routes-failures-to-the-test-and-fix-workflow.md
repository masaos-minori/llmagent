# Scheduled CI result check that routes failures to the test-and-fix workflow

## Priority
Low

## Summary
Add a periodic, read-only check of the latest CI result on `master` that reports a red run or a repeated failure of the same test, and points the reader to the `python-test-and-fix` workflow. The check must not change code or re-run anything by itself.

## Background
CI is defined in `.github/workflows/ci.yml` (`lint` and `test` jobs on push and pull request). Flaky failures have so far been found by chance after the fact:

- `issues/done/20261020-194610_testflaky001_clock-boundary-assertions-in-shared-json_utils-tests-make-ci-flaky.md` was filed from one red run (CI run `39406860045`) whose next run passed. It is fixed by commit `2e27d444a` (`Explicit in code`: the test now uses `freeze_time`).
- `issues/done/20260927-075303_test002_flaky-tests-observed-in-full-suite-run.md` and `issues/done/20261019-143959_testfix002_flaky-mdq-mtime-test.md` are earlier flaky-test cases.

A project memory note records CI as green on 2026-10-20 with one flaky test. That test is the one fixed above, so the note is stale and no known flaky test is open (`Needs confirmation`: this was checked against issue and commit history only, not against recent CI runs).

## Problem
Nothing watches CI between sessions. A red or intermittently failing run is noticed only when someone looks, so a flaky test can recur several times before an issue is filed. The test suite uses `pytest-randomly`, `pytest-rerunfailures`, and `pytest-xdist` (`pyproject.toml` dev dependencies), which makes order-dependent or timing-dependent failures plausible, but no record of failures per test accumulates.

## Reason for Change
Evidence is thin: there have been three flaky-test issues in about a month, each found by chance. This is a low-cost improvement to detection, not a fix for a known defect, hence Low priority. It becomes worthwhile only if a notification channel is already available.

## Implementation Intent
Use the existing scheduling mechanism rather than new CI infrastructure: a scheduled agent or recurring session task that reads recent run results with the `gh` CLI (available on this machine) and reports. Output is a short report only. Any follow-up (issue filing, test fixing) stays a human-approved step handed to `python-test-and-fix` and `issue-creator`. The check should group failures by test identifier so a repeat across runs is visible.

## Target Files or Areas
- A scheduled-task definition (location Unknown; depends on the chosen mechanism, such as the `schedule` or `loop` skill)
- `.github/workflows/ci.yml` (read only; no change expected)
- A short operational note in docs or `rules/` if the check is adopted (location Unknown)

## Required Changes
- Choose the mechanism (cloud scheduled agent, local recurring task, or GitHub Actions scheduled workflow) and record the reason.
- Define the query: latest N runs on `master`, conclusion, failed job, failed test identifiers.
- Define the report: red run summary and tests that failed in two or more of the last N runs.
- Define where the report is delivered (see Unresolved Questions).
- Write the operational note: schedule, owner, how to disable.

## Constraints
- Read-only against the remote: no re-run, no workflow dispatch, no push.
- No credentials stored in the repository; use the existing `gh` authentication only.
- Must not send repository content to an external service not already in use (`AGENTS.md` Execution policy: sending messages to external services needs confirmation).

## Acceptance Criteria
- A scheduled run produces a report for a known-red run and for a known-green period, verified once on real data.
- The report lists failed test identifiers and flags repeats.
- The check performs no write operation (verified by reading the command list it uses).
- The schedule and the way to disable it are documented.

## Testing Expectations
Manual verification against live run history. If a helper script is added under `tools/`, apply `routing.md` "Adding a new tool" validation, including a unit test for the grouping logic with fixed sample data.

## Documentation Impact
An operational note is needed: schedule, delivery channel, ownership, and the rule that follow-up is manual. If a `tools/` script is added, update `tools/TOOL_DESCRIPTIONS.md`.

## Out of Scope
- Fixing any flaky test.
- Changing `ci.yml`, pytest plugins, or retry settings.
- Automatically filing issues or opening pull requests from CI failures.
- Lazy loading of the Step 0 mandatory-load set — no action required: the fixed load is absorbed by the prompt cache (user decision 2026-10-24).

## Dependencies
Sibling-issue check: no open issue under `issues/` covers CI monitoring (`N/A: none` overlap). Loosely related to the closed flaky-test issues listed in Background.

## Unresolved Questions
- Is a delivery channel (notification, chat, or only a file in the session) acceptable and available? Unknown.
- Is the remote CI the GitHub Actions workflow in `.github/workflows/ci.yml`, and does `gh` have access to its runs? Assumed yes; not verified.
- Is any scheduled task already running in this repository that this would duplicate? Unknown (the scheduling state was not inspected).
- Should this stay open at all given the thin evidence, or be closed until a fourth flaky case appears?

## AI Implementation Instruction
Keep the change read-only and minimal. Do not modify CI configuration or tests. Do not create or enable a schedule without explicit user confirmation of the delivery channel. Stop and report if `gh` cannot read run history.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-173506
- **Related target files**: `.github/workflows/ci.yml`
