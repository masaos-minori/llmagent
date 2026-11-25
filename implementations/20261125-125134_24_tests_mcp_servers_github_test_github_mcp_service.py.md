## Goal

Update the existing audit-failure tests for the intent and applied-audit semantics (REQ-004, REQ-005, REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Existing cases at lines 202-210 and 860 expect a write to raise `GitHubAuditError` from the post-call audit; after the change an unwritable path fails at the intent audit (before the API) and a post-call failure raises `GitHubAppliedAuditError`, a subclass.
- Other tests that assert audit-after-write ordering are triaged as Fallout (Plan UNK-04).

## Design decisions

- Test-only change; behavior under test is defined by the code documents of the release unit.

## Alternatives considered

N/A: test-only row.

## Implementation
### Target file
`tests/mcp_servers/github/test_github_mcp_service.py`

### Procedure
Adjust the two cases and add helper-level cases.

### Method
- For the line-860 write case assert the API stub is not called when the audit path is unwritable.
- Add helper-level cases for `_write_intent_audit` and `_complete_write_audit` (phase field, identifiers, counter).
- Keep the empty-path skip cases unchanged.

### Details
- Follow the existing fixture style of the file.

## Compatibility considerations

Test-only.

## Security considerations

N/A: test code.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/github/test_github_mcp_service.py tests/mcp_servers/github`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- The audit tests describe the new ordering and outcomes.

## Out of Scope

- Production code (other documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the test file described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: REQ-004, REQ-005, REQ-009
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `tests/mcp_servers/github/test_github_mcp_service.py`
