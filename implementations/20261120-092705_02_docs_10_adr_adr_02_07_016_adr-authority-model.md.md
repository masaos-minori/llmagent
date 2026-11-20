## Goal

- Sync ADR-016 Implementation Notes with the new core finding codes, and — only after maintainer approval — define the per-type edge semantics in Decision 3 and replace the hard-coded circular-pair counts with a pointer to the generated section.

## Scope
**Release unit**: model-regen

- Implementation Notes sync for `EDGE_DUPLICATE` (new) / `ADR_STATUS_INVALID` (new) — ungated (documentation of Phase 1 tool behavior).
- REQ-019 (Decision 3 edge-type semantics, proposal P1) and REQ-025 (pair-count wording, proposal P6) — gated.

## Assumptions
- The Summary (line 31) and Problem (line 47) sentences contain "seven intentional circular pairs" (verified in Step 2); the pending `Current Decision Approval` bullet at line 165 (AAL-018) already covers the 6->7 count change and section rename, so REQ-025 extends that pending scope rather than creating a competing edit (Plan Assumption).
- ADR-016 Decision 10 already documents that ADR-016 owning no decision target is intentional — no fix is needed for that claim.
- The canonical allowed-status sentence in ADR-016 must keep equality with `governance_01` "ADR Status Definitions" (`Proposed` / `Accepted` / `Withdrawn`), which the core cross-checks.

## Design decisions
- Implementation Notes land ungated with Phase 1 because they only report checker behavior, like the `tools/TOOL_DESCRIPTIONS.md` sync.
- The semantics sentence is inserted into Decision 3 as the approved P1 text; the count sentences become a pointer to the generated `Intentional Circular References` section rather than a new number (P6), so future pair changes need no ADR edit.

## Alternatives considered
- Editing the count to "seven"/"six" directly — rejected by the Plan: the count is decision-text territory already pending under AAL-018.

## Implementation
### Target file
`docs/10_adr/adr_02_07_016_adr-authority-model.md`
### Procedure
- Ungated: extend the Implementation Notes with the new finding codes `EDGE_DUPLICATE` (new) and `ADR_STATUS_INVALID` (new) (codes the core produces per REQ-001/REQ-004/REQ-005; the codes are created by the core procedure document).
- Gated (after the approval record only): add the approved P1 semantics sentence to Decision 3 — dependent-side source, decision-owner target, `Reference` carries no direction claim, normative body references must appear as model edges plus front matter (REQ-019).
- Gated (after the approval record only): replace the "seven" phrasing in the Summary and Problem lines with the P6 pointer wording (REQ-025); coordinate with the pending AAL-018 bullet so one approval covers both.
### Method
- Direct text edits; gated edits quote the approved proposal text from the Plan's Design section without paraphrasing.
### Details
- N/A: the row's text targets are pinned by line numbers verified in Step 2; nothing beyond the Proposal texts is file-level detail.

## Compatibility considerations
- `tools/check_adr_structure.py` section-header and status checks must keep passing; body edits stay inside existing sections.

## Security considerations
- N/A: documentation row.

## Rollback considerations
- Revert the commit; the gated edits revert together with the model change (release unit model-regen).

## Validation plan
- `uv run python tools/check_adr_structure.py` — section headers and Status stay compliant.
- `uv run python tools/check_adr_reference.py` — no front matter/model divergence.
- Gated portion: after implementation, `uv run python tools/generate_adr_authority.py --check` confirms the generated Intentional Circular References section matches the pointer wording.

## Completion criteria
- Implementation Notes name both new finding codes; checkers pass.
- Gated portion (once approved and executed): Decision 3 states the approved per-type semantics, and no hard-coded pair count remains in the file (AC-5).

## Out of Scope
- `config/adr_authority.toml` model edits and the Index wording (their own procedure documents); any other ADR decision text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Sync Implementation Notes with the new finding codes (ungated, lands with Phase 1) | Pending | — | — | |
| 2 | Add the approved P1 edge-type semantics to Decision 3 (REQ-019) | Pending | — | — | Gated: plans/20261120-075008_adrchk015_adr-graph-semantics.md phase 3 - requires a maintainer approval record citing a governance_03 Part 5 AAL entry (UNK-01) |
| 3 | Replace the "seven" pair counts with the generated-section pointer (REQ-025) | Pending | — | — | Gated: plans/20261120-075008_adrchk015_adr-graph-semantics.md phase 3 - folds into the pending AAL-018 approval scope (UNK-03) |
| 4 | Run `check_adr_structure.py` and `check_adr_reference.py` | Pending | — | — | |

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
- **Requirement ID**: REQ-019 (edge-type semantics definition), REQ-025 (pair-count wording), REQ-026 (generated-section pointer target)
- **Source issue**: issues/20261117-123015_adrchk015_adr-graph-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-075008_adrchk015_adr-graph-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-092705
- **Related target files**: `docs/10_adr/adr_02_07_016_adr-authority-model.md`
