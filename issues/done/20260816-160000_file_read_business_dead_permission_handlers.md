# Confirm whether `except PermissionError` handlers around `rglob()` in `read_business.py` are dead code

## Priority
Medium

## Summary
`scripts/mcp_servers/file/read_business.py`'s `search_files` and `_collect_grep_matches` each
wrap a `base.rglob("*")` traversal in `except PermissionError: ...`. Under this environment's
Python 3.14, `pathlib.Path.rglob()`'s internal `scandir()` calls are wrapped in their own
`try: ... except OSError: pass` (confirmed by reading `/usr/lib/python3.14/glob.py` and by a live
experiment: a chmod-000 subdirectory under an `rglob("*")` walk raises nothing). This means these
two `except PermissionError` blocks are provably unreachable on this runtime.

## Reason for Change
Found during a `prompts/04_refactor.md` cycle on `read_business.py` (2026-08-15). Not removed
there because doing so would be a behavior change on any Python version (or future `pathlib`
implementation) where `rglob()` still propagates `PermissionError` to the caller — this is a
version-coupled decision, not a pure refactor, and needs an explicit choice about which Python
versions this project supports/targets.

## Implementation Intent
Confirm the project's supported Python version range (check `pyproject.toml`'s
`requires-python`/`target-version` and any CI matrix). If only 3.13+ (where this swallowing
behavior may or may not hold — verify per-version) is supported, decide explicitly whether to:
(a) keep the defensive handler for forward/backward compatibility (document the version
dependency in a comment), or (b) remove it and rely on `pathlib`'s internal swallowing
(document that decision and the version assumption it relies on).

## Target Files or Areas
- `scripts/mcp_servers/file/read_business.py` (`search_files`, `_collect_grep_matches`)
- `pyproject.toml` (`requires-python`, to confirm supported version range)

## Required Changes
- Verify the `rglob()`-swallows-`PermissionError` behavior across the project's actual supported
  Python version range (not just 3.14).
- Decide (a) keep or (b) remove, and document the decision with an inline comment referencing
  this issue and the version assumption.
- If removed: confirm test coverage doesn't rely on the now-removed branch (2 characterization
  tests were added in the 2026-08-15 cycle specifically asserting the *swallowed* behavior via
  `pathlib`'s internal handling, not this file's `except` — these should still pass either way).

## Acceptance Criteria
- A decision (keep or remove) is made and documented with its version-dependency rationale.
- If removed: `radon cc` shows no complexity regression elsewhere; existing behavior (silent
  skip of unreadable subtrees during search) is unchanged from the caller's perspective.
- All existing `tests/mcp_servers/file/test_read_service.py` tests pass unchanged.

## Testing Expectations
Full `tests/mcp_servers/file/test_read_service.py` suite; if removed, re-verify the two
2026-08-15 characterization tests
(`test_search_files_permission_error_during_traversal_is_swallowed`,
`test_grep_files_permission_error_during_traversal_is_swallowed`) still pass (they should, since
they assert observable behavior, not code coverage of the specific `except` block).

## Documentation Impact
None expected beyond the inline code comment documenting the version-dependency rationale.

## Out of Scope
- Do not change any other exception-handling logic in `read_business.py`.
- Do not change the project's supported Python version range as part of this issue — only
  document the existing range's implication for this specific code path.

## AI Implementation Instruction
Verify the `rglob()` swallowing behavior empirically (a chmod-000 subdirectory test) against
whatever Python version(s) this project's `pyproject.toml` declares support for, not just the
current runtime, before deciding to remove the handlers.
