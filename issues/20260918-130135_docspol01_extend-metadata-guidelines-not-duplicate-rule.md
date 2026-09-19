# Extend the existing mechanical-content Guidelines instead of adding a duplicate Documentation Policy rule

## Priority
Medium

## Summary
A proposed documentation-slimming policy plans to add a new
"Mechanically-Derivable Content Rule" to `docs/00_governance_01_documentation-policy.md`,
but `docs/00_governance_02_documentation-metadata.md` already has a "Guidelines for
Recording Information Verifiable via Implementation Reference" section with an almost
identical Delete / Compress / Replace-with-Source-Reference / Retain /
Move-to-Known-Issues / Move-to-Needs-Confirmation decision framework. Adding a second,
separately-worded rule risks two governance sources disagreeing over time.

## Background
N/A: covered by Summary.

## Problem
Confirmed by direct comparison: the existing Guidelines section's "Information to be
Deleted or Compressed Normally" (implementation details at file/line level, default
config values verifiable in code, file-structure enumerations, CLI argument
references, JSON examples, API schema definitions) and "Information to be Retained"
(design intent, boundaries/responsibilities, error-handling/performance/security
design decisions, extensibility decisions) already cover the same ground the proposed
new rule's 3-condition mechanical-content test and its retain-exemption list
(invariants, correlated constraints, security boundaries, unresolved-rationale-as-
information, responsibility boundaries, operational pitfalls, known limitations) would
restate independently.

## Reason for Change
Two governance documents independently defining "what counts as removable mechanical
content" is itself the kind of duplication this policy exists to prevent (per
`docs/00_governance_01_documentation-policy.md`'s own Claim Type Taxonomy treating a
repeated non-canonical statement as a drift risk). A future edit to one rule and not
the other would silently diverge.

## Implementation Intent
Extend `docs/00_governance_02_documentation-metadata.md`'s existing Guidelines section
with the additional distinctions the new proposal adds beyond what is already there
(the explicit 3-condition mechanical-content test, and the additional retain
categories: correlated constraints with their rationale, security boundaries, "the
absence of rationale is itself the information" case, and operational pitfalls) — do
not create a second, separately-maintained rule. `docs/00_governance_01_documentation-policy.md`
should link to this section rather than restate it, consistent with how it already
links out to `00_governance_02_documentation-metadata.md` in its Related Documents.

## Target Files or Areas
`docs/00_governance_02_documentation-metadata.md`; `docs/00_governance_01_documentation-policy.md`
(cross-reference only)

## Required Changes
- Extend the "Guidelines for Recording Information Verifiable via Implementation
  Reference" section's Decision Categories with the additional exemption cases
  (correlated constraints, security-boundary defaults, unresolved-rationale-as-
  information, operational pitfalls) not currently listed.
- Add the explicit 3-condition mechanical-content test (verifiable from code/config/
  schema alone; changes only when code changes; a wrong statement is caught by
  execution, not review) as the section's stated rationale for the existing
  Delete/Compress boundary, if not already implicit.
- Add a short cross-reference from `docs/00_governance_01_documentation-policy.md`
  pointing to this section, rather than duplicating its content there.

## Constraints
Do not change the section's existing Decision Categories table structure — extend its
rows/exemption list, do not redesign the table shape. Do not remove any existing
guidance.

## Acceptance Criteria
- `docs/00_governance_02_documentation-metadata.md`'s Guidelines section documents
  both the 3-condition test and all retain-exemption categories in one place.
- No second, independently-worded "what to delete" rule exists in
  `docs/00_governance_01_documentation-policy.md`.

## Testing Expectations
No unit/integration tests apply (documentation-only). Run `uv run python
tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` after
the edit.

## Documentation Impact
This issue's entire deliverable is the documentation update itself.

## Out of Scope
Applying the extended rule to any specific document's content — that is the
mechanical-content removal work itself, scoped separately once the docs-inventory
re-baseline issue lands.

## Dependencies
N/A: none — this is a policy-text consolidation independent of the re-baseline or ADR
decision.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Extend, do not duplicate. If any wording conflict exists between the two documents'
current text, resolve it in favor of the existing Metadata-doc section's wording and
remove the conflicting alternative, rather than keeping both.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260918-130135
- **Related target files**: docs/00_governance_02_documentation-metadata.md, docs/00_governance_01_documentation-policy.md
