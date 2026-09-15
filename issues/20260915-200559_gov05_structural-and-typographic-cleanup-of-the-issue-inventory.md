# Structural and typographic cleanup of the issue inventory

## Priority
Low

## Summary
Four mechanical defects in `docs/00_governance_03_issue-and-uncertainty-management.md` and related governance documents: a misplaced entry in the Active Items sequence, an unexplained gap in the CI identifier series, a malformed field indentation in NC-033, and inconsistent capitalization of issue identifiers.

## Background
This issue is derived from a consolidated audit of the governance documentation set recorded in `memo3.md` (repository root) — an 18-item review of `docs/00_governance_03_issue-and-uncertainty-management.md` and related documents, later consolidated into 9 issues. No further background beyond the Summary and Reason for Change is needed.

## Problem
`SHARED-001` sits between `EVENTBUS-007` and `EVENTBUS-008`, breaking the otherwise area-grouped sequence. The CI series runs CI-001, CI-003, CI-004 — with no CI-002 entry and no removal placeholder, unlike CI-004/005/006 which each have one. NC-033's `Blocking` field carries a leading space, rendering it as a nested list item under `Resolution Target` instead of a sibling field. `Ci-001` and `Ci-005` appear in place of `CI-001` and `CI-005`, and at least one instance of `First Foun` appears in place of `First Found`.

## Reason for Change
These are batched because every one is a whitespace-, ordering-, or spelling-level edit requiring no external verification, and because reviewing four such changes in one pass costs far less than four separate reviews. None changes the meaning of any entry.

**Ordering.** The `SHARED-001` misplacement obscures whether `EVENTBUS-008` belongs to the EventBus group and produces noisier diffs than necessary when entries are added or removed nearby.

**CI-002.** The document's disposal convention relies on placeholders precisely so that "resolved and removed" can be distinguished from "never existed," and a bare gap defeats it. The gap also leaves the identifier open to accidental reuse.

**NC-033 indentation.** Visually this is nearly invisible, but a field-extracting parser will either miss the field or bind it to the wrong parent — at which point NC-033 appears to omit one of the fifteen required fields. This matters directly to the automated-conformance-check issue, which will parse exactly this structure.

**Identifier capitalization.** These typos break case-sensitive grep and any reference resolution that matches identifiers exactly — which is to say, they will break the referential-integrity check the moment it is deployed.

## Implementation Intent
Eliminate the mechanical defects that would otherwise produce false positives or false negatives when the automated conformance check runs, and record the ordering convention so that future entries do not reintroduce the same drift.

The sequencing matters: this issue should land before or alongside the conformance-check issue, because the NC-033 indentation and the identifier capitalization would both cause that check to report misleading results.

## Target Files or Areas
- `docs/00_governance_03_issue-and-uncertainty-management.md`
- `docs/adr/ADR-002-config-isolation.md`
- `docs/adr/ADR-013-eventbus-authentication-authorization.md`
- `issues/done/` (for CI-002 history recovery)

## Required Changes

**Ordering**
- Move `SHARED-001` after the EventBus group, or adopt and apply a documented ordering rule throughout.
- State the ordering convention explicitly in the Active Items section.

**CI-002**
- Determine CI-002's history from repository history or `issues/done/`.
- If it existed and was resolved, add a removal placeholder in the established form.
- If it was never allocated, add a short note recording that so the gap is explained.

**NC-033**
- Remove the leading space before `- **Blocking**: No`.
- Scan both Part 1 and Part 2 for any other indentation anomaly and normalize.

**Identifiers**
- Correct `Ci-001` -> `CI-001` and `Ci-005` -> `CI-005` wherever they appear, including in ADR documents.
- Correct `First Foun` -> `First Found`.
- Grep for other case-inconsistent identifier forms across `docs/` and correct them.

## Constraints
- Do not alter any entry's content while reordering — move headings and bodies as whole units.
- Do not reuse CI-002 for a new issue.
- Do not fabricate a resolution narrative for CI-002; if history is unavailable, record that.
- Whitespace and spelling only for NC-033 and the identifier corrections — do not alter field values.
- Keep the reordering in its own commit so the diff remains reviewable.

## Acceptance Criteria
- [ ] Active Items follow a stated, consistent order.
- [ ] The ordering rule is documented in the section.
- [ ] No entry content changed during reordering.
- [ ] The CI-002 gap is explained in the document.
- [ ] No new entry is assigned the CI-002 identifier.
- [ ] NC-033's `Blocking` field is at the same indentation level as its other fields.
- [ ] All Part 2 entries expose exactly fifteen top-level fields to a parser.
- [ ] No occurrence of `Ci-` remains where `CI-` is meant.
- [ ] No occurrence of `First Foun` remains.

## Testing Expectations
Not required for code — documentation-only change with no behavior impact. Manually verify the file parses identically apart from ordering, and confirm the NC-033 fix with a parser that counts top-level fields per entry (e.g. the referential-integrity check from the conformance-check issue, once available), not by visual inspection alone.

## Documentation Impact
Yes. `docs/00_governance_03_issue-and-uncertainty-management.md` gains a documented ordering convention, a CI-002 gap explanation, corrected NC-033 indentation, and corrected identifier capitalization. `docs/adr/ADR-002-config-isolation.md` and `docs/adr/ADR-013-eventbus-authentication-authorization.md` receive the same identifier-capitalization correction where applicable.

## Out of Scope
- Resolving NC-033's underlying question about `lang` field enforcement.
- Auditing identifier gaps in series other than `CI-*`.
- Any content or field-value change.

## Dependencies
This issue should land before or alongside the automated-conformance-check issue, since the NC-033 indentation and identifier-capitalization defects would cause that check's first run to report misleading results. `memo3.md`'s suggested Execution Order places this first, ahead of every other issue in the set, for exactly this reason.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Do not rewrite unrelated files. Delete resolved entries recorded in `docs/00_governance_03_issue-and-uncertainty-management.md` rather than retaining them with a closed-out status, per that document's Current-Specification-Only Policy. Move headings and their bodies as whole units and verify the file parses identically apart from ordering. Confirm the NC-033 fix with a parser that counts top-level fields per entry, not by visual inspection. Search history before writing the CI-002 note, and report "history unavailable" rather than inventing a cause.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260915-200559
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md, docs/adr/ADR-002-config-isolation.md, docs/adr/ADR-013-eventbus-authentication-authorization.md
