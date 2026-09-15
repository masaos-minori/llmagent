# Remove the redundant file/class/config/test listing in each ADR's Implementation Notes — it duplicates the same ADR's own Related Documents > Implementation References

## Priority
Medium

## Summary
Every one of the 13 ADRs in `docs/adr/` opens its `## Implementation Notes` section with a near-identical four-item list (実装ファイル / 主要ClassまたはFunction / 設定ファイル・設定Key / 対応するテスト), immediately followed by the boilerplate line "この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。" This boilerplate itself says the API/Class/Function detail belongs in Implementation Reference — yet the same ADRs also carry a `### Implementation References` subsection under `## Related Documents` that duplicates the same file/symbol list. Per this session's classification criteria (delete: file/line/function-only description; is fully derivable by reading the source; becomes stale on implementation change), this four-item list is a "delete" candidate in every ADR that has one.

## Background
This issue follows a review requested in this session: classify each item in every ADR's Implementation Notes section against four buckets (delete / promote to ADR-Decision-or-design-body / move to Known Issue / move to Needs Confirmation). This issue covers the one pattern common to all 13 ADRs — the redundant file/class/config/test list — while ADR-specific findings (ADR-004's missing Known Deviations section, ADR-006's transaction/monotonicity/legacy-migration notes, ADR-007's Circuit Breaker state description) are filed as separate, more targeted issues from the same review.

## Problem
Confirmed by direct reading of all 13 files under `docs/adr/`:
- `ADR-001` through `ADR-014` (excluding none) each have an `## Implementation Notes` section starting with a bulleted list of 実装ファイル / 主要Class・Function / 設定ファイル・Key / 対応するテスト (ADR-012/013 use an English equivalent: "Implementation files" / "Key symbols" / "Corresponding tests").
- Every one of these ADRs also has a `### Implementation References` subsection under `## Related Documents` listing the same or a near-identical set of files and symbols (confirmed for ADR-001, ADR-002, ADR-004 by direct reading; the pattern is structurally identical across the template, so the same duplication is expected in the remainder — verify each file individually during implementation rather than assuming).
- The boilerplate sentence immediately following the list in every ADR ("この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。" / the English equivalent) already states that this detail's canonical home is Implementation Reference, not Implementation Notes — meaning the list's presence in Implementation Notes directly contradicts the ADR's own stated intent for that section.
- This list satisfies every "delete" criterion from this review: it is describable purely by file name/function name, it is derivable by reading the source, and it becomes stale the moment a referenced file is renamed or a function is renamed/removed (with no mechanism currently enforcing the two copies stay in sync — `tools/check_adr_reference.py` only checks that a cited *source file* contains an ADR-ID backreference, it does not check that the two lists inside the same ADR match each other).

## Reason for Change
Maintaining the same file/symbol list in two places within one document is pure duplication with no benefit and a real cost: a future rename or removal must be applied twice, and nothing currently catches a drift between the two copies. The ADR's own boilerplate already states Implementation Reference is the intended home.

## Implementation Intent
Remove the four-item file/class/config/test list from each ADR's `## Implementation Notes` section, keeping the section for genuinely non-file-listing content only (design rationale for *how* the Decision is realized, expressed as prose — not as a bulleted file/symbol inventory). Where an ADR's Implementation Notes section has no remaining content after removing the list (e.g. ADR-012, ADR-013, and most others per the audit above), consider whether the section should state "No additional Implementation Notes beyond Implementation References" or be omitted per the template's own rules (confirm with `docs/00_governance_01_documentation-policy.md`'s section-header requirements before removing a mandatory heading outright).

## Target Files or Areas
- `docs/adr/ADR-001-workflow-engine-mandatory.md`
- `docs/adr/ADR-002-config-isolation.md`
- `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`
- `docs/adr/ADR-004-environment-failure-handling-policy.md`
- `docs/adr/ADR-005-rag-source-derived-index-relationships.md`
- `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
- `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`
- `docs/adr/ADR-008-sqlite-4db-separation.md`
- `docs/adr/ADR-009-rag-ft5-text-separation.md`
- `docs/adr/ADR-010-rag-fallback.md`
- `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`
- `docs/adr/ADR-013-eventbus-authentication-authorization.md`
- `docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md`

## Required Changes
- For each ADR listed above: compare its Implementation Notes file/class/config/test list against its own Related Documents > Implementation References subsection; where they duplicate (expected in all 13, but verify each individually — do not assume without checking), remove the list from Implementation Notes.
- Before removing, reconcile any discrepancy found between the two lists (e.g. a file present in one but not the other) by updating Implementation References to be the single accurate copy, since Implementation References is the section the boilerplate already designates as canonical.
- Preserve any non-list prose already present in a given ADR's Implementation Notes (e.g. ADR-004's two caveat bullets, ADR-006's transaction/monotonicity/legacy-migration notes, ADR-007's Circuit Breaker description) — those are handled by their own separate issues from this review, not this one.
- After the edit, confirm each ADR's `## Implementation Notes` section still satisfies `docs/00_governance_01_documentation-policy.md`'s required-section-header rule (the heading itself is likely mandatory even if its list content is removed) — if the policy requires non-empty content under every mandatory heading, replace the removed list with a one-line pointer: "See Related Documents > Implementation References for the current file/symbol list."

## Constraints
Do not remove the `### Implementation References` subsection itself — it is the surviving canonical copy per this issue's own reasoning. Do not remove Implementation Notes' non-list prose content (caveats, transaction/ordering explanations) — those are scoped to separate issues from this review, not this one.

## Acceptance Criteria
- No ADR's Implementation Notes section contains a bulleted file/class/config/test list that duplicates its own Implementation References subsection.
- Each ADR's Implementation Notes section still satisfies the mandatory-heading requirement in `docs/00_governance_01_documentation-policy.md` (either via a one-line pointer or via surviving non-list prose).
- `tools/check_adr_reference.py`, `tools/check_adr_invariant_matrix.py`, `tools/check_docs_quality.py`, and `tools/check_docs_structure.py` all still pass after the edit.

## Testing Expectations
Not applicable — documentation-only change. Run the four tools listed in Acceptance Criteria after editing all 13 files.

## Documentation Impact
This issue's entire scope is the 13 ADR files listed in Target Files or Areas.

## Out of Scope
- ADR-004's missing Known Deviations section — tracked in a separate, dedicated issue from the same review.
- ADR-006's transaction-guarantee/monotonicity/legacy-migration Implementation Notes content — tracked in a separate issue from the same review (these are prose, not the file-list pattern this issue targets).
- ADR-007's Circuit Breaker 5-state description — tracked in a separate issue from the same review.
- Whether a new tool should be built to detect this class of duplication automatically going forward — tracked in a separate issue from the same review (see the tooling-decision issue).

## Dependencies
N/A: none — can be implemented independently, though it is part of the same review batch as the other Implementation Notes issues filed alongside it.

## Unresolved Questions
Whether `docs/00_governance_01_documentation-policy.md`'s section-header rule strictly requires non-empty prose under `## Implementation Notes`, or whether a heading with only a one-line pointer satisfies it — resolve during implementation by reading that policy document's exact requirement before deciding whether a placeholder line is needed.

## AI Implementation Instruction
Do not blindly delete the list from all 13 files in one mechanical pass without first diffing each ADR's Implementation Notes list against its own Implementation References subsection — a genuine discrepancy (a file/symbol present in one list but not the other) must be reconciled into Implementation References before the Implementation Notes copy is removed, not silently dropped.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-124438
- **Related target files**: docs/adr/ADR-001-workflow-engine-mandatory.md, docs/adr/ADR-002-config-isolation.md, docs/adr/ADR-003-runtime-tool-registry-routing-authority.md, docs/adr/ADR-004-environment-failure-handling-policy.md, docs/adr/ADR-005-rag-source-derived-index-relationships.md, docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md, docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md, docs/adr/ADR-008-sqlite-4db-separation.md, docs/adr/ADR-009-rag-ft5-text-separation.md, docs/adr/ADR-010-rag-fallback.md, docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md, docs/adr/ADR-013-eventbus-authentication-authorization.md, docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md
