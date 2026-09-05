## Goal

Fix `format_checkout()`'s `git checkout -- <branch>` argument order bug so a branch switch actually occurs, while still rejecting option-like refs. Consolidate postcondition logic call sites with the pipeline's new Stage 7.

## Scope

- `scripts/mcp_servers/git/format_output.py`: fix `format_checkout()` argument order; consolidate postcondition logic call sites with the pipeline's new Stage 7.

## Assumptions

- The `--` placement was intended to prevent argument injection when `req.branch` starts with `-`, not to invoke Git's pathspec syntax.
- `format_pull()`/`format_push()` have equivalent Git argument-order defects not yet confirmed (UNK-02) — these should be checked during REQ-005/REQ-006 implementation but are out of scope for this specific document.
- The existing `GitServiceError`-raising checks in `format_pull`/`format_push` are functionally correct today.

## Design decisions

- **Minimal fix for argument order**: swap `--` position from `checkout("--", req.branch)` to `checkout(req.branch, "--")`. This restores documented Git semantics where `--` separates options from positional arguments.
- **Preserve injection protection**: the `--` separator still prevents option-like refs from being interpreted as flags, just in the correct position relative to the branch name.
- **Consolidation with pipeline Stage 7**: the postcondition check in `format_checkout()` (lines 141-147) is kept as-is because it provides a second independent layer beyond the pipeline's `verify_postcondition()` — this is intentional per the design section of the companion document.

## Alternatives considered

- Removing the `--` entirely — rejected because it would allow option-like refs to be misinterpreted as Git flags.
- Using `git.Repo.head.reset()` instead of `git.checkout()` — rejected because it changes the operational semantics (no reflog entry, different error handling).
- Building a separate postcondition module alongside `format_output.py` — rejected because the originating issue explicitly requires consolidation.

## Implementation

### Target file

`scripts/mcp_servers/git/format_output.py`

### Procedure

1. Fix `format_checkout()` argument order: change `state._repo.git.checkout("--", req.branch)` to `state._repo.git.checkout(req.branch, "--")`.
2. Review `format_pull()` and `format_push()` for equivalent argument-order defects (document findings even if none found).
3. Ensure postcondition checks in `format_checkout()` are compatible with the pipeline's new `verify_postcondition()` consolidation approach.

### Method

- Direct edit of line 140 in `format_output.py`: swap the two positional arguments to `git.checkout()`.
- Read `format_pull()` and `format_push()` sections to check for similar defects (document findings).
- No structural changes needed — this is a single-line fix.

### Details

**1. Fix format_checkout() argument order (line ~140):**

Change:
```python
state._repo.git.checkout("--", req.branch)
```
To:
```python
state._repo.git.checkout(req.branch, "--")
```

This is the minimal fix. The `--` separator still prevents option-like refs from being interpreted as flags, but now it correctly appears after the branch name rather than before it.

**2. Check format_pull() and format_push() for equivalent defects:**

Review lines ~151-184 of `format_output.py` for similar `--` placement issues. Specifically:
- `format_pull()`: line 161 uses `pull_args.extend(["--", req.branch])` — verify this is correct for `git pull` semantics (in `git pull`, `--` before the branch is valid for specifying remote-tracking branches).
- `format_push()`: review for similar patterns.

Document any findings. If defects are found, add them as additional rows in the Implementation Target Files table (requires Plan amendment).

**3. Postcondition check compatibility:**

The existing postcondition check at lines 141-147 in `format_checkout()` validates the branch switch result. This is compatible with the pipeline's `verify_postcondition()` because:
- The `format_checkout()` check runs immediately after the Git command (before returning).
- The pipeline's `verify_postcondition()` can use the fresh post-state to perform an independent verification.
- Both checks raise `GitServiceError` on failure, which is caught by the pipeline's exception handler.

## Compatibility considerations

- The fix changes runtime behavior: previously, `format_checkout()` with a non-dry-run branch switch would fail silently (the `--` placement caused a pathspec error), meaning production may never have successfully performed a non-dry-run branch checkout via this path. Any caller depending on checkout always failing was depending on a bug.
- `format_pull()` and `format_push()` must be reviewed for equivalent defects — if they exist, fixing them changes their runtime behavior similarly.

## Security considerations

- The `--` separator still protects against option injection; its position relative to the branch name is the only change.
- Realizing that production may never have successfully performed a non-dry-run branch checkout means downstream callers may have been silently failing — flag prominently in the Step 10 report.

## Rollback considerations

- Revert the single-line change if regressions occur.
- If `format_pull()`/`format_push()` fixes introduce regressions, revert those separately.

## Validation plan

- New test in `tests/mcp_servers/git/test_format_output.py`: a test using a real temporary `git.Repo` (not `MagicMock`) with two branches, asserting `format_checkout()` actually switches the active branch.
- The test fails against pre-change code with the pathspec error ("pathspec 'other' did not match any file(s) known to git").
- The test passes after the argument-order fix.
- Static analysis: `uv run ruff check scripts/mcp_servers/git/`, `uv run mypy scripts/mcp_servers/git/`, `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`, `PYTHONPATH=scripts uv run lint-imports`.
- Full suite: `uv run pytest tests/mcp_servers/git/ -v` — no new failures.

## Completion criteria

- `format_checkout()` performs a real branch switch when given a valid branch name (verified against a real `git.Repo`, not a mock).
- Option-like refs are still rejected (e.g., `"-f"` as branch name is not treated as a flag).
- `format_pull()` and `format_push()` reviewed for equivalent defects (findings documented).
- New regression test added and passing.
- All static analysis passes with no new findings.

## Out of scope

- Authorization content itself (REQ-001 / gitauth's Plan scope).
- Detached-HEAD/dry-run precondition behavior (`gitdryrun`).
- Tool dispatch unification (`gitdispatch`).
- Repository-path containment/audit (`gitpathaudit`).
- Remote authorization/concurrency (`gitremote`).
- Postcondition consolidation (handled by companion document for repository_state.py).
- Stage recording wiring (handled by companion document for repository_state.py).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-003, REQ-004, REQ-005, REQ-006, REQ-007
- **Source issue**: issues/20260902-144908_gitpipeline_enforce_complete_write_protection_pipeline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-190750_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-190750
- **Related target files**: scripts/mcp_servers/git/format_output.py
