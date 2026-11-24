## Goal

Extend `TestGitHubConfigFromDictTypeValidation` with cases for the two new config fields (REQ-003: strict boolean for the search opt-in, REQ-006: read-size limit, REQ-008: strict numeric parsing rejects NaN, infinity, negative, and `bool`-for-number), so the config-builder contract stated by AC-4 and AC-8 is asserted.

## Scope
**Release unit**: N/A: not part of a release unit — no Plan `Implementation steps` entry cites this file, so it is not covered by the boundary-test release unit. The Plan step that adds the fields cites `scripts/mcp_servers/github/github_models_config.py` and `config/github_mcp_server.toml`; this row is the test coverage for those. Reported as a Plan Gap in Step 4 for the same reason.

## Assumptions

- This row has its own document rather than being a companion because the Plan names `tests/mcp_servers/github/test_github_server_auth.py` from two rows (the config module row and the config-file row), which fails the companion condition in `skills/plan-to-implementation-procedure/SKILL.md`.
- The existing tests assert individual field defaults rather than a whole-object equality, so adding two fields does not break them; only `test_missing_keys_return_defaults` (line 123) gains assertions.
- `test_shipped_toml_uses_the_agent_variable` (line 115) reads the shipped TOML for `auth_token` only, so the two new keys do not affect it.

## Design decisions

- Assert the documented defaults (`False`, `0`) and the rejections; do not assert the parsing implementation, so the test stays a contract test on `from_dict()` (matches the existing style of this class).
- Use the strict cases only for the new fields; existing cases for `max_file_size_kb` and `allowed_repos` stay as they are, because `get_typed()` behavior must not change (REQ-008).

## Alternatives considered

- Creating a separate test file for the config module — rejected by the Plan: this file is the one that characterizes `GitHubConfig.from_dict()`, and a second file would split the same contract across two.

## Implementation
### Target file
`tests/mcp_servers/github/test_github_server_auth.py`

### Procedure
1. In `test_missing_keys_return_defaults`, add `assert cfg.allow_global_search is False` and `assert cfg.max_file_read_size_kb == 0`.
2. Add cases for the strict rejections: a non-boolean for `allow_global_search` (`ValueError`), and `NaN`, `float("inf")`, and a negative value for `max_file_read_size_kb` (`ValueError`).
3. Add one acceptance case that documents the `0` meaning as a value, not as a rejection (AC-6: `0` means unlimited), so the range rule and the "unlimited" convention are both asserted.

### Method
- Keep the class's existing pattern: construct through `GitHubConfig.from_dict()` with a dict, assert the value or the raised `ValueError`. No fixture changes.

### Details
- The tests are pure config parsing, no network or filesystem access, so they run in the unit stage of `rules/toolchain.md`.

## Compatibility considerations

- This file is the only place that asserts `from_dict()` defaults; adding assertions here is what keeps AC-4 checkable. No existing assertion is removed or changed.

## Security considerations

- A config field that accepts `NaN` or a negative value silently changes a security control's meaning; these cases are what make the strict parser observable.

## Rollback considerations

- N/A: revert the commit; test-only change.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/mcp_servers/github/test_github_server_auth.py` | Unit (config builder contract) | `uv run pytest tests/mcp_servers/github/test_github_server_auth.py` | Defaults `False`/`0`; strict rejections for the new fields; existing cases stay green (AC-4, AC-8) |
| Same file | Quality gate | `uv run ruff check tests/mcp_servers/github/test_github_server_auth.py` | No finding |

## Completion criteria

- The two new fields' defaults and their strict rejection rules are asserted here, and no existing `get_typed()` case changes behavior.

## Out of Scope

- Adding the fields themselves (row 3) and the shipped values (row 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the cases described in Implementation > Procedure/Method/Details | Completed | 20261124-152854 | 20261124-152854 |  |
| 2 | Run the tests for this file (`uv run pytest tests/mcp_servers/github/test_github_server_auth.py`) | Completed | 20261124-152854 | 20261124-152854 |  |
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
- **Requirement ID**: REQ-003 (strict boolean search opt-in), REQ-006 (read-size limit), REQ-008 (strict numeric parsing)
- **Source issue**: issues/done/20261119-140509_mcpai002_github-read-security-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095007_mcpai002_github-read-security-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103302
- **Related target files**: `tests/mcp_servers/github/test_github_server_auth.py`