## Goal

Pin the declared retry policy of every GitHub write to `never` (REQ-001, REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The registry test already loads every GitHub tool declaration; the new case iterates the write and dangerous tiers from `shared.tool_constants`.

## Design decisions

- Test-only change; behavior under test is defined by the code documents of the release unit.

## Alternatives considered

N/A: test-only row.

## Implementation
### Target file
`tests/mcp_servers/github/test_github_tool_registry.py`

### Procedure
Add one parametrized case over the nine write names.

### Method
- Assert `retry_policy == "never"` for each name in `GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS`.
- Assert `retry_policy_is_retryable` is false for each declared value.

### Details
- Follow the existing fixture style of the file.

## Compatibility considerations

Test-only.

## Security considerations

N/A: test code.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/github/test_github_tool_registry.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- The case fails before the declarations change and passes after.

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
- **Requirement ID**: REQ-001, REQ-009
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `tests/mcp_servers/github/test_github_tool_registry.py`
