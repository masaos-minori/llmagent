## Goal

Route the completion audit of `create_or_update_file`, `push_files`, and `delete_file` through the applied-audit helper and mark the API call as a write (REQ-005, REQ-006).

## Scope
**Release unit**: R1-github-write-safety

## Assumptions

- The helpers and the write flag exist after the security document (earlier `seq`).
- Audit call sites: lines 111, 156, 185 (confirmed in Step 3a).

## Design decisions

- The service method keeps its API call and audit position; only the helper and the write flag change, so the diff per method is two lines.

## Alternatives considered

N/A: mechanical substitution.

## Implementation
### Target file
`scripts/mcp_servers/github/github_service_file.py`

### Procedure
In each write method of `scripts/mcp_servers/github/github_service_file.py`, pass `write=True` to `_run_github` and replace `_write_github_audit_log` with `_complete_write_audit`.

### Method
- Pass `write=True` as a keyword to `self._run_github(...)` in each write method.
- Replace `self._write_github_audit_log(` with `self._complete_write_audit(` keeping the operation name and identifier fields unchanged.

### Details
- Do not add payload fields to the audit call; remove nothing else (the logged title is a separate concern).

## Compatibility considerations

A completion-audit failure now raises `GitHubAppliedAuditError`, a subclass of the previous `GitHubAuditError`.

## Security considerations

Reports an applied-but-unaudited write explicitly so the caller does not retry.

## Rollback considerations

Revert the release unit together.

## Validation plan

- `uv run pytest tests/mcp_servers/github`
- `uv run mypy scripts/mcp_servers/github/github_service_file.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- No write method calls `_write_github_audit_log` directly and each passes `write=True`.

## Out of Scope

- The helper definitions and the funnel.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-184920 | 20261125-184920 | write=True and _complete_write_audit applied to the write methods |
| 2 | Add or update tests per Validation plan | Completed | 20261125-184920 | 20261125-184920 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-184920 | 20261125-184920 | ruff/mypy/bandit/lint-imports pass; tests/mcp_servers/github 590 passed |

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
- **Requirement ID**: REQ-005, REQ-006
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `scripts/mcp_servers/github/github_service_file.py`