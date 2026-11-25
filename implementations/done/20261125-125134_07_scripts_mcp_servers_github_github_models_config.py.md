## Goal

Add the two timeout settings (REQ-002) and the two typed outcome errors (REQ-003, REQ-005) to the GitHub configuration models.

## Scope
**Release unit**: R1-github-write-safety

## Assumptions

- `GitHubConfig.from_dict` parses strictly with the helper functions already used for `max_per_page` (a positive-number helper exists); a boolean or string value must be rejected.
- `GitHubAuditError` stays; the new applied-audit error subclasses it so existing handlers still catch it.

## Design decisions

- Defaults `connect_timeout_sec = 5` and `read_timeout_sec = 30` apply when the keys are absent (Plan UNK-03); zero and negative values are rejected so a timeout can never be disabled.
- `GitHubOutcomeUnknownError` (new) is a `RuntimeError` subclass (not `ValueError`) so the dispatcher records a terminal row and re-raises instead of converting it to a validation error.

## Alternatives considered

Reusing `GitHubUpstreamError` for ambiguous failures was rejected: it is also raised for definite 4xx-style failures and cannot carry the no-retry meaning.

## Implementation
### Target file
`scripts/mcp_servers/github/github_models_config.py`

### Procedure
Add the fields to `GitHubConfig`, parse them in `from_dict`, and define the two error classes.

### Method
- Add the float fields `connect_timeout_sec` (new) and `read_timeout_sec` (new) to `GitHubConfig` with defaults 5.0 and 30.0.
- Parse both in `from_dict` as strictly positive numbers (reject bool, string, zero, negative) with the same helper style as `max_per_page`.
- Define GitHubOutcomeUnknownError`(RuntimeError)` and `GitHubAppliedAuditError` (new)`(GitHubAuditError)` with docstrings stating that a timeout never implies non-application and that the write was applied.
- Leave `github_models.py` unchanged: it is a reference file, so a re-export of the new names is a separate Plan amendment if a test requires it.

### Details
- `load()` keeps its existing validations; no cross-field rule is needed for the timeouts.

## Compatibility considerations

Additive fields with defaults; an existing TOML without the keys still loads.

## Security considerations

A strictly positive timeout prevents an unbounded blocking call to the upstream API.

## Rollback considerations

Revert the release unit together.

## Validation plan

- `uv run pytest tests/mcp_servers/github/test_github_config_strict_parsing.py tests/mcp_servers/github/test_github_exception_handlers.py`
- `uv run mypy scripts/mcp_servers/github/github_models_config.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- The two settings parse strictly with the stated defaults.
- Both error classes exist with the stated bases.

## Out of Scope

- Using the timeouts to build the client (init document).
- Handler mapping.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-183651 | 20261125-183651 | changed: scripts/mcp_servers/github/github_models_config.py |
| 2 | Add or update tests per Validation plan | Completed | 20261125-183651 | 20261125-183651 | added TestWriteTimeouts and TestWriteOutcomeErrors |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-183651 | 20261125-183651 | ruff/mypy/bandit/lint-imports pass; targeted tests pass (50 passed); docstring/module-size/reference-table gates pass |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-005
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `scripts/mcp_servers/github/github_models_config.py`