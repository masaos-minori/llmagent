# Rewrite docs/00_governance_08 as a completion record instead of a stale "in-progress" migration plan

## Priority
Medium

## Summary
`docs/00_governance_08_known-issues-migration-plan.md` is still written as a forward-looking plan, but git history and the actual Known Issues files show the described 5-area (RAG/MCP/Agent/EventBus/Shared) migration was completed on 2026-07-23 (commit `7b04065c`), leaving the plan document in contradiction with the current state of the repository.

## Reason for Change
A "plan" document describing already-completed work risks misleading readers into thinking work remains to be done. Stale pre-migration format details and priority ordering no longer have operational value in their current framing.

## Implementation Intent
Convert the document from a plan to a completion record: add an explicit status field, remove or annotate sections that only made sense pre-migration, generalize the reusable parts (Migration Policy, Priority Criteria) so they serve future similar migrations, and replace duplicated file listings with a reference to `docs/00_index.md`.

## Target Files or Areas
`docs/00_governance_08_known-issues-migration-plan.md`

## Required Changes
- Add a `Status: Completed (2026-07-23)` field near the top, and reword the introduction to describe the migration as completed, not planned.
- Delete "Current Format Summary" (pre-migration format details, ~lines 23-61) — historical detail already lives in each file's own migration notes.
- Either delete "Suggested Migration Order" (~lines 85-93) as no-longer-relevant, or — if kept — annotate it as "proposal at time of writing; actual execution was a single combined commit (`7b04065c`), not staged in this order" (confirm via `git log` before choosing).
- Add a note to "Migration Policy" that it was the policy adopted for the 2026-07-23 RAG/MCP/Agent/EventBus/Shared migration.
- Update "Risks" and "Acceptance Criteria for Future Migration" to record verification results for the completed migration (e.g. confirm each of the 5 files' migration notes record source format and migration date) rather than framing them as future-only concerns.
- Generalize "Priority Criteria" (~lines 74-83) to remove area-specific framing, presenting the 6 criteria as reusable general principles for prioritizing future documentation migrations.
- Replace the "Target Files" list and the "Related Governance Documents" file enumeration with a reference to `docs/00_index.md`'s existing known-issues file listing.

## Acceptance Criteria
The document's status (completed vs. planned) is unambiguous from its opening lines; no section describes a hypothetical future state that has already happened; file listings are not duplicated with `docs/00_index.md`.

## Testing Expectations
Not required (documentation-only). Manually verify the 2026-07-23 completion claim against `git log` and the 5 target files' migration notes before finalizing.

## Documentation Impact
`docs/00_governance_08` substantially restructured; no changes to `docs/00_index.md` required beyond the reference already existing there.

## Out of Scope
Do not alter `docs/00_index.md`'s own known-issues listing in this issue. Do not change the actual Known Issues files or their migration notes.

## AI Implementation Instruction
Verify the completion claim and commit reference against `git log` before writing the Status field. Preserve the Migration Policy and Risks content's substance — only reframe from future-tense to completed/reusable framing.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §1 (連結文書としての問題 item 2), §2 削除候補 items 2-3, §3 要約候補 items 6-7, §4 強化候補 (Migration Policy, Risks/Acceptance Criteria), §5 例4, §6 Needs confirmation items (文書ステータス, Suggested Migration Orderとコミットの整合性)
- Generated at: 2026-08-02
