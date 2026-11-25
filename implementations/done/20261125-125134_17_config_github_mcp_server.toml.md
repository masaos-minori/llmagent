## Goal

Document and set the two GitHub client timeouts (REQ-002).

## Scope
**Release unit**: R1-github-write-safety

## Assumptions

- The keys are optional (defaults apply); the shipped file sets them explicitly so the operator sees them.
- The file is validated by the strict parser; the keys must be positive numbers.

## Design decisions

- Values match the code defaults: connect 5 seconds, read 30 seconds, with a comment saying a timeout never proves a write did not apply.

## Alternatives considered

N/A: configuration entry only.

## Implementation
### Target file
`config/github_mcp_server.toml`

### Procedure
Add the two keys with comments after `max_file_read_size_kb`.

### Method
- Add `connect_timeout_sec = 5` with a comment.
- Add `read_timeout_sec = 30` with a comment stating that a write that times out is reported as `outcome_unknown` and is never retried automatically.

### Details
- Keep the file's comment style and key order conventions.

## Compatibility considerations

Additive; the strict parser accepts the new keys after the config-models document.

## Security considerations

Bounded upstream calls.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/github/test_github_config_strict_parsing.py`

## Completion criteria

- The file carries both keys and loads under the strict parser.

## Out of Scope

- Parser changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the configuration per Implementation > Procedure/Method/Details | Completed | 20261125-190024 | 20261125-190024 | added connect_timeout_sec = 5 and read_timeout_sec = 30 after max_file_read_size_kb with the no-retry comments |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-190024 | 20261125-190024 | strict parsing 44 passed; check_config_comment_length 0 errors |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `config/github_mcp_server.toml`