## Goal
- Render the explicit config dependency, capability state, and the restart-required notice in `/mcp status` in `cmd_mcp.py` (REQ-007, REQ-008).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the diagnostic row rendering and one notice line in this file, plus the test companion.
- Out of scope: the diagnostics data source (seq 13).

## Assumptions
- Verified in Step 3a: `_format_tool_diagnostic_rows()` (`cmd_mcp.py:167-185`) renders `config_dependent` from the diagnostics row, which currently carries the status-derived value (fixed in seq 13); the table headers are pinned by `test_cmd_mcp.py:1074`.
- The restart notice states that a change in tool availability requires a restart (D-2), with no live swap.

## Design decisions
- Add a capability-state column fed from the explicit diagnostics row; the notice is one line under the tool table when any tool is excluded with reason `capability`.

### Corrections made in Step 3b
- Corrected in Step 3b: no capability-state column. A capability-excluded tool has no diagnostics row (seq 13's decision), so every row that exists is a tool whose capabilities are not degraded and a
  state column would always read `ok`. The display lists the excluded tools instead, through the read-only `RuntimeToolRegistry.excluded_tools()` accessor added for this cycle (owner decision,
  2026-11-26), which is what the Plan's Risk mitigation for REQ-006 requires.
- Corrected in Step 3b: the `degraded` and `unavailable` states are not shown separately. The map Tool Discovery hands to the registry is `server_key` to capability names, so the state is not carried
  to the display path; the row shows the reason string `capability` (owner decision, 2026-11-26).
- Corrected in Step 3b: `excluded_tools()` is added in `scripts/shared/runtime_tool_registry.py`, which is seq 13's target file and not this row of the frozen Implementation Target Files, so it is
  recorded as a deviation; `tools/amend_plan.py` cannot register it against the archived plan.
- Corrected in Step 3b: the notice is written only on the `/mcp status` path (`_write_tool_diagnostics()`), which is what AC-08 names. `/mcp tools` (`_cmd_mcp_tools()`) is unchanged.
- Corrected in Step 3b: the pinned row at `test_cmd_mcp.py:1074` keeps its value (`False`, the field default); it is annotated as the declared field and a new case pins the divergence
  (`config_dependent=True` renders `True`).

## Alternatives considered
- N/A: rendering-only change, no public-contract impact.

## Implementation
### Target file
`scripts/agent/commands/cmd_mcp.py`

### Procedure
1. Render `config_dependent` from the explicit field value the diagnostics row now carries (no inference from `status`).
2. List the tools the registry dropped at construction, with the reason it recorded, and write the restart-required notice line when any of them was dropped for a capability.

### Method
- Read only the keys `diagnostics()` provides (`config_dependent`, `disabled_reason`, `enabled`, `enabled_for_llm`, `server_key`) plus the excluded map from `excluded_tools()`; do not recompute anything here.

### Details
- The excluded-tool list with its reason must remain visible (Plan Risk mitigation).

### Companion test files
- `tests/agent/commands/test_cmd_mcp.py`
  - Procedure: update the pinned table headers and rows (`test_cmd_mcp.py:1074`) to the explicit values, and assert the restart notice rendering (T-07, T-08).
  - Validation: `uv run pytest tests/agent/commands/test_cmd_mcp.py` (45 passed; 3 cases added: the excluded tool listed with reason `capability` plus the notice, no notice when the exclusion is
    `posture`, and the row rendering the declared `config_dependent=True`. The pinned row keeps its value and is annotated as the declared field. Added the `_capability_tool()` helper so a case can
    carry both a declared capability and the explicit flag.)
- `tests/shared/test_runtime_tool_registry.py` (deviation file, seq 13's target)
  - Validation: 60 passed; 1 case added for `excluded_tools()`, including that the returned view is read-only.

### Deviation
- `scripts/shared/runtime_tool_registry.py` is not in this row of the frozen Implementation Target Files. The read-only `excluded_tools()` accessor was added there because the display path cannot
  enumerate the tools the registry dropped, and `diagnostics()` has no row for them. Recorded here; the archived plan cannot be amended.

## Compatibility considerations
- Header change affects only this display path; the companion test pins the shape.

### Corrected in Step 3b
- No header change was made. `_TOOL_DIAGNOSTIC_HEADERS` and the pinned row shape stay as they are; the change adds a section below the table for the tools the registry dropped, so the existing
  pinned assertions stay valid. The section is also printed when `diagnostics()` returns no rows but an exclusion exists, which is the case the Plan's Risk mitigation names.

## Security considerations
- N/A: the display path prints tool metadata, never token values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/commands/test_cmd_mcp.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; `wc -c scripts/agent/commands/cmd_mcp.py` below 24576 (current size 15960 B); then the sequence in `rules/toolchain.md`.
- Ran: 45 tests passed in `test_cmd_mcp.py` and 60 in `tests/shared/test_runtime_tool_registry.py`; ruff format/check clean; mypy clean on `cmd_mcp.py` and `runtime_tool_registry.py`; lint-imports 6 contracts kept; bandit clean; `wc -c` 16883 B for `cmd_mcp.py` and 16523 B for `runtime_tool_registry.py`, both below 24576; check_docstrings, check_mock_patch_targets, check_module_size clean; reference table no drift; 75 cited ADR tests pass. Full suite pending at end of batch.

## Completion criteria
- Rows show the explicit values; the restart notice appears on a capability exclusion; tests pass.

## Out of Scope
- The diagnostics implementation (seq 13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the rendering and notice | Completed | 20261126-190929 | 20261126-190929 | Changed files: scripts/agent/commands/cmd_mcp.py, scripts/shared/runtime_tool_registry.py (deviation, seq 13's target). No capability-state column: a capability-excluded tool has no diagnostics row, so the display lists the dropped tools through the new read-only excluded_tools() accessor with reason 'capability' and writes the restart-required notice when any exclusion is a capability. Degraded/unavailable states are not shown separately (owner decision 2026-11-26). File size 16883 B, below 24576. |
| 2 | Update the companion tests | Completed | 20261126-190929 | 20261126-190929 | 3 cases added in tests/agent/commands/test_cmd_mcp.py (excluded tool listed with reason capability plus the notice, no notice for a posture exclusion, row renders the declared config_dependent=True) and 1 case in tests/shared/test_runtime_tool_registry.py for the read-only accessor. 45 and 60 tests passed. The pinned row at :1074 keeps its value and is annotated as the declared field. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-190929 | 20261126-190929 | ruff format/check pass; mypy clean on both source files; lint-imports 6 contracts kept; bandit pass; check_docstrings, check_mock_patch_targets, check_module_size pass; reference table no drift; 75 cited ADR tests pass. Full suite pending at end of batch. Docs: N/A, the docs rows for this module are seq 33-38. |

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
- **Requirement ID**: `REQ-007` (explicit metadata rendering), `REQ-008` (restart-required notice)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/agent/commands/cmd_mcp.py`, `tests/agent/commands/test_cmd_mcp.py`