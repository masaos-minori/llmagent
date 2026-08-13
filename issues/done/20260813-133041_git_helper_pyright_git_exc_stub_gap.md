# Resolve pyright `reportAttributeAccessIssue` on `git.exc.*` across GitPython call sites

## Priority
Low

## Summary
`pyright scripts/shared/git_helper.py` reports 2 pre-existing errors
(`"exc" is not a known attribute of module "git"`) at the `except git.exc.*` clauses in
`get_repo_info`. The same pattern recurs at `scripts/mcp_servers/git/git_service.py:65`,
indicating a repo-wide GitPython type-stub gap rather than a local issue.

## Reason for Change
Found during a behavior-preserving refactor cycle on `scripts/shared/git_helper.py`
(2026-08-13). Confirmed present before that cycle's change and unaffected by it (Evidence
label: Explicit in code — reproduced via direct `pyright` invocation). Left unfixed there since
resolving it requires a repo-wide decision (add a type-stub dependency, use
`if TYPE_CHECKING: import git.exc`, or a justified `# type: ignore`) affecting more than one
file.

## Implementation Intent
Pick one consistent resolution and apply it at both known call sites (and any others found via
a repo-wide grep):
- Add/verify a `types-GitPython`-equivalent stub dependency if one exists and resolves the gap.
- Or use an explicit `import git.exc` (rather than relying on `git.exc` attribute access through
  the `git` module) if that resolves pyright's resolution.
- Or, if neither works cleanly, add a justified `# type: ignore[attr-defined]` per
  `rules/coding.md`'s suppression-governance rule (inline justification required).

## Target Files or Areas
- `scripts/shared/git_helper.py`
- `scripts/mcp_servers/git/git_service.py`
- Any other `except git.exc.*` call site found via `rg "git\.exc\." scripts/`

## Required Changes
- Apply the chosen fix consistently at every `git.exc.*` reference.
- If a `# type: ignore` is used, include the inline justification per `rules/coding.md`.

## Acceptance Criteria
- `uv run pyright scripts/shared/git_helper.py scripts/mcp_servers/git/git_service.py` reports 0
  errors related to `git.exc`.
- No change to exception-handling behavior (same exception types caught, same control flow).

## Testing Expectations
Type checks only (`mypy`, `pyright`) — this is a static-analysis fix with no runtime behavior
change. Existing tests for both files must continue to pass unchanged.

## Documentation Impact
None required.

## Out of Scope
- Do not change which exceptions are caught or how they are handled — only the type-checker
  visibility of the `git.exc` module.

## AI Implementation Instruction
Run `rg "git\.exc\." scripts/` first to find every call site before choosing a fix so the same
resolution is applied everywhere. Prefer a real stub/import fix over `# type: ignore`; only use
the suppression if no stub-based fix resolves it, and include the justification inline.
