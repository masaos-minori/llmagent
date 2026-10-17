## Goal

Make Stage 5b of `scripts/mcp_servers/git/repository_state.py` actually re-read the repository HEAD
identity from the live repository object immediately before the mutating Git call, instead of
comparing the single snapshot with itself (REQ-008).

## Scope

- Add a module-level `_live_head_identity` (new) helper that reads HEAD from the snapshot's repository
  object.
- Replace the self-comparison in Stage 5b with a comparison between the live identity and the
  authorized identity.
- Skip the check when the snapshot carries no real repository object.

## Assumptions

- `RepositoryState` already holds the live repository object in `_repo`
  (`scripts/mcp_servers/git/repository_state.py:71`) and records `head_type` and `active_branch` at
  snapshot time (`scripts/mcp_servers/git/repository_state.py:105-116`), so both sides of the
  comparison are the same kind of value.
- Pipeline tests build states either with `MagicMock(spec=RepositoryState)` or with a real
  `RepositoryState` whose `_repo` is a plain `MagicMock`; neither is an instance of `git.Repo`.

## Design decisions

- Guard the re-read with `isinstance(repo, git.Repo)` rather than a truthiness or `is not None` test:
  `MagicMock(spec=git.Repo)` passes `isinstance`, but no pipeline snapshot in this repository uses
  that form, and a plain `MagicMock` is correctly excluded. This resolves UNK-04.
- Implement the read as a module-level function, not a `RepositoryState` method: a
  `MagicMock(spec=RepositoryState)` would auto-create any new method and return a mock value, which
  would make the guard fire in tests that must not deny.
- Compare the full identity pair `(head_type, active_branch)` instead of only the detached/attached
  flag, because the guard now reads a live repository and no longer depends on fields that test
  doubles may not populate. This also catches branch-name drift, which the old comparison could not.
- Fail closed when the live read raises: return the `_HEAD_UNREADABLE` (new) sentinel so Stage 5b
  denies rather than silently skipping, because an unreadable HEAD means drift cannot be ruled out.

## Alternatives considered

- Take a second `RepositoryState.snapshot()` for the re-check: rejected — it opens a second repository
  handle per request and contradicts the single-shared-snapshot decision the pipeline documents at
  `scripts/mcp_servers/git/repository_state.py:385-387`.
- Compare only `is_detached_head` against the live value: rejected — it leaves the common drift case
  (attached HEAD moved to another branch) undetected.

## Implementation

### Target file

`scripts/mcp_servers/git/repository_state.py`

### Procedure

1. Add the `_HEAD_UNREADABLE` (new) sentinel and the `_live_head_identity` (new) function above
   `WriteProtectionPipeline`.
2. Replace the self-comparison block in Stage 5b with the live comparison.
3. Rewrite the Stage 5b comment so it describes the live re-read instead of the no-op.

### Method

Read HEAD from the repository object the snapshot already holds; no new snapshot, no new lock, no
change to the stage ordering or the recorded `PipelineStage` entries.

### Details

- New module-level code, placed before `class WriteProtectionPipeline`
  (`scripts/mcp_servers/git/repository_state.py:300`):

```
_HEAD_UNREADABLE: tuple[str, None] = ("unreadable", None)


def _live_head_identity(state: RepositoryState) -> tuple[str, str | None] | None:
    """Return (head_type, active_branch) read from the live repository object.

    Returns None when the snapshot holds no real git.Repo, which is the case for
    test doubles and for snapshots built without a repository reference.
    """
    repo = state._repo
    if not isinstance(repo, git.Repo):
        return None
    try:
        if repo.head.is_detached:
            return ("detached", None)
        return ("branch", repo.active_branch.name)
    except (ValueError, TypeError, git.exc.GitError) as exc:
        logger.warning("Stage 5b: live HEAD read failed for %s: %s", state.path, exc)
        return _HEAD_UNREADABLE
```

- Stage 5b currently reads `if self._state.is_detached_head != self._state.is_detached_head:` at
  `scripts/mcp_servers/git/repository_state.py:374` with its rejection at
  `scripts/mcp_servers/git/repository_state.py:375-379`. Replace the condition with:

```
            live_identity = _live_head_identity(self._state)
            if live_identity is not None and live_identity != (
                self._state.head_type,
                self._state.active_branch,
            ):
```

- Keep the existing `PipelineResult.reject` call and its message unchanged, and keep the
  `record_stage` entry at `scripts/mcp_servers/git/repository_state.py:380-382`.
- Replace the comment block at `scripts/mcp_servers/git/repository_state.py:361-373`, which currently
  states that the guard is a no-op, with a comment that states the guard reads the live HEAD identity
  and skips only when the snapshot holds no real repository object.
- `is_detached_head` (`scripts/mcp_servers/git/repository_state.py:120-122`) stays: it is still used by
  `verify_preconditions` at `scripts/mcp_servers/git/repository_state.py:188`.

## Compatibility considerations

- Calls that previously always passed Stage 5b can now be denied when HEAD drifted between
  authorization and execution. That is the intended behaviour change (AC-008).
- `tests/mcp_servers/git/test_repository_state.py` contains tests that assert the no-op does not deny
  drifted HEAD; Plan row 10 inverts them.
- The recorded stage list, `PipelineResult` shape, and lock scope are unchanged.

## Security considerations

- The re-read closes the authorization-to-execution window that the Plan records as the git-mcp
  postcondition gap.
- The rejection message contains no path or branch content beyond what the pipeline already reports.

## Rollback considerations

N/A: revert the commit. Reverting restores a guard that cannot fail, so any rollback must re-register
MCP-006 in the known-issue ledger.

## Validation plan

- `uv run pytest -q tests/mcp_servers/git/test_repository_state.py tests/mcp_servers/git/test_git_service_dispatch.py tests/mcp_servers/git/test_git_concurrency.py`
- `uv run pytest -q tests/mcp_servers/git/`
- `uv run ruff format --check . && uv run ruff check . && uv run mypy --no-namespace-packages scripts/ && uv run lint-imports`
- `uv run python tools/generate_reference_table.py --check`

## Completion criteria

- A snapshot whose HEAD identity differs from the live repository identity is denied at Stage 5b with
  the existing rejection message (AC-008).
- A snapshot whose HEAD identity matches the live repository identity passes Stage 5b and records the
  stage as it does today.
- A snapshot whose `_repo` is not a real `git.Repo` never denies at Stage 5b.
- `tests/mcp_servers/git/test_git_service_dispatch.py` and
  `tests/mcp_servers/git/test_git_concurrency.py` still pass unchanged.

## Out of scope

- Adding a second `RepositoryState` snapshot per request.
- Changing Stage 7 postcondition verification.
- Fixing the swapped request-context binding in `scripts/mcp_servers/git/git_server.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the live-identity helper and sentinel | Completed | 20261017-183000 | 20261017-184500 | REQ-008 |
| 2 | Replace the Stage 5b self-comparison and rewrite its comment | Completed | 20261017-183000 | 20261017-184500 | REQ-008 |
| 3 | Add or update tests per Validation plan | Completed | 20261017-183000 | 20261017-185200 | Owned by Plan row 10 row 10 landed |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

## Work Items Created

- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-008
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162434
- **Related target files**: `scripts/mcp_servers/git/repository_state.py`