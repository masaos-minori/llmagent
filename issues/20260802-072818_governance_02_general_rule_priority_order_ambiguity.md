# Clarify whether docs/00_governance_02 General Rule's numbered list denotes priority order

## Priority
High

## Summary
The General Rule states a 3-tier canonical-source hierarchy (code > latest review document > area guide) as a numbered list, but the document never states explicitly whether the numbering represents priority order or is simply an enumeration, nor which tier wins when "latest review document" and "area guide's designated canonical source" conflict.

## Reason for Change
This is the core logic used to resolve conflicts about which document is authoritative; ambiguity here can cause conflict-resolution work to proceed in the wrong order or reach the wrong conclusion.

## Implementation Intent
Explicitly state that the numbered list is a priority order, and specify the resolution rule when tier 2 and tier 3 disagree.

## Target Files or Areas
`docs/00_governance_02_canonical-source-rule.md`

## Required Changes
- Add an explicit statement, e.g. "本リストは優先順位順であり、1が最優先。矛盾時は上位を採用する。" (confirm the intended semantics with the document owner if not already implied elsewhere before finalizing wording).

## Acceptance Criteria
The document explicitly states the numbered list is a priority order and defines the tie-break rule for tier 2 vs. tier 3 conflicts.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/00_governance_02` gains an explicit priority-order statement.

## Out of Scope
Do not change the 3 tiers themselves, only clarify their ordering semantics.

## AI Implementation Instruction
This is a genuine semantic ambiguity — if the intended answer is not confirmable from existing context, add this as a Needs Confirmation entry in `docs/00_governance_07` rather than asserting an unconfirmed interpretation as fact.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §4 強化候補 (General Ruleの優先順位), §6 Needs confirmation item (General Ruleの優先順位適用順序)
- Generated at: 2026-08-02
