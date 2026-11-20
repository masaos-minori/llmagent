## Goal
Complete the ADR-017 Completion Checklist with the six canonical follow-on items the sibling Accepted ADRs carry, per plan REQ-004 (complete the checklist without introducing new requirements).

## Scope
**Release unit**: N/A: not part of a release unit
- Append six checklist items after the existing eleven in `## Completion Checklist` (L194-end). No other section changes.

## Assumptions
- The "governed checklist template" is the 17-item shared set used by ADR-012/014/015 (Plan Assumption; no standalone checklist template file exists).
- Each added item is verified true against ADR-017's own sections before marking (Plan REQ-004 evidence: Verification L142 with Automated Tests subsection covering INV-01..05; Known Deviations L157 has no discrepancy to register; Required Reviewers L169 and Approval Record L173 exist; Review Triggers L161 recorded; ADR-017 is registered in `docs/10_adr/adr_01_index.md` and referenced from `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` and `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`).
- Gated Plan: `tools/plan_dependency_order.py` reports this plan gated (prose) by `issues/20261117-123022_adrchk022_history-comment-removal.md` phase all; the owner chose to proceed with this Plan first (2026-11-20). Overlap is section-disjoint: adrchk022 edits ADR-017 history text, not the checklist.

## Design decisions
- Items are copied verbatim from the shared item strings (ADR-012 checklist), including the long Owner/Reviewers parenthetical, so no new requirement text is introduced.
- Before appending, re-verify the six claims against the current file (adrchk022 or another plan may have landed since this analysis).

## Alternatives considered
- N/A: the only alternative (leaving the checklist short) contradicts the Plan's confirmed defect.

## Implementation
### Target file
- `docs/10_adr/adr_02_03_017_mcp-authentication.md`

### Procedure
1. After the last existing item "- [x] Exceptions or out-of-scope cases are clear", append the six items (Details) in the given order.

### Method
Copy-only: no wording changes to the copied items and none to the file's normative sections (Decision, Invariants, Failure Policy). If any of the six claims is no longer true at execution time, do not mark that item `[x]`; report it and re-check the Plan instead.

### Details
Append exactly:

```markdown
- [x] Each Invariant has a corresponding Verification
- [x] Automatable verification does not rely only on Manual Review
- [x] Discrepancies with the current implementation are registered as Known Issues
- [x] The Owner and required Reviewers are defined (the task-level approval decision defined by `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard is used as acceptance evidence; no individual Approval Record [approver, approval date, approval reference] has been created)
- [x] Review Triggers are recorded
- [x] The ADR is registered in the ADR index and the Document Guides of related areas
```

## Compatibility considerations
- N/A: checklist section only; outside guard blocks; the Owner/Reviewers parenthetical is copied verbatim from the sibling ADRs and matches the governance_01 standard wording already applied to ADR-017's Approval Record.

## Security considerations
- N/A: checklist completion only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py` — 0 errors for ADR-017.
- `uv run pytest tests/tools/test_check_adr_structure.py -q`.
- `uv run python tools/check_adr_reference.py` — index/guide registration claim stays consistent.

## Completion criteria
- The checklist holds the 17 canonical items in canonical order; every `[x]` is backed by an existing ADR-017 section; no normative text changed; validation commands pass.

## Out of Scope
- adrchk022's history-text removal in ADR-017 (open Issue, runs after this Plan per owner decision); edits to ADR-017 Decision/Invariants/Verification; index regeneration (generator-owned).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-20 | 2026-11-20 | Gated: issues/20261117-123022_adrchk022_history-comment-removal.md phase all - section-disjoint overlap on ADR-017; owner chose this Plan first (2026-11-20) Six items appended verbatim from Details; wording confirmed identical to sibling Accepted ADR checklist corpus |
| 2 | Run the documentation checkers named in `routing.md` Tools (Validation plan) | Completed | 2026-11-20 | 2026-11-20 | Gated: issues/20261117-123022_adrchk022_history-comment-removal.md phase all - section-disjoint overlap on ADR-017; owner chose this Plan first (2026-11-20) check_adr_structure clean; test_check_adr_structure 34 passed; check_adr_reference/docs checkers green |

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
- **Requirement ID**: REQ-004 (append the six missing canonical Completion Checklist items to ADR-017)
- **Source issue**: issues/20261117-123021_adrchk021_adr-editorial-defects.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-172527_adrchk021_adr-editorial-defects.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-174933
- **Related target files**: docs/10_adr/adr_02_03_017_mcp-authentication.md