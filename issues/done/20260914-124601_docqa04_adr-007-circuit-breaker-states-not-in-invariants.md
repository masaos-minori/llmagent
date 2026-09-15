# ADR-007's Circuit Breaker 5-state model is named only in Implementation Notes, not in Invariants or Decision — determine whether it should be promoted

## Priority
Low

## Summary
`docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`'s `## Implementation Notes` states "Circuit Breaker: 5-state（HEALTHY → DEGRADED → UNAVAILABLE → HALF_OPEN → HEALTHY）" as a single bullet. The ADR's `## Invariants` section (INV-07) only says "接続Timeout、応答Timeout、Retry、Semaphore、Circuit Breaker、構造化エラー、ログを共通Transport層で扱う" — it requires that a Circuit Breaker exist in the shared transport layer, but does not name or constrain the specific 5-state model. Per this review's classification criteria, a specific state machine that every MCP client caller must interpret consistently ("複数実装が同じ制約を守る必要がある") is a promotion candidate rather than a pure implementation-detail note — but it could also be legitimately implementation-only if no other component needs to know the specific state names to behave correctly.

## Background
This issue follows a review requested in this session: classify each item in every ADR's Implementation Notes section against four buckets (delete / promote to ADR-Decision-or-design-body / move to Known Issue / move to Needs Confirmation). This issue covers ADR-007's Circuit Breaker note specifically — it is filed as a judgment-call issue rather than a direct fix, since the promote-vs-leave-as-is decision depends on a fact (whether other code depends on the specific state names) that requires a repository-wide check.

## Problem
Confirmed by direct reading of `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`:
- INV-07 (line ~231): names "Circuit Breaker" as one of several concerns the shared Transport layer must handle, but states no state model.
- Implementation Notes (line ~350): "Circuit Breaker: 5-state（HEALTHY → DEGRADED → UNAVAILABLE → HALF_OPEN → HEALTHY）" — this is the only place in the ADR where the specific 5 states and their transition order are named.
- Whether any other component (`scripts/shared/mcp_server_health_registry.py`, per the Implementation Notes' own file list, or callers that branch on health state) depends on exactly these 5 state names/order was not verified during this issue's drafting.

## Reason for Change
If other code branches on these specific state names (e.g. `McpServerHealthRegistry.record_failure()` transitioning through exactly these states, or a caller checking `state == "DEGRADED"`), then this state model is a cross-implementation constraint that belongs in Invariants or Decision Details (breaking it would break every caller relying on the state semantics) — a "promote" case per this review's criteria. If it is purely an internal implementation detail of one class with no external dependents on the specific names, it is correctly placed in Implementation Notes as-is, and no change is needed.

## Implementation Intent
Check `scripts/shared/mcp_server_health_registry.py` (and any caller of it) for whether the 5 specific state names (`HEALTHY`/`DEGRADED`/`UNAVAILABLE`/`HALF_OPEN`) are referenced outside that one file/class. If yes, add an Invariant naming the 5-state model explicitly (so a future refactor cannot silently rename or reorder states without violating a stated Invariant). If no, leave Implementation Notes as-is — this is the one item in this review's ADR-007 audit that may resolve to "no change needed."

## Target Files or Areas
- `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`
- `scripts/shared/mcp_server_health_registry.py` (read-only investigation)

## Required Changes
- Grep the repository for the 5 state name literals (`HEALTHY`, `DEGRADED`, `UNAVAILABLE`, `HALF_OPEN`) to determine how many distinct files/classes reference them.
- If more than one component depends on the specific names/transitions, add an Invariant to ADR-007 stating the 5-state model and transition order explicitly, with a Verification entry citing the relevant test (search `tests/test_mcp_*.py` for existing coverage first).
- If only `scripts/shared/mcp_server_health_registry.py` itself references them, leave Implementation Notes unchanged and close this issue as "no change needed" with the grep evidence recorded.

## Constraints
Do not invent a new Invariant if the investigation shows the state model is genuinely internal to one file — do not promote content just because this review flagged it as a candidate; the promotion criterion (multiple implementations depending on the same constraint) must actually hold.

## Acceptance Criteria
- The grep-based dependency check is performed and its result (how many files reference the 5 state names) is recorded in the issue's resolution.
- If promoted: a new Invariant with a Verification entry exists in ADR-007, and `docs/adr-index.md`'s Invariant Verification Matrix is updated if this ADR's Invariants are indexed there.
- If not promoted: the issue is closed with the investigation result recorded, and no ADR change is made.

## Testing Expectations
If promoted, search `tests/test_mcp_*.py` for existing Circuit Breaker state-transition test coverage before adding a new test; add one only if none exists.

## Documentation Impact
Possible edit to `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` and `docs/adr-index.md`, contingent on the investigation's outcome.

## Out of Scope
- The file/class/config/test list at the top of ADR-007's Implementation Notes — tracked in the common-pattern issue from the same review.
- Other ADRs' Implementation Notes prose (ADR-004, ADR-006) — tracked in separate issues from the same review.

## Dependencies
N/A: none — can be implemented independently, though it is part of the same review batch as the other Implementation Notes issues filed alongside it.

## Unresolved Questions
Whether any component outside `scripts/shared/mcp_server_health_registry.py` depends on the specific 5 state names or their transition order — this is the central fact this issue needs resolved before a promote/no-change decision can be made; it was not checked during this issue's drafting.

## AI Implementation Instruction
Perform the grep-based dependency check first and record the result before making any ADR edit. Do not add a new Invariant unless the check confirms multiple components depend on the specific state names — if the check is inconclusive or ambiguous, report the finding rather than defaulting to either promoting or leaving unchanged.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-124601
- **Related target files**: docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md, scripts/shared/mcp_server_health_registry.py
