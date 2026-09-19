## Goal
Extend `docs/00_governance_02_documentation-metadata.md`'s "Guidelines for
Recording Information Verifiable via Implementation Reference" section with the
4 additional retain-exemption categories and the explicit 3-condition
mechanical-content test (`REQ-001`, `REQ-002`).

## Scope
In scope: extending the existing "Information to be Retained" list and/or
"Decision Categories" table (lines 154-187) with new content. Out of scope:
redesigning the table's row/column structure; removing any existing guidance;
applying this rule to any specific document's content.

## Assumptions
- Section content unchanged since the Plan was written — re-confirmed at
  `docs/00_governance_02_documentation-metadata.md:154-187` (verbatim match to
  the Plan's Problem section quote).
- The 4 new categories land as additional bullets in "Information to be
  Retained" (extending the existing 6-item list) plus, where a category needs a
  Decision Categories row of its own (the "absence of rationale is itself the
  information" case does not fit neatly as a retain-bullet), one addition to
  that table — this is the source Plan's own stated Assumption, carried forward
  unchanged since no contradicting evidence was found.

## Design decisions
Extend in place rather than restructure: append the 4 new bullets to the
existing "Information to be Retained" list (preserving its current 6 items
verbatim) and add the 3-condition test as a new introductory paragraph directly
under the "Guidelines for Recording Information Verifiable via Implementation
Reference" heading (before "### Information to be Deleted or Compressed
Normally"), since it is meant to be the section's overall rationale, not scoped
to one subsection.

## Alternatives considered
Placing the 3-condition test as a new "### Rationale" subsection between
"Information to be Deleted" and "Information to be Retained" was considered, but
rejected — the source issue asks for it "as the section's stated rationale for
the existing Delete/Compress boundary," which reads more naturally as
introductory framing than as a subsection sandwiched between the two lists.

## Implementation
### Target file
docs/00_governance_02_documentation-metadata.md

### Procedure
1. Insert a short paragraph stating the 3-condition mechanical-content test
   (verifiable from code/config/schema alone; changes only when code changes; a
   wrong statement is caught by execution, not review) immediately after the
   section's existing one-line description ("Criteria for deciding whether to
   include implementation details in design documents.", line 156) and before
   "### Information to be Deleted or Compressed Normally" (line 158).
2. Append 4 new bullets to "Information to be Retained" (after its existing 6th
   bullet, "Decisions regarding future extensibility", line 175): correlated
   constraints with their rationale, security-boundary defaults, the "absence of
   rationale is itself the information" case, and operational pitfalls.
3. If the "absence of rationale is itself the information" category needs a
   Decision Categories table row of its own (it does not fit the existing
   Delete/Compress/Replace/Retain/Move-to-Known-Issues/Move-to-Needs-Confirmation
   rows cleanly), add one row after the existing "Move to Needs Confirmation"
   row (line 186), otherwise fold it into the "Retain" row's Example column.

### Method
Direct text edit (`Edit` tool) — no code generation.

### Details
- 3-condition test paragraph (exact wording, adapted from the source issue's
  Implementation Intent): "Content in this category is removable when all three
  conditions hold: it is verifiable from code, configuration, or schema alone;
  it changes only when the code changes; and a wrong statement about it is
  caught by execution (a test failing, a config load erroring), not by review."
- 4 new "Information to be Retained" bullets:
  - "Correlated constraints and their rationale (e.g. why two fields must satisfy
    a relationship, not just that they do)"
  - "Security-boundary defaults and why they are set that way"
  - "The absence of a documented rationale, when that absence is itself
    operationally significant (e.g. 'no retry policy is intentional, not an
    oversight')"
  - "Operational pitfalls (a config combination that is valid but
    inadvisable)"
- Do not alter the existing "Information to be Deleted or Compressed Normally"
  list (lines 160-166) or the existing "Information to be Retained" bullets
  (lines 170-175) — extend only.

## Compatibility considerations
Documentation-only, additive change to an existing governance section — no
runtime, schema, or code impact. Existing readers of the Decision Categories
table see only new rows/bullets, no reordering of existing content.

## Security considerations
N/A: no code, credentials, or runtime behavior described or changed.

## Rollback considerations
Trivial: `git checkout -- docs/00_governance_02_documentation-metadata.md`
reverts this purely additive change with no downstream dependency (the seq 02
document's cross-reference addition in the Policy doc references this section by
heading, not by exact line number, so it survives this file's revert
independently).

## Validation plan
- Run `uv run python tools/check_docs_quality.py` and `uv run python
  tools/check_docs_structure.py` — expect no new findings.
- Manual review: confirm the Decision Categories table's existing 6 rows are
  unchanged and the 4 new retain bullets are present.

## Completion criteria
- The 3-condition test paragraph and all 4 new retain-exemption categories are
  present in `docs/00_governance_02_documentation-metadata.md`'s Guidelines
  section.
- No existing bullet, row, or heading in this section was removed or
  reordered.
- `tools/check_docs_quality.py`/`tools/check_docs_structure.py` report no new
  findings.

## Out of scope
Applying this extended rule to any specific document's content (separate
content-migration work); redesigning the Decision Categories table's column
structure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only — manual review + structural checks only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Scoped to `tools/check_docs_quality.py` + `tools/check_docs_structure.py` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this document's own Target file IS the documentation being updated |

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
- **Requirement ID**: REQ-001, REQ-002 (add 4 retain-exemption categories; add the 3-condition mechanical-content test)
- **Source issue**: issues/done/20260918-130135_docspol01_extend-metadata-guidelines-not-duplicate-rule.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-104700_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-114337
- **Related target files**: docs/00_governance_02_documentation-metadata.md
