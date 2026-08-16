# Replace `try/except ValueError` loop in `git_security._check_repo_path` with `Path.is_relative_to()`

## Priority
Low

## Summary
`scripts/mcp_servers/git/git_security.py`'s `_check_repo_path` uses a
`try: target.relative_to(allowed) / except ValueError: continue` loop to check whether a
resolved path falls under an allowed directory. `Path.is_relative_to()` (Python 3.9+) is
semantically equivalent and would remove the exception-based control flow.

## Reason for Change
Found during a `prompts/04_refactor.md` cycle on `git_security.py` (2026-08-14). Not implemented
there because this function is a security-boundary path-traversal check, and the refactor
procedure's Core Rules direct minimizing changes to exception handling in general — this file was
additionally flagged as exception-behavior-sensitive by the orchestrating session, so the change
was deferred pending explicit sign-off rather than implemented under a "no product decision"
refactor cycle.

## Implementation Intent
Add a `hypothesis` property test asserting `old_impl(target, allowed) == new_impl(target,
allowed)` across a wide range of generated path strings (including trailing slashes, `../`
traversal sequences, case variations, empty strings) before making the change, since only 5
existing example-based tests currently exercise this function. Only apply the change once the
property test passes for both implementations.

## Target Files or Areas
- `scripts/mcp_servers/git/git_security.py` (`_check_repo_path`)
- `tests/mcp_servers/git/test_mcp_git.py` (existing `TestCheckRepoPath` tests)

## Required Changes
- Add a `hypothesis`-based property test comparing the current `try/except ValueError` logic
  against a `Path.is_relative_to()`-based reimplementation across generated inputs.
- If equivalence holds, replace the loop body with `Path.is_relative_to()`.
- Re-run all 5 existing `TestCheckRepoPath` tests plus the new property test.

## Acceptance Criteria
- New `hypothesis` property test passes, demonstrating equivalence across generated inputs.
- All existing `TestCheckRepoPath` tests pass unchanged after the swap.
- No change to `_check_repo_path`'s return value (`tuple[bool, str]`) or message content for any
  tested input.

## Testing Expectations
`hypothesis` property test (new) + existing `tests/mcp_servers/git/test_mcp_git.py` full suite;
`bandit` re-scan (security-relevant file).

## Documentation Impact
None expected.

## Out of Scope
- Do not change `_check_write` or any other guard in this file.
- Do not weaken the allowlist-matching semantics in any way — this is a pure control-flow swap,
  not a security-policy change.

## AI Implementation Instruction
This file is security-sensitive (path-traversal guard). Do not implement the swap until the
`hypothesis` property test demonstrates equivalence across a wide input range, and require
explicit maintainer sign-off before merging given the security sensitivity, per
`rules/coding.md`'s explicit sign-off gates.
