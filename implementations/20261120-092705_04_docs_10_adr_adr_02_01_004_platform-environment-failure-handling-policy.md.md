## Goal

- After approval, list the ADR-006/ADR-008 body mentions in ADR-004's front matter and `## Related ADRs` once their forward model edges exist, and reflect the approved `Requires`-edge reversal on this ADR's lists.

## Scope
**Release unit**: model-regen

- REQ-024 (ADR-004 -> ADR-006 / ADR-008 `Reference` edges, list side) and REQ-021 (front matter side of the reversal). The whole row is approval-gated.

## Assumptions
- The body cites ADR-006/ADR-008 (line 247 area, verified in Step 2) and today only the reverse edges (`ADR-006 -> ADR-004`, `ADR-008 -> ADR-004`) exist in the model — verified via a full config read.
- The reversal makes ADR-004 the source of the `agent.workflow-control` `Requires` edge (ADR-001 stays the decision owner), so Decision 7 requires the owning-side front matter of the new `ADR-004 --Requires--> ADR-001` edge to list ADR-001; whether the entry already exists must be read from the current front matter before editing.

## Design decisions
- Add the entries only in the same gated commit as the approved `ADR-004 -> ADR-006` / `ADR-004 -> ADR-008` model edges (Plan P5), because an unlisted edge or a listed-but-model-less `adr_02_*` related edge both fail the cross-check.

## Alternatives considered
- N/A: the additions are mandated by the approved proposal P5.

## Implementation
### Target file
`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
### Procedure
- Gated (after the approval record, same commit as the model edge additions): add the ADR-006 and ADR-008 entries to the front matter `related` list and to the `## Related ADRs` section (REQ-024).
- Gated: confirm the front matter carries the `ADR-001` entry required by the post-reversal `ADR-004 --Requires--> ADR-001` edge (REQ-021).
### Method
- Direct front matter and section-list edits; no decision-text changes.
### Details
- N/A: the two additions and the confirmation target are pinned by the verified body-mention locations and the model edge read in Step 2.

## Compatibility considerations
- Must land with the model edges and the Index regeneration (release unit model-regen); in isolation the cross-check fails.

## Security considerations
- N/A: documentation row.

## Rollback considerations
- N/A: revert the commit (the gated model-regen package reverts atomically).

## Validation plan
- `uv run python tools/check_adr_reference.py` — no `FRONTMATTER_DIVERGENCE` findings after the model edges land.

## Completion criteria
- Front matter and `## Related ADRs` list ADR-001, ADR-006, and ADR-008 consistently with the post-approval model, and the cross-check passes (AC-2, AC-6).

## Out of Scope
- The model edge additions themselves (`config/adr_authority.toml` row) and any change to ADR-004's failure-classification decision text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add ADR-006/ADR-008 to front matter and Related ADRs; confirm the ADR-001 entry (REQ-021, REQ-024) | Pending | — | — | Gated: plans/20261120-075008_adrchk015_adr-graph-semantics.md phase 3 - requires a maintainer approval record citing a governance_03 Part 5 AAL entry (UNK-01) |
| 2 | Run `check_adr_reference.py` | Pending | — | — | Gated: plans/20261120-075008_adrchk015_adr-graph-semantics.md phase 3 - validation only meaningful after the model edges land |

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
- **Requirement ID**: REQ-021 (reversal, ADR-004 side), REQ-024 (unlisted-mention edges, list side)
- **Source issue**: issues/20261117-123015_adrchk015_adr-graph-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-075008_adrchk015_adr-graph-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-092705
- **Related target files**: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
