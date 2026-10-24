## Goal
- Update the pinned default expectation in `tests/agent/test_config_builders.py` to the new `masked_fields` default (`REQ-004`: pin the new default).

## Scope
- Change line 155 (`"masked_fields": ["file_content"],` inside the defaults expectation) only.

## Assumptions
- Line 155 confirmed 2026-10-24; the explicit-override case at line 192 (`["custom_field"]`) is unaffected.
- This test fails until rows `01` to `03` land; `code-implementation` executes rows in `seq` order, so it runs green at its own validation step only after those rows.

## Design decisions
- Assert the literal list, not `ToolConfig().masked_fields`, so a drift between the code defaults and the test is caught.

## Alternatives considered
N/A: one-line expectation update.

## Implementation
### Target file
`tests/agent/test_config_builders.py`

### Procedure
1. Replace `["file_content"]` with `["content", "old_text", "new_text"]` on line 155.

### Method
- Single-line edit; keep surrounding entries unchanged.

### Details
- Do not touch the line-192 override case.

## Compatibility considerations
N/A: test-only edit.

## Security considerations
N/A: test-only edit.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py -q` passes after rows `01` to `03`.
- `uv run ruff format`, `uv run ruff check` on the file.

## Completion criteria
- The defaults expectation pins `["content", "old_text", "new_text"]` and the file passes.

## Out of Scope
- Other expectations and the `tests/agent/commands/test_cmd_config_char.py` snapshot tests (substring matches, unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the pinned default at line 155 | Pending | — | — | |
| 2 | Run `tests/agent/test_config_builders.py` and ruff | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (pin the new default)
- **Source issue**: `issues/20261024-124138_tool005_default-masked-fields-names-match-no-real-tool-argument.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-221904_default-masked-fields-names-match-no-real-tool-argument.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235437
- **Related target files**: `tests/agent/test_config_builders.py`
