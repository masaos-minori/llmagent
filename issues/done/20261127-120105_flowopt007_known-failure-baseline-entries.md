# Record the known failing tests in the baseline after their issues exist

## Priority
Low

## Summary
Register the failing tests that cannot be fixed immediately in `tools/known_test_failures_baseline.txt` with the issue that tracks each, so a full run reports them as known instead of new.

## Background
Evidence (`Explicit in code`): `tools/known_test_failures_baseline.txt` has no entries; its header says an entry needs a reason naming an issue path and is added only with `--add` and the owner's approval. `tools/compare_test_baseline.py` then reports a listed failure as known, and still reports every other failure as new. On 2026-11-27 each of four full runs listed three known-in-practice failures as `new failures` and needed a clean-HEAD check.

## Problem
Failures everyone knows about look like new failures in every run.

## Reason for Change
A repeated manual comparison per run; no correctness risk.

## Implementation Intent
Add the entries once their tracking issues exist, with the owner's approval.

## Target Files or Areas
- `tools/known_test_failures_baseline.txt`

## Required Changes
- After the owner approves, add the three git MCP test ids with `uv run python tools/compare_test_baseline.py --add` and the reason naming the git MCP failing-tests issue.
- Add the eventbus test only if it still fails after its issue is fixed or while it stays open and the owner approves.
- Remove an entry as soon as its test passes (`--update`).

## Constraints
- Never skip, xfail, or deselect a test; the baseline only changes how the comparison reports.
- Entries require the owner's approval.

## Acceptance Criteria
- [ ] A full run reports the listed tests as known and every other failure as new.
- [ ] Each entry names an issue path.

## Testing Expectations
`uv run python tools/compare_test_baseline.py <junit.xml>` on a run with and without a new failure; `tools/check_tool_descriptions_sync.py` is not affected.

## Documentation Impact
N/A: no documentation change.

## Out of Scope
- Fixing the tests (the dependencies).

## Dependencies
- Depends on: issues/20261127-120103_flowopt005_git-mcp-failing-tests.md (the entries cite it), and issues/20261127-120104_flowopt006_eventbus-outbox-flake.md for the eventbus test.

## Unresolved Questions
- `不明`: whether the owner accepts baselining while the issues are open (the file's rule requires approval).

## AI Implementation Instruction
Do not add an entry without the owner's explicit approval; stop and ask.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-120105
- **Related target files**: `tools/known_test_failures_baseline.txt`
