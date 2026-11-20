## Goal

- After approval, list the ADR-009 body mention in ADR-005's front matter and `## Related ADRs` once the approved forward model edge exists.

## Scope
**Release unit**: model-regen

- REQ-024 (ADR-005 -> ADR-009 `Reference` edge, list side). The whole row is approval-gated.

## Assumptions
- The body mentions ADR-009 and today only the reverse `ADR-009 -> ADR-005` edge exists in the model (verified in Step 2 by a full config read); the row is therefore blocked on the approved edge addition, not on this document.

## Design decisions
- Add the entries only in the same gated commit as the approved `ADR-005 -> ADR-009` model edge (Plan P5), so the cross-check never sees a listed edge without a model edge.

## Alternatives considered
- N/A: the addition is mandated by the approved proposal P5.

## Implementation
### Target file
`docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`
### Procedure
- Gated (after the approval record, same commit as the model edge addition): add the ADR-009 entry to the front matter `related` list and to the `## Related ADRs` section (REQ-024).
### Method
- Direct front matter and section-list edits; no decision-text changes.
### Details
- N/A: one addition; the verified body mention and the reverse-only edge state pin the precondition.

## Compatibility considerations
- Must land with the model edge and the Index regeneration (release unit model-regen); in isolation the cross-check fails.

## Security considerations
- N/A: documentation row.

## Rollback considerations
- N/A: revert the commit (the gated model-regen package reverts atomically).

## Validation plan
- `uv run python tools/check_adr_reference.py` — no `FRONTMATTER_DIVERGENCE` findings after the model edge lands.

## Completion criteria
- ADR-005 lists ADR-009 in front matter and Related ADRs consistently with the post-approval model, and the cross-check passes (AC-2).

## Out of Scope
- The model edge addition itself (`config/adr_authority.toml` row) and any change to ADR-005's decision text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add ADR-009 to front matter and Related ADRs (REQ-024) | Pending | — | — | Gated: plans/20261120-075008_adrchk015_adr-graph-semantics.md phase 3 - requires a maintainer approval record citing a governance_03 Part 5 AAL entry (UNK-01) |
| 2 | Run `check_adr_reference.py` | Pending | — | — | Gated: plans/20261120-075008_adrchk015_adr-graph-semantics.md phase 3 - validation only meaningful after the model edge lands |

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
- **Requirement ID**: REQ-024 (unlisted-mention edge, ADR-005 list side)
- **Source issue**: issues/20261117-123015_adrchk015_adr-graph-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-075008_adrchk015_adr-graph-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-092705
- **Related target files**: `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`
