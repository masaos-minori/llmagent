## Goal
Make `GitHubConfig.load()` refuse a `github_mcp_server.toml` whose `protected_branches` is empty or absent, while an empty `path_denylist` stays valid under the ADR-004 exception (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit


## Assumptions
- Plan Step 3a finding: rejecting in `GitHubConfig.from_dict()` was measured to fail 202 tests in 9 files (all of `test_service_dispatch.py`, `test_service_file.py`, `test_service_issues.py`, `test_service_pull_requests.py`, `test_service_repository.py`, `test_github_mcp_service.py`, `test_github_server_auth.py`, `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` build configs through `from_dict()` without `protected_branches`), most of them are not target rows; the check lives in `load()`, used at `scripts/mcp_servers/github/github_server.py:74`.
- The shipped `config/github_mcp_server.toml:19` sets `protected_branches` non-empty and `:28` ships `path_denylist = []`; both must still load.
- The empty `path_denylist` exception is the maintainer's decision (2026-11-10); its rationale text is pending (UNK-01) and is not written here.

## Design decisions
- Validate in `load()` after `from_dict()`; raise `ValueError` naming `protected_branches` and `github_mcp_server.toml`.
- Do not touch `path_denylist` handling: no validation, no default change.

## Alternatives considered
Rejecting in `from_dict()` was rejected (measured fallout). A separate `validate()` method was rejected as new surface for one check.

## Implementation
### Target file
`scripts/mcp_servers/github/github_models_config.py`

### Procedure
- Edit `GitHubConfig.load()` (`scripts/mcp_servers/github/github_models_config.py:62-64`): bind `from_dict(ConfigLoader().load(...))` to a local, raise `ValueError` when its `protected_branches` is empty, else return it; update the docstring.
- Leave `from_dict()` (lines 45-59) and the field defaults (lines 32-33) unchanged.

### Method
- Message: `github_mcp_server.toml: protected_branches must not be empty`. `ConfigLoader` is already imported (line 15); no new import.

### Details
- `GitHubConfig.load()` callers: `scripts/mcp_servers/github/github_server.py:74` (import time, server refuses to start).
- Runtime consequence handled in `scripts/mcp_servers/github/github_service_security.py` (skip branch removal, posture check) by its own document.

### Companion test files
- `tests/mcp_servers/github/test_service_security.py`
  - Procedure: Update the module docstring lines 13-16 (the "protected_branches empty -> skip entirely" remark); change the two `"protected_branches": []` fixtures (around lines 182 and 276, both calling `create_or_update_file` with `branch="main"`) to a non-empty list that does not match `main` such as `["release/*"]`; add `test_load_rejects_empty_protected_branches` (new), `test_load_rejects_absent_protected_branches` (new), and `test_load_allows_empty_path_denylist` (new) that patch `mcp_servers.github.github_models_config.ConfigLoader` and assert `pytest.raises(ValueError, match="protected_branches")` or a successful load.
  - Validation: `uv run pytest tests/mcp_servers/github/test_service_security.py -v`; `uv run python tools/check_mock_patch_targets.py`

## Compatibility considerations
An operator `github_mcp_server.toml` with an empty or missing `protected_branches` stops loading and the server does not start; the shipped file is non-empty. `from_dict()` behavior is unchanged, so test and tool code that builds configs directly is unaffected.

## Security considerations
Removes an allow-all path for protected branches. `path_denylist` empty stays permitted by the registered ADR-004 exception; the error text names keys only, never the token.

## Rollback considerations
Revert the commit that carries this change; no persisted state is touched.

## Validation plan
- `uv run pytest tests/mcp_servers/github tests/mcp_servers/cicd -v` (confirms `from_dict()` users are untouched)
- `uv run ruff format` and `uv run ruff check` on the two files; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`
- `uv run python tools/check_module_size.py`

## Completion criteria
- `GitHubConfig.load()` raises `ValueError` for an empty or absent `protected_branches` and loads the shipped file; an empty `path_denylist` still loads (`AC-04`).
- `from_dict()` untouched; the github suite passes.

## Out of Scope
- The skip-branch removal and posture text in `github_service_security.py` (separate document).
- Writing the ADR-004 rationale (pending maintainer statement, UNK-01) and the `config/github_mcp_server.toml` annotation (separate document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the empty-list rejection to `GitHubConfig.load()` and update its docstring | Done | 20261110-172551 | 20261110-172551 | |
| 2 | Update the two `[]` fixtures and add the rejection and acceptance cases in `tests/mcp_servers/github/test_service_security.py` (companion) | Done | 20261110-172551 | 20261110-172551 | Fixtures now `["release/*"]` (non-empty, non-matching `main`); module docstring remark updated; new `TestGitHubConfigLoad` with 3 cases |
| 3 | Run the validation sequence (`rules/toolchain.md`) and `check_module_size.py` | Done | 20261110-172551 | 20261110-172551 | 545 github+cicd tests passed; check_mock_patch_targets clean; check_module_size ALL OK; ruff clean; mypy deferred to batch end gate |

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
- **Requirement ID**: `REQ-004` (reject an empty `protected_branches` at config load; keep `path_denylist` empty permitted)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/mcp_servers/github/github_models_config.py`, `tests/mcp_servers/github/test_service_security.py`
