# ADR-004 lacks a standard "## Known Deviations" section; Known Issue-shaped content is embedded in Implementation Notes and a non-standard duplicated heading instead

## Priority
High

## Summary
`docs/adr/ADR-004-environment-failure-handling-policy.md` does not have the standard `## Known Deviations` section that every other ADR in this project has (confirmed absent from its heading list via `grep -n "^## "`). Instead, four Known Issue-shaped entries (two "解消済み", two "報告のみ") are embedded inside `## Implementation Notes` (lines 454-455, informally) and inside a section titled `## Alignment with INV-01/INV-02`, which itself appears twice in the file (lines 353 and 461) — a heading that does not exist in this project's standard ADR section list (`00_governance_01_documentation-policy.md`: Context, Assumptions, Decision, Rationale, Alternatives Considered, Consequences, Invariants, Verification, Implementation Notes, Known Deviations, Review Triggers, Approval, Related Documents, Completion Checklist).

## Background
This issue follows a review requested in this session: classify each item in every ADR's "Implementation Notes" section against four buckets (delete — file/line/function-only description; promote to ADR/design body — explains why an order/constraint matters, and violating it risks data corruption/security issues or must hold across multiple implementations; move to Known Issue — design and implementation disagree, or the deviation's intentionality is unclear; move to Needs Confirmation — the rationale behind a value or behavior is unknown). While auditing all 13 ADRs' Implementation Notes for this classification, ADR-004 was found to have a structural deviation from the template itself, which is reported here rather than silently worked around.

## Problem
Confirmed by direct reading (`grep -n "^## " docs/adr/ADR-004-environment-failure-handling-policy.md`):
- No `## Known Deviations` heading exists anywhere in the file.
- `## Alignment with INV-01/INV-02` appears twice (line 353, inside/near Verification, and line 461, immediately after Implementation Notes) — the second occurrence is where the four Known Issue-shaped entries actually live (lines 469-472), not under any heading named `Known Deviations`.
- Two entries are marked "解消済み" (resolved) with resolution evidence (`plans/done/20260903-091417_plan.md` REQ-004, etc.) — content that is exactly what a `Known Deviations` (or its resolved-and-archived form) section is for.
- Two entries are marked "報告のみ（Known Issue未登録）" (report-only, not registered as a Known Issue) — one of these explicitly recommends registering a new Known Issue but does not do so within this ADR itself.
- Two additional single-bullet items inside `## Implementation Notes` proper (lines 454-455) describe implementation behavior with an explicit caveat about its limitations ("メモリ上の集約オブジェクトであり、`workflow.sqlite`等へ永続化されない", "固定遅延... 設定可能な試行回数を持つ汎用Retry Policyではない") — these read as Known Deviation-shaped statements (implementation is provisional / narrower than a generic policy) rather than pure "how the code implements the Decision" notes, per this issue's classification criteria ("実装が暫定状態にある").
- By contrast, `docs/adr/ADR-002-config-isolation.md` demonstrates this project's standard Known Issue entry format inside its own `## Implementation Notes` section (`### CI-001: ...` with structured `**Known Issue**`/`**Type**`/`**Summary**`/`**Conflicting Source**`/`**Expected Design**`/`**Observed Implementation**`/`**Impact**`/`**Recommended Action**`/`**Owner**`/`**Status**`/`**Resolution Target**` fields) — ADR-004's entries use a much less structured free-text format and are not under a `Known Deviations` heading at all.

## Reason for Change
A missing standard section heading is not merely cosmetic here: it means ADR-004's actual known deviations (resolved and unresolved) are not discoverable the way every other ADR's are (e.g. `docs/adr-index.md` or a future tool that greps for `## Known Deviations` across `docs/adr/*.md` would silently miss ADR-004's four entries). The two "報告のみ（Known Issue未登録）" items are explicitly flagged by the ADR's own text as needing registration but were apparently never followed up.

## Implementation Intent
Restructure ADR-004 to add a standard `## Known Deviations` section (in the position the template expects, between Implementation Notes and Review Triggers) and move the four existing entries into it, reformatting them to match ADR-002's structured Known Issue field format. Resolve the duplicate `## Alignment with INV-01/INV-02` heading by merging or renaming the two occurrences so the heading appears at most once (or is renamed if its content genuinely differs between the two locations — verify during implementation). For the two "報告のみ（Known Issue未登録）" items, either register them as proper entries in `docs/00_governance_03_issue-and-uncertainty-management.md` (per that document's Known Issue registration process) or explicitly resolve why they were left unregistered, rather than leaving the ADR's own recommendation unaddressed.

## Target Files or Areas
- `docs/adr/ADR-004-environment-failure-handling-policy.md`
- `docs/00_governance_03_issue-and-uncertainty-management.md` (if the two unregistered items are formally registered there)

## Required Changes
- Add a `## Known Deviations` section to ADR-004 in the template-standard position.
- Move all four existing Known Issue-shaped entries (currently at lines 469-472) into the new section, reformatted per ADR-002's `### {ID}: {title}` + structured field format.
- Resolve the duplicated `## Alignment with INV-01/INV-02` heading (lines 353 and 461) — merge into one occurrence, or rename one if the content is genuinely distinct (verify by reading both in full during implementation).
- Re-evaluate the two single-bullet Implementation Notes items (lines 454-455): if they describe a genuine implementation limitation distinct from a "how it's implemented" note, move them into the new Known Deviations section as well (per this issue's classification criteria, "実装が暫定状態にある").
- Register the two "報告のみ（Known Issue未登録）" items as proper Known Issues in `docs/00_governance_03_issue-and-uncertainty-management.md`, or record an explicit decision not to (with reason), rather than leaving the ADR's own "推奨する" unaddressed.

## Constraints
Do not alter the substantive resolution history recorded in the two "解消済み" entries (the plan references, dates, and resolution descriptions) — only relocate and reformat them; do not delete or reword the evidence trail.

## Acceptance Criteria
- `grep -n "^## Known Deviations" docs/adr/ADR-004-environment-failure-handling-policy.md` matches exactly once.
- `grep -c "^## Alignment with INV-01/INV-02" docs/adr/ADR-004-environment-failure-handling-policy.md` returns 1 (or the duplicate is renamed to a distinct, non-duplicate heading if genuinely different content).
- The four existing Known Issue-shaped entries appear under the new Known Deviations section, in ADR-002's structured field format.
- The two previously-unregistered "報告のみ" items either appear in `docs/00_governance_03_issue-and-uncertainty-management.md` as registered Known Issues, or the ADR records an explicit decision not to register them and why.
- `tools/check_docs_structure.py`, `tools/check_docs_quality.py`, and any other ADR-structure-checking tool in `tools/` still pass (or, if none currently checks for `Known Deviations` heading presence across all ADRs, consider whether such a check belongs in this issue's scope — see the companion issue on tooling for Implementation Notes classification, which covers this same document-structure-checking gap).

## Testing Expectations
Not applicable — documentation-only change. Run `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, and `tools/check_adr_reference.py`/`tools/check_adr_invariant_matrix.py` after the change to confirm no regression.

## Documentation Impact
This issue's entire scope is `docs/adr/ADR-004-environment-failure-handling-policy.md` and, if the two unregistered items are formally registered, `docs/00_governance_03_issue-and-uncertainty-management.md`.

## Out of Scope
- The other 12 ADRs' Implementation Notes classification — tracked in separate issues from the same review (see related issues on the common duplicate-with-Implementation-References pattern, ADR-006's transaction/monotonicity/legacy-migration notes, and ADR-007's Circuit Breaker state description).
- Re-litigating the substance of the four existing deviation entries — this issue is about their structural placement and format, not whether their resolutions were correct.

## Dependencies
N/A: none — can be implemented independently, though it is part of the same review batch as the other Implementation Notes classification issues filed alongside it.

## Unresolved Questions
Whether the two `## Alignment with INV-01/INV-02` occurrences (lines 353, 461) contain genuinely distinct content that should become two separately-named sections, or whether one is a leftover duplicate from an earlier edit that should be merged — resolve during implementation by reading both occurrences in full.

## AI Implementation Instruction
Read both `## Alignment with INV-01/INV-02` occurrences in full before deciding whether to merge or rename them. Follow ADR-002's `### CI-001: ...` structured field format exactly when moving entries into the new Known Deviations section — do not invent a different format. Do not alter the substantive content of the two "解消済み" entries' resolution evidence.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-124357
- **Related target files**: docs/adr/ADR-004-environment-failure-handling-policy.md, docs/00_governance_03_issue-and-uncertainty-management.md
