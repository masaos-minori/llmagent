# Add a review checklist that separates compatibility, migration, and fallback changes

## Priority
Low

## Summary
Add one review checklist that asks, for any change that adds backward compatibility, a data migration, or a runtime fallback, the questions specific to that kind of change, and that prevents a fallback from being filed as compatibility. Place the checklist in a single canonical location and reference it from the other review documents.

## Background
- Source: an investigation of the design documents dated 2026-10-20 that listed backward-compatibility features. It read documents only; the facts below were re-checked against the current rules and skills on 2026-10-20.
- The Glossary in `docs/00_governance/governance_02_documentation-metadata.md` already defines Backward Compatibility, Migration, Operational Fallback, Obsolete, and Dead Code as distinct terms, and says a fallback is a live per-call runtime decision, distinct from a static compatibility property. (Explicit in code: read from the document)
- The governance review rule in `governance_01_documentation-policy.md` lists the changes that need review (for example, any change that removes or renames a documented feature) and the merge conditions. It has no item that asks what a compatibility or migration change must record. (Explicit in code: read from the document)
- `skills/python-code-review/workflow.md` reviews correctness, data consistency, architecture, resource lifecycle, errors and configuration, tests, and documentation mismatches. A search of `skills/` and `rules/` for compatibility, migration, sunset, or expiry questions finds none beyond a pointer to the database documents. (Explicit in code: absence verified by search)
- The related issues in this set show the cost of the gap: a compatibility layer with no known caller, an unused legacy helper, an alias with no stated status, and migrations with no recorded baseline.

## Problem
Nothing prompts a reviewer or an implementer to ask who uses a new compatibility layer, when it ends, or how a migration preserves data and rolls back. A runtime fallback can also be mistaken for compatibility, or the reverse, because the review questions are not written down where reviews happen.

## Reason for Change
A short checklist applied at review time is cheaper than finding unowned compatibility code months later. Making each kind of change answer its own questions keeps compatibility, migration, and fallback from drifting into each other and gives later cleanup a recorded owner and end condition.

## Implementation Intent
- Write the checklist once, in the document where design and code reviews already look, and make the other documents point to it.
- Compatibility: owner, known consumers, how the end is decided, how use is observed, and the test that proves the old path and its removal.
- Migration: source version, target version, how existing data is preserved, how a failure is recovered, and the condition under which the migration is removed.
- Fallback: confirm that a runtime alternate path is not being introduced as compatibility, and that it has the failure policy the relevant decision requires.
- Keep each list short enough to apply during a review.

## Target Files or Areas
- `skills/python-code-review/workflow.md` (candidate canonical location; Phase 2 and Phase 3)
- `skills/python-design/workflow.md` (a pointer for design-time use)
- `docs/00_governance/governance_01_documentation-policy.md` (a pointer from the review rule, if the owner wants it there)
- `docs/00_governance/governance_02_documentation-metadata.md` (read only; the term definitions the checklist relies on)

## Required Changes
- Decide the one canonical location for the checklist; the candidate is the code review workflow.
- Write the three short checklists (compatibility, migration, fallback) in that location.
- Add a pointer from the design workflow, and from the governance review rule if chosen, instead of copying the lists.
- Update `routing.md` only if the canonical location changes how the review task loads its files.
- Run the skill and rule reference checks listed below.

## Constraints
- State each rule in one place only; other documents reference it (`AGENTS.md` Global Rule 5 treats single statements as canonical).
- A change to `skills/*.md` that revises a procedure is not a documentation task for `python-documentation`; follow the exception stated in `routing.md`.
- Do not add a new document type or a new checker in this issue.
- Written in English, in line with the existing skills.

## Acceptance Criteria
- The compatibility, migration, and fallback checklists exist in exactly one canonical location.
- The design workflow, and the governance review rule if chosen, point to it without repeating the lists.
- The checklists use the Glossary terms and do not redefine them.
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` pass.
- If a `docs/` file changed, the documentation checkers pass.

## Testing Expectations
- Not required for code: documentation and procedure change.
- Run `uv run python tools/check_skills_references.py`, `uv run python tools/check_skills_heading_cycles.py`, and, if a `docs/` file changed, `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, and `uv run python tools/check_docs_content_policy.py --strict`.

## Documentation Impact
Yes. Add the checklists (intent and constraints for reviewers) in one canonical skill location and the pointers elsewhere. No history of why the checklist was added is written into current documents.

## Out of Scope
- Making the checklist a CI check, or adding enforcement tooling (`compat007` covers the exception manifest).
- Changing the Glossary term definitions (`compat009` covers its examples).
- Reviewing any specific existing compatibility item.

## Dependencies
- Related: `compat007` tracks exceptions and owners mechanically; this checklist is the review-time counterpart and can be done independently.
- Sibling-issue check: no open issue under `issues/` touches `skills/python-code-review/` or `skills/python-design/`.

## Unresolved Questions
- Which location should be canonical: the code review workflow, the design workflow, or the shared design rules? (Needs confirmation; the owner chooses)
- Should the governance review rule also reference the checklist?

## AI Implementation Instruction
- Write each list once and reference it elsewhere; do not copy the lists into several files.
- Do not change the Glossary definitions or add enforcement tooling.
- Follow the procedure-edit exception in `routing.md`; do not apply the documentation skill's code-documentation phases to a workflow edit.
- Run the reference and cycle checks before finishing.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261020-123444
- **Related target files**: `skills/python-code-review/workflow.md`, `skills/python-design/workflow.md`, `docs/00_governance/governance_01_documentation-policy.md`, `docs/00_governance/governance_02_documentation-metadata.md`
