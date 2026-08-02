# Simplify docs/01_overview-files-04-shared-part1.md file listing and document the 3-DB separation rationale

## Priority
Medium

## Summary
`docs/01_overview-files-04-shared-part1.md` (~lines 33-46) contains a manually-maintained file listing that currently matches actual source (not yet stale) but carries the same ongoing drift risk as other reviewed file-listing sections. Separately, the file states that state is split across `rag.sqlite`/`session.sqlite`/`workflow.sqlite` (~lines 29-31) without explaining why 3 separate databases were chosen instead of one.

## Reason for Change
Even though this listing is currently accurate, the pattern of drift confirmed elsewhere in this document set shows the maintenance cost of manual file listings is not justified. The 3-DB split is described as the most important "where is the source of truth" information in the file, but its design rationale (lock-contention avoidance vs. concern separation vs. something else) is undocumented, risking an uninformed consolidation in the future.

## Implementation Intent
Replace the manual file listing with a pointer to the implementation tree. Add the 3-DB separation rationale once confirmed with the document's author/designer.

## Target Files or Areas
`docs/01_overview-files-04-shared-part1.md`

## Required Changes
- Replace the file listing (~lines 33-46) with a pointer to `scripts/shared/` for the current file list, keeping only the design-intent summary already present.
- Confirm the actual reason for the 3-DB split (lock-contention avoidance, backup-unit separation, schema independence, or another reason) — if not confirmable from source/commit history, register it as a Needs Confirmation item in `docs/00_governance_07` rather than asserting a guessed rationale.
- Once confirmed, add a sentence stating the rationale, e.g. "The 3-DB split avoids lock contention between data with different write frequencies (session state, workflow state, RAG index)."

## Acceptance Criteria
The file listing is replaced with an implementation-tree pointer; the 3-DB separation rationale is either documented (if confirmed) or explicitly tracked as a Needs Confirmation item (if not).

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/01_overview-files-04-shared-part1.md` updated; possibly `docs/00_governance_07` gains one new NC entry if the rationale cannot be confirmed.

## Out of Scope
Do not change the actual database schema or split in this issue — documentation only.

## AI Implementation Instruction
Do not assert a guessed rationale for the 3-DB split as fact. Check commit history/design docs first; if genuinely unconfirmable, register it as a Needs Confirmation item instead of writing a plausible-sounding but unverified explanation.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §2 削除候補 item 5, §4 強化候補 (files-04-shared-part1), §6B (rag.sqlite/session.sqlite/workflow.sqliteの3DB分離理由)
- Generated at: 2026-08-02
