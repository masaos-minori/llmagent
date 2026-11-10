## Goal
Make `GitConfig.load()` refuse a `git_mcp_server.toml` whose `protected_branches` is empty or absent, so the git server cannot start with the protected-branch boundary silently removed (`REQ-004`, ADR-004 Decision Group 1).

## Scope
**Release unit**: N/A: not part of a release unit


## Assumptions
- Plan Step 3a finding: rejecting inside `GitConfig.from_dict()` was measured to fail tests outside the target table (the experiment failed 202 tests in 9 files across git and github test modules, 7 of them in `tests/mcp_servers/git/test_git_models.py`); the check therefore lives in `GitConfig.load()`, the production entry used by `scripts/mcp_servers/git/git_server.py:65`. The Plan's REQ-004 text was corrected accordingly.
- `from_dict()` stays a pure parser; direct `GitConfig(...)` construction and `from_dict()` with an empty list remain valid for unit tests.
- The shipped `config/git_mcp_server.toml:36` sets `protected_branches = ["main", "master", "release"]`, so the shipped configuration keeps loading (`tests/mcp_servers/git/test_git_models.py:126-128` asserts it).
- The comment above that key in `config/git_mcp_server.toml:33-34` says an empty list means no protection; that file is a Plan Reference File (not a target), so the stale comment is reported, not edited (see Out of Scope).

## Design decisions
- Validate in `load()` after `from_dict()` and raise `ValueError` whose message names `protected_branches` and the file `git_mcp_server.toml`; `ValueError` matches the other config validation errors raised by `get_typed()` in this module.
- Absent key and an explicit empty list are both rejected, because `from_dict()` already defaults the absent key to `[]`.

## Alternatives considered
Rejecting in `from_dict()` was rejected (measured fallout outside the frozen table). Adding a pydantic validator was rejected: `GitConfig` is a dataclass, not a model.

## Implementation
### Target file
`scripts/mcp_servers/git/git_models.py`

### Procedure
- Edit `GitConfig.load()` (currently `scripts/mcp_servers/git/git_models.py:99-102`): bind the `from_dict()` result to a local, raise `ValueError` when `cfg.protected_branches` is empty, otherwise return it.
- Update the `load()` docstring to state that an empty `protected_branches` is a load error.
- Leave `from_dict()` (lines 62-96) and the `protected_branches` field default (line 53) unchanged.

### Method
- Message shape: `git_mcp_server.toml: protected_branches must not be empty` (key and file named so an operator can fix it).
- No new import is needed; `ConfigLoader` is already imported at module level (line 15).

### Details
- Callers of `GitConfig.load()`: `scripts/mcp_servers/git/git_server.py:65` (import-time, so the server refuses to start) and `tests/mcp_servers/git/test_git_models.py:127,131`, `tests/mcp_servers/git/test_git_security_compliance.py:174` (shipped config, non-empty).
- `from_dict()` and the `GitConfig` default of `[]` stay valid; the runtime enforcement in `scripts/mcp_servers/git/repository_state.py` and `scripts/mcp_servers/git/git_ref_validation.py` is unchanged.

### Companion test files
- `tests/mcp_servers/git/test_git_models.py`
  - Procedure: In `TestGitConfigLoad` add `test_load_rejects_empty_protected_branches` (new) and `test_load_rejects_absent_protected_branches` (new): patch `mcp_servers.git.git_models.ConfigLoader` so `load()` returns a dict with `protected_branches` empty or missing, and assert `pytest.raises(ValueError, match="protected_branches")`; add a case that a non-empty list loads; keep the shipped-config assertion at line 126-128.
  - Validation: `uv run pytest tests/mcp_servers/git/test_git_models.py -v`; `uv run python tools/check_mock_patch_targets.py` (the patch target is the module that imports `ConfigLoader`).

## Compatibility considerations
An operator `git_mcp_server.toml` with an empty or missing `protected_branches` stops loading and the git server does not start; the shipped file is non-empty. No API or persisted-schema change.

## Security considerations
Closes an allow-all path: an empty list currently disables the protected-branch guard (ADR-004 Decision Group 1 forbids a safety boundary that depends on being non-empty). Fail-closed at load; the message must not echo any token.

## Rollback considerations
Revert the commit that carries this change; no persisted state is touched.

## Validation plan
- `uv run pytest tests/mcp_servers/git -v`
- `uv run ruff format scripts/mcp_servers/git/git_models.py tests/mcp_servers/git/test_git_models.py` and `uv run ruff check` on both
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`
- `uv run python tools/check_module_size.py` (the module must not grow past the gate)

## Completion criteria
- `GitConfig.load()` raises `ValueError` naming `protected_branches` for an empty or absent list and returns the shipped config unchanged.
- `from_dict()` is unchanged and the rejection tests pass (`AC-04`).

## Out of Scope
- Editing `config/git_mcp_server.toml` (its comment at lines 33-34 still says an empty list means no protection; report it for a Plan amendment).
- Documents (`docs/22_mcp/mcp_04_05_git.md`) are separate rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the empty-list rejection to `GitConfig.load()` and update its docstring | Done | 20261110-172551 | 20261110-172551 | |
| 2 | Add the rejection and acceptance cases to `tests/mcp_servers/git/test_git_models.py` (companion) | Done | 20261110-172551 | 20261110-172551 | 3 new cases via monkeypatched ConfigLoader |
| 3 | Run the validation sequence (`rules/toolchain.md`) and `check_module_size.py` | Done | 20261110-172551 | 20261110-172551 | 419 git tests passed; check_mock_patch_targets clean; check_module_size ALL OK; ruff clean; mypy deferred to batch end gate |

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
- **Requirement ID**: `REQ-004` (reject an empty `protected_branches` at config load)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/mcp_servers/git/git_models.py`, `tests/mcp_servers/git/test_git_models.py`
