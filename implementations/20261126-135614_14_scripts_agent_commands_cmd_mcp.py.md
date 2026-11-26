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

## Alternatives considered
- N/A: rendering-only change, no public-contract impact.

## Implementation
### Target file
`scripts/agent/commands/cmd_mcp.py`

### Procedure
1. Render `config_dependent` from the explicit field value the diagnostics row now carries (no inference from `status`).
2. Add the capability state column and the restart-required notice line when a `capability` exclusion exists.

### Method
- Read only the keys `diagnostics()` provides (`config_dependent`, `disabled_reason`, plus the capability state added by seq 13); do not recompute anything here.

### Details
- The excluded-tool list with its reason must remain visible (Plan Risk mitigation).

### Companion test files
- `tests/agent/commands/test_cmd_mcp.py`
  - Procedure: update the pinned table headers and rows (`test_cmd_mcp.py:1074`) to the explicit values, and assert the restart notice rendering (T-07, T-08).
  - Validation: `uv run pytest tests/agent/commands/test_cmd_mcp.py`.

## Compatibility considerations
- Header change affects only this display path; the companion test pins the shape.

## Security considerations
- N/A: the display path prints tool metadata, never token values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/commands/test_cmd_mcp.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; `wc -c scripts/agent/commands/cmd_mcp.py` below 24576 (current size 15960 B); then the sequence in `rules/toolchain.md`.

## Completion criteria
- Rows show the explicit values; the restart notice appears on a capability exclusion; tests pass.

## Out of Scope
- The diagnostics implementation (seq 13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the rendering and notice | Pending | — | — | |
| 2 | Update the companion tests | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
