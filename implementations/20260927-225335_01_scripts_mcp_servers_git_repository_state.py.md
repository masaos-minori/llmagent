# Implementation Procedure — `repository_state.py`

## Goal

Split the write-protection pipeline orchestration off the frozen `RepositoryState`
snapshot so `RepositoryState` holds only immutable data + pure helpers, and remove dead
backward-compat delegation methods plus the dead `structured_result`. Drives Requirements
`REQ-001`–`REQ-005` of plan `plans/20260927-194329_plan.md`.

## Scope

Only `scripts/mcp_servers/git/repository_state.py`. The companion test update lives in a
separate implementation procedure for
`tests/mcp_servers/git/test_repository_state.py`.

## Assumptions

- `PipelineResult.reject` / `PipelineResult.ok_result` keep calling `audit()`; `audit()`
  stays on `RepositoryState`.
- `WriteProtectionPipeline.run()` remains the sole owner of stage sequencing; the retained
  `verify_authorization` / `verify_preconditions` / `verify_postcondition` methods are pure
  snapshot operations it invokes.
- Test-side impact is handled by the sibling test implementation procedure, not here.

## Design decisions

- Inline `check_dirty_worktree` / `check_detached_head` bodies into `verify_preconditions`,
  then delete the two methods: both are called internally by `verify_preconditions` and
  have no external production caller, so inlining preserves behavior while removing the
  duplication.
- Delete `validate_protected` / `validate_ref` / `structured_result` outright: zero callers
  anywhere outside tests.

## Alternatives considered

- Moving `verify_*` entirely out of `RepositoryState` into the pipeline: rejected — they are
  pure functions of the immutable snapshot, existing tests and `run()` already treat them as
  the entry points, and moving them would expand blast radius without behavioral benefit.

## Implementation

### Target file

`scripts/mcp_servers/git/repository_state.py`

### Procedure

1. Remove `check_dirty_worktree` and `check_detached_head`; inline their guards into
   `verify_preconditions` (below).
2. Delete `validate_protected` and `validate_ref` (zero production callers).
3. Delete `structured_result` (zero production callers).
4. Retain unchanged: `verify_authorization`, `verify_postcondition`, `audit`, all data
   fields/properties, `WriteProtectionPipeline`, `PipelineStage`, `PipelineResult`, and the
   six module-level helpers (`_normalize_branch_name`, `_is_protected_branch`,
   `_is_safe_ref`, `_validate_ref`, `_resolve_remote_url`, `_redact_remote_url`).

Rewrite `verify_preconditions` so it contains the guards directly:

```python
def verify_preconditions(
    self,
    command: str,
    dry_run: bool = False,
    allow_detached_head: bool = False,
) -> tuple[bool, str]:
    """Stage 5: Command-specific precondition checks.

    dirty-worktree and detached-HEAD guards apply only to write commands
    when dry_run is False. When dry_run is False, the detached-HEAD guard
    is skipped only when allow_detached_head is True; the dirty-worktree
    guard remains unconditional.
    """
    if dry_run:
        return True, ""
    if self.is_dirty:
        return False, "[DENIED] worktree has uncommitted changes (dirty worktree)"
    if self.is_detached_head and not allow_detached_head:
        return False, "[DENIED] repository is in a detached HEAD state"
    return True, ""
```

### Method

Read the target file in full first. Apply surgical edits only to the symbols named above.
Preserve exact rejection-message strings and the `(dry_run, allow_detached_head, is_dirty,
is_detached_head)` → return-value contract of the current split implementation. Do not touch
imports, formatting of untouched regions, or any symbol outside Scope.

### Details

- Behavior contract for the inlined `verify_preconditions`: identical results to the prior
  `check_dirty_worktree` + `check_detached_head` split for every input combination; message
  literals are unchanged.
- Discrepancy between Plan and current source: the Plan "Affected areas" states all four
  delegation methods have "zero production callers". This is false for
  `check_dirty_worktree` / `check_detached_head` — they are called only by
  `verify_preconditions` (internal caller, no external production caller). They are removed
  via inlining (Procedure step 1), not direct deletion. `validate_protected`,
  `validate_ref`, and `structured_result` are true zero-caller deletions (steps 2–3). The
  Plan's Implementation steps ("inline the two dirty-worktree / detached-HEAD checks into
  `verify_preconditions`") already encode the correct action; this note only corrects the
  affected-areas narrative. Freeze scope is unaffected.

## Compatibility considerations

- `MagicMock(spec=RepositoryState)` in `tests/mcp_servers/git/test_repository_state.py`
  auto-provides removed attributes on access; the test-side removal is handled by the sibling
  test procedure.
- `git_server`, `format_output`, `git_models`, `git_security` import `RepositoryState` and
  use `snapshot()` / data fields / retained helper methods only — unaffected by removing the
  four methods.

## Security considerations

Behavior-preserving. No authorization/postcondition logic changes; existing rejection
messages preserved. Removing `validate_ref` does not weaken ref validation — its logic never
reached any production caller; validation still occurs via `_validate_ref` inside
`RepositoryState.snapshot`.

## Rollback considerations

Revert the four edits: restore `check_dirty_worktree` / `check_detached_head` and re-wire
`verify_preconditions` to call them; restore `validate_protected` / `validate_ref` /
`structured_result`. All four are isolated method-body changes with no signature or import
impact.

## Validation plan

Run after implementing (executed by the code-implementation phase, not here):

```bash
uv run ruff format scripts/mcp_servers/git/repository_state.py
uv run ruff check scripts/mcp_servers/git/repository_state.py
uv run mypy scripts/
PYTHONPATH=scripts uv run lint-imports
uv run bandit -r scripts/mcp_servers/git/repository_state.py -c pyproject.toml
uv run pytest tests/mcp_servers/git/test_repository_state.py -v
```

See `plans/20260927-194329_plan.md` acceptance criteria AC-001–AC-003 for the full
post-implementation sequence (full suite, diff-cover ≥ 90%, pre-commit gate).

## Completion criteria

- `ruff check` / `mypy` / `lint-imports` / `bandit` pass on the changed file with no new
  findings.
- `pytest tests/mcp_servers/git/test_repository_state.py` passes with the removed-member
  tests deleted/rewritten and REQ-005 regression tests added.
- Acceptance criteria AC-001–AC-003 in `plans/20260927-194329_plan.md` all hold.

## Out of scope

- `tests/mcp_servers/git/test_repository_state.py` — separate implementation procedure.
- `WriteProtectionPipeline` orchestration shape (already the orchestrator owner).
- Module-level helpers, imports, and formatting of untouched regions.
- `deploy/deploy.sh` — Python-only change, rsynced, no cp-line impact.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-28 | 2026-09-28 | Inlined dirty/detached guards into verify_preconditions; removed 4 dead delegation methods + orphaned DispatchResult import |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-28 | 2026-09-28 | Sibling test procedure applied in same cycle (coupled refactor) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-28 | 2026-09-28 | ruff clean; bandit clean; mypy & lint-imports failures pre-existing (baseline-confirmed); pytest 75/75 green on affected module |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-28 | 2026-09-28 | None in scope |

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
- **Requirement ID**: `REQ-001` (pipeline orchestration separation), `REQ-002` (remove dead delegation methods), `REQ-003` (retain audit), `REQ-004` (retain verify_* helpers), `REQ-005` (retain module helpers)
- **Source issue**: issues/done/20260927-185308_gitref001_refactor-repository_state-pipeline-separation-of-concerns.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-194329_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-225335
- **Related target files**: scripts/mcp_servers/git/repository_state.py
