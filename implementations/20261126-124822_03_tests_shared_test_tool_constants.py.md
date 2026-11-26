## Goal
- Pin `trigger_workflow` as side-effecting, declared non-retryable, and absent from `RETRYABLE_TOOLS` (REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: new assertions in `tests/shared/test_tool_constants.py`.
- Out of scope: the constants and the tool declaration, which already carry the values (`scripts/shared/tool_constants.py`, `scripts/mcp_servers/cicd/cicd_tools.py:37`).

## Assumptions
- No code row of the Plan names this file in its Related Tests, so it keeps its own document.
- Verified in Step 3a: `trigger_workflow` declares `retry_policy: "never"`, is in `CICD_WRITE_TOOLS` and therefore in `ALL_SIDE_EFFECTING_TOOLS`, and is not in `RETRYABLE_TOOLS`; the module already drift-checks the declarations against `RETRYABLE_TOOLS` (`test_tool_constants.py:105-151`) but names no specific tool.
- The declared field is the authority; the sets are reference data.

## Design decisions
- Read the declaration through the same TOOL_LIST loader the drift test uses, so the new assertion cannot diverge from it.

## Alternatives considered
- N/A: test-only row.

## Implementation
### Target file
`tests/shared/test_tool_constants.py`

### Procedure
1. Add one test (or a small class) that locates the `trigger_workflow` declaration with the helper the drift test uses.
2. Assert `retry_policy == "never"` (through `retry_policy_is_retryable` being false), that `"trigger_workflow"` is in `ALL_SIDE_EFFECTING_TOOLS`, and that it is not in `RETRYABLE_TOOLS`.

### Method
- No new fixtures; reuse the file's existing imports.

### Details
- Keep the existing drift test untouched.

## Compatibility considerations
- Test-only.

## Security considerations
- N/A: no secret involved.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/shared/test_tool_constants.py`; `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- The three assertions pass; the existing drift test passes; all validation commands pass.

## Out of Scope
- Constants, declarations, and other tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the assertions described in Implementation > Procedure | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (explicit `trigger_workflow` classification)
- **Source issue**: issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-113156_mcpdd001_dedup-keyless-config-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-124822
- **Related target files**: `tests/shared/test_tool_constants.py`
