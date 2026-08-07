# Reduce diff-memo-style detail in docs/05_agent_90_inconsistencies_and_known_issues.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-agent-review.md` to `docs/05_agent_90_inconsistencies_and_known_issues.md`: keep the operational meaning of each known issue and its fix-judgment criteria; remove bare code-diff memos and "confirmed at file:line" notes with no operational framing.

## Reason for Change
This chapter is the canonical source for known issues and unresolved items (per `memo-doc-agent-review.md` §「章間の正本ルール」: 既知問題・未解決事項 = `05_agent_90_inconsistencies_and_known_issues`), but a Known Issues section that degrades into a plain bug list or diff memo loses its value as an operational/decision reference, per this same memo's explicit prohibition (§「禁止事項」: Known Issues を単なるバグ一覧にすること).

## Implementation Intent
Restructure each entry to explain: what the issue means, why it is a problem, what operators should watch for, and the criteria for deciding whether/how to fix it — not just "diff observed at file X line Y."

## Target Files or Areas
`docs/05_agent_90_inconsistencies_and_known_issues.md`

## Required Changes
- Keep: the meaning of each known issue, why it is a problem, operational cautions, fix-decision criteria, the classification of items as removed/migrated/needs-confirmation, and the reasoning behind each Needs Confirmation entry.
- Remove or compress: bare code-diff memos, "confirmed at file X line Y" notes with no accompanying operational meaning, plain implementation-visible enumerations.
- Before removing any entry, verify against current code per `rules/coding.md` §「Documentation notes — "Current behavior" classification」 whether the discrepancy still applies; do not delete a note without this verification.
- Cross-reference actual bug-track issues under `issues/` where an "Implementation fix required" classification applies, rather than duplicating the description inline.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-agent-review.md` §「修正後の章構成テンプレート」 where applicable to a known-issues chapter.
- No entry is a bare diff memo or unexplained file:line note; each has stated operational meaning.
- Every entry is classified per `rules/coding.md`'s five-way classification (Accepted current specification / Implementation fix required / Documentation fix required / Issue already tracked / Obsolete and removable) before being kept, cross-referenced, fixed, or deleted.

## Testing Expectations
Not required for behavior (documentation-only). Run `python tools/check_agent_docs_consistency.py` after editing (includes the obsolete diagnostics/event-name reference check relevant to this chapter).

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/05_agent_*.md` chapters.
- Fixing the underlying code issues themselves (file separate issues under `issues/` per the "Implementation fix required" classification if discovered during this cleanup).

## AI Implementation Instruction
Follow `memo-doc-agent-review.md` §「05_agent_90_inconsistencies_and_known_issues」 and `rules/coding.md`'s "Current behavior" classification table. Do not silently delete a discrepancy note without first verifying against current code that it no longer applies. If a new "Implementation fix required" item is discovered, file it as a separate issue under `issues/` rather than only noting it here. Mark unclear items as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-agent-review.md` §「05_agent_90_inconsistencies_and_known_issues」
- Generated at: 2026-08-05
