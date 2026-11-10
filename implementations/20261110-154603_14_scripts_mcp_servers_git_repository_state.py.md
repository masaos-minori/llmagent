## Goal
Stop `repository_state.py` from treating an empty `protected_branches` as a supported "never protected" mode now that config load rejects it (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit


## Assumptions
- Behavior for `[]` is identical with or without the early returns: `any(...)` over an empty list is False, and `_is_protected_branch()` then returns False at the end. So the change is a wording and guard cleanup, not a behavior change.
- `None` must stay safe: `RepositoryState.snapshot(path)` passes `protected_branches=None` by default (`tests/mcp_servers/git/test_repository_state.py:136-138`), and `any(... for p in None)` would raise `TypeError`.

## Design decisions
- Narrow both guards from `if not protected_branches` to `if protected_branches is None`, so only an unset argument short-circuits and an empty list is no longer special-cased.
- Reword the `_matches_protected()` docstring: an unset list matches nothing; an empty list cannot come from a loaded config.

## Alternatives considered
Deleting the guards entirely was rejected: `None` is the documented default of the `protected_branches` parameter in `snapshot()` and `verify_authorization()` and would raise. Making the parameter non-optional was rejected as an interface change outside the Plan.

## Implementation
### Target file
`scripts/mcp_servers/git/repository_state.py`

### Procedure
- In `_matches_protected()` (`scripts/mcp_servers/git/repository_state.py:251-262`) change the guard to `is None` and the docstring wording.
- In `_is_protected_branch()` (line 265-283) change `if not protected_branches: return False` to `is None`, and adjust the docstring if it mentions an empty list.

### Method
- Keep every other line, including the detached-HEAD and empty-normalized-name returns.

### Details
- Callers: `snapshot()` (line 89) and `verify_authorization()` (line 154), both pass the config list or `None`.
- Module size is not affected (byte count unchanged to within a few bytes).

### Companion test files
- `tests/mcp_servers/git/test_repository_state.py`
  - Procedure: Replace `test_is_not_protected_branch_empty_list` (asserts `_is_protected_branch(repo, [])` is False, around line 46 of the `_is_protected_branch` test class) with a `None` case `_is_protected_branch(repo, None) is False`; keep a case showing a non-matching list returns False.
  - Validation: `uv run pytest tests/mcp_servers/git/test_repository_state.py -v`

## Compatibility considerations
No behavior change for `None`, `[]`, or non-empty lists; no public signature change.

## Security considerations
Does not weaken any enforced check; the fail-closed guarantee for an empty list comes from the config-load rejection in `scripts/mcp_servers/git/git_models.py`.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/mcp_servers/git -v`
- `uv run ruff check scripts/mcp_servers/git/repository_state.py` and `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`

## Completion criteria
- No code or docstring in `repository_state.py` describes an empty `protected_branches` as "never protected"; `None` still returns False; the git tests pass.

## Out of Scope
- The config-load rejection (separate document for `scripts/mcp_servers/git/git_models.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Narrow the two guards and reword the docstring in `repository_state.py` | Pending | — | — | |
| 2 | Replace the empty-list test case with a `None` case (companion) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (remove the empty-list "never protected" wording and branch)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/mcp_servers/git/repository_state.py`, `tests/mcp_servers/git/test_repository_state.py`
