## Goal
Remove/invalidate the "Canonical Source Precedence" universal ranking table as
normative, and ensure the six-step resolution sequence, claim-type-scoping
statement, intended-vs-observed-state statement, anti-auto-conversion statement, and
six required conflict outcomes are all explicitly present (REQ-001 through REQ-007).

## Scope
- In scope: the "## Canonical Source Precedence" section (currently lines 54-67,
  containing the Rank 1-6 table) and, if not already satisfied by concurrent work
  (see Assumptions), the "## Claim Type Taxonomy" section's framing (lines 69-171)
  and the "## Resolution Workflow"/"### Routing Rules" sections (currently lines
  253-273).
- Out of scope: the "### Decision Target Canonical Source Matrix" subsection's actual
  per-target rows (lines 151-166) — preserve unchanged, only its introductory framing
  may need a one-sentence adjustment if it still describes itself as an alternative
  to the (now-removed) ranking; "## Area Canonical Maps" (lines 173-223) and any
  section beyond line 273 — not touched by this row.

## Assumptions
- **Major drift found this cycle (2026-09-06) — re-verify before implementing**: a
  concurrent session has already landed substantial related work on this exact file
  since this Plan's authoring (2026-09-05), via commits `13aa48498` ("add routing
  rules and Canonical Source Conflict / Configuration Drift tracking sections") and
  `0b92a993e` ("add documentation_canonical_sources.toml and update documentation
  policy"), both dated 2026-09-06:
  - The "## Claim Type Taxonomy" section (`M-01-01`) is fully implemented (13 claim
    types, a Resolution Matrix table with Canonical source kind/Auxiliary
    evidence/Conflict destination columns, and a "Multi-Type Documents" note already
    stating REQ-003's exact concept: "Classification is by claim, not by the document
    as a whole").
  - A "## Resolution Workflow" section (5-step: detect → classify → apply → update →
    record) and a "### Routing Rules" subsection (7 numbered rules, each mapping a
    conflict category to a destination) already exist — the Routing Rules already
    cover 6 of the Issue's 7 verbatim-cited outcomes (design-vs-code → Known Issue;
    Specification-vs-acceptance-test → blocking Canonical Source Conflict;
    deployed-vs-approved config → Configuration Drift; undetermined intent → Needs
    Confirmation; missing canonical source → design/governance gap; multiple
    normative sources → blocking Canonical Source Conflict), plus one extra rule
    (`functional-requirement-vs-implementation → Known Issue`) the Issue's list did
    not name.
  - **Still NOT satisfied** as of this cycle: REQ-001 (the Rank 1-6 table at lines
    60-67 still physically exists, marked only "pending replacement" — not yet
    removed/invalidated); REQ-004 (no explicit statement that intended and observed
    state can be represented simultaneously — `rg` confirms no match for this
    concept's wording); REQ-005 (no explicit prohibition on auto-converting
    implementation deviations into approved specifications — `rg` confirms no
    match).
  - Re-run the `rg` sweep from this Plan's Tests section immediately before
    implementing this row, since a third session could plausibly still be active on
    this same file.

## Design decisions
- Given the above, this row's actual remaining work is narrower than the Plan's
  authoring-time Design section assumed: do not re-author the six-step resolution
  sequence or six conflict outcomes from scratch — reconcile with what
  `13aa48498`/`0b92a993e` already added (rename/merge the existing 7-rule Routing
  Rules into exactly the Issue's 6 named outcomes only if a reviewer determines the
  extra rule is redundant; otherwise leave it as a superset, which does not violate
  REQ-007's "the six required conflict outcomes" as long as all six are present
  somewhere in the routing table). Focus the concrete edit on: (a) replacing the
  Rank 1-6 table's body with the invalidation statement (REQ-001); (b) adding the
  two missing explicit statements (REQ-004, REQ-005) as short notes near the
  "Code is canonical for current behavior, NOT for adopted design" line (168-171),
  which already carries the adjacent conceptual weight.
- Retain the "## Canonical Source Precedence" heading itself (per the Plan's own
  Design section) so existing cross-references (e.g. line 231's
  `` `## Canonical Source Precedence` > `### Decision Target Canonical Source Matrix` ``)
  remain valid.

## Alternatives considered
- Re-author the entire six-step sequence and conflict-outcome table from scratch,
  ignoring the concurrent session's additions: rejected — would create a second,
  possibly-conflicting parallel mechanism (Routing Rules vs. a new sequence) in the
  same document, exactly the kind of "two competing authority models" defect this
  Plan exists to eliminate.

## Implementation
### Target file
`docs/00_governance_01_documentation-policy.md`

### Procedure
1. Re-read the current file in full before editing (per Assumptions, it may have
   changed again since this cycle's read) — re-locate all headings by name, not by
   the line numbers cited here.
2. Replace the "Canonical Source Precedence" Rank 1-6 table's body with: one sentence
   stating the ranking is no longer normative, superseded by the Claim Type Taxonomy
   and Decision Target Canonical Source Matrix below (REQ-001) — remove the table
   itself, not just the existing "pending replacement" note (which currently coexists
   with the still-present table).
3. Confirm the "Multi-Type Documents" note already satisfies REQ-003 verbatim enough
   — if a reviewer finds its wording insufficient, strengthen it; do not duplicate a
   second statement of the same rule.
4. Add a short note (near line 168-171's existing "Code is canonical for current
   behavior, NOT for adopted design" text) stating: intended state (e.g. an ADR's
   adopted design) and observed state (e.g. current runtime behavior) may both be
   documented simultaneously without one silently overwriting the other (REQ-004).
5. Add a short prohibition statement: an automatic documentation change MUST NOT
   convert an implementation deviation into an approved specification without
   explicit review (REQ-005).
6. Confirm the "Routing Rules" subsection's 7 entries collectively cover all 6 of the
   Issue's required outcomes (Method below already confirms 6/6 present); reconcile
   the extra 7th rule only if it creates ambiguity, not merely because it is
   additional.
7. Re-run this Plan's `rg` sweep (`rg -i "ultimate authority|trust the code|Code >
   Tests" docs/`) to confirm no other restatement remains in this file after editing.

### Method
Confirmed this cycle (2026-09-06) via direct read (full sections, lines 54-273):
Rank 1-6 table still present (lines 60-67); Claim Type Taxonomy (69-149), Decision
Target Canonical Source Matrix (151-171), Area Canonical Maps (173-223), Conflict
Resolution Rule (225-232), Code vs Document Conflict Rule (234-242), Known Issues
Registration Rule (244-251), Resolution Workflow (253-261), Routing Rules (263-273)
all already exist. `git log` confirms Routing Rules/Resolution Workflow landed via
commits `13aa48498`/`0b92a993e`, both 2026-09-06 (same day as this cycle, concurrent
session). No match found via `rg` for REQ-004/REQ-005's specific concepts ("intended
state"/"observed state"/auto-conversion prohibition wording) — these remain genuinely
unimplemented.

### Details
No change to the Decision Target Canonical Source Matrix's per-target rows, Area
Canonical Maps, or any section beyond line 273.

## Compatibility considerations
Existing cross-references to the "Canonical Source Precedence" heading (e.g. line
231) remain valid since the heading itself is retained.

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if `check_docs_quality.py`/
`check_docs_structure.py` flag an issue, or if the concurrent session's parallel
edits conflict with this row's edit (re-read and reconcile rather than force-apply).

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_governance_01_documentation-policy.md`
- `uv run python tools/check_docs_structure.py docs/00_governance_01_documentation-policy.md`
- `rg -i "ultimate authority|trust the code|Code > Tests" docs/` — confirm no
  remaining unconditional universal-ranking statement.

## Completion criteria
- The Rank 1-6 table no longer exists as normative content.
- REQ-003 (claim-type scoping), REQ-004 (intended/observed state), REQ-005
  (anti-auto-conversion) are each explicitly stated somewhere in this file.
- All 6 of the Issue's required conflict outcomes are present in the Routing Rules
  (or equivalent) table.

## Out of scope
- `docs/00_governance_04_documentation-checks.md` — tracked in seq 02.
- `docs/06_eventbus_00_document-guide.md` — tracked in seq 03 (already
  substantially satisfied, see that document).
- The Decision Target Canonical Source Matrix's per-target content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | REQ-001: Rank 1-6 table invalidated; REQ-004: intended/observed state coexistence added; REQ-005: anti-auto-conversion prohibition added |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | check_docs_quality.py passed; check_docs_structure.py flagged size limit (pre-existing) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: no docs/00_index.md task-scope mapping for changed file |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007
- **Source issue**: issues/20260903-103025_m0102_replace-universal-source-ranking-with-target-based-resolution.md
- **Source plan**: plans/20260905-164741_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-145512
- **Related target files**: docs/00_governance_01_documentation-policy.md
