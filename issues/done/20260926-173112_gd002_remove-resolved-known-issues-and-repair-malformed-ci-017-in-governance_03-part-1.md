# Remove resolved Known Issues and repair malformed CI-017 in governance_03 Part 1

## Priority
Medium

## Summary
Part 1 (Known Issues) of `docs/00_governance/governance_03_issue-and-uncertainty-management.md` retains two entries whose `Status=resolved`: CI-017 and CI-018. Both must be removed from the Active Items inventory per the document's Current-Specification-Only policy, and CI-017 additionally carries duplicated and out-of-order fields that must be repaired (or removed along with the entry).

## Background
The document states in Part 1 ("An item is removed from this active inventory once it is resolved or no longer applies to the current system") and restates it in the resolution rules. Active Items follow an ID-group ordering convention (DESIGN-*, EVENTBUS-*, SHARED-*, CI-*). CI-017 and CI-018 are both marked `Status=resolved` yet still appear in the Active Items list, contradicting that rule.

## Problem
- CI-017 (`docs/rag_04_04_dto-models_config.md` DTOs no longer exist): `Status=resolved` but present in Active Items. Its body is also malformed — `Recommended Action` and `Resolution Target` each appear twice (the second set duplicated after an `Impact` line that sits out of field order), indicating a botched edit.
- CI-018 (RAG exception hierarchy fragmented): `Status=resolved` but present in Active Items. Structurally intact but should not be in the active inventory.

Both violate the removal-on-resolution rule; CI-017 additionally produces a malformed entry.

## Reason for Change
An "active" inventory that keeps resolved entries misrepresents what still needs attention and directly contradicts the document's own governing rule. CI-017's duplicated fields also make the entry internally inconsistent and harder to parse by tooling that reads the field list.

## Implementation Intent
Delete the CI-017 and CI-018 entries from Part 1 Active Items, removing their trailing separator blank lines so the surrounding entries join cleanly. Because deletion removes the malformed CI-017 entirely, no separate field-order repair is needed; if instead the intent were to retain CI-017, deduplicate the repeated `Recommended Action`/`Resolution Target` fields and restore canonical field order (`... Impact → Recommended Action → Resolution Target`). Do not move resolved items to another section — the Current-Specification-Only Policy calls for removal, not relocation.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` — Part 1 (Known Issues) Active Items only

## Required Changes
- Remove the CI-017 entry (including its field list and trailing blank-line separators).
- Remove the CI-018 entry (including its field list and trailing blank-line separators).
- Verify no other Active Items entry carries `Status=resolved` (or another inactive/resolved value); remove any found under the same rule.

## Constraints
- Remove only entries whose `Status` is `resolved`. Leave all `open` and `deferred` entries in place.
- Preserve the ID-group ordering convention of the remaining CI-* entries.
- Do not modify Part 2 (Needs Confirmation), Part 3, or Part 4.
- Do not add new entries or rewrite existing entries' content.

## Acceptance Criteria
- No Part 1 Active Items entry has `Status=resolved`.
- CI-017 and CI-018 are absent from the document.
- All `open`/`deferred` entries are unchanged except for adjacency after the deletions.

## Testing Expectations
Not required (documentation-only). Optionally run `uv run python tools/check_docs_structure.py docs/00_governance/*.md` to confirm no new structural findings.

## Documentation Impact
This issue is itself the documentation update. No downstream artifact consumes Part 1 beyond human review and the known-issue checks.

## Out of Scope
- Resolving the underlying RAG/code matters behind CI-017 or CI-018.
- Changing the lifecycle/status vocabulary.
- Editing any part other than Part 1 Active Items.
- Editing any other governance document.

## Dependencies
- N/A: none (independent of the NC/data-quality investigation in the companion governance_03 issue).

## Unresolved Questions
- Were CI-017 and CI-018 resolved because the underlying documentation mismatch was actually fixed, or merely marked resolved administratively? Either way the removal rule applies, so this does not block the change; record the cause in your completion notes.

## AI Implementation Instruction
Edit only Part 1 Active Items of `docs/00_governance/governance_03_issue-and-uncertainty-management.md`. Delete the CI-017 and CI-018 entries and their trailing separator blank lines so neighboring entries join without extra gaps. Do not touch any other section or entry. If you find another entry with `Status=resolved`, remove it too and report it; otherwise leave every other entry untouched.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260926-173112
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
