# Add a class front-matter field and resolve NC-032's additionalProperties question together

## Priority
Medium

## Summary
`docs/00_governance_01_documentation-policy.md` defines 7 document classes
(Governance, Guide, Specification, Reference, Operations, Note, Known Issues), but
`docs/00_governance_02_documentation-metadata.md`'s required front-matter fields
(title/area/tags/related) and `schemas/doc_front_matter.json` have no `class` field, so
no document's class can be determined mechanically. Add the field, and resolve the
already-tracked `NC-032` (`additionalProperties` strict-vs-permissive) in the same
change, since both touch the same schema file.

## Background
Confirmed by reading `schemas/doc_front_matter.json`: `required` lists exactly
`title`/`area`/`tags`/`related`; no `class` property exists; `additionalProperties:
true` is the current permissive setting `NC-032`
(`docs/00_governance_03_issue-and-uncertainty-management.md`) tracks as an open
question.

## Problem
Any automated process that needs to act only on Reference-class (or any specific-
class) documents — including the mechanical-content check work if it should exempt
Reference documents differently from other classes, or a future audit of Note/Known-
Issues documents for staleness — currently has no mechanical way to identify a
document's class; it requires reading each document's content.

## Reason for Change
Both the mechanical-content check work and any Reference-class migration benefit from
being able to select "all `class: Reference` documents" without manual
classification. Resolving `NC-032` alongside this change avoids a second schema edit
shortly after this one.

## Implementation Intent
Add `class` as an optional (not required, to avoid a breaking migration for all
currently-existing documents at once) enum field to `schemas/doc_front_matter.json`,
with the 7 values from `docs/00_governance_01_documentation-policy.md`'s Document
Classification. Add a new `tools/manage_frontmatter.py` subcommand that assists
classification, following the existing `add-missing` subcommand's "never guess, report
ambiguous" pattern (and the existing `rename-category-to-area` subcommand as the
precedent for adding a new front-matter key programmatically) rather than silently
guessing every document's class. Resolve `NC-032` by deciding `additionalProperties`
in the same change, since adding a new known property is the natural point to also
decide whether to close off unknown ones.

## Target Files or Areas
`schemas/doc_front_matter.json`; `tools/manage_frontmatter.py`;
`docs/00_governance_02_documentation-metadata.md`;
`docs/00_governance_03_issue-and-uncertainty-management.md`

## Required Changes
- Add an optional `class` property to `schemas/doc_front_matter.json` with an enum of
  the 7 documented classes.
- Decide and set `additionalProperties` (`true` or `false`) in the same schema edit,
  resolving `NC-032`.
- Add a `tools/manage_frontmatter.py` subcommand (e.g. `classify` or `add-class`) that
  infers `class` where confidently derivable (e.g. from existing area-guide/heading
  conventions) and reports the rest as ambiguous, following `add-missing`'s existing
  pattern — never silently guessing.
- Document the new optional `class` field in
  `docs/00_governance_02_documentation-metadata.md`'s "Recommended Additional Fields"
  section, alongside the existing `status` field.
- Remove `NC-032` from the active Needs Confirmation inventory once
  `additionalProperties` is decided, per that document's own removal policy.

## Constraints
`class` must be optional, not required — do not force every currently-existing
document to gain the field in this issue; that is a separate, larger classification
effort. If the Reference-class ADR is still unresolved when this issue is
implemented, use its shared premise (a `Reference` class exists) rather than waiting —
the enum values themselves don't depend on which option that ADR picks.

## Acceptance Criteria
- `schemas/doc_front_matter.json` accepts a valid `class` value from the documented
  7-class enum and rejects an invalid one.
- `NC-032` no longer appears in
  `docs/00_governance_03_issue-and-uncertainty-management.md`'s active inventory.
- `tools/manage_frontmatter.py`'s new subcommand runs against the current `docs/` tree
  in a dry-run/report mode without modifying any file, and reports which documents it
  could not confidently classify.

## Testing Expectations
Add unit tests for the new `manage_frontmatter.py` subcommand covering a confidently-
classifiable case and an ambiguous case. Run `uv run python tools/check_docs_structure.py`
after the schema change to confirm `check_schema_compliance` still passes against
documents that now optionally carry `class`.

## Documentation Impact
Update `docs/00_governance_02_documentation-metadata.md`'s Recommended Additional
Fields section (new `class` field) and
`docs/00_governance_03_issue-and-uncertainty-management.md` (remove `NC-032`).

## Out of Scope
Actually classifying all existing documents — this issue adds the field and the
assistive tooling only; a bulk-classification pass is separate follow-up work.

## Dependencies
Loosely related to the Reference-class ADR issue (see Constraints) but not blocked by
it.

## Unresolved Questions
N/A: none — the schema gap, the required NC-032 decision, and the existing tool
precedents were all directly confirmed.

## AI Implementation Instruction
Keep `class` optional. Do not attempt to classify all existing documents in this
issue. Decide `additionalProperties` explicitly (state the choice and a one-line
reason) rather than leaving it as a follow-up — this issue is the natural point to
close `NC-032`, per Reason for Change.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260918-130249
- **Related target files**: schemas/doc_front_matter.json, tools/manage_frontmatter.py
