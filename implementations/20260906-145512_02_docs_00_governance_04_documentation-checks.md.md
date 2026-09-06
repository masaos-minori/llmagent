## Goal
Update Manual Check 9's numbered list item 1 ("Code is the ultimate authority for
behavioral claims") to reference the new claim-type/decision-target resolution
sequence instead of asserting unconditional code authority (REQ-008).

## Scope
- In scope: item 1 only, within "### 9. Canonical Source Verification" (currently
  line 184).
- Out of scope: item 2 (the recency-rule line, currently line 185 — `M-01-03`'s
  scope, a separate Plan in this same issue batch; confirmed still present, not
  touched here) and item 3 (the area-document-guide line, line 186 — unrelated to the
  universal-ranking defect).

## Assumptions
- This row's edit should reference whichever mechanism seq 01 lands in
  `docs/00_governance_01_documentation-policy.md` (the Claim Type Taxonomy +
  Resolution Matrix + Routing Rules, already substantially in place per seq 01's
  Assumptions) — re-check seq 01's actual landed section names before finalizing this
  row's wording, rather than assuming a "six-step resolution sequence" heading that
  may not exist verbatim under that name.

## Design decisions
- Replace item 1's text with a short pointer (e.g. "Canonical authority is resolved
  per claim type and decision target — see
  `00_governance_01_documentation-policy.md`'s Claim Type Taxonomy and Decision
  Target Canonical Source Matrix") rather than restating the resolution logic inline
  — keeps this checklist item a pointer to the single normative source, consistent
  with `skills/DESIGN.md`'s general "reference, don't duplicate" pattern already
  used elsewhere in this document set.

## Alternatives considered
- Remove item 1 entirely without replacement: rejected — Manual Check 9's own
  purpose ("Canonical Source Verification") needs at least a pointer to where
  canonical-authority questions are resolved; removing it silently would leave a
  numbered list with a gap in intent, not just in wording.

## Implementation
### Target file
`docs/00_governance_04_documentation-checks.md`

### Procedure
1. Re-confirm item 1's current line number (this cycle: line 184) before editing.
2. Replace "Code is the ultimate authority for behavioral claims" with a short
   pointer to `docs/00_governance_01_documentation-policy.md`'s claim-type/
   decision-target resolution mechanism (exact section name confirmed against seq
   01's landed state, per Assumptions).
3. Leave items 2 and 3 unchanged.

### Method
Confirmed this cycle (2026-09-06) via direct read: "### 9. Canonical Source
Verification" (line 180), item 1 at line 184 reads exactly "Code is the ultimate
authority for behavioral claims" — no drift from the Plan's citation. Item 2 (line
185, recency rule) confirmed still present and unrelated to this row (`M-01-03`'s
scope).

### Details
No change to any other Manual Check in this document.

## Compatibility considerations
N/A: documentation-only.

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if `check_docs_quality.py`/
`check_docs_structure.py` flag an issue.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_governance_04_documentation-checks.md`
- `uv run python tools/check_docs_structure.py docs/00_governance_04_documentation-checks.md`
- `rg -i "ultimate authority" docs/` — confirm no remaining match.

## Completion criteria
- Item 1 no longer asserts unconditional code authority; it points to the
  claim-type/decision-target resolution mechanism instead.
- Items 2 and 3 unchanged.

## Out of scope
- Item 2 (recency rule) — `M-01-03`'s scope, a separate Plan.
- Item 3 (area document-guide) — unrelated.
- `docs/00_governance_01_documentation-policy.md` — tracked in seq 01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20260903-103025_m0102_replace-universal-source-ranking-with-target-based-resolution.md
- **Source plan**: plans/20260905-164741_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-145512
- **Related target files**: docs/00_governance_04_documentation-checks.md
