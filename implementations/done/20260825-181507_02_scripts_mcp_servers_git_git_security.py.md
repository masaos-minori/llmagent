## Goal

`REQ-001`/`REQ-002`: add `_check_dirty_worktree()` and `_check_detached_head()` to
`GitSecurityGuards`, following the existing `_check_protected_branch()`
`tuple[bool, str]` pattern.

## Scope

- **In-Scope**: add two new methods to `GitSecurityGuards`
  (`scripts/mcp_servers/git/git_security.py`); extend `__init__` to accept and store
  `allow_detached_head: bool = False`.
- **Out-of-Scope**: `_check_repo_path()`, `_check_write()`, `_is_safe_ref()`,
  `_check_protected_branch()` — unchanged; wiring these new checks into
  `git_checkout()`/`git_pull()` — see the companion `git_service.py` implementation
  procedure document (REQ-004).

## Assumptions

- Confirmed via Read (`scripts/mcp_servers/git/git_security.py:1-58`) that every
  existing check method (`_check_repo_path`, `_check_write`, `_check_protected_branch`)
  returns `tuple[bool, str]` with `(True, "")` for allow and `(False, "[DENIED] ...")`
  for deny — the two new methods follow this exact convention.
- **Critical finding**: `GitSecurityGuards.__init__` (lines 23-32) stores each config
  value as its own instance attribute (`self._allowed`, `self._read_only`,
  `self._protected_branches`) — there is no `self._cfg` attribute holding a `GitConfig`
  object. The source Plan's REQ-002 text ("`self._cfg.allow_detached_head` が `False`
  の場合") describes a `self._cfg`-based access pattern that does not match this class's
  actual structure. The correct implementation follows the same per-field pattern as
  `protected_branches`: add `allow_detached_head: bool = False` as a new `__init__`
  parameter, store it as `self._allow_detached_head`, and have
  `_check_detached_head()` read `self._allow_detached_head` (not `self._cfg.
  allow_detached_head`).
- Confirmed via Read (`scripts/mcp_servers/git/git_service.py:85-87`) that
  `GitService.__init__` constructs the mixin via `GitSecurityGuards.__init__(self,
  allowed_repo_paths, read_only, protected_branches or [])` — this call site must also
  be updated to pass `allow_detached_head` (see the companion `git_service.py`
  implementation procedure document's own scope; if that document's edit does not
  already cover this specific constructor call, it must be added there, not here, since
  `GitService.__init__` lives in `git_service.py`, not this file).

## Design decisions

- `_check_dirty_worktree(self, repo: git.Repo) -> tuple[bool, str]`: `if
  repo.is_dirty(untracked_files=True): return False, "[DENIED] worktree has
  uncommitted changes (dirty worktree) — commit, stash, or discard changes first"`;
  else `return True, ""`.
- `_check_detached_head(self, repo: git.Repo) -> tuple[bool, str]`: `if
  repo.head.is_detached and not self._allow_detached_head: return False, "[DENIED]
  repository is in a detached HEAD state — checkout a branch first, or set
  allow_detached_head=true in git_mcp_server.toml"`; else `return True, ""`.
- Add `allow_detached_head: bool = False` as the last `__init__` parameter (after
  `protected_branches`), matching its Optional-with-default style, and store it
  unconditionally (no `or` fallback needed, since it is already a plain `bool` with a
  default, unlike `protected_branches: list[str] | None`).

## Alternatives considered

- Storing a full `GitConfig` object on the mixin instead of per-field attributes (which
  would have made the source Plan's `self._cfg.allow_detached_head` phrasing accurate):
  rejected — would require refactoring every other field
  (`allowed_repo_paths`/`read_only`/`protected_branches`) to match, a much larger change
  than this Requirement's scope, for no benefit over the existing per-field pattern this
  class already uses consistently.

## Implementation

### Target file
`scripts/mcp_servers/git/git_security.py`

### Procedure
1. Add `allow_detached_head: bool = False` to `__init__`'s parameter list (after
   `protected_branches`), and add `self._allow_detached_head = allow_detached_head` to
   its body.
2. Add `_check_dirty_worktree()` and `_check_detached_head()` per Design decisions,
   placed after `_check_protected_branch()` for locality with the other check methods.
3. Add `import git` if not already present (needed for the `git.Repo` type hint — check
   whether this file currently imports `git` at all; it may only import `Path` per the
   current header).

### Method
One `__init__` parameter/attribute addition plus two new methods, following the
existing check-method pattern exactly.

### Details
- `repo.head.is_detached` and `repo.is_dirty(untracked_files=True)` are both
  `GitPython` `Repo` properties/methods already used elsewhere in this codebase
  (`format_output.py:format_status()` uses the same `is_dirty(untracked_files=True)`
  call) — no new GitPython API surface is introduced.

## Compatibility considerations

- `__init__`'s new parameter has a default (`False`), so the existing call site in
  `git_service.py` continues to work even before it is updated to pass the new
  argument explicitly — though it should still be updated (see the companion
  `git_service.py` document) so the config value is actually threaded through, not left
  at its default.

## Security considerations

- Implements the core detection logic for ADR-012 Decision #5's dirty-worktree/
  detached-HEAD safety gate.

## Rollback considerations

- Remove the two new methods and revert `__init__`'s signature/body.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/git/git_security.py` | Unit | `PYTHONPATH=scripts uv run pytest tests/mcp_servers/git/ -v` | New check methods behave per Design decisions; existing `_check_repo_path`/`_check_write`/`_check_protected_branch` tests unaffected |

## Completion criteria

- `_check_dirty_worktree()` returns `(False, ...)` for a dirty repo, `(True, "")`
  otherwise.
- `_check_detached_head()` returns `(False, ...)` for a detached-HEAD repo unless
  `self._allow_detached_head` is `True`.
- `__init__` accepts and stores `allow_detached_head`.

## Out of scope

- Wiring these checks into `git_checkout()`/`git_pull()`, and updating the
  `GitSecurityGuards.__init__(...)` call site in `GitService.__init__` — see the
  companion `git_service.py` implementation procedure document (REQ-004).
- `GitConfig.allow_detached_head` field/parsing — see the companion `git_models.py`
  implementation procedure document (REQ-003).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `allow_detached_head` to `__init__` | Pending | — | — | |
| 2 | Add `_check_dirty_worktree()` and `_check_detached_head()` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) scoped to this file and its tests | Pending | — | — | |
| 4 | Documentation update | N/A | — | — | Not in scope for this file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Assumption | `_check_dirty_worktree()` と `_check_detached_head()` が未実装。手順書の前提と実際のコードに依存関係あり。 | No | 2026-08-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002` — add dirty-worktree/detached-HEAD check methods
- **Source issue**: `issues/20260823_git_dirty_worktree_detached_head_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-133945_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-181507
- **Related target files**: `scripts/mcp_servers/git/git_security.py`
