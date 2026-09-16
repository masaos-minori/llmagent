# Assign owners, resolution targets, and confirmed discovery dates to all active entries

## Priority
Medium

## Summary
Most active entries in both Part 1 and Part 2 of `docs/00_governance_03_issue-and-uncertainty-management.md` carry `Owner: Unassigned` or `Assigned To: Unassigned`, and many carry `First Found: Unconfirmed`, leaving the Resolution Rules with no accountable party and no way to measure whether the inventory is draining.

## Background
This issue is derived from a consolidated audit of the governance documentation set recorded in `memo3.md` (repository root) — an 18-item review of `docs/00_governance_03_issue-and-uncertainty-management.md` and related documents, later consolidated into 9 issues. No further background beyond the Summary and Reason for Change is needed.

## Problem
`Owner: Unassigned` appears on CI-001, CI-003, CI-007 through CI-016, EVENTBUS-001, EVENTBUS-002, and EVENTBUS-005 through EVENTBUS-007. `Assigned To: Unassigned` appears on the majority of NC-021 through NC-035. `First Found: Unconfirmed` appears on CI-003, CI-007 through CI-016, EVENTBUS-001, EVENTBUS-002, and EVENTBUS-005 through EVENTBUS-007. Confirmed dates exist for contrast: CI-001 and RAG-005 at `2026-08-22`, RAG-006 at `2026-09-13`.

## Reason for Change
These are batched because both require the same operation — a single sweep across every active entry in both parts, touching the same fields on the same records. Splitting them would mean walking the entire inventory twice.

**Ownership.** The Resolution Rules are specific about what closes an entry: a Known Issue is resolved only when implementation and design agree, or design is formally changed; a Needs Confirmation entry is removed only after evidence establishes intent and the canonical source is updated. Neither can happen without someone responsible for making it happen. The document already establishes that `Unassigned` is not an acceptable terminal state — the Temporary Exception Process requires an owner to be "a specific person, not `Team` or `Unassigned`." Applying a weaker standard to the inventory than to its own exception process is inconsistent.

The shape of the backlog is the clearest symptom. CI-008 through CI-016 are nine structurally identical entries, all "ADR invariant verified by code inspection, but no automated test." They accumulated one at a time, all unassigned, and none has moved. That is not nine independent oversights; it is a systemic gap in ADR-to-test traceability that no one owns. Assigning nine separate owners would miss the point — this is one initiative.

**Discovery dates.** Without a date there is no way to distinguish an issue filed last week from one that has sat for months, no way to sort by age, and no way to tell whether the inventory is growing or shrinking. It is also a small but systematic Evidence-Required Rule violation: `Unconfirmed` is a placeholder for evidence that was never gathered, and it has been copied forward into every new entry that followed the pattern.

## Implementation Intent
Make every active entry accountable and measurable, so that the Resolution Rules have someone to bind and the backlog has a shape that can be reported on.

For ownership, recover assignments from the RACI Model and repository history where possible. Where an owner genuinely cannot be determined, leave an explicit `TODO(owner)` marker and report it for human assignment rather than assigning arbitrarily — a wrong owner is worse than a flagged gap, because it looks resolved.

For CI-008 through CI-016, treat them as one initiative with one owner and a shared resolution target, rather than nine assignments. The natural framing is an ADR-invariant test suite, and the batching decision should be recorded in the document so the reasoning survives.

For dates, recover from repository history, the 2026-09-03 consolidation record, or the originating issue files. Where recovery genuinely fails, use the consolidation date as a lower bound and annotate it explicitly as such, so it is never mistaken for the true discovery date.

## Target Files or Areas
- `docs/00_governance_03_issue-and-uncertainty-management.md`

## Required Changes

**Ownership**
- Assign a named owner to every active entry in Part 1 and Part 2.
- Add a `Resolution Target` field to each Part 1 entry, matching Part 2's existing field.
- Treat CI-008 through CI-016 as a single batched initiative with one owner and one shared resolution target, and record that decision in the document.
- Establish a periodic review cadence and document it.

**Discovery dates**
- Recover dates from repository history, the 2026-09-03 consolidation record, or the originating issue files.
- Replace `Unconfirmed` with the recovered date.
- Where recovery fails, use the consolidation date as an explicitly annotated lower bound.

## Constraints
- `Team` is acceptable only where the entry already uses it and no individual can be identified.
- Do not resolve or close entries as a shortcut to reducing the assignment count.
- Do not invent owner names.
- Do not guess dates.
- Annotate every lower-bound date so it cannot be mistaken for the true discovery date.
- Use the same date format as existing confirmed entries.
- Run this sweep after the other content-fixing issues remove or reclassify entries, so owners are not assigned to doomed records.

## Acceptance Criteria
- [ ] No active entry in Part 1 or Part 2 has `Unassigned`, except where a `TODO(owner)` marker was left and reported.
- [ ] Every Part 1 entry has a `Resolution Target`.
- [ ] The CI-008 through CI-016 batching decision is recorded in the document.
- [ ] A periodic review cadence is documented.
- [ ] No active Part 1 entry has `First Found: Unconfirmed`.
- [ ] Every substituted lower-bound date is annotated as such.
- [ ] No entry was resolved or closed as part of this sweep.

## Testing Expectations
Not required for code — documentation-only change with no behavior impact. Manually verify each Acceptance Criteria item by reading the edited sections, and run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` to confirm no new structural findings.

## Documentation Impact
Yes. `docs/00_governance_03_issue-and-uncertainty-management.md` gains a `Resolution Target` field on every Part 1 entry, named owners in place of `Unassigned`, confirmed or annotated-lower-bound discovery dates in place of `Unconfirmed`, a recorded CI-008–CI-016 batching decision, and a documented periodic review cadence. No other document is affected.

## Out of Scope
- Resolving any individual entry.
- Writing the ADR-invariant tests for CI-008 through CI-016.
- Changing any field other than owner, resolution target, and discovery date.

## Dependencies
Run after the entry-content issues (self-contradiction fix, status-vocabulary fix, RAG-entries fix, ADR-010 registration, EventBus reconciliation) so owners are not assigned to entries that end up removed or reclassified. `memo3.md`'s suggested Execution Order places this eighth, after the other content issues.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Do not rewrite unrelated files. Delete resolved entries recorded in `docs/00_governance_03_issue-and-uncertainty-management.md` rather than retaining them with a closed-out status, per that document's Current-Specification-Only Policy. Do not invent owner names or dates — where history cannot resolve them, leave a `TODO(owner)` marker or an annotated lower-bound date and report which entries require human input.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260915-200530
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
