## Goal

Remove the GitHub writes from the retry reference set (REQ-001) so it matches the `never` declarations in the tool tables.

## Scope
**Release unit**: R1-github-write-safety

## Assumptions

- `RETRYABLE_TOOLS` is reference data: it never decides the class; the declarations do, and the drift test compares them.
- Only eight GitHub names are in the set today (`github_create_pull_request` already is not).

## Design decisions

- Delete exactly the eight GitHub entries and keep the other servers' entries untouched.
- Update the block comment to say no GitHub write is retryable until a tested reconciler exists.

## Alternatives considered

N/A: a reference-set edit with one possible outcome.

## Implementation
### Target file
`scripts/shared/tool_constants.py`

### Procedure
Delete the eight `github_*` names from `RETRYABLE_TOOLS` and adjust its comment.

### Method
- Remove `github_add_issue_comment`, `github_create_branch`, `github_create_issue`, `github_create_or_update_file`, `github_delete_file`, `github_merge_pull_request`, `github_push_files`, `github_update_pull_request` from the frozenset.
- Remove the now-empty `# github server (github)` comment line.

### Details
- No other constant in the module changes.

### Companion test files
- `tests/shared/test_tool_constants.py`
  - Procedure: Add a case asserting no name in `GITHUB_TOOLS` is in `RETRYABLE_TOOLS`; keep the existing declared-versus-reference drift assertions.
  - Validation: `uv run pytest tests/shared/test_tool_constants.py`

## Compatibility considerations

The set is reference data; `rg RETRYABLE_TOOLS scripts` finds only the definition, so no runtime consumer changes.

## Security considerations

N/A: reference data only.

## Rollback considerations

N/A: revert the release unit together with the declarations.

## Validation plan

- `uv run pytest tests/shared/test_tool_constants.py`
- `uv run mypy scripts/shared/tool_constants.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- No GitHub name remains in `RETRYABLE_TOOLS`.
- The drift test passes against the tool tables.

## Out of Scope

- The declarations themselves (tool-table documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-183213 | 20261125-183213 | changed: scripts/shared/tool_constants.py |
| 2 | Add or update tests per Validation plan | Completed | 20261125-183213 | 20261125-183213 | added test_no_github_tool_is_retryable; passes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-183217 | 20261125-183329 | drift test fails until tool tables declare never (allowed red state, later members 03-06) drift test passes after members 03-06 landed |

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
- **Related target files**: `scripts/shared/tool_constants.py`, `tests/shared/test_tool_constants.py`