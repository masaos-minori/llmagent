## Goal

Remove every reference to the `ToolConfig.tool_definitions` config field from `tests/agent/test_llm_turn_runner.py` (`REQ-001`, `REQ-002`). The field is removed by row 2 (`config_dataclasses.py`), so any test that assigns `ctx.cfg.tool.tool_definitions` raises `AttributeError`, and docstrings describing a "config-driven fallback" now contradict the fail-closed source (`_stream_llm` raises when the registry is absent).

## Scope
**Release unit**: static-catalog removal

## Assumptions
- Three code assignments set the removed field and must go: `tests/agent/test_llm_turn_runner.py` line 40 (`ctx.cfg.tool.tool_definitions = []`), line 329 (`runner._ctx.cfg.tool.tool_definitions = []`), and lines 344-346 (`runner._ctx.cfg.tool.tool_definitions = [{"name": "static_tool", ...}]`). If `agentcfg001` adds fields to `ToolConfig` first, these line numbers shift and must be re-verified.
- `_stream_llm()` (`scripts/agent/llm_turn_runner.py:363-367`) raises `RuntimeError` when `registry is None` with the message "no config-driven fallback"; it never reads `ctx.cfg.tool.tool_definitions`. `_filter_disabled_tool_definitions()` is already absent from `scripts/agent/`.
- All other `tool_definitions` references in the file point to the `RuntimeToolRegistry.llm_tool_definitions()` METHOD (lines 298, 300, 312, 326, 354, 356, 981, 1031), not the removed config field, and stay untouched.

## Design decisions
- Delete only the three `ctx.cfg.tool.tool_definitions` assignments; leave every `registry.llm_tool_definitions()` mock and assertion intact so the registry-authority tests keep their coverage.
- Rewrite the three docstrings that name the removed config field so they match the current fail-closed source (registry-is-None raises; there is no config fallback), rather than deleting the tests.

## Alternatives considered
- Leave the assignments and patch `ToolConfig` to keep the field: rejected by `REQ-002`, which removes the field so the assignment raises at runtime.
- Delete the affected test methods entirely: rejected because they still validate real behavior (registry authority, fail-closed raise); only the field references must go.

## Implementation
### Target file
`tests/agent/test_llm_turn_runner.py`

### Procedure
Drop the three `ToolConfig.tool_definitions` assignments and correct the three docstrings that reference the removed field.

### Method
- In `TestStreamLlmToolDefs.__init__`/setup (line 40): delete `ctx.cfg.tool.tool_definitions = []`.
- In `test_registry_not_none_includes_live_registered_tool_absent_from_static_config`: delete the `runner._ctx.cfg.tool.tool_definitions = []` line (329) and reword its docstring (318-319) to drop the "absent from ctx.cfg.tool.tool_definitions" clause (the registry is the sole authority regardless).
- In `test_registry_is_none_raises_no_static_fallback`: delete the `runner._ctx.cfg.tool.tool_definitions = [{...}]` block (344-346) and reword its docstring (341-342) to cite the source's actual message ("runtime tool registry is the sole source ... no config-driven fallback").
- Reword the class docstring (287-292) to remove the stale "_filter_disabled_tool_definitions() ... registry-is-None fallback to ctx.cfg.tool.tool_definitions" description and state the current contract instead.

### Details
- Confirm no `ctx.cfg.tool.tool_definitions` / `runner._ctx.cfg.tool.tool_definitions` attribute access remains anywhere in the file.
- Leave every `mock_registry.llm_tool_definitions.return_value` / `.assert_called_once()` / `registry.llm_tool_definitions.return_value` reference (lines 298, 300, 312, 326, 354, 356, 981) and the `test_llm_tool_definitions_identical_across_turns` method (1031) untouched.
- Keep the `RuntimeError` assertion in `test_registry_is_none_raises_no_static_fallback` intact; with the field assignment gone, the test still verifies that a None registry raises.

## Compatibility considerations
Test-only change. Aligns the turn-runner tests with the removed `ToolConfig.tool_definitions` field (row 2) and the existing fail-closed `_stream_llm` behavior. No production compatibility impact.

## Security considerations
N/A: test-only. The fail-closed guarantee (registry absent → raise, `REQ-001`) is preserved and still asserted.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run `tests/agent/test_llm_turn_runner.py::TestStreamLlmToolDefs`; assert the registry-authority and registry-is-None tests still pass with the field assignments removed. Run the full `test_llm_turn_runner.py` to confirm no `AttributeError` and that the `registry.llm_tool_definitions()` tests are unaffected.

## Completion criteria
`test_llm_turn_runner.py` contains no `ctx.cfg.tool.tool_definitions` assignment or attribute access, the three affected docstrings no longer describe a config-driven fallback, and all `TestStreamLlmToolDefs` cases pass.

## Out of Scope
The `ToolConfig.tool_definitions` field removal (`config_dataclasses.py`, row 2), the section builder (row 3), the config-field-registry row (row 4), the `agent.toml` blocks (row 1), and the LLM-authority source (`llm_turn_runner.py`, referenced as a read-only file).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Line numbers are against current source; re-verify if `agentcfg001` lands first. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Editing existing tests; no new tests required. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docstring corrections are part of the field removal. |

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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `tests/agent/test_llm_turn_runner.py`
