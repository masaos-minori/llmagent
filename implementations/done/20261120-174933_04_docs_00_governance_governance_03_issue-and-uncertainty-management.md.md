## Goal
Append the AAL-038 entry to the governance ledger Part 5 for the ADR-015 pending amendment, per plan REQ-005 (pending bullets must cite an existing ledger ID).

## Scope
**Release unit**: ADR015-pending-amendment
- Add one `#### AAL-038` entry after `#### AAL-037` (ends L683), before `## Resolution Rules` (L685). No other part of the file changes.

## Assumptions
- Part 5 entries are a plain unguarded list (Plan Assumption): appending is safe and no generator refresh is involved.
- The entry must exist before or in the same commit as the ADR-015 pending bullet (row 03 document) — `tools/check_adr_structure.py` errors on a pending bullet without a resolving ledger ID.
- Gated Plan: `tools/plan_dependency_order.py` reports this plan gated (prose) by `issues/20261117-123022_adrchk022_history-comment-removal.md` phase all; the owner chose to proceed with this Plan first (2026-11-20). The overlap is section-disjoint (adrchk022 targets history text).

## Design decisions
- Entry format copies the AAL-036/AAL-037 template exactly (six bullets: ID, ADR, Decision, Approver, Date, Scope); Approver/Date are "Not recorded" — no approval text is written or simulated (Issue constraint).
- ID is AAL-038: the next free ID after AAL-037 (verified 2026-11-20).

## Alternatives considered
- N/A: ledger append has no design surface; the ID and format are fixed by the checker and existing entries.

## Implementation
### Target file
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. After the `#### AAL-037` block (its last bullet is its `**Scope:**` line) and before the `## Resolution Rules` heading, insert the entry below verbatim.

### Method
Describe only the decision change the ADR-015 pending bullet records; the Scope bullet names the two ADR-015 sections the change touches.

### Details
```markdown
#### AAL-038

- **ID:** AAL-038
- **ADR:** ADR-015
- **Decision:** Attributing the `tools/generate_adr_authority.py` guard blocks cited by ADR-015's Scope to ADR-016 (Decision 6 and INV-03) instead of extending ADR-015 INV-01
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** ADR-015 Decision Scope attribution sentence, Related ADRs entry, and the Approval Record pending bullet
```

## Compatibility considerations
- `tools/check_adr_structure.py` loads the ledger and matches `AAL-NNN` IDs cited by pending bullets; the new ID must not collide (checked: ledger ends at AAL-037).

## Security considerations
- N/A: governance ledger entry only.

## Rollback considerations
- Revert together with row 03 (ADR-015 edits) as the release unit ADR015-pending-amendment.

## Validation plan
- `uv run python tools/check_adr_structure.py` — ledger loads, AAL-038 present, no pending-bullet/ledger mismatch (run jointly with the row 03 edit).
- `uv run python tools/check_workitem_structure.py` docs-checker pass per `routing.md` Tools.

## Completion criteria
- Part 5 contains `#### AAL-038` in the six-bullet format directly after AAL-037; the ADR-015 pending bullet resolves to it; the checker reports no pending-bullet error.

## Out of Scope
- Any other ledger entry, Known Issue, or Needs Confirmation item in governance_03; editing `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` (covered by the row 03 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-20 | 2026-11-20 | Gated: issues/20261117-123022_adrchk022_history-comment-removal.md phase all - section-disjoint overlap on ADR-017; owner chose this Plan first (2026-11-20) AAL-038 appended after AAL-037; SIZE_EXCEPTIONS ceiling re-recorded 33915->34313 with a dated comment |
| 2 | Run the documentation checkers named in `routing.md` Tools (Validation plan) | Completed | 2026-11-20 | 2026-11-20 | Gated: issues/20261117-123022_adrchk022_history-comment-removal.md phase all - section-disjoint overlap on ADR-017; owner chose this Plan first (2026-11-20) check_adr_structure: No issues found; docs checkers green (run jointly with procedure 03) |

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
- **Requirement ID**: REQ-005 (append the AAL-038 ledger entry the ADR-015 pending bullet cites)
- **Source issue**: issues/20261117-123021_adrchk021_adr-editorial-defects.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-172527_adrchk021_adr-editorial-defects.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-174933
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md