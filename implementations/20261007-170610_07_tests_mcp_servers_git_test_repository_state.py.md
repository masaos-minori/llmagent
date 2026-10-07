# Implementation Procedure

## Goal

Update `tests/mcp_servers/git/test_repository_state.py` for the two changes made to
`repository_state.py` in this Plan: the new `verify_authorization()` operation-context
signature (`REQ-002`) and the single-snapshot rewrite of `WriteProtectionPipeline.run()`
(`REQ-006`), and add the Stage 5b-input / destination-based Stage 3 rejection test
(Test 4; `REQ-005`, `REQ-002`). Driven by `REQ-003`, `REQ-005`; Tests 4.

## Scope

Modifies only `tests/mcp_servers/git/test_repository_state.py`. Cross-file effects are
dependencies, not targets:

- `scripts/mcp_servers/git/repository_state.py` — new
  `verify_authorization(tool_name, requested_branch, protected_branches, active_ref)`
  signature and the removed in-pipeline snapshots (own document,
  `implementations/..._repository_state_py.md`).
- `scripts/mcp_servers/git/git_service.py` — the pre-pipeline `_validate_protected()`
  early-rejection layer this test bypasses by calling `pipeline.run()` directly (own
  document).

## Assumptions

- `WriteProtectionPipeline.run()` already declares `requested_branch` /
  `protected_branches` / `active_ref` parameters (repository_state.py lines 304-306);
  the body threads them to `verify_authorization()`.
- `verify_authorization()` now derives the destination from `tool_name` +
  `requested_branch` and normalizes both sides via `_normalize_branch_name()` before
  comparing against `protected_branches`.
- `MagicMock(spec=RepositoryState)` call sites keep working: a mock's
  `verify_authorization(...)` accepts any arguments and returns its preset
  `.return_value`, so the signature change does not break them.

## Design decisions

- **Fix only the real call site.** Of the two `verify_authorization()` call sites in
  this file, only line 148 calls it on a real snapshot state and breaks; line 300
  calls it on a `MagicMock` and is unaffected. Verify with `rg` before editing — do
  not assume both break.
- **Test 4 calls `pipeline.run()` directly to bypass the pre-pipeline check.** Calling
  the pipeline directly (not through `GitService` dispatch) means
  `_validate_protected()` never runs, so a rejection here proves Stage 3 alone rejects
  a protected destination (`REQ-002`: "even when the pre-pipeline check is bypassed").
- **A real temporary repository exercises the real normalization.** Test 4 builds a
  live repo so `_normalize_branch_name()` / `_is_protected_branch()` run for real,
  rather than relying on a stubbed mock return value.

## Alternatives considered

- **Stub `verify_authorization` on a `MagicMock` for Test 4.** Rejected: a stubbed
  return value does not exercise the destination/normalization logic being added, so
  it would not actually verify `REQ-002`/`REQ-005`.
- **Drive Test 4 through `GitService.git_checkout`.** Rejected: the dispatch path
  runs the pre-pipeline `_validate_protected()` first, so a rejection could come from
  either layer; calling `pipeline.run()` directly isolates Stage 3.

## Implementation

### Target file

`tests/mcp_servers/git/test_repository_state.py`

### Procedure

1. Fix the real `verify_authorization()` call at line 148 (new signature).
2. Update tests broken by the single-snapshot rewrite (`REQ-006`).
3. Add the Stage 5b-input / destination-based Stage 3 rejection test (Test 4;
   `REQ-002`, `REQ-005`).

### Method

#### Step 1 — Fix the real call at line 148 (`verify_authorization` signature)

`test_verify_authorization_delegates_to_state` (line 146) calls
`state.verify_authorization()` on a real snapshot. The new signature requires the
operation context; pass a tool name:

```python
def test_verify_authorization_delegates_to_state(self, working_repo: str) -> None:
    state = RepositoryState.snapshot(working_repo)
    ok, err = state.verify_authorization("git_status")
    assert ok is True
    assert err == ""
```

Line 300 (`test_protected_branch_rejected`) uses `snap = MagicMock(spec=RepositoryState)`
and is unaffected — leave it unchanged.

#### Step 2 — Update tests broken by the single-snapshot rewrite (REQ-006)

The single-snapshot change removes the Stage 5b re-check snapshot and the post-state
snapshot from `WriteProtectionPipeline.run()`. Two existing tests encode the removed
behavior:

- `test_head_drifted_since_authorization_is_rejected` (lines 473-497) asserts that a
  HEAD detached between the authorization snapshot and the pipeline run is rejected at
  `Stage 5b`. Under the single-snapshot design there is no re-snapshot, so the Stage
  5b guard no longer fires and `op()` runs. This is a **behavior change**, not a test
  bug. Update it to reflect the new semantics — either remove it or re-scope it to
  assert that the operation runs against the single authorized snapshot (HEAD drift is
  no longer caught at Stage 5b). Recommend removing it and recording the removed TOCTOU
  guard as a Plan Gap follow-up (see below), since asserting a guard that no longer
  exists would be misleading.
- `test_pipeline_run_proceeds_to_stage_5_when_auth_passes` (lines 656-667) patches
  `RepositoryState.snapshot` expecting a Stage 5b re-snapshot. With the in-pipeline
  snapshot removed, `pipeline.run()` no longer calls `snapshot()`, so the
  `with patch.object(RepositoryState, "snapshot", ...)` wrapper is unnecessary. Remove
  the patch (and its stale comment); the assertion `result.ok is True` still holds
  against the mock state.

> **Behavior-change note.** Removing the Stage 5b re-snapshot means the pipeline no
> longer detects a HEAD state change between authorization and execution. This is an
> intentional consequence of REQ-006 ("one authorization snapshot per call"), but it
> removes a TOCTOU guard. Confirm this is acceptable; if a real re-check is desired it
> is a behavior change beyond this procedure — flag it as a Plan Gap.

#### Step 3 — Stage 5b-input / destination-based Stage 3 rejection test (Test 4; REQ-002, REQ-005)

Add a class that calls `pipeline.run()` directly with a protected destination and
asserts rejection at Stage 3 even though the pre-pipeline check was bypassed, and that
the inputs reach `verify_authorization()`.

```python
# ── Stage 3 destination protection with pipeline inputs (REQ-002, REQ-005) ───────


class TestStage3DestinationProtection:
    """REQ-002/REQ-005: Stage 3 rejects a protected destination using the
    inputs run() receives, even when the pre-pipeline check is bypassed."""

    def test_protected_destination_rejected_at_stage_3_without_precheck(
        self, working_repo: str
    ) -> None:
        from mcp_servers.git.repository_state import WriteProtectionPipeline

        # HEAD is on main (protected); call the pipeline directly so the
        # git_service pre-pipeline _validate_protected() never runs.
        state = RepositoryState.snapshot(
            working_repo, protected_branches=["main"]
        )
        pipeline = WriteProtectionPipeline(state)

        op_called = False

        def _op() -> str:
            nonlocal op_called
            op_called = True
            return "should not run"

        result = pipeline.run(
            "git_checkout",
            _op,
            requested_branch="main",
            protected_branches=["main"],
            active_ref="main",
        )
        assert result.ok is False
        assert result.rejected_at_stage == "Stage 3"
        assert op_called is False

    def test_unprotected_destination_allowed(self, working_repo: str) -> None:
        from mcp_servers.git.repository_state import WriteProtectionPipeline

        state = RepositoryState.snapshot(
            working_repo, protected_branches=["main"]
        )
        pipeline = WriteProtectionPipeline(state)
        result = pipeline.run(
            "git_checkout",
            lambda: "ok",
            requested_branch="develop",
            protected_branches=["main"],
            active_ref="develop",
        )
        assert result.ok is True
```

If `working_repo`'s current branch is not `main`, create a branch/commit setup so the
destination comparison is meaningful (the fixture's branch is whatever the CI repo
defaults to); adjust `requested_branch`/`protected_branches` to match, or build a
fresh repo in the test as in `test_git_service_dispatch.py`'s
`TestDestinationBasedProtection`.

### Details

- The mock-based `TestStage3Authorization` tests set
  `snap.verify_authorization.return_value` explicitly, so they accept the new
  positional/keyword call convention unchanged — no edit required there.
- Do not touch `test_git_security_compliance.py`: its `verify_authorization()` call
  (line ~1058) is inside a `mock_pipeline_run` stub operating on a `MagicMock`
  `fake_state`, whose `verify_authorization.return_value` is preset — the real
  signature change does not reach it. Verified via `rg`.

## Compatibility considerations

- Any other real (non-mock) caller of `verify_authorization()` outside this file must
  also pass the operation context. The only production caller is
  `WriteProtectionPipeline.run()` in `repository_state.py` (own document). Confirm no
  other real call site exists before running the suite.
- Making `branch` required (`REQ-004`, `git_models.py`) means `requested_branch` is
  always non-empty for pull/push; the commit/add `None`-destination fallback in
  `verify_authorization()` remains the only implicit-HEAD path.

## Security considerations

- Test 4 is the key assertion that Stage 3 is the single authoritative protected-branch
  check: a protected destination is rejected even when the pre-pipeline
  `_validate_protected()` is skipped. Keep this direct-call form — driving it through
  dispatch would let the pre-pipeline check mask a Stage 3 regression.
- Removing the Stage 5b TOCTOU re-check (Step 2) does not weaken any protected-branch
  or ref rejection; it only removes the HEAD-drift detection. State this explicitly in
  the commit message.

## Rollback considerations

- Revert the single commit touching `test_repository_state.py`. The edits are local to
  three tests plus one new class; reverting restores the prior suite unchanged.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| New `verify_authorization` signature | Unit (real snapshot) | `uv run pytest tests/mcp_servers/git/test_repository_state.py::TestGuardDelegation -v` | line 148 passes with a tool name |
| Single-snapshot behavior | Unit (temp repo) | `uv run pytest tests/mcp_servers/git/test_repository_state.py::TestHeadIdentityRecheck -v` | updated/removed per new semantics |
| Destination-based Stage 3 + inputs | Integration (temp repo) | `uv run pytest tests/mcp_servers/git/test_repository_state.py::TestStage3DestinationProtection -v` | protected destination rejected at Stage 3 without precheck; unprotected allowed |
| Whole git-mcp module | Full suite | `uv run pytest tests/mcp_servers/git/ -v` | no new failures |
| Toolchain | Static/type/security | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | clean per `rules/toolchain.md` |

## Completion criteria

- The only real `verify_authorization()` call in the file passes the operation
  context; mock-site calls remain valid.
- Tests encoding the removed Stage 5b TOCTOU re-check are updated or removed, with the
  behavior change recorded.
- `pipeline.run()` with a protected `requested_branch` rejects at Stage 3 when called
  directly (pre-pipeline check bypassed); an unprotected destination is allowed.
- Full git-mcp suite and toolchain pass with no new failures.

## Out of scope

- The `verify_authorization()` signature and single-snapshot rewrite itself —
  `repository_state.py`, own document.
- Forwarding the pipeline inputs from `git_service._run_tool()` — own document.
- The allow-list ref validation and schema tests — `git_service.py` /
  `test_git_service_dispatch.py`, own documents.
- Modifying `test_git_security_compliance.py` — verified unaffected (MagicMock call in
  a pipeline stub).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix real `verify_authorization()` call (line 148) | Pending | — | — | new signature |
| 2 | Update tests broken by single-snapshot rewrite (REQ-006) | Pending | — | — | behavior change |
| 3 | Add destination-based Stage 3 rejection test (Test 4) | Pending | — | — | REQ-002/005 |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (checkout away from a protected branch allowed), `REQ-005` (pipeline inputs reach Stage 5b re-check), `REQ-002` (route protected-branch decision to destination)
- **Source issue**: `issues/20261007-153840_gitref01_fix-git-mcp-ref-validation-and-protected-branch-check.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261007-162035_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261007-170610
- **Related target files**: `tests/mcp_servers/git/test_repository_state.py`

---

## Plan Gap (for plan amendment, not implementation)

The plan's Row 2 lists "remove module-level `_is_safe_ref`/`_validate_ref`
duplicates" as a change (already documented in the repository_state.py document). This
document adds a second Plan Gap:

**REQ-006 removes the Stage 5b TOCTOU re-check.** The plan's Design section states the
two in-pipeline snapshots are removed and "the Stage 5b re-check keeps comparing
`is_detached_head` (a property)". With a single shared snapshot, that comparison is an
identity no-op (`self._state.is_detached_head != self._state.is_detached_head`), so the
pipeline no longer detects a HEAD detached/attached drift between the authorization
snapshot and execution. `test_repository_state.py::TestHeadIdentityRecheck`
(`test_head_drifted_since_authorization_is_rejected`) encodes the removed behavior and
must be removed/re-scoped. Recommend amending the plan's REQ-006 wording to note that
the TOCTOU re-check is intentionally dropped (defense-in-depth reduced to a single
snapshot), rather than leaving the Design section implying a live re-check.
