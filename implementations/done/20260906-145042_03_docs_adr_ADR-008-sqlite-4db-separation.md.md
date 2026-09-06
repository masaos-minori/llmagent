## Goal
Verify (and correct only if needed) that ADR-008's `SHARED-003` cross-reference in
its Related Documents section remains accurate after seq 01's `SHARED-003` status
change to `resolved` (REQ-006).

## Scope
- In scope: the `SHARED-003` cross-reference in Related Documents (currently line
  512: "SHARED-003（workflow/eventbus復旧手続きの実務Runbook未整備）").
- Out of scope: any other content in this ADR (Decision Details, Invariants,
  glossary — `H-07-01`'s scope per `plans/20260905-162730_plan.md`).

## Assumptions
- This row executes after seq 01 lands (or the implementer re-checks `SHARED-003`'s
  actual current status/description in
  `docs/00_governance_03_issue-and-uncertainty-management.md` directly before
  editing this row, since seq 01 and seq 03 may not execute in strict sequence).

## Design decisions
- Update the cross-reference's parenthetical description to match `SHARED-003`'s
  corrected text (runbook exists, resolved) rather than removing the cross-reference
  entirely — the ID reference itself (`SHARED-003`) remains valid and useful for
  traceability even after the underlying issue is resolved; only the stale
  parenthetical summary needs correcting.

## Alternatives considered
- Remove the `SHARED-003` cross-reference entirely now that it is resolved:
  rejected — Related Documents sections in this repository's ADRs generally retain
  references to resolved issues for historical traceability (matching this same
  line's retention of the unrelated `CI-002` reference alongside it); only the
  parenthetical's *content* needs to track current status.

## Implementation
### Target file
`docs/adr/ADR-008-sqlite-4db-separation.md`

### Procedure
1. Re-read `docs/00_governance_03_issue-and-uncertainty-management.md`'s
   `SHARED-003` entry immediately before editing this row, to use its actual
   post-seq-01 text (not this document's own paraphrase) for the corrected
   parenthetical.
2. If `SHARED-003`'s status is `resolved` (seq 01 landed), update line 512's
   parenthetical from "workflow/eventbus復旧手続きの実務Runbook未整備" ("operator
   runbook for workflow/eventbus recovery procedures not yet prepared") to reflect
   that the runbook now exists and is resolved — keep the `CI-002` reference on the
   same line unchanged.
3. If `SHARED-003` is not yet updated at implementation time (seq 01 not yet
   landed), leave this line unchanged and report `Not applicable — seq 01 not yet
   implemented` rather than guessing at the eventual corrected text.

### Method
Confirmed this cycle (2026-09-06) via direct read: the `SHARED-003` cross-reference
is at line 512, alongside an unrelated `CI-002` reference on the same bullet line —
confirmed via `rg`, no drift from the Plan's "~511-512" citation.

### Details
No change to any other Related Documents entry or any other section of this ADR.

## Compatibility considerations
N/A: documentation-only.

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if `check_docs_structure.py` flags an
issue.

## Validation plan
- `uv run python tools/check_docs_structure.py docs/adr/ADR-008-sqlite-4db-separation.md`
- Manual cross-check: the corrected parenthetical matches `SHARED-003`'s actual
  current text in `docs/00_governance_03_issue-and-uncertainty-management.md`.

## Completion criteria
- The `SHARED-003` cross-reference's parenthetical accurately reflects its current
  status, or this row explicitly reports `Not applicable` if seq 01 has not yet
  landed.
- `check_docs_structure.py` reports no new finding.

## Out of scope
- Any other ADR-008 content — `H-07-01`'s scope (`plans/20260905-162730_plan.md`).
- `docs/00_governance_03_issue-and-uncertainty-management.md` itself — tracked in
  seq 01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | SHARED-003 cross-reference parenthetical updated: 「workflow/eventbus復旧手続きの実務Runbook未整備」→「workflow/eventbus復旧手続きの実務Runbook整備済み、resolved」 |
| 2 | Add or update tests per Validation plan | Done | — | — | No new tests needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | check_docs_structure.py reports pre-existing warnings (size limit, broken links, missing sections) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | — | — | Related Documents entry updated as specified |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260903-110307_h0709_reconcile-shared-001-002-003-and-nc-021.md
- **Source plan**: plans/20260905-164204_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-145042
- **Related target files**: docs/adr/ADR-008-sqlite-4db-separation.md
