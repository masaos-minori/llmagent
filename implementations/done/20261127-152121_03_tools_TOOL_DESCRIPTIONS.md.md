## Goal
- Document `--headroom` in the Index and Work Items rows of `tools/check_skill_size.py` (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

- Runs after the tool procedure (seq 01).

## Assumptions
- Verified in Step 3a: the Index row (`check_skill_size.py | Lint/Docs | ...`) and the Work Items row (`check_skill_size.py | skills/**/*.md, ...`) exist; the Work Items row ends with the option list `--root PATH`, `--limit BYTES`, `--baseline PATH`, `--no-baseline`, `--update-baseline`, `--top N`.

## Design decisions
- Append sentences to the existing cells; do not restructure the rows.

## Alternatives considered
N/A: the Plan fixes the wording and the places.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Index row: append "; `--headroom PATH [PATH ...]` prints the size, ceiling, and headroom of the named files".
2. Work Items row: append "`--headroom PATH [PATH ...]` prints, for each path, `{relpath}: {size} B, ceiling {N} B (baseline|limit), headroom {N} B` (the ceiling is the baseline entry or the limit; headroom may be negative), prints `not covered by the size gate` for an existing path outside the covered patterns, exits 2 for a missing path, is report-only (no file is written and the gate is not run), and cannot be combined with `--update-baseline`."

### Method
- Exact-string edits; check each anchor occurs once with `rg -c` before editing, and measure `wc -c` before and after.

### Details
- Plain ASCII punctuation as in the neighboring text.

## Compatibility considerations
N/A: procedure text only; `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` must still pass.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` exits 0.

## Completion criteria
- The option is described in both rows and the sync check passes.

## Out of Scope
- Any other text of this file and the other target files of the Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the option text to the two rows | Completed | 20261127-152529 | 20261127-152535 | Changed: tools/TOOL_DESCRIPTIONS.md (Index and Work Items rows of check_skill_size.py) |
| 2 | Run `uv run python tools/check_tool_descriptions_sync.py` | Completed | 20261127-152535 | 20261127-152535 | check_tool_descriptions_sync.py: No issues found |

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
- **Requirement ID**: `REQ-005` (document the option)
- **Source issue**: issues/20261127-120059_flowopt001_skill-size-fallout-check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-151623_flowopt001_skill-size-fallout-check.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-152121
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`