## Goal

Write the intent audit before every non-preview write (REQ-004), at the one funnel all nine writes pass through.

## Scope
**Release unit**: R1-github-write-safety

## Assumptions

- `_execute_with_dry_run` runs authorization first, then the dry-run branch, then the execute callback; a preview must write no audit and call no API.
- The intent helper exists after the security document (earlier `seq`).

## Design decisions

- The funnel gains an `op` string so the intent record names the operation; the nine call sites pass their operation name.
- The intent audit runs after authorization (a denied repository audits nothing) and before the callback.

## Alternatives considered

Auditing inside each service method was rejected: it would sit after argument handling and could drift per method.

## Implementation
### Target file
`scripts/mcp_servers/github/github_service_dispatch_writes.py`

### Procedure
Add the `op` parameter to `_execute_with_dry_run`, call the intent audit before `execute_callback`, and pass `op` from each call site.

### Method
- Add a keyword `op: str` to `_execute_with_dry_run`.
- After the dry-run branch and before awaiting `execute_callback`, call `self._write_intent_audit(op, repo=f"{req.owner}/{req.repo}")`.
- Pass `op=` from each of the nine `fmt_*` methods using the same names the completion audits use (for example `create_issue`, `merge_pull_request`).

### Details
- Update the module docstring sentence about the funnel to mention the intent audit.

### Companion test files
- `tests/mcp_servers/github/test_service_dispatch.py`
  - Procedure: Add cases: the intent audit runs before the callback for a real call, is skipped for a dry run and for a denied repository, and an intent failure prevents the callback.
  - Validation: `uv run pytest tests/mcp_servers/github/test_service_dispatch.py`

## Compatibility considerations

Behavior change: a write whose audit path is configured but unwritable now fails before the API call instead of after.

## Security considerations

Fail-closed: no applied write without a recorded intent.

## Rollback considerations

Revert the release unit together.

## Validation plan

- `uv run pytest tests/mcp_servers/github/test_service_dispatch.py tests/mcp_servers/github/test_github_write_outcomes.py`
- `uv run mypy scripts/mcp_servers/github/github_service_dispatch_writes.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- Every real write is preceded by an intent audit; previews are not.

## Out of Scope

- The completion audit and the failure translation (other documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Add or update tests per Validation plan | Pending | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `scripts/mcp_servers/github/github_service_dispatch_writes.py`, `tests/mcp_servers/github/test_service_dispatch.py`
