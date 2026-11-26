# Report only new test failures against a recorded baseline

## Priority
Medium

## Summary
Add a tool that compares a pytest run with a recorded set of known failing test ids and reports only the new failures, the newly fixed tests, and the count of unchanged known failures, so a full-suite run with a known unrelated failure no longer needs manual triage each time.

## Background
Evidence (`Explicit in code`): the repository already keeps baselines that only shrink, for example `tools/check_module_size_baseline.txt` and `tools/check_archived_status_baseline.txt`; no equivalent exists for test failures.

In one working session the full suite (about five minutes in parallel with coverage) was run five times with the same 26 failures and 88 errors from one unrelated defect (issues/20261126-151436_wfeff001_cmd-mcp-import-nameerror.md). Each run needed a grouping of the failing files and a check that none touched a changed file. `skills/code-implementation/workflow.md` Step 4 and `skills/python-test-and-fix/SKILL.md` forbid hiding a failure (the failure is neither skipped nor deselected).

## Problem
A known, unrelated failure forces the same manual triage after every full run, and a genuinely new failure could be missed in a long list.

## Reason for Change
Token and time cost per run, and a correctness risk from reading long failure lists. Not urgent.

## Implementation Intent
A read-only comparison tool plus a baseline file whose entries each cite a tracking issue. The tool never changes what runs and never marks a test as passed; it only classifies the failures of a run. Entries may only be removed in normal use, as with the existing baselines.

## Target Files or Areas
- `tools/compare_test_baseline.py` (new) and its baseline file
- `tools/TOOL_DESCRIPTIONS.md`, `rules/tool-gates.md`
- `skills/code-implementation/workflow.md` (Step 4 triage of a pre-existing failure)

## Required Changes
- Read the failing and erroring test ids of a pytest run (a JUnit XML file written with `--junitxml`, or another machine-readable output; choose one and justify it for `-n logical` runs).
- Compare with the baseline file: report new failures (exit 1), baseline entries that now pass (to be removed, exit 0 with a notice), and the count of unchanged known failures.
- Require each baseline entry to carry a reason that names an issue path; refuse an entry without one.
- Provide an explicit update mode that can only remove entries or add entries with a reason, never from a plain run.
- Register the tool in `tools/TOOL_DESCRIPTIONS.md` and `rules/tool-gates.md`, and point Step 4 of `skills/code-implementation/workflow.md` to it for the "pre-existing, unrelated failure" branch.

## Constraints
- A failure must never be hidden from the suite itself: no skip, xfail, or deselect.
- The tool must work on xdist (`-n logical`) output.
- New or errored tests at collection time (module import errors) must count as new failures.

## Acceptance Criteria
- [ ] A run with only baseline failures reports no new failure and exits 0.
- [ ] A run with one additional failing test exits 1 and names it.
- [ ] A baseline entry that now passes is reported for removal.
- [ ] A baseline entry without an issue path is rejected.

## Testing Expectations
Unit tests with synthetic JUnit XML (known only, new, fixed, collection error, entry without reason); ruff, mypy, bandit on the tool; `tools/check_tool_descriptions_sync.py`.

## Documentation Impact
Yes. `tools/TOOL_DESCRIPTIONS.md` row, the `rules/tool-gates.md` row, and the Step 4 pointer.

## Out of Scope
- Fixing the current failures (issues/20261126-151436_wfeff001_cmd-mcp-import-nameerror.md).
- Changing how tests are selected or run.

## Dependencies
- Related: issues/20261126-151436_wfeff001_cmd-mcp-import-nameerror.md (fixes the current known failures; this tool is for future ones).

## Unresolved Questions
- `不明`: which pytest output (JUnit XML or another) records collection errors under `-n logical` reliably.
- `不明`: whether the baseline should live next to the other baselines under `tools/` or under `tests/`.

## AI Implementation Instruction
Do not change test selection or markers. Stop and report if the chosen output format cannot represent collection errors.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261126-151437
- **Related target files**: `tools/compare_test_baseline.py`, `tools/TOOL_DESCRIPTIONS.md`, `rules/tool-gates.md`, `skills/code-implementation/workflow.md`
