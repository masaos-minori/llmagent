## Goal
Add a "Recency Is Not Authority" subsection to the "## Canonical Source Precedence"
section: the normative sentence, the four permitted uses of recency, and the six
prohibited uses (REQ-002, REQ-003, REQ-004).

## Scope
- In scope: appending one new subsection to "## Canonical Source Precedence"
  (currently lines 54-171, per `M-01-02`'s seq 01 of `plans/done/20260905-164741_plan.md`
  — this row's new subsection should be added after that Plan's own edits land, at
  the end of this section, before "## Area Canonical Maps").
- Out of scope: any other section; `M-01-01`/`M-01-02`'s own content (Claim Type
  Taxonomy, Resolution Matrix, Routing Rules) — read only, not modified by this row.

## Assumptions
- **Execution order**: this row depends on `M-01-01` (Claim Type Taxonomy) and
  `M-01-02` (resolution sequence, ranking-table removal) both landing first in this
  same file — confirmed this cycle (2026-09-06) that `M-01-01`'s taxonomy is already
  present; `M-01-02`'s own seq 01
  (`implementations/20260906-145512_01_docs_00_governance_01_documentation-policy.md.md`,
  generated earlier this same session) documents that the old ranking table is
  **not yet removed** as of this cycle — re-confirm both have actually landed
  (not just been documented) before implementing this row; if not, this row is
  blocked per its own Phase 0 gate.
- No conflicting recency-authority statement exists yet in this file (confirmed via
  `rg` this cycle — no match for "most recent"/"latest reviewed"/"newest"/"last
  modified" as an authority claim in this file).

## Design decisions
- Place the new subsection at the end of "## Canonical Source Precedence" (after the
  Decision Target Canonical Source Matrix, before "## Area Canonical Maps") rather
  than inside the Claim Type Taxonomy — this rule qualifies the whole
  resolution-sequence section, not one specific claim type.

## Alternatives considered
- Add the recency rule as a new top-level `##` section instead of a subsection of
  "Canonical Source Precedence": rejected — the Plan's own Design section places it
  as a subsection there specifically so it sits adjacent to the resolution sequence
  it qualifies, per the Plan's own reasoning.

## Implementation
### Target file
`docs/00_governance_01_documentation-policy.md`

### Procedure
1. Confirm Phase 0's prerequisite (M-01-01/M-01-02 actually landed, not just
   documented) before proceeding.
2. Add a new "### Recency Is Not Authority" subsection at the end of "## Canonical
   Source Precedence", containing: the normative sentence ("Review date,
   modification date, commit date, and document recency do not determine canonical
   authority..."); a "Permitted uses of recency" bulleted list (staleness detection
   for non-canonical content; investigation prioritization; periodic-review
   scheduling; same-file revision identification); a "Prohibited uses of recency"
   bulleted list (overriding an Accepted ADR; a canonical Specification; an official
   API contract/schema; deployed configuration; an Operations runbook; promoting a
   Note/Reference to canonical status).

### Method
Confirmed this cycle (2026-09-06) via direct read (full section, lines 54-171): no
recency-based authority statement exists in this file today. `M-01-01`'s Claim Type
Taxonomy is present; `M-01-02`'s ranking-table removal (that Plan's own REQ-001) is
confirmed NOT YET landed as of this cycle (per that Plan's seq 01 document,
generated earlier this same session) — this row's Phase 0 gate is not yet clear.

### Details
No change to any existing subsection's content.

## Compatibility considerations
N/A: additive new subsection.

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if `check_docs_quality.py` flags an
issue.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_governance_01_documentation-policy.md`
- `rg -i "most recent|latest reviewed|newest|last modified|authoritative|source of truth" docs/` —
  semantic review of every match (do not blindly flag legitimate maintenance
  "review date" mentions).

## Completion criteria
- "### Recency Is Not Authority" subsection exists with the normative sentence, 4
  permitted uses, and 6 prohibited uses.

## Out of scope
- `docs/00_governance_04_documentation-checks.md` — tracked in seq 02.
- `M-01-01`/`M-01-02`'s own content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked on M-01-01/M-01-02 actually landing — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `M-01-02`'s ranking-table removal (REQ-001) not yet landed as of 2026-09-06 | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260903-103026_m0103_remove-document-recency-as-canonical-authority-rule.md
- **Source plan**: plans/20260905-165006_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-145739
- **Related target files**: docs/00_governance_01_documentation-policy.md
