## Goal

Replace `verify_postcondition()`'s unconditional-success placeholder with real per-operation checks; add `post_state` field to `PipelineResult`; capture fresh post-operation `RepositoryState` in `run()`; wire `record_stage()` calls into `run()` for each stage actually executed.

## Scope

- `scripts/mcp_servers/git/repository_state.py`: modify `verify_postcondition()`, add `post_state` to `PipelineResult`, update `run()` to capture post-state and wire `record_stage()` calls.
- `scripts/mcp_servers/git/format_output.py`: consolidate postcondition logic call sites with the pipeline's new Stage 7.

## Assumptions

- `gitauth`'s Plan (`plans/20260904-162951_plan.md`) lands its Stage 3 call addition before or independently of this Plan's implementation; the `run()` method already has Stage 3 authorization (confirmed by current source inspection).
- `format_output.py`'s existing `GitServiceError`-raising checks (`format_pull`/`format_push`) are functionally correct today (only `format_checkout`'s argument order was broken per REQ-007).
- The consolidated `docs/00_governance_03_issue-and-uncertainty-management.md` is the correct current home for a new Known Issue entry.

## Design decisions

- **Consolidation over duplication**: `verify_postcondition()` reuses `format_output.py`'s existing `GitServiceError`-raising mechanism rather than building a second parallel postcondition mechanism. `verify_postcondition()` reflects whether Stage 6 completed without a postcondition-triggered exception, and uses the fresh post-state to add an independent verification layer (e.g., confirming `active_branch` matches the request).
- **Separate pre/post state fields**: `PipelineResult.post_state` is distinct from `repository_state` (pre-state), not derived from it.
- **Stage recording via `record_stage()`**: each stage call site in `run()` records its outcome; `all_stages_succeeded` and `last_failed_stage` derive from real recorded data instead of vacuous defaults.

## Alternatives considered

- Building a separate postcondition module alongside `format_output.py` — rejected because the originating issue explicitly requires consolidation.
- Adding `post_state` to `RepositoryState` instead of `PipelineResult` — rejected because `PipelineResult` is the natural owner of pre/post state comparison.

## Implementation

### Target file

`scripts/mcp_servers/git/repository_state.py`

### Procedure

1. Add `post_state: RepositoryState | None = None` field to `PipelineResult`.
2. In `WriteProtectionPipeline.run()`, after Stage 6 execution (line ~529), capture a fresh post-operation `RepositoryState.snapshot()` and assign it to `result.post_state`.
3. Replace `verify_postcondition()` body (lines 162-169) with real operation-specific checks:
   - For checkout: verify resulting branch matches requested target, or detached HEAD is explicitly permitted.
   - For pull: detect unresolved conflicts via `index.unmerged_blobs()` and incomplete merge/rebase state.
   - For push: detect rejected/error/forced/deleted/partial outcomes using structured GitPython results, consolidating with `format_push()`'s existing rejection-marker string matching.
4. Wire `record_stage()` calls into `run()` for each stage actually executed (Stage 3, 5, 6, 7).

### Method

- Modify `PipelineResult` dataclass fields and `reject()`/`ok_result()` factory methods to accept and store `post_state`.
- Modify `WriteProtectionPipeline.run()` to insert post-state capture between Stage 6 and Stage 7, and add `record_stage()` calls at each stage boundary.
- Rewrite `verify_postcondition()` to inspect the operation type (from `tool_name` parameter or context) and perform appropriate postcondition checks against the fresh post-state.

### Details

**1. PipelineResult changes (line ~464):**

```python
@dataclass(frozen=True)
class PipelineResult:
    ok: bool
    rejected_at_stage: str | None = None
    rejection_message: str = ""
    output: str = ""
    repository_state: RepositoryState | None = None
    post_state: RepositoryState | None = None  # NEW
    audit_record: dict[str, object] | None = None
```

Update `reject()` (line ~474) and `ok_result()` (line ~486) to accept and pass through `post_state`.

**2. run() changes (line ~515):**

After Stage 6 execution (around line 529), before Stage 7:

```python
# Capture fresh post-state for postcondition checks
post_state = self._state.snapshot()

# Stage 7: Verify postcondition
ok, msg = self._state.verify_postcondition(output, post_state, tool_name)
if not ok:
    return PipelineResult.reject(post_state, "Stage 7", msg)

return PipelineResult.ok_result(post_state, output, post_state=post_state)
```

Add `record_stage()` calls at each stage boundary:

```python
# After Stage 3 success:
self.record_stage(PipelineStage(name="Stage 3", index=3, result=(ok, msg)))

# After Stage 5 success:
self.record_stage(PipelineStage(name="Stage 5", index=5, result=(ok, msg)))

# After Stage 6 success:
self.record_stage(PipelineStage(name="Stage 6", index=6, result=(True, "")))

# After Stage 7:
self.record_stage(PipelineStage(name="Stage 7", index=7, result=(ok, msg)))
```

**3. verify_postcondition() rewrite (line ~162):**

```python
def verify_postcondition(
    self, result: object, post_state: RepositoryState, tool_name: str
) -> tuple[bool, str]:
    """Stage 7: Postcondition verification — operation-specific checks."""
    if tool_name == "git_checkout":
        # REQ-004: verify resulting branch matches requested target
        if post_state.active_branch != self._requested_branch:
            return False, f"expected branch {self._requested_branch!r}, got {post_state.active_branch!r}"
    elif tool_name == "git_pull":
        # REQ-005: detect unresolved conflicts
        if post_state._repo.index.unmerged_blobs():
            return False, "pull postcondition failed: unresolved merge conflicts remain"
    elif tool_name == "git_push":
        # REQ-006: detect rejected/error/forced/deleted/partial outcomes
        # Consolidate with format_push()'s existing rejection-marker string matching
        if isinstance(result, str):
            if "rejected" in result.lower() or "error" in result.lower():
                return False, f"push postcondition failed: {result}"
    return True, ""
```

Note: `_requested_branch` needs to be stored during Stage 5 or passed as part of context. Consider adding a `_pending_operation` field to track this.

## Compatibility considerations

- `PipelineResult` is frozen dataclass — adding `post_state` changes its constructor signature. All callers of `PipelineResult.ok_result()` and `PipelineResult.reject()` must be updated to pass `post_state=None` by default for backward compatibility.
- `verify_postcondition()` signature change adds two parameters (`post_state`, `tool_name`). Current call site at line ~537 passes only one argument — must be updated.
- The `_requested_branch` tracking mechanism may require extending `RepositoryState` or passing context through the pipeline.

## Security considerations

- Postcondition checks prevent silent acceptance of failed operations — critical for write-protection pipeline integrity.
- Consolidating postcondition logic with `format_output.py` avoids duplicate security validation paths that could disagree.

## Rollback considerations

- If `post_state` addition breaks existing callers, revert to removing the field and restoring original `reject()`/`ok_result()` signatures.
- If `verify_postcondition()` rewrite introduces regressions, restore the placeholder `(True, "")` as an emergency fallback while debugging.
- If `record_stage()` wiring causes issues, remove calls but keep the `stages` property functional.

## Validation plan

- Unit tests in `tests/mcp_servers/git/test_repository_state.py`:
  - Assert `verify_postcondition()` rejects a simulated failed-checkout state.
  - Assert `PipelineResult.post_state` differs from `repository_state` (pre-state) after a mutating operation.
  - Assert `record_stage()` populates `stages` such that `all_stages_succeeded`/`last_failed_stage` reflect an injected failure.
- Static analysis: `uv run ruff check scripts/mcp_servers/git/`, `uv run mypy scripts/mcp_servers/git/`, `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`, `PYTHONPATH=scripts uv run lint-imports`.
- Full suite: `uv run pytest tests/mcp_servers/git/ -v` — no new failures.

## Completion criteria

- `PipelineResult` has `post_state` field and all factory methods accept it.
- `run()` captures fresh post-state after Stage 6 and passes it to `verify_postcondition()`.
- `verify_postcondition()` performs real operation-specific checks (not unconditional success).
- `record_stage()` called at each stage boundary in `run()`.
- `all_stages_succeeded` and `last_failed_stage` report accurate results from recorded stages.
- All unit tests pass; static analysis passes with no new findings.

## Out of scope

- Authorization content itself (REQ-001 / gitauth's Plan scope).
- Detached-HEAD/dry-run precondition behavior (`gitdryrun`).
- Tool dispatch unification (`gitdispatch`).
- Repository-path containment/audit (`gitpathaudit`).
- Remote authorization/concurrency (`gitremote`).
- Re-executing `plans/done/20260901-223706_plan.md`'s own scope.

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-008
- **Source issue**: issues/20260902-144908_gitpipeline_enforce_complete_write_protection_pipeline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-190750_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-190750
- **Related target files**: scripts/mcp_servers/git/repository_state.py
