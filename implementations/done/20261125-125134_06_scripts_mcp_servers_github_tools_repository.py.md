## Goal

Declare `retry_policy = "never"` for `github_create_branch` (REQ-001), the classification owner for these tools.

## Scope
**Release unit**: R1-github-write-safety

## Assumptions

- The declared `retry_policy` is the sole classification authority; `never` is outside `RETRY_POLICY_RETRYABLE_VALUES`, so the dedup class is non-retryable.
- No reconciler exists for any GitHub write, so the conservative value is correct (Plan UNK-02 covers the two writes the Issue lists only as candidates).

## Design decisions

- Change only the `retry_policy` value of the named entries; every other tool field stays as it is.

## Alternatives considered

Keeping `same_logical_call_only` until a reconciler exists was rejected: it lets a dedup-store outage proceed unprotected and makes an interrupted call replayable.

## Implementation
### Target file
`scripts/mcp_servers/github/tools_repository.py`

### Procedure
Edit the `retry_policy` of the named entries in `scripts/mcp_servers/github/tools_repository.py`.

### Method
- Set `"retry_policy": "never"` for `github_create_branch`.

### Details
- Do not touch `reconciliation_policy`; it remains `external_state`, describing where evidence would live once a reconciler exists.

## Compatibility considerations

Behavior change by design: the Agent records `non_retryable` for these calls, the dispatcher fails them closed on a store failure and refuses interrupted-row recovery.

## Security considerations

Reduces duplicate-write exposure; no new surface.

## Rollback considerations

N/A: revert the commit (together with the release unit).

## Validation plan

- `uv run pytest tests/mcp_servers/github/test_github_tool_registry.py tests/shared/test_tool_constants.py`
- `uv run mypy scripts/mcp_servers/github/tools_repository.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- Every named entry declares `never`.
- The registry and drift tests pass.

## Out of Scope

- The reference set (its own document).
- Any reconciler.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-183329 | 20261125-183329 | changed: `scripts/mcp_servers/github/tools_repository.py` |
| 2 | Add or update tests per Validation plan | Completed | 20261125-183329 | 20261125-183329 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-183329 | 20261125-183329 | ruff/mypy/bandit/lint-imports pass; targeted tests pass (42 passed) |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `scripts/mcp_servers/github/tools_repository.py`