# [Critical] Fix confirmed factual error in docs/01_overview-arch-03-features.md tool-routing priority description

## Priority
High

## Summary
`docs/01_overview-arch-03-features.md` (~lines 54-56) describes tool routing as a two-stage fallback: "(1) startup-time `/v1/tools` live discovery map, (2) `shared/tool_registry.py` static registry." This directly contradicts `scripts/shared/route_resolver.py`'s own docstring, which states `RuntimeToolRegistry` is "the sole routing authority," that the discovery map is "validation-only, never used by resolve()," and that "ToolRegistry is no longer consulted here."

## Reason for Change
This is the single most severe finding in this review: a confirmed factual error (not speculation) about a core runtime mechanism. An implementer debugging a routing-related incident who trusts this description will look for a fallback path that does not exist, leading to misdiagnosis.

## Implementation Intent
Rewrite the routing description to match `route_resolver.py`'s actual documented behavior: `RuntimeToolRegistry` is the sole authority; the discovery map is validation-only; the static registry is not consulted for routing (config `tool_names` is drift-validation-only).

## Target Files or Areas
`docs/01_overview-arch-03-features.md`

## Required Changes
- Replace the two-stage fallback description (~lines 54-56) with: "`RuntimeToolRegistry` (`shared/route_resolver.py`) is the sole routing authority. The startup-time `/v1/tools` discovery map is validation-only and is not used for routing; the static registry (`tool_registry.py`) is not currently consulted for routing either (the `tool_names` config value is used only for drift validation)."
- Verify this description against the current `scripts/shared/route_resolver.py` docstring/implementation before finalizing, in case the mechanism has changed since this review was written.

## Acceptance Criteria
The routing description matches `route_resolver.py`'s current, actual behavior exactly, with no residual reference to a two-stage fallback that does not exist.

## Testing Expectations
Not required (documentation-only). Manually re-verify against `scripts/shared/route_resolver.py`'s docstring immediately before finalizing, since this is a high-stakes correction.

## Documentation Impact
`docs/01_overview-arch-03-features.md` corrected — this is the highest-priority fix in the entire review.

## Out of Scope
Do not change `scripts/shared/route_resolver.py` or any routing behavior in this issue — documentation only.

## AI Implementation Instruction
This is a confirmed factual error (verified against `route_resolver.py`'s own docstring) — apply the fix directly. Re-read the current docstring before writing the replacement text, since routing behavior is exactly the kind of thing that could have changed again since this review was authored.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §1 (再構成の基本方針 item 3), §5 例2, §6A (arch-03-features.md「ツールルーティング優先順位」)
- Generated at: 2026-08-02
