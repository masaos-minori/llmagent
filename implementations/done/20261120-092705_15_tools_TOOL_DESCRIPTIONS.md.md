## Goal

- Sync the three tool-description rows for `check_adr_authority.py`, `check_adr_reference.py`, and `generate_adr_authority.py` with the behaviors this Plan adds, as mandated by the Tool Descriptions Sync Check.

## Scope
**Release unit**: N/A: not part of a release unit

- REQ-015 (tool-description sync) — ungated; no approval record needed (Plan Assumption).

## Assumptions
- Verified current rows (Step 2 read; re-locate each row by tool name before editing since row numbers shift with unrelated edits): the `check_adr_authority.py` row (row 183 area), `check_adr_reference.py` row (row 185 area, already documents the `FRONTMATTER_DIVERGENCE` cross-check), and `generate_adr_authority.py` row (row 203 area).
- The rows must describe the tools only after the corresponding code rows land (Phase 1 codes, Phase 2 flow and governance block), so this document executes after those rows in the same phase commit.

## Design decisions
- Describe new behavior inside the existing row cells (finding codes `EDGE_DUPLICATE` / `ADR_STATUS_INVALID`, cross-check independence on a vacuous matrix, the governance_01 `adr-section-header-list` block and refusal on model findings) rather than adding new rows — one row per tool is the file's invariant.

## Alternatives considered
- N/A: mandated sync; the only degree of freedom is wording, fixed by the code rows' shipped behavior.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`
### Procedure
- Update the `check_adr_authority.py` row: name the new finding codes it surfaces through the core (REQ-015, with REQ-001/REQ-004/REQ-005).
- Update the `check_adr_reference.py` row: the front matter cross-check runs independently of the matrix result, so a vacuous matrix fails while still reporting cross-check findings (REQ-015, with REQ-008).
- Update the `generate_adr_authority.py` row: add the governance_01 `adr-section-header-list` guarded block to its guarded-block list and note generation refusal on any model finding (REQ-015, with REQ-014/REQ-003).
### Method
- Cell-text edits preserving the table shape and the existing GV references in each row.
### Details
- N/A: wording mirrors the implemented behavior; no new claims beyond the code rows this Plan ships.

## Compatibility considerations
- `tools/check_tool_descriptions_sync.py` compares these rows against tool docstrings/CLI — run it after the code rows land (AC-3).

## Security considerations
- N/A: documentation row.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` — exit 0 (AC-3).

## Completion criteria
- All three rows match the shipped tool behavior and the sync check passes (AC-3).

## Out of Scope
- The tools' code (their own rows) and governance_04's rule registry (its own row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the three tool rows after their code rows land (REQ-015) | Completed | 20261120 | 20261120 | — |
| 2 | Run `check_tool_descriptions_sync.py` | Completed | 20261120 | 20261120 | — |

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
- **Requirement ID**: REQ-015 (tool-description sync)
- **Source issue**: issues/20261117-123015_adrchk015_adr-graph-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-075008_adrchk015_adr-graph-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-092705
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
