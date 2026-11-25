## Goal

Cover the two new timeout keys in the strict-parsing suite (REQ-002, REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `_patch_loader` and `_BASE_CONFIG` already model a loader result; the new cases add the keys.

## Design decisions

- Test-only change; behavior under test is defined by the code documents of the release unit.

## Alternatives considered

N/A: test-only row.

## Implementation
### Target file
`tests/mcp_servers/github/test_github_config_strict_parsing.py`

### Procedure
Add a timeout test class.

### Method
- Defaults apply when the keys are absent.
- Reject zero, negative, boolean, and string values for each key with an error naming the key.
- Accept positive integers and floats.

### Details
- Follow the existing fixture style of the file.

## Compatibility considerations

Test-only.

## Security considerations

N/A: test code.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/github/test_github_config_strict_parsing.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- The timeout parsing rules are pinned.

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
- **Requirement ID**: REQ-002, REQ-009
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `tests/mcp_servers/github/test_github_config_strict_parsing.py`
