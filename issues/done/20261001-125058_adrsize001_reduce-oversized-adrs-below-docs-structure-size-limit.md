# Reduce oversized ADRs below the docs structure size limit

## Priority
Low

## Summary
Some ADRs under `docs/10_adr/` still exceed the 24576-byte per-file limit of `tools/check_docs_structure.py` after being translated to English under `langadr001`. Reduce each listed ADR below the limit without changing any decision, invariant, status, or identifier.

## Background
- `langadr001` (`plans/done/20261001-105822_plan.md`, REQ-005) required recording each ADR's size after translation and filing a follow-up issue for any ADR still over the limit, without restructuring ADRs in that Plan.
- Translating Japanese text (3 bytes per character in UTF-8) to English reduced sizes only slightly.

## Problem
ADRs still over the limit after translation (bytes before translation → after):
- `docs/10_adr/ADR-002-config-isolation.md`: 26322 → 25948
- `docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`: 27503 → 26235
- `docs/10_adr/ADR-004-environment-failure-handling-policy.md`: 44686 → 42787
- `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`: 26900 → 26152
- `docs/10_adr/ADR-008-sqlite-4db-separation.md`: 35223 → 34120

## Reason for Change
- `check_docs_structure.py` reports these files as non-conforming, so every task touching them inherits a failing structure check.

## Implementation Intent
- Prefer removing in-file duplication (for example template guidance sentences that restate governance rules, or repeated Known Deviations prose already held in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`) over splitting an ADR.
- If a split is unavoidable, keep the ADR ID and file as the canonical decision record and move only reference material, updating `docs/10_adr/adr-index.md` and inbound links.

## Target Files or Areas
- The ADR files listed under Problem.

## Required Changes
- For each listed ADR, reduce size to at most 24576 bytes with a section-by-section mapping of what was removed or moved.

## Constraints
- No change to decisions, invariants (INV-xx), Known Issue IDs, statuses, or dates.
- ADR checkers (`check_adr_structure.py`, `check_adr_reference.py`, `check_adr_invariant_matrix.py`, `check_known_deviation_sync.py`) must keep their current results.

## Acceptance Criteria
- `uv run python tools/check_docs_structure.py "docs/10_adr/*.md"` reports no size finding for the listed ADRs.
- ADR checker outputs are unchanged.

## Testing Expectations
Documentation-only. Run the ADR checkers, `check_docs_structure.py`, `check_docs_quality.py`, and `uv run pytest tests/tools/test_check_docs_quality.py` (snapshot may need reconciliation).

## Documentation Impact
Yes. ADR structure only; no decision change.

## Out of Scope
- Translation (done by `langadr001`); `docs/00_governance/governance_01_documentation-policy.md` size (`docsize001`).

## Dependencies
- Follows `langadr001` implementation (`implementations/done/20261001-115707_*`).

## Unresolved Questions
- Whether template guidance sentences inside ADRs (e.g. Implementation Notes boilerplate) may be removed from ADRs in favor of the governance template, which would also simplify `langdoc001` REQ-006.

## AI Implementation Instruction
- Process one ADR per change; record the mapping; do not alter decision content.

## Traceability
- **Workflow phase**: code-implementation
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261001-105822_plan.md
- **Source implementation procedure**: implementations/done/20261001-115707_02_docs_10_adr_ADR-002-config-isolation.md.md
- **Generated at**: 20261001-125058
- **Related target files**: docs/10_adr/ADR-002-config-isolation.md, docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md, docs/10_adr/ADR-004-environment-failure-handling-policy.md, docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md, docs/10_adr/ADR-008-sqlite-4db-separation.md
