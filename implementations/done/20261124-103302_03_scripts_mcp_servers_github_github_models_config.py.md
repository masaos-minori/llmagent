## Goal

Add the two configuration fields this Plan introduces: `allow_global_search` (new) as a strict boolean, default `false` (REQ-003: search-boundary opt-in), and `max_file_read_size_kb` (new) as a strict non-negative integer, default `0` = unlimited (REQ-006: read-size limit), parsed through the shared helpers (REQ-008: one strict-parsing definition).

## Scope
**Release unit**: N/A: not part of a release unit (Plan Phase 4 is validated on its own)

## Assumptions

- Defaults keep current behavior: `false` scopes searches, `0` means unlimited, matching the existing `max_file_size_kb` convention (Plan Assumptions).
- `get_typed()` already rejects a non-boolean where a boolean is expected, so the boolean field needs no new parser; the numeric field uses `get_non_negative_number` (new), declared by `implementations/20261124-103302_02_scripts_shared_config_utils.py.md`.
- `tests/mcp_servers/github/test_github_server_auth.py` is not a companion of this document: the Plan names it from two rows (this row and `config/github_mcp_server.toml`), so it fails the companion condition and has its own procedure document (`implementations/20261124-103302_18_tests_mcp_servers_github_test_github_server_auth.py.md`).

## Design decisions

- Parse the new numeric field with the shared strict accessor rather than `get_typed()` (REQ-008, Plan D-1); the boolean field stays on `get_typed()` because its contract is already strict.
- No new settings beyond the two (Plan Out of Scope): no lossy-decoding field, no search-mode switch.

## Alternatives considered

- Reusing `max_file_size_kb` for reads — rejected by REQ-006: the read path checks the content metadata size before decoding, so it needs its own limit.
- Defaulting `allow_global_search` (new) to `true` — rejected: that keeps today's unbounded global search as the default and makes the boundary opt-out, contrary to REQ-003.

## Implementation
### Target file
`scripts/mcp_servers/github/github_models_config.py`

### Procedure
1. Add two fields to `GitHubConfig` (the dataclass at lines 28-44): `allow_global_search` (new) `bool = False`, `max_file_read_size_kb` (new) `int = 0`, placed with the existing numeric fields so the field order stays grouped by kind.
2. In `from_dict()` (line 45), parse `allow_global_search` (new) with `get_typed(d, "allow_global_search", bool, "a boolean", default=False)` and `max_file_read_size_kb` (new) with `get_non_negative_number(d, "max_file_read_size_kb", int, "an integer", default=0)`.
3. Change nothing else: existing fields, `get_str()` calls, and the exception types stay as they are.

### Method
- The two fields are read-only policy values for this Plan: the guard (`github_service_security.py`) and the search query builder consume them; this module performs no enforcement of its own.
- Error behavior is the shared helpers' behavior: `ValueError` naming the key for a wrong type, a `bool` where a number is expected, NaN, infinity, or a negative value.

### Details
- The module already imports `get_str` and `get_typed` from `shared.config_utils`; add `get_non_negative_number` to that import line. This is the only new import in the group (Plan D-1 keeps `shared` a leaf).
- `check_docs_consistency.py --domain mcp` resolves the two key names against `config/github_mcp_server.toml`, so the field names here must match the config keys written by row 10 exactly.

## Compatibility considerations

- Additive: `GitHubConfig` gains fields with defaults, so `GitHubConfig()` and `from_dict({})` callers — including `tests/mcp_servers/github/test_github_security_validation.py` and the startup path — keep working with the same behavior.
- No response model change: `scripts/mcp_servers/github/github_models_file.py` keeps `GetFileContentsResponse.encoding` as `utf-8` and no response model echoes `owner`/`repo` (Plan Reference Files).

## Security considerations

- Both fields are security controls, so parse-time strictness is part of the boundary: a NaN or negative read limit would silently mean "unlimited", and a truthy non-boolean would silently mean "global search allowed".

## Rollback considerations

- High: removing the two fields reverts to the current state; no persisted state and no deployed value depends on them beyond the new config keys in row 10.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/mcp_servers/github/github_models_config.py` | Unit (config builder contract) | `uv run pytest tests/mcp_servers/github/test_github_server_auth.py` | Absent keys yield `False`/`0`; non-boolean for the new field and NaN/infinity/negative for the other new field are rejected (AC-4, AC-8) |
| Same file | Quality gates | `uv run ruff check scripts/mcp_servers/github/github_models_config.py`, `uv run mypy scripts/mcp_servers/github/github_models_config.py`, `uv run bandit scripts/mcp_servers/github/github_models_config.py` | No finding |

## Completion criteria

- `from_dict()` returns the documented defaults when the keys are absent, and rejects the invalid types and ranges named by AC-4.
- The two fields are read by the guard through this config object only; no second definition of either value exists in the GitHub package (REQ-010).

## Out of Scope

- The runtime enforcement of the two settings (guard rows `github_service_security.py`, `github_service_file.py`) and the posture reporting (row 20).
- The shipped values in `config/github_mcp_server.toml` (row 10) and the config-builder test cases (row 18).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the two fields and parse them through the shared helpers per Procedure/Method/Details | Completed | 20261124-152854 | 20261124-152854 | max_file_read_size_kb and allow_global_search parsed through get_non_negative_number()/get_typed(); ruff and mypy clean |
| 2 | Config-builder test cases are executed by row 18's document (`tests/mcp_servers/github/test_github_server_auth.py`) | Completed | 20261124-152854 | 20261124-152854 | Not a companion of this document: named by two Plan rows |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261124-152854 | 20261124-152854 |  |

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
- **Requirement ID**: REQ-003 (search-boundary opt-in), REQ-006 (read-size limit), REQ-008 (strict numeric parsing)
- **Source issue**: issues/done/20261119-140509_mcpai002_github-read-security-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095007_mcpai002_github-read-security-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103302
- **Related target files**: `scripts/mcp_servers/github/github_models_config.py`