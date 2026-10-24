## Goal
- Add default-config end-to-end masking tests: `write_file`-shaped and `edit_file`-shaped arguments produce `***` at `content`, `edits[*].old_text`, and `edits[*].new_text` without explicit `masked_fields` (`REQ-005`).

## Scope
- Add one test class to `tests/agent/test_tool_result_formatter.py`; existing tests unchanged.

## Assumptions
- The file's `_cfg()` helper sets `"masked_fields": []` by default, so the new tests MUST build the config without that key (or take the list from `ToolConfig()`), otherwise they would not exercise the default.
- `mask_args(args, masked_fields)` masks at any depth (`scripts/agent/tool_result_formatter.py:42-64`, commit `3cdacc601`).
- These tests fail until rows `01` and `02` (`scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`) land (Plan Phase 1 failing-first).

## Design decisions
- Cover two default paths: `ToolConfig().masked_fields` (dataclass default) and `build_agent_config` with no `masked_fields` key (builder fallback), asserting both feed `mask_args` identically.

## Alternatives considered
N/A: test-only addition following the file's class-per-function layout.

## Implementation
### Target file
`tests/agent/test_tool_result_formatter.py`

### Procedure
1. Add the test class `TestMaskArgsDefaultConfig` (new) after `TestMaskArgs`; import `ToolConfig` from `agent.config_dataclasses` next to the existing `AgentConfig` import.
2. Test A: `mask_args({"path": "/tmp/f", "content": "body"}, ToolConfig().masked_fields)` returns `content` as `***` and `path` unchanged.
3. Test B: `edit_file`-shaped `{"path": ..., "edits": [{"old_text": "a", "new_text": "b"}]}` yields `***` at both nested keys.
4. Test C: build a config via `build_agent_config` using the `_cfg` defaults with the `masked_fields` key removed, then assert `cfg.tool.masked_fields == ["content", "old_text", "new_text"]`.

### Method
- Keep every test annotated `-> None`; assert on exact dict equality as `TestMaskArgs` does.

### Details
- For test C copy the `_cfg` default dict handling: pop `masked_fields` before `build_agent_config` rather than editing `_cfg`'s shared defaults.

## Compatibility considerations
N/A: test-only addition.

## Security considerations
N/A: dummy values only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Before rows `01` and `02`: the new class fails; after: `uv run pytest tests/agent/test_tool_result_formatter.py -q` passes.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` plus mypy on the test file.

## Completion criteria
- The three tests exist, fail against the `file_content` default, and pass with the new default; existing tests unchanged.

## Out of Scope
- Changes to `mask_args` and to the existing `_cfg` defaults.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestMaskArgsDefaultConfig` (new) with tests A to C | Pending | — | — | |
| 2 | Run the tests before and after rows `01` and `02` | Pending | — | — | |
| 3 | Run ruff and mypy | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (default-config end-to-end masking tests)
- **Source issue**: `issues/20261024-124138_tool005_default-masked-fields-names-match-no-real-tool-argument.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-221904_default-masked-fields-names-match-no-real-tool-argument.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235437
- **Related target files**: `tests/agent/test_tool_result_formatter.py`
