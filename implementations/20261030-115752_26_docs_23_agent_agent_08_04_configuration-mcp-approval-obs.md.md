# Implementation Procedure: `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`

## Goal

Convert the Component Criticality Classification table into a generated guard block rendered from the registry by `tools/generate_reference_table.py` (REQ-005: table becomes an AUTO-GENERATED guard block, ADR-015 pattern; AC-4).

## Scope

- `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`: the table block at :51-64 (intro line :51, header + 10 rows :53-64, shell row :55, mdq row :64) is replaced by the guard-marked generated block; surrounding prose (:40-50 heading/criteria summary, :66 subprocess/reclassification paragraph) stays hand-written.
- No generator edits in this row (row 9 owns them); land 09 and 26 in the same commit group (row 9 Compatibility note).

## Assumptions

- Row 9's generator output reproduces the current table byte-for-byte except for the guard comments and welcome line (row 9 renders the same three columns from the registry, whose `rationale` field carries the current rationale text — row 1 Design decision).
- `agent_08_04` currently has no AUTO-GENERATED markers (verified: no `AUTO-GENERATED` string in the file).

## Design decisions

- Block placement: guard start marker immediately after the intro line :51 (the sentence about ADR-004 Group 3 item 13 stays hand-written above the block so the ADR citation is not generated text), generated table, guard end marker before the :66 paragraph.
- The heading `#### Component Criticality Classification` (:40) stays outside the markers; row 9's `DOMAIN_HEADING` wiring must render the table under its own welcome line without duplicating this heading (adjust in row 9 if the renderer insists on a heading — coordinate, do not duplicate).

## Alternatives considered

- N/A: conversion prescribed by REQ-005.

## Implementation

### Target file

`docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`

### Procedure

1. Run `uv run python tools/generate_reference_table.py --type mandatoriness` (row 9) and insert its guarded output replacing :53-64.
2. Verify the diff shows: guard markers + welcome line added, table rows identical text, prose outside the block untouched.
3. `uv run python tools/generate_reference_table.py --check` exits 0.

### Method

Generator writes the doc in place (`render_updated_doc`, `tools/generate_reference_table.py:342`); this row reviews the resulting diff rather than hand-writing the block.

### Details

- Row 8's checker 3 requires the markers present in this file; a hand-restored table is drift.
- Docs quality: no Japanese characters (`check_docs_japanese.py`), content policy unchanged (the table is a generated reference, not implementation detail).

## Compatibility considerations

- `check_docs_consistency.py --domain mcp` cross-checks classification claims; the generated block is now the authoritative rendered copy (row 28 registers the registry as canonical source for mandatoriness claims).
- Cross-plan: no other Frozen plan targets this file.

## Security considerations

- N/A: docs conversion; drift protection arrives with rows 8/9.

## Rollback considerations

- Revert together with row 9 (single commit group) so `--check` never sees a guarded doc with an unguarded generator or vice versa.

## Validation plan

- `uv run python tools/generate_reference_table.py --check`; `uv run python tools/check_docs_consistency.py --domain mcp`; `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`.

## Completion criteria

- The classification table lives only inside guard markers, `--check` and the docs checker set pass, and a registry edit (row 1 file) changes the rendered table on regeneration (plan AC-4).

## Out of Scope

- Generator implementation (row 9), drift checker (row 8), registry content (row 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace :53-64 with the generated guarded block | Pending | — | — | Needs row 9 |
| 3 | Run generator `--check` + docs checker set | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Row 9 (generator domain) must land in the same commit group | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005 (classification table becomes generated guard block from the registry)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`
