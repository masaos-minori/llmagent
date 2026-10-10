# Restore push error-path test coverage in the git MCP tests

## Priority
Low

## Summary
Add tests for how a failing push is reported by the git MCP formatter and pipeline, now that the old output-marker tests were removed and nothing else covers that path.

## Background
An upstream change removed the stdout rejection-marker detection for pushes (a rejected push normally exits non-zero, so the git library raises and the pipeline reports an error). The three tests that asserted the old behavior were deleted. During the work that led to this issue, replacement tests were written and then dropped to avoid duplicating the upstream fix; the saved drafts covered the points below.

## Problem
- No test asserts that a command error raised by the push call propagates out of the push formatter unchanged.
- No test asserts that the pipeline turns an exception raised by a write operation into a service error that names the tool (here the push tool).
- No test records the intended removal: a successful push whose output merely contains a rejection-like text is returned as a normal result.
- A regression that swallows a push failure, or that reintroduces text matching, would pass the suite.

## Reason for Change
The error path is the only protection against a rejected push being reported as success; it should be pinned by tests.

## Implementation Intent
- Add small, focused tests next to the existing push tests, without changing production code.

## Target Files or Areas
- `tests/mcp_servers/git/test_format_output.py`
- `tests/mcp_servers/git/test_repository_state.py`

## Required Changes
- Formatter test: a mocked push raising the git command error propagates the error.
- Formatter test: a mocked push returning rejection-like text returns that text unchanged.
- Pipeline test: an operation raising an exception for the push tool is reported as a service error whose message contains the tool name and the cause.
- Postcondition test: the push postcondition passes for any result text (documents the removal).

## Constraints
- Test only; use the module's existing helpers and fixtures.
- Confirm with the owner that the removal of text matching is intended before pinning it (it was stated as intended for the previous work).

## Acceptance Criteria
- The four tests exist and pass; breaking the error path makes at least one fail.

## Testing Expectations
Run the two test modules and the git MCP test directory.

## Documentation Impact
Not required.

## Out of Scope
- Changing the formatter, pipeline, or postcondition code.

## Dependencies
- Related to the upstream git MCP audit work that removed the old checks.

## Unresolved Questions
- Whether the owner wants the "output text alone does not fail" behavior pinned by a test or left unspecified.

## AI Implementation Instruction
Add tests only. Derive them from the current code, and stop to ask if the intended push-failure contract is unclear.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261008-143632_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-150557
- **Related target files**: `tests/mcp_servers/git/test_format_output.py`, `tests/mcp_servers/git/test_repository_state.py`
