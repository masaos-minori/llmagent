## Goal

Replace the bare `int()` / `list()` coercions in `GitHubConfig.from_dict` with `get_typed(...)`-style validation while preserving `get_str` and the fail-closed `load()` empty-`protected_branches` guard (REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Scope follows the frozen Acceptance Criteria: only `int()` / `float()` / `list()` are replaced. The `bool(...)` coercions (`allow_force_push`, `require_pr_review`) are retained (scope boundary, per the Plan's Assumptions/UNK-01).
- `get_str` is retained for string fields.

## Design decisions
- Route every bare `int()` field through `get_typed(..., int, ..., default=<dataclass default>)` and every bare `list()` field through `list(get_typed(..., list, "a list", default=[]))`.

## Alternatives considered
- Replacing `bool(...)` too: rejected as out of scope for the frozen acceptance gate (UNK-01); recommended as a follow-up.

## Implementation
### Target file
`scripts/mcp_servers/github/github_models_config.py`

### Procedure
1. Replace every bare `int()` in `GitHubConfig.from_dict` (`max_file_size_kb`, `default_per_page`, `max_per_page`) with `get_typed(..., int, ..., default=<dataclass default>)` (REQ-002).
2. Replace every bare `list()` (`allowed_repos`, `path_denylist`, `protected_branches`) with `list(get_typed(..., list, "a list", default=[]))` (REQ-002).
3. Leave `get_str` (audit_log_path, llm_url, auth_token) and `bool(...)` (allow_force_push, require_pr_review) untouched.
4. Confirm `GitHubConfig.load`'s empty-`protected_branches` fail-closed guard (line 72) is unchanged.

### Method
- Edit the field expressions in `from_dict` (lines 48-56). Import `get_typed` alongside the existing `get_str`. Do not touch `load()`.

### Details
- Copy each `default=` verbatim from the dataclass field / current default (`max_file_size_kb=0`, `default_per_page=DEFAULT_PER_PAGE`, `max_per_page=100`, lists default to `[]`).

### Companion test files
- `tests/mcp_servers/github/test_github_server_auth.py`
  - Procedure: add a wrong-typed-value + missing-key-default test asserting `ValueError` for a numeric/list field via `GitHubConfig.from_dict` (T-002; REQ-005)
  - Validation: `uv run pytest tests/mcp_servers/github` green

## Compatibility considerations
- Valid-config behavior unchanged for correct types and missing keys; wrong-typed values now raise `ValueError` at load.

## Security considerations
- Fail-fast config boundary; do not weaken. The `protected_branches` empty-check in `load()` is unchanged.

## Rollback considerations
- Revert the commit; confined to `GitHubConfig.from_dict`.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/github/github_models_config.py` + `tests/mcp_servers/github/test_github_server_auth.py` | Unit | `uv run pytest tests/mcp_servers/github` | green; new wrong-typed test asserts `ValueError`; empty-`protected_branches` guard still fails closed |
| Changed files | Lint / type | `uv run ruff check` + `uv run mypy` on `github_models_config.py` | clean |

## Completion criteria
- No bare `int()` / `list()` remains in `GitHubConfig.from_dict`; wrong types raise `ValueError`; missing keys return defaults; `GitHubConfig.load` still fails closed on empty `protected_branches` (AC-002).

## Out of Scope

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
- **Requirement ID**: `REQ-002` (route `GitHubConfig.from_dict` int/list fields through `get_typed`; preserve `get_str` and the empty-`protected_branches` guard)
- **Source issue**: issues/20261118-025551_mcpget001_mcp-models-type-coercion.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-041831_mcpget001_mcp-models-type-coercion.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-070059
- **Related target files**: `scripts/mcp_servers/github/github_models_config.py`, `tests/mcp_servers/github/test_github_server_auth.py`
