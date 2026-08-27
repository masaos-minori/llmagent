## Goal

`REQ-001`/`REQ-002`/`REQ-003`: add explicit postcondition verification to
`format_checkout()`, `format_pull()`, and `format_push()`, implementing ADR-012
Decision #6 ("verify the resulting branch/HEAD and detect unresolved conflicts before
reporting success" — a guarantee distinct from exit-code checking, which
`_wrap_git_op()` already provides).

## Scope

- **In-Scope**: `format_checkout()` (lines 118-133) — verify
  `repo.active_branch.name == req.branch` and `not repo.head.is_detached` after
  checkout; `format_pull()` (lines 136-147) — verify `repo.index.unmerged_blobs()` is
  empty after pull; `format_push()` (lines 150-156) — verify the push result string
  contains no known rejection marker.
- **Out-of-Scope**: GIT-001 (dirty-worktree/detached-HEAD pre-checks) — handled by a
  separate Plan (`plans/20260825-133945_plan.md`); `git_add`/`git_commit` — ADR-012
  Decision #6's Conflicting Source cites only this file's checkout/pull/push functions;
  replacing `repo.git.push()` with the porcelain `repo.remote().push()` API — out of
  scope per the source Plan's own decision to add a verification layer only.

## Assumptions

- **Critical finding (resolves the source Plan's Design-section open question and
  UNK-01)**: confirmed via Read (`scripts/mcp_servers/git/git_service.py:65`) that
  `_GIT_ERRORS = (git.exc.GitError, OSError, ValueError)` does **not** include
  `GitServiceError` (`scripts/mcp_servers/git/git_models.py:66`, a `RuntimeError`
  subclass) — so a `GitServiceError` raised inside `format_checkout`/`format_pull`/
  `format_push` is **not** caught by `_wrap_git_op()`'s `except _GIT_ERRORS`; it
  propagates past it. This is not a bug to fix: confirmed via Read
  (`scripts/mcp_servers/git/git_server.py:62-63`) that the server registers
  `@app.exception_handler(GitServiceError)`, i.e. `GitServiceError` is deliberately
  designed to bypass `_wrap_git_op()`'s generic GitPython-error wrapping and be handled
  at the FastAPI application layer instead — the exact same pattern already used by
  `format_commit()`'s existing `raise GitServiceError("nothing staged to commit")`
  (line 113). The three new postcondition checks follow this same, already-established
  pattern; no change to `_GIT_ERRORS` or `_wrap_git_op()` is needed or appropriate.
- **UNK-01 resolution, and a scope-relevant finding for REQ-003**: confirmed via
  reading GitPython's `git.cmd.Git.execute()` docstring (`with_exceptions: bool =
  True` is the default) that a non-zero-exit git command — including the standard
  non-fast-forward `git push` rejection — already raises `GitCommandError` (a
  `git.exc.GitError` subclass) *before* `format_push()`'s own code can inspect any
  return string. This means REQ-003's string-marker check can only ever trigger in the
  narrow case GitPython/git itself does not treat as a command failure (exit code 0)
  while still reporting a rejection in its output text — consistent with the source
  Plan's own Assumptions ("現時点で確認された具体的な悪用可能な脆弱性への対処ではなく
  ...後条件確認の実装である"). Implement the check as specified regardless — it is
  cheap, harmless when unreached, and satisfies ADR-012 Decision #6's documentation
  requirement for an independent verification layer — but do not expect the added
  regression test to be reachable via a real non-fast-forward push exception path; it
  must instead directly test the string-check logic with a mocked/crafted return value
  (see the companion `test_format_output.py` document, REQ-004).
- Confirmed via Read (`scripts/mcp_servers/git/format_output.py:118-156`) that all
  three functions' GitPython calls (`repo.git.checkout`/`create_head`/`checkout()`,
  `repo.git.pull`, `repo.git.push`) precede the point where a success message is
  constructed and returned — verification code is inserted between the GitPython call
  and the `return` statement in each function.

## Design decisions

- `format_checkout()`: after the existing `if req.create: ... else: ...` branch (lines
  127-132), before `return f"Switched to branch '{req.branch}'"`, add: `if
  repo.active_branch.name != req.branch or repo.head.is_detached: raise
  GitServiceError(f"checkout postcondition failed: expected branch {req.branch!r}, got
  {'<detached HEAD>' if repo.head.is_detached else repo.active_branch.name!r}")`.
- `format_pull()`: after `result = repo.git.pull(*pull_args)` (line 146), before
  `return result or "Already up to date."`, add: `if repo.index.unmerged_blobs(): raise
  GitServiceError("pull postcondition failed: unresolved merge conflicts remain")`.
- `format_push()`: after `result = repo.git.push(req.remote, "--", branch)` (line 155),
  before `return result or f"Pushed '{branch}' to '{req.remote}'"`, add: `_rejection_markers
  = ("[rejected]", "non-fast-forward", "failed to push"); if result and any(m in result
  for m in _rejection_markers): raise GitServiceError(f"push postcondition failed:
  rejection marker detected in output: {result!r}")`.
- Keep the rejection-marker list as a small module-level or function-local tuple
  (not a class attribute) — it is a self-contained detail of `format_push()`, not
  shared state.

## Alternatives considered

- Replacing `repo.git.push()` with `repo.remote().push()` (porcelain API,
  `PushInfo.flags` inspection) for a more rigorous check: rejected per the source
  Plan's own Out-of-Scope — this Requirement adds a verification layer on top of the
  existing CLI-based call, not a redesign of the push mechanism.
- Catching `GitCommandError` inside `format_push()` and re-raising as
  `GitServiceError` to unify all push failures under one exception type: rejected —
  out of scope for this Requirement (which only adds a *new*, independent check for the
  exit-code-0-but-rejected edge case); the existing `GitCommandError` → `_wrap_git_op()`
  → `GitServiceError` path for genuine non-zero exits is untouched and already works.

## Implementation

### Target file
`scripts/mcp_servers/git/format_output.py`

### Procedure
1. In `format_checkout()`, insert the branch/detached-HEAD postcondition check per
   Design decisions, immediately before the final `return` statement.
2. In `format_pull()`, insert the unmerged-blobs check per Design decisions,
   immediately before the final `return` statement.
3. In `format_push()`, insert the rejection-marker check per Design decisions,
   immediately before the final `return` statement.
4. `GitServiceError` is already imported (line 22) — no new import needed.

### Method
Three independent postcondition-check insertions, one per function, each following
the exact `raise GitServiceError(...)` pattern `format_commit()` already establishes
in this file.

### Details
- Do not alter `format_add`, `format_commit`, `format_status`, `format_log`,
  `format_diff`, `format_branch`, `format_show`, or any other function in this file.
- The `format_push()` check is best-effort by design (see Assumptions) — it is not
  expected to be the primary defense against a rejected push, since a genuine
  non-fast-forward rejection already raises `GitCommandError` before this code runs.

## Compatibility considerations

- All three checks only add a new failure path (`GitServiceError`) for a state that
  was already anomalous (checkout landed on the wrong branch/detached HEAD; pull left
  unresolved conflicts; push output contains a rejection marker despite exit code 0) —
  no change to the success-path return values for well-behaved operations.
- `GitServiceError` bypasses `_wrap_git_op()`'s `except _GIT_ERRORS` and propagates to
  the FastAPI `@app.exception_handler(GitServiceError)` — this is the established,
  intentional routing (see Assumptions), not a new integration point.

## Security considerations

- Directly implements ADR-012 Decision #6, closing Known Deviations `GIT-002` — adds
  an independent verification layer catching state-mismatch cases that exit-code
  checking alone would miss.

## Rollback considerations

- Remove the three inserted checks; no other state or behavior depends on them.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/git/format_output.py` | Unit | `PYTHONPATH=scripts uv run pytest tests/mcp_servers/git/test_format_output.py -v` | New postcondition-check tests pass (both success and failure paths); existing tests for these three functions remain green |
| Repository-wide | Full suite | `PYTHONPATH=scripts uv run pytest` | No new failures |

## Completion criteria

- `format_checkout()` raises `GitServiceError` when the resulting branch/HEAD does not
  match the requested branch.
- `format_pull()` raises `GitServiceError` when unresolved conflicts remain after pull.
- `format_push()` raises `GitServiceError` when a known rejection marker is present in
  the push result string, even though the call did not raise `GitCommandError`.
- All three functions' happy paths return their existing success messages unchanged
  (AC-04, regression-safe).

## Out of scope

- `_GIT_ERRORS`/`_wrap_git_op()` — no change (see Assumptions on why `GitServiceError`
  intentionally bypasses this path).
- `tests/mcp_servers/git/test_format_output.py` — see the companion implementation
  procedure document for REQ-004.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm `_GIT_ERRORS`/`GitServiceError` relationship (UNK-01) | Pending | — | — | Resolved during Step 3 of this workflow — see Assumptions |
| 2 | Add postcondition check to `format_checkout()` | Pending | — | — | |
| 3 | Add postcondition check to `format_pull()` | Pending | — | — | |
| 4 | Add postcondition check to `format_push()` | Pending | — | — | |
| 5 | Run the validation sequence (`rules/toolchain.md`) scoped to this file and its tests | Pending | — | — | |
| 6 | Documentation update | N/A | — | — | Not in scope for this file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Assumption | `format_checkout()`/`format_pull()`/`format_push()` にポストコンディション検証が未実装。手順書の前提と実際のコードに依存関係あり。 | No | 2026-08-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003` — postcondition checks for checkout/pull/push
- **Source issue**: `issues/20260823_git_postcondition_verification_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-134130_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-182037
- **Related target files**: `scripts/mcp_servers/git/format_output.py`
