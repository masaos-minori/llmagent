# `GitSecurityGuards` is dead code; three docs cite it as the active protected-branch enforcement mechanism

## Priority
Medium

## Summary
`scripts/mcp_servers/git/git_security.py`'s `GitSecurityGuards` class is never
imported, instantiated, or mixed into `GitService` — confirmed by `rg -n
"GitSecurityGuards" scripts/ tests/` finding only the class's own definition
and a stale comment in `git_service.py`'s module docstring. The actual
protected-branch enforcement is `GitService._check_protected_branch()`
(defined directly on `GitService`, called via `GitService._validate_protected()`).
Three documentation files still describe `GitSecurityGuards` as the active
mechanism (one already corrected as part of a related, narrower fix — see
Background).

## Background
This issue was discovered while verifying a documentation claim flagged in a
prior investigation: `docs/00_security_02_high-risk-tool-common-policy.md`
line 187 cited `GitSecurityGuards._check_protected_branch()` as the enforcing
method. Direct source inspection found `GitSecurityGuards` is not wired into
`GitService` at all (`class GitService:` declares no base class), and the
class's own docstring even says "Mixed into GitService via inheritance so
tests can still call `svc._check_repo_path()` and `svc._check_write()`" — a
claim the current code does not fulfill. That one doc line has already been
corrected directly (see `docs/00_security_02_high-risk-tool-common-policy.md`,
same section) as part of the narrower task that surfaced this issue. The
broader finding — three *other* files repeating the same stale claim, plus the
dead class itself — is filed here instead of fixed inline, since it is outside
that narrower task's scope.

## Problem
`rg -n "GitSecurityGuards" scripts/ tests/ docs/` (confirmed by direct read at
the time of filing) finds:
- `scripts/mcp_servers/git/git_security.py:12` — the class's own definition
  (`class GitSecurityGuards:`), never imported elsewhere in `scripts/` or
  `tests/`.
- `scripts/mcp_servers/git/git_service.py:8` — a module-docstring comment
  ("git_security.py — GitSecurityGuards mixin (repo-path + read-only guards)")
  describing an architecture the code no longer has.
- `docs/04_mcp_04_05_git.md:107,111,130` — describes `GitSecurityGuards` as "a
  mixin on `GitService`" enforcing repo-path/read-only/protected-branch checks
  "for every write tool," labeled `(Explicit in code)`.
- `docs/04_mcp_90_inconsistencies_and_known_issues.md:84` — "Protected-branch
  enforcement is implemented via `GitSecurityGuards._check_protected_branch()`
  / `GitService._validate_protected()`."
- `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md:205,240` — lists
  `GitSecurityGuards` as a "key symbol" and as defined in
  `scripts/mcp_servers/git/git_service.py` (also the wrong file — the class
  actually lives in `git_security.py`).

The actual enforcement path, confirmed by direct read of
`scripts/mcp_servers/git/git_service.py`: `GitService` defines its own
`_check_repo_path()`, `_check_write()`, `_is_safe_ref()`,
`_check_protected_branch(branch)`, and `_validate_protected(branch)` methods
directly (not inherited from `GitSecurityGuards`), and `git_checkout()`/
`git_pull()`/`git_push()` call `self._validate_protected(req.branch)`, which
calls `self._check_protected_branch(branch)` — all on `GitService` itself.
`test_check_protected_branch` (cited by the docs above) instantiates and calls
these methods directly on a `GitService` instance (`svc: GitService`), not on
`GitSecurityGuards`.

## Reason for Change
- Four (now three, after the narrower fix) documentation locations attribute
  behavior to a class that is not actually used, one of them explicitly
  labeled `(Explicit in code)` — a confidence label that is currently
  incorrect.
- `GitSecurityGuards` itself is dead code: a fully-defined, docstring-documented
  class with zero callers, which readers of `git_security.py` would reasonably
  assume is live given `git_service.py`'s own header comment describing it as
  mixed in.
- Risk of confusing a future contributor into modifying `GitSecurityGuards`
  expecting it to take effect, when it does not.

## Implementation Intent
Two independent tracks, either or both may be pursued:
1. **Documentation correction**: update the three remaining doc citations (and
   `git_service.py`'s stale header comment) to name `GitService`'s own
   `_check_protected_branch()`/`_validate_protected()` methods instead of
   `GitSecurityGuards`, following the pattern already applied to
   `docs/00_security_02_high-risk-tool-common-policy.md` line 187.
2. **Dead code removal**: evaluate whether `GitSecurityGuards`
   (`scripts/mcp_servers/git/git_security.py`, entire class) can be deleted
   outright, following the same zero-caller verification and Path A
   `python-refactoring` procedure already applied to
   `RepositoryState`/`WriteProtectionPipeline`'s dead
   `_check_dirty_worktree()`/`_check_detached_head()` methods in this same
   codebase area.

## Target Files or Areas
- `scripts/mcp_servers/git/git_security.py` — `GitSecurityGuards` class
  (dead-code removal candidate)
- `scripts/mcp_servers/git/git_service.py` — stale module-docstring comment
  (line 8 at time of filing)
- `docs/04_mcp_04_05_git.md` — three citations
- `docs/04_mcp_90_inconsistencies_and_known_issues.md` — one citation
- `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` — two citations
  (also cites the wrong source file for the class)

## Required Changes
- Verify `GitSecurityGuards` has zero callers/instantiations anywhere in the
  repository (already confirmed once at filing time; re-verify at
  implementation time in case the code has since changed).
- If pursuing dead-code removal: delete the class, its file if nothing else
  remains in it, and update `git_service.py`'s stale docstring comment.
- If pursuing documentation-only correction: replace each `GitSecurityGuards`
  citation with the accurate `GitService._check_protected_branch()`/
  `_validate_protected()` reference; correct ADR-012's "Key symbols" and
  "defined in" file-path claims.

## Constraints
- If `GitSecurityGuards` is deleted, confirm no test imports it directly
  (`rg -n "from mcp_servers.git.git_security import\|GitSecurityGuards"
  tests/`) before removal.
- Documentation edits must follow `skills/DESIGN.md` Evidence labels — the
  `(Explicit in code)` label in `04_mcp_04_05_git.md` must be re-verified
  against the corrected understanding, not left attached to a now-corrected
  but still class-misattributed statement without re-confirmation.

## Acceptance Criteria
- No `docs/*.md` file attributes protected-branch (or repo-path/read-only)
  enforcement to `GitSecurityGuards` unless that class is actually confirmed
  wired into `GitService` at implementation time.
- `git_service.py`'s module docstring accurately describes the current
  guard-composition architecture.
- If `GitSecurityGuards` is deleted: `rg -n "GitSecurityGuards"` returns no
  result anywhere in `scripts/`, `tests/`, or `docs/`, and the full
  `tests/mcp_servers/git/` suite still passes.

## Testing Expectations
If code is deleted: run `tests/mcp_servers/git/` in full and confirm no
regression (per the same validation already performed for the related
`_check_dirty_worktree()`/`_check_detached_head()` cleanup in this codebase
area). If documentation-only: no automated test applies; manual review plus
`tools/check_docs_consistency.py --domain mcp`.

## Documentation Impact
This issue is largely a documentation-accuracy fix; see Target Files or Areas
above for the specific `docs/*.md` locations affected.

## Out of Scope
- Any change to the actual protected-branch enforcement behavior — this issue
  is about correcting stale attribution, not changing what is enforced.
- The narrower fix already applied to `docs/00_security_02_high-risk-tool-common-policy.md`
  line 187 and the `_check_dirty_worktree()`/`_check_detached_head()` dead-code
  removal in `repository_state.py` — both already completed, not part of this
  issue's remaining scope.

## Dependencies
N/A: none — self-contained, though implementers may want to sequence the
dead-code-removal track before the documentation-correction track (or vice
versa) rather than doing both simultaneously, to keep the diff reviewable.

## Unresolved Questions
- Should `GitSecurityGuards` be deleted outright, or kept as documented dead
  code with a `# noqa`/comment explaining its non-use? This issue does not
  decide that — Implementation Intent above lists both tracks as options for
  the implementer/maintainer to choose between.

## AI Implementation Instruction
- Re-verify `GitSecurityGuards`'s zero-caller status via `rg` before acting —
  do not assume this issue's evidence is still current.
- If choosing the dead-code-removal track, apply `skills/python-refactoring`'s
  Path A procedure (single file, no behavior change, not referenced in
  `deploy.sh`) — the same procedure already used for the related
  `_check_dirty_worktree()`/`_check_detached_head()` cleanup.
- If choosing the documentation-only track, route through
  `skills/python-documentation` per `routing.md`'s Documentation row.
- Do not implement both tracks in the same uncoordinated pass without
  re-reading each other's effect — deleting the class first changes what the
  documentation-correction track needs to say (no more "still exists but
  unused" nuance).
- Stop and report back if `GitSecurityGuards` is found to have gained a caller
  since this issue was filed — that would mean the class is no longer dead,
  and the fix approach here no longer applies.
