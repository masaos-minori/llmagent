# Implementation Procedure

## Goal

Make the write-protection pipeline in `RepositoryState` / `WriteProtectionPipeline`
(`scripts/mcp_servers/git/repository_state.py`) destination-aware and snapshot-stable:
`verify_authorization()` (Stage 3) evaluates protection against the operation
destination instead of always the current HEAD, the per-call inputs
(`protected_branches` / `requested_branch` / `active_ref`) are threaded through
`run()`, and exactly one `RepositoryState.snapshot()` is taken per dispatched call
(the two in-pipeline snapshots are removed). Driven by `REQ-002` (destination-based
protected-branch decision), `REQ-003` (checkout away from a protected branch is
allowed), `REQ-005` (pipeline inputs reach the Stage 5b re-check), and `REQ-006`
(single snapshot per call).

## Scope

Modifies only `scripts/mcp_servers/git/repository_state.py`. Cross-file effects are
dependencies, not targets:

- `scripts/mcp_servers/git/git_service.py` — forwards `requested_branch` /
  `protected_branches` / `active_ref` into `pipeline.run()` and takes the single
  `_run_tool()` snapshot; own document (`implementations/..._git_service.py.md`).
- `tests/mcp_servers/git/test_repository_state.py` — updated for the new
  `verify_authorization()` signature and the removed in-pipeline snapshots (own
  document).
- `tests/mcp_servers/git/test_git_security_compliance.py` — real call
  `self._state.verify_authorization()` (line ~1058) and mock sites must stay
  compatible with the new signature.

## Assumptions

- `run()` already declares `requested_branch` / `protected_branches` / `active_ref`
  parameters (lines 304-306); they currently default to `None`/`""` and are unused.
  Only the body must change, not the signature.
- `verify_postcondition()` already accepts `requested_branch` (line 171); its
  checkout/pull/push branches are kept.
- `format_output.py::format_checkout()` retains its own post-checkout refresh
  snapshot (line 152) and internal postcondition assertion; that snapshot is OUT
  of this document's removal scope (REQ-006 explicitly preserves it).
- `_normalize_branch_name()` and `_is_protected_branch()` remain available as the
  normalization/comparison primitives.

## Design decisions

- **Destination computed from tool + `requested_branch`.** `verify_authorization()`
  gains an operation-context parameter set and picks the destination:
  `requested_branch` for `git_pull` / `git_push` / `git_checkout`, current
  `active_branch` for `git_add` / `git_commit`. One normalized comparison against
  the configured list satisfies "Stage 3 is the single authoritative
  protected-branch check".
- **HEAD-protected rejection scoped to commit/add.** Because Stage 3 now evaluates
  the destination, restricting the current-HEAD protected rejection to
  `git_add`/`git_commit` lets `git_checkout` leave a protected branch (target =
  unprotected branch is not protected) while still rejecting checkout *into* a
  protected branch. INV-03 holds for all tools.
- **One snapshot, passed through.** The authorization snapshot is taken once in
  `_run_tool()` (git_service) and used for Stage 3, 5b, and 7; the two in-pipeline
  `snapshot()` calls are deleted. The Stage 5b re-check keeps comparing
  `is_detached_head` (a property), not `active_branch`.
- **Live helpers retained.** `_validate_ref()` (used by `snapshot()` at line 115)
  and `_is_safe_ref()` (used by `_validate_ref()` at line 473) are NOT removed —
  they are live and unit-tested (`test_repository_state.py`), contrary to the
  plan's "remove duplicates" wording. See Plan Gap below.

## Alternatives considered

- **Pass a `destination: str | None` argument instead of `(tool_name,
  requested_branch)`.** Rejected: the plan specifies the destination is derived
  inside Stage 3 from the tool context, keeping `run()`'s call site uniform across
  tools and matching "the pre-pipeline `_validate_protected()` is retained as an
  early-rejection layer".
- **Keep the second snapshot for Stage 7 only.** Rejected by REQ-006, which removes
  both in-pipeline snapshots; the checkout postcondition is enforced inside
  `format_checkout()` (line 155), not solely by the pipeline.

## Implementation

### Target file

`scripts/mcp_servers/git/repository_state.py`

### Procedure

1. Make `verify_authorization()` destination-aware (REQ-002, REQ-003).
2. Thread `protected_branches` / `requested_branch` / `active_ref` through
   `run()` and remove the two in-pipeline snapshots (REQ-005, REQ-006).

### Method

#### Step 1 — Destination-aware `verify_authorization()` (REQ-002, REQ-003)

Change the signature (line 137) from `verify_authorization(self)` to accept the
operation context:

```python
def verify_authorization(
    self,
    tool_name: str,
    requested_branch: str | None = None,
    protected_branches: list[str] | None = None,
    active_ref: str = "",
) -> tuple[bool, str]:
    """Stage 3: authorization check against the operation destination."""
    if protected_branches is None:
        protected_branches = []
    # Destination = the branch the operation actually changes.
    if tool_name in ("git_add", "git_commit"):
        destination = self.active_branch          # current HEAD
    else:
        destination = requested_branch            # pull/push/checkout target
    # Ref-option injection guard (unchanged semantics).
    if not self.ref_valid:
        return False, f"[DENIED] Ref {destination!r} looks like a CLI option"
    # Protected check against the destination (normalized, case-insensitive).
    if destination:
        normalized_dest = _normalize_branch_name(destination)
        if any(
            _normalize_branch_name(p) == normalized_dest for p in protected_branches
        ):
            return False, f"[DENIED] {destination!r} is a protected branch"
    return True, ""
```

Behavior map this produces:

- `git_add` / `git_commit` on a protected HEAD → `destination = active_branch` →
  rejected (preserves INV-03 for all tools).
- `git_checkout` FROM a protected branch (target = unprotected) →
  `destination = requested_branch` (unprotected) → allowed (REQ-003).
- `git_checkout` INTO a protected branch → `destination` protected → rejected
  (INV-03).
- `git_pull` / `git_push` onto a protected branch → `destination = req.branch`
  protected → rejected (REQ-002, the force-push-via-`branch` closure).

Update the internal caller in `run()` (line 310) to pass the context:

```python
ok, msg = self._state.verify_authorization(
    tool_name, requested_branch, protected_branches, active_ref
)
```

#### Step 2 — Single snapshot; remove in-pipeline snapshots (REQ-005, REQ-006)

In `WriteProtectionPipeline.run()`:

- Delete the Stage 5b re-check snapshot (lines 342-346). Keep the
  `is_detached_head` comparison but compare against `self._state` (the single
  passed-in snapshot):

  ```python
  if self._state.is_detached_head != self._state.is_detached_head:
  ```

  Note: with a single shared snapshot this comparison is trivially equal, so the
  5b guard becomes a no-op identity check. If a real TOCTOU re-check is desired,
  that is a behavior change beyond this procedure — see Plan Gap.

- Delete the post-state snapshot (lines 366-371). Pass the single `self._state`
  as the postcondition state:

  ```python
  ok, msg = self._state.verify_postcondition(
      output, self._state, tool_name, requested_branch
  )
  ```

  Caveat: for `git_checkout` the pipeline's `verify_postcondition` then compares
  the pre-checkout snapshot's `active_branch` against `requested_branch`. The real
  postcondition is enforced inside `format_checkout()` (line 155, which refreshes
  its own snapshot). Confirm this does not double-fail a successful checkout; if
  it does, adjust the checkout branch of `verify_postcondition` or the post_state
  passed here — this is the open interaction noted in the Plan Gap, resolve at
  implementation time against the test suite.

### Details

- Retain module-level `_validate_ref()` (line 456) and `_is_safe_ref()` (line 451):
  both are live (`snapshot()` calls `_validate_ref` at line 115; `_validate_ref`
  calls `_is_safe_ref` at line 473) and covered by unit tests. Do NOT delete them.
- `verify_preconditions()`, `verify_postcondition()`, `audit()`, and the
  `PipelineResult` factory methods are unchanged except the `run()` body above.

## Compatibility considerations

- `verify_authorization()` now requires the operation context. Every existing caller
  must pass it: `run()` (above), and the real call in
  `test_git_security_compliance.py` (~line 1058) plus the direct-call tests in
  `test_repository_state.py` (lines 148, 300). Mock sites
  (`snap.verify_authorization.return_value = ...`) are unaffected by the signature
  change but must still be reachable with the new call convention.
- `branch` becoming required (REQ-004, `git_tools.py`/`git_models.py`) means
  `git_pull`/`git_push` always carry a non-empty `requested_branch`; the
  commit/add `None`-destination path is the only implicit-HEAD case.

## Security considerations

- Stage 3 is now the single authoritative protected-branch check against the
  destination, so a protected destination is rejected even if the pre-pipeline
  `_validate_protected()` were bypassed (REQ-002). Fail-closed: an empty/`None`
  `requested_branch` for commit/add falls back to the current-HEAD check; an
  unset `protected_branches` defaults to `[]` (no match → allow), consistent with
  the pre-existing snapshot behavior.
- Removing the in-pipeline snapshots makes the audited state identical to the
  decision state within one call (REQ-006); it does not weaken any rejection.

## Rollback considerations

- Revert the single commit touching `repository_state.py`. The public
  `RepositoryState` dataclass and `run()` signature are unchanged, so the git_service
  forwarder and tests only need the one-file revert.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| Destination-based Stage 3 | Integration (temp repo) | `uv run pytest tests/mcp_servers/git/test_repository_state.py -v` | checkout FROM protected branch succeeds; checkout/push/pull INTO protected branch rejected at Stage 3 |
| Pipeline inputs | Integration | `uv run pytest tests/mcp_servers/git/test_repository_state.py -v` | `run()` receives `protected_branches`/`requested_branch`/`active_ref`; protected destination rejected even when pre-pipeline check bypassed |
| Single snapshot | Unit | dispatched write call records exactly one `snapshot()` | one `RepositoryState.snapshot()` per dispatched call |
| Whole git-mcp module | Full suite | `uv run pytest tests/mcp_servers/git/ -v` | no new failures |
| Toolchain | Static/type/security | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | clean per `rules/toolchain.md` |

## Completion criteria

- `verify_authorization()` rejects a protected destination named by
  `requested_branch` (pull/push/checkout) and a protected current HEAD for
  commit/add; checkout away from a protected branch is allowed.
- `run()` forwards `protected_branches`/`requested_branch`/`active_ref` to Stage 3
  and the Stage 5b re-check; exactly one `snapshot()` is taken per dispatched call.
- `_validate_ref()` / `_is_safe_ref()` remain present and their unit tests pass.
- Full git-mcp suite and toolchain pass with no new failures.

## Out of scope

- Forwarding the inputs from `git_service._run_tool()` — own document.
- Making `branch` required in schema/models — REQ-004, own documents.
- Audit record / error-path changes (separate issue).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement destination-aware `verify_authorization()` + single-snapshot in repository_state.py | Pending | — | — | REQ-002/003/005/006 |
| 2 | Add or update tests per Validation plan | Pending | — | — | test_repository_state.py own row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: doc updates are Rows 8-10 |

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
- **Requirement ID**: `REQ-002` (route protected-branch decision to destination), `REQ-003` (checkout away from a protected branch allowed), `REQ-005` (pipeline inputs reach Stage 5b re-check), `REQ-006` (single snapshot per call)
- **Source issue**: `issues/20261007-153840_gitref01_fix-git-mcp-ref-validation-and-protected-branch-check.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261007-162035_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261007-170610
- **Related target files**: `scripts/mcp_servers/git/repository_state.py`

---

## Plan Gap (for plan amendment, not implementation)

The plan's Row 2 lists "remove module-level `_is_safe_ref`/`_validate_ref`
duplicates" as a change. Adversarial verification shows both are **live** and
unit-tested:

- `_validate_ref()` (line 456) is called by `RepositoryState.snapshot()` at line
  115 (`ref_valid=_validate_ref(active_ref, branch_name)`).
- `_is_safe_ref()` (line 451) is called by `_validate_ref()` at line 473.
- `test_repository_state.py` contains direct unit tests for `_validate_ref()`
  (option-like/malformed ref rejection, empty-ref resolution).

Deleting them would break `snapshot()` and those tests. This document therefore
RETAINS both and does not implement the removal. Recommend amending the plan's Row
2 Reason for Modification / Evidence to drop the removal (or routing it to a
dedicated cleanup issue), rather than removing the symbols here.
