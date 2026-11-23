## Goal

Add the two inventory rows for the new tool so `check_tool_descriptions_sync.py` passes.

## Scope
**Release unit**: skill-size-gate

In scope: one row in the summary table (near line 120) and one row in the per-tool table (near line 282). No other row changes.

## Assumptions

- Verified: `check_config_comment_length.py` has a row in each table (lines 120 and 282); the sync checker requires a row for every `tools/*.py`.

## Design decisions

- Summary row: category `Lint/Docs`, one sentence that the tool checks the size of the pipeline instruction files against a default limit and a baseline of ceilings, runs in CI. Per-tool row: target `skills/**/*.md`, `rules/*.md`, `prompts/*.md`, `templates/*.md`, `routing.md`, `AGENTS.md`, `CLAUDE.md`; the limit, the baseline file, the violation and stale and shrunk semantics, and the two update modes.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Insert both rows next to the config comment rows, keeping the tables' column count and alignment.

### Method
Two Edit operations.

### Details
- Run the sync checker after the edit.

## Compatibility considerations

N/A: no behavior change.

## Security considerations

N/A: documentation only; no approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py`
- `uv run python tools/run_validation_gates.py`

## Completion criteria

- Both rows exist and the sync checker passes.

## Out of Scope

Other tool rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-160632 | 20261123-161116 | Added the summary and per-tool rows |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Completed | 20261123-161116 | 20261123-161116 | check_tool_descriptions_sync and validation gates pass |

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
- **Requirement ID**: `REQ-002` (gate, CI, inventory wiring)
- **Source issue**: issues/20261123-155457_skillsize001_compress-skill-workflows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-155813_skillsize001_compress-skill-workflows.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-160210
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
