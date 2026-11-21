## Goal

Drop every `ToolConfig.tool_definitions` reference from `tests/agent/test_tool_preparation.py` (`REQ-002`). The field is removed by row 2 (`config_dataclasses.py`) and its builder line by row 3 (`config_section_builders.py::_build_tool_config`, line 219). Once gone, the `"tool_definitions"` fixture key and the regression test that proves "a stale `tool_definitions` entry is ignored" both reference a concept that no longer exists.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- Three references exist (verified against current source): the `defaults` fixture key `"tool_definitions": []` at line 35, the method `test_unregistered_name_rejected_despite_matching_tool_definitions_entry` (line 91) with its docstring (94-96), and the `_cfg(tool_definitions=[{"function": {"name": "stale_tool"}}])` call at line 97.
- `prepare_tool_calls()` (`scripts/agent/tool_preparation.py`) never reads `ctx.cfg.tool.tool_definitions` — the fail-closed preparation path relies solely on the RuntimeToolRegistry. Confirmed via the Plan's Reference Files.
- `_build_tool_config` reads the key via `_get_or_default(cfg, "tool_definitions", _get_list, [])` (line 219); row 3 removes that read, so any leftover fixture key becomes harmless dead data — but it should be dropped for cleanliness and to match REQ-002.

## Design decisions
- Delete the `"tool_definitions": []` key from the `defaults` dict (line 35).
- Rewrite the single regression test to assert the fail-closed rejection of an unregistered tool name without the (now-nonexistent) tool_definitions angle: rename it, update the docstring, and call plain `_cfg()`.

## Alternatives considered
- Leave the fixture key and only rewrite the test: rejected because the key still names a removed field and REQ-002 removes the field entirely.
- Delete the regression test entirely: rejected because it still validates real behavior (unregistered names are rejected); only its tool_definitions premise must go.

## Implementation
### Target file
`tests/agent/test_tool_preparation.py`

### Procedure
Remove the fixture key and convert the tool_definitions regression test to a plain unregistered-name rejection test.

### Method
- Delete `"tool_definitions": [],` from the `defaults` dict (line 35).
- Rename `test_unregistered_name_rejected_despite_matching_tool_definitions_entry` (line 91) to `test_unregistered_name_rejected` (new).
- Reword the docstring (94-96) to describe the fail-closed rejection of an unregistered name via the RuntimeToolRegistry, with no mention of `tool_definitions` or a "stale entry".
- Change the body call at line 97 from `_cfg(tool_definitions=[{"function": {"name": "stale_tool"}}])` to plain `_cfg()`. Keep the rest of the assertions (lines 98-108) unchanged: `runtime_tools.get` still raises `KeyError`, so the name is still rejected and `tool_spec_for_call` is still not called.

### Details
- Confirm no `tool_definitions` string remains anywhere in the file (method name, docstring, fixture key, `_cfg(...)` call).
- Do not touch other classes/methods in the file; they do not reference the field.
- The renamed test still lives in `TestPrepareToolCallsUnknownTool`; keep it there.

## Compatibility considerations
Test-only change. Aligns the fixture and regression test with the removed `ToolConfig.tool_definitions` field (rows 2-3). No production compatibility impact.

## Security considerations
N/A: test-only. The fail-closed rejection of unregistered tool names (the behavior under test) is preserved.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run `tests/agent/test_tool_preparation.py::TestPrepareToolCallsUnknownTool::test_unregistered_name_rejected`; assert the unregistered name is still rejected and `tool_spec_for_call` is not called. Run the full `test_tool_preparation.py` to confirm the fixture change did not break `_cfg()` for other tests.

## Completion criteria
`test_tool_preparation.py` contains no `tool_definitions` reference (fixture key, method name, docstring, or `_cfg(...)` call), and the renamed unregistered-name rejection test passes.

## Out of Scope
The `ToolConfig.tool_definitions` field removal (`config_dataclasses.py`, row 2), the section-builder removal (`config_section_builders.py`, row 3), the `agent.toml` blocks (row 1), and the `tool_preparation.py` fail-closed path (read-only reference file).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120 | 20261120 | Deleted `"tool_definitions": []` from the `defaults` dict; renamed `test_unregistered_name_rejected_despite_matching_tool_definitions_entry` → `test_unregistered_name_rejected`; reworded docstring to the fail-closed RuntimeToolRegistry contract; changed `_cfg(tool_definitions=[...])` to plain `_cfg()`. All other assertions preserved. |
| 2 | Add or update tests per Validation plan | Completed | 20261120 | 20261120 | Editing one existing test; no new tests required. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120 | 20261120 | ruff format/check clean; `test_unregistered_name_rejected` 1 + full `test_tool_preparation.py` 12 pass; full-suite diff vs baseline IDENTICAL (zero new failures). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Test-only change; docs rows are out of scope. |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `tests/agent/test_tool_preparation.py`
