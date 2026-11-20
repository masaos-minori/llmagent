## Goal

- Adjust ADR-001's front matter `related` list to match the approved `Requires`-edge reversal so the ADR stays compliant with ADR-016 Decision 7.

## Scope
**Release unit**: model-regen

- REQ-021 (front matter side): the reversal moves the `Requires` edge to `ADR-004 --Requires--> ADR-001`; this document only edits ADR-001's front matter.

## Assumptions
- The whole row is approval-gated: nothing here is edited until the Phase 3 approval record exists (Plan UNK-01).
- Proposal P2 states ADR-001's front matter keeps both entries after the reversal, so the expected edit is confirmation, not addition (Plan Design section).

## Design decisions
- Keep ADR-001's `ADR-004` entry even though the reversal removes the model edge that made it mandatory: it remains backed by the flipped intentional `ADR-001 --Reference--> ADR-004` pair and the Plan's P2 decision.

## Alternatives considered
- N/A: the entry policy is fixed by the approved proposal P2.

## Implementation
### Target file
`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
### Procedure
- Gated (after the approval record and after the `config/adr_authority.toml` reversal lands in the same commit): confirm the front matter `related` list still carries the `adr_02_01_004_...md` entry (and the other entries P2 requires); adjust only if `tools/check_adr_reference.py` reports a `FRONTMATTER_DIVERGENCE` finding against the post-reversal model.
### Method
- Direct front matter edit; no body changes.
### Details
- N/A: single-list row; the plan evidence (model holds `ADR-001 --Requires--> ADR-004`, verified in Step 2) pins the precondition.

## Compatibility considerations
- Run only together with the model reversal (release unit model-regen): an isolated front matter edit would break the cross-check.

## Security considerations
- N/A: documentation row.

## Rollback considerations
- N/A: revert the commit (the gated model-regen package reverts atomically).

## Validation plan
- `uv run python tools/check_adr_reference.py` — reports no `FRONTMATTER_DIVERGENCE` after the reversal.

## Completion criteria
- ADR-001 front matter passes the front matter/model cross-check against the post-reversal model, matching proposal P2.

## Out of Scope
- The model reversal itself (`config/adr_authority.toml` row) and ADR-004's own list additions (its own document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Adjust/confirm the front matter `related` list after the approved reversal (REQ-021) | Completed | 20261120 | 20261120 | Approved 2026-11-20 by ADR-016 Approval Record amendment; no front matter change needed (ADR-004 entry already present) |
| 2 | Run `check_adr_reference.py` | Completed | 20261120 | 20261120 | Gated: plans/20261120-075008_adrchk015_adr-graph-semantics.md phase 3 - validation only meaningful after the model reversal lands |

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
- **Requirement ID**: REQ-021 (reversed `Requires` edge, front matter side)
- **Source issue**: issues/20261117-123015_adrchk015_adr-graph-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-075008_adrchk015_adr-graph-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-092705
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
