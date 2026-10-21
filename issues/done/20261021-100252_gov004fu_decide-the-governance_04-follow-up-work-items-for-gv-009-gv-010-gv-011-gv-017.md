# Decide the governance_04 follow-up work items for GV-009 GV-010 GV-011 GV-017

## Priority
Low

## Summary
Resolve the contradiction in `docs/00_governance/governance_04_documentation-checks.md` between the Verification Matrix Follow-up column (`None`) and the "Follow-up Work Needed" section (open items) for GV-009, GV-010, GV-011, and GV-017, by confirming the owner's intent and making both places say the same thing.

## Background
The Verification Matrix lists `None` in the Follow-up column for GV-009, GV-010, GV-011, and GV-017. The "Follow-up Work Needed" section lists work for the same rules:

- GV-009, GV-010: automate conflict detection for unregistered prose across documents (registered claims are already checked by GV-019).
- GV-011: extend the `stale_patterns` custom rule config to cover canonical document references (the document does not say what to extend).
- GV-017: the section notes four slash-command removed-name patterns are implemented; `--check-removed-names` is not on by default (the corpus currently passes).

## Problem
Which statement is current is unknown. It depends on whether the owner still intends to automate these checks. Until decided, the document contradicts itself.

## Reason for Change
A governance document that gives two answers about the same rule cannot serve as the verification contract. Leaving the intent undecided also keeps possibly obsolete work items open.

## Implementation Intent
Ask the owner, per rule, whether the automation is still intended. Then make the matrix and the section agree:

- Intended: put a concrete Follow-up in the matrix and keep a concrete, actionable item in the section (for GV-011, state what is to be extended).
- Not intended: record the check as manual or warning-only by design and remove the item from the section.

Do not implement any automation in this issue.

## Target Files or Areas
- `docs/00_governance/governance_04_documentation-checks.md` (Verification Matrix rows GV-009, GV-010, GV-011, GV-017; "Follow-up Work Needed")

## Required Changes
- Record the owner's decision per rule (GV-009, GV-010, GV-011, GV-017).
- Update the matrix Follow-up column and the "Follow-up Work Needed" section so they are consistent.
- For each rule decided as "intended", file a separate implementation issue (not part of this issue).
- Keep the document current-specification-only: no history wording.

## Constraints
- `skills/DESIGN.md` Docs content policy and `docs/00_governance/governance_01_documentation-policy.md` Current-Specification-Only Policy apply.
- The matrix remains the single place for gate, blocking, and timing facts; do not change a rule's gate or timing here.

## Acceptance Criteria
- For each of GV-009, GV-010, GV-011, GV-017, the matrix Follow-up column and the "Follow-up Work Needed" section agree.
- Any item kept open is concrete enough to start (GV-011 names what is extended).
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, and `check_docs_content_policy.py` pass for the edited file.

## Testing Expectations
- Documentation-only: run the docs checkers listed in `routing.md` for an edited `docs/*.md` file.
- Manual review of consistency between the matrix and the section.

## Documentation Impact
Yes. Intent and follow-up status of four verification rules in `governance_04`.

## Out of Scope
- Implementing any automation or `stale_patterns` extension.
- Enabling `--check-removed-names` by default.
- Changing gates, timing, or blocking status of any rule.
- GV-016 CI wiring and the compression policy for `governance_01`/`governance_04` (separate issues).

## Dependencies
N/A: none (sibling-issue check: open issues `compat001` and `compat002` do not overlap). Related issues filed in the same batch touch `governance_04` too (GV-016 wiring, compression policy); coordinate edit order to avoid conflicts.

## Unresolved Questions
- Is automating unregistered prose conflict detection (GV-009, GV-010) still intended?
- What should be extended for GV-011's `stale_patterns` config?
- Should `--check-removed-names` become the default for GV-017?

## AI Implementation Instruction
Do not decide the owner's intent. Stop and report if no decision is recorded. Edit only `governance_04`. Do not add automation. Keep wording in the current tense.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-100252
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
