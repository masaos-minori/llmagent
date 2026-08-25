## Goal

`REQ-004`: wire `_check_dirty_worktree()`/`_check_detached_head()` into `git_checkout()`/
`git_pull()` (skipping both checks when `req.dry_run` is `True`), implementing ADR-012
Decision #5, without touching the shared `_run_tool()`/`_validate_repo()` path used by
`git_add`/`git_commit`/`git_push`.

## Scope

- **In-Scope**: `git_checkout()` (currently lines 226-242) and `git_pull()` (lines
  244-263) — add the two new checks, gated on `not req.dry_run`; `GitService.__init__`
  (lines 74-86) — add an `allow_detached_head: bool = False` parameter and pass it to
  `GitSecurityGuards.__init__(...)`; `build_service(cfg: GitConfig) -> GitService`
  (lines 305-320) — read `cfg.allow_detached_head` and pass it to `GitService(...)`, so
  the config value configured via `git_mcp_server.toml` actually reaches the mixin
  (otherwise it silently stays at the default regardless of config).
- **Out-of-Scope**: `_run_tool()`, `_validate_repo()`, `git_add()`, `git_commit()`,
  `git_push()` — per the source Plan's explicit rejection of the issue's original
  "call from `_validate_repo()`" proposal (would incorrectly block `git_add`/
  `git_commit`, which are the normal way to resolve a dirty worktree).

## Assumptions

- Confirmed via Read (`scripts/mcp_servers/git/git_service.py:90-141,226-263`) that:
  - `_run_tool(tool_name, repo_path, op)` (lines 129-141) calls `_validate_repo()`, then
    `repo = self._open_repo(repo_path)`, then `self._wrap_git_op(tool_name, lambda:
    op(repo))` — `op: Callable[[git.Repo], str]` already receives the opened `repo`.
  - `git_checkout()`/`git_pull()` both call `_validate_ref()`/`_validate_protected()`
    (and `git_pull` additionally validates `req.remote`) *before* calling `_run_tool()`,
    i.e. before the repo is opened — these existing checks work on plain strings
    (`req.branch`, `req.remote`), not on an opened `git.Repo`, so they cannot check
    dirty/detached state without opening the repo themselves.
  - `format_checkout(repo, req)`/`format_pull(repo, req)` (the `op` callables passed to
    `_run_tool()`) already receive the opened `repo` as their first argument.
- **Resolves the source Plan's own open design question** (Design section: "実装時に
  確定する" — where to call the new checks without duplicating `_open_repo()` or
  touching `_run_tool()`'s shared signature): rather than adding a pre-check hook
  parameter to `_run_tool()` (which the source Plan considered), the checks are placed
  *inside* each handler's own `op` lambda, before delegating to `format_checkout`/
  `format_pull` — the `op` lambda already receives `repo` and already returns `str`
  (identical to the shape a denial message needs), so no `_run_tool()` signature change
  is needed at all, and `git_add`/`git_commit`/`git_push` (which pass their own,
  unmodified `op` lambdas) are structurally untouched.

## Design decisions

- In `git_checkout()`, replace `lambda repo: format_checkout(repo, req)` with a named
  inner function (or an expanded lambda body) that, when `not req.dry_run`, calls
  `self._check_dirty_worktree(repo)` then `self._check_detached_head(repo)`, returning
  the first denial message encountered; otherwise falls through to
  `format_checkout(repo, req)`. Apply the identical pattern to `git_pull()`'s
  `lambda repo: format_pull(repo, req)`.
- Order the two new checks after the existing pre-`_run_tool()` validations
  (`_validate_ref`/`_validate_protected`/remote check) — those are cheap, string-only
  checks that should short-circuit before a repo is even opened; the new checks need an
  opened `repo`, so they naturally belong inside the `op` callable.
- Skip both checks entirely when `req.dry_run` is `True` — per the source Plan's
  Assumptions, `dry_run=True` is the "documented safe exception" ADR-012 Decision #5
  allows, confirmed via `format_checkout`/`format_pull`'s own dry-run branches never
  mutating the working tree.

## Alternatives considered

- Adding an optional pre-check callable parameter to `_run_tool()` (one of the two
  options the source Plan's Design section proposed): rejected in favor of the
  op-lambda approach above — avoids widening `_run_tool()`'s shared signature (used by
  every `git_*` handler including read-only ones), keeping the blast radius limited to
  exactly the two handlers this Requirement targets.
- Opening the repo in the handler before calling `_run_tool()` (the source Plan's other
  proposed option) and passing it in some new way: rejected — would require
  `_run_tool()` to accept an already-open `repo` instead of a `repo_path`, again
  widening its shared contract; the op-lambda approach needs no such change.

## Implementation

### Target file
`scripts/mcp_servers/git/git_service.py`

### Procedure
1. In `git_checkout()` (lines 226-242), after the existing `_validate_protected` check
   and before the `return await self._run_tool(...)` line, change the `op` argument
   from `lambda repo: format_checkout(repo, req)` to a function that first runs the two
   new checks (when `not req.dry_run`) and only calls `format_checkout(repo, req)` if
   both pass.
2. Apply the identical pattern to `git_pull()` (lines 244-263).
3. In `GitService.__init__` (lines 76-86), add `allow_detached_head: bool = False` to
   the parameter list (after `protected_branches`), and change the body's
   `GitSecurityGuards.__init__(self, allowed_repo_paths, read_only, protected_branches
   or [])` to `GitSecurityGuards.__init__(self, allowed_repo_paths, read_only,
   protected_branches or [], allow_detached_head)`. This must land after the companion
   `git_security.py` document's `__init__` signature change exists.
4. In `build_service(cfg: GitConfig) -> GitService` (lines 305-320), add
   `allow_detached_head = bool(cfg.allow_detached_head)` alongside the other
   `cfg.*`-derived locals, and pass `allow_detached_head=allow_detached_head` to the
   `GitService(...)` call. This must land after the companion `git_models.py`
   document's `GitConfig.allow_detached_head` field exists.
5. Do not modify `_run_tool()`, `_validate_repo()`, `_open_repo()`, or any other
   handler in this file.

### Method
Two handler-local `op` callable rewrites; no shared helper signature changes.

### Details
- Example shape for `git_checkout()` (illustrative, confirm exact style against the
  file's existing lambda-vs-def convention before writing):
  ```python
  def _checkout_op(repo: git.Repo) -> str:
      if not req.dry_run:
          ok, err = self._check_dirty_worktree(repo)
          if not ok:
              return err
          ok, err = self._check_detached_head(repo)
          if not ok:
              return err
      return format_checkout(repo, req)
  return await self._run_tool("git_checkout", req.repo_path, _checkout_op)
  ```

## Compatibility considerations

- `git_add`/`git_commit`/`git_push` and all read-only tools are unaffected — their own
  `op` lambdas are not touched, and `_run_tool()`'s shared signature does not change.
- A `git_checkout`/`git_pull` call with `dry_run=False` against a dirty or
  detached-HEAD repo now returns a denial message instead of proceeding — this is the
  intended new behavior, not a regression, per ADR-012 Decision #5.

## Security considerations

- Directly closes ADR-012 Known Deviations `GIT-001` — prevents `git_checkout`/
  `git_pull` from discarding uncommitted changes or landing in an unexpected
  detached-HEAD state without an explicit, policy-permitted exception.

## Rollback considerations

- Revert both handlers' `op` argument to the plain `lambda repo: format_checkout(repo,
  req)` / `lambda repo: format_pull(repo, req)`.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/git/git_service.py` | Unit/Integration | `PYTHONPATH=scripts uv run pytest tests/mcp_servers/git/ -v` | New dirty/detached-HEAD denial tests pass; existing `git_add`/`git_commit`/`git_push`/read-only tool tests unaffected |
| Repository-wide | Full suite | `PYTHONPATH=scripts uv run pytest` | No new failures |
| Repository-wide | Type check | `uv run mypy scripts/` | No new errors |

## Completion criteria

- `git_checkout()`/`git_pull()` with `dry_run=False` against a dirty worktree return a
  denial message without executing the git operation.
- The same, with `dry_run=False` against a detached HEAD and `allow_detached_head=False`
  (default).
- `dry_run=True` skips both checks (regression-safe preview behavior preserved).
- `git_add`/`git_commit`/`git_push` and all read-only handlers are unmodified.

## Out of scope

- `scripts/mcp_servers/git/git_security.py`'s two new check methods — see the
  companion implementation procedure document for REQ-001/REQ-002.
- `scripts/mcp_servers/git/git_models.py`'s `GitConfig.allow_detached_head` field — see
  the companion implementation procedure document for REQ-003.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `git_checkout()`'s `op` callable to run the two new checks (skipped when `dry_run`) | Pending | — | — | |
| 2 | Apply the identical rewrite to `git_pull()` | Pending | — | — | |
| 3 | Add `allow_detached_head` parameter to `GitService.__init__`, pass through to `GitSecurityGuards.__init__` | Pending | — | — | Apply after companion `git_security.py` document lands |
| 4 | Update `build_service()` to read `cfg.allow_detached_head` and pass it to `GitService(...)` | Pending | — | — | Apply after companion `git_models.py` document lands |
| 5 | Run the validation sequence (`rules/toolchain.md`) scoped to this file and its tests | Pending | — | — | |
| 6 | Documentation update | N/A | — | — | Not in scope for this file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004` — wire dirty-worktree/detached-HEAD checks into `git_checkout()`/`git_pull()`
- **Source issue**: `issues/20260823_git_dirty_worktree_detached_head_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-133945_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-181507
- **Related target files**: `scripts/mcp_servers/git/git_service.py`
