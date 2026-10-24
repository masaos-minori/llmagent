## Goal
- Extend audit-path masking coverage from the `["secret"]` fixtures to the real default names, asserting a default-configured audit row hides file bodies (`REQ-005`).

## Scope
- Add one test next to `test_masked_fields_applied_to_nested_args` (line 432) in `tests/agent/test_tool_approval_preflight.py`; existing tests unchanged.

## Assumptions
- Existing sibling tests build `cfg = _make_cfg(masked_fields=["secret"])`, call `_audit_approval(ctx, "write_file", "medium", {...}, "approved")`, and read `audit.info.call_args[0][0]` (read 2026-10-24, lines 417-448). `_make_cfg` defaults `masked_fields` to `[]` (line 53), so the new test MUST pass the default list explicitly.
- Taking the list from `ToolConfig().masked_fields` makes the test follow the shipped default; it fails until rows `01` and `02` land.

## Design decisions
- Use `_make_cfg(masked_fields=list(ToolConfig().masked_fields))` so the test exercises the dataclass default through the real audit writer path.

## Alternatives considered
N/A: single added test following the neighboring cases.

## Implementation
### Target file
`tests/agent/test_tool_approval_preflight.py`

### Procedure
1. Import `ToolConfig` from `agent.config_dataclasses` if the file does not already import it.
2. Add the test method `test_default_masked_fields_hide_file_bodies` (new) in the same class as the `["secret"]` cases.
3. Send `{"path": "/tmp/f", "content": "file-body-secret", "edits": [{"old_text": "old-secret", "new_text": "new-secret"}]}` through `_audit_approval` and assert none of the three secret strings appears in the payload and `"***"` does.

### Method
- Mirror the neighboring test's structure and assertions exactly.

### Details
- Do not alter `_make_cfg`'s defaults or the existing tests.

## Compatibility considerations
N/A: test-only addition.

## Security considerations
N/A: dummy values only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- After rows `01` and `02`: `uv run pytest tests/agent/test_tool_approval_preflight.py -q` passes with the existing `["secret"]` cases unchanged.
- `uv run ruff format`, `uv run ruff check` on the file.

## Completion criteria
- The new test passes with the new default and would fail against `["file_content"]`.

## Out of Scope
- `tool_approval.py` preview behavior and other test classes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_default_masked_fields_hide_file_bodies` (new) | Completed | — | 20261025-003208 |  |
| 2 | Run the file before and after rows `01` and `02` | Completed | — | 20261025-003208 |  |
| 3 | Run ruff on the file | Completed | — | 20261025-003208 |  |

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
- **Requirement ID**: `REQ-005` (default-names audit-path test)
- **Source issue**: `issues/20261024-124138_tool005_default-masked-fields-names-match-no-real-tool-argument.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-221904_default-masked-fields-names-match-no-real-tool-argument.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235437
- **Related target files**: `tests/agent/test_tool_approval_preflight.py`