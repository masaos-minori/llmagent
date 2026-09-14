# Reconcile EventBus ADRs and active known issues with implementation

## Priority
Medium

## Summary
`ADR-002`, `ADR-013`, `CI-001`, `CI-005`, and `EVENTBUS-008` contain overlapping or conflicting claims about EventBus configuration, authentication, and authorization — most notably, `EVENTBUS-008` currently states "No authentication middleware is implemented" while `scripts/eventbus/auth.py` already defines a role/token-based authentication mechanism (284 lines: `Role` enum, route-to-role map, per-role token maps) — so this issue reconciles the governance documents with the actual, post-`eventbus02`/`eventbus03`/`eventbus05`/`eventbus09` implementation.

## Background
Verified during issue drafting: `docs/adr/ADR-002-config-isolation.md` and `docs/adr/ADR-013-eventbus-authentication-authorization.md` both exist under `docs/adr/`; `CI-001` and `CI-005` are filed in `docs/00_governance_03_issue-and-uncertainty-management.md` Part 1; `EVENTBUS-008` is filed in the same document. `EVENTBUS-008`'s current text explicitly states no authentication middleware exists, which is stale relative to the current `scripts/eventbus/auth.py` (Evidence: Confirmed by repository inspection — file exists and defines `Role`, `_ROUTE_ROLE_MAP`, and per-role token maps as of this issue's filing).

## Problem
Several governance documents make claims about EventBus configuration loading and authentication/authorization that no longer match, or never fully matched, the current implementation: whether EventBus's configuration loader is an accepted architectural exception or a bug to fix (`CI-001` vs. `ADR-002`), and whether any authentication exists at all (`EVENTBUS-008`'s current wording vs. `scripts/eventbus/auth.py`'s actual content). Left unreconciled, an implementer or reviewer could reasonably read the active documents as contradicting each other or the code.

## Reason for Change
`ADR-002`, `ADR-013`, `CI-001`, `CI-005`, and `EVENTBUS-008` contain overlapping or conflicting claims about configuration, authentication, and authorization.

## Implementation Intent
Maintain one current, evidence-backed architectural description and remove obsolete active-issue statements — performed only after `eventbus02`, `eventbus03`, `eventbus05`, and `eventbus09` (which change the actual authentication/authorization/config-validation behavior this issue documents) have landed, so the reconciliation reflects the implemented state rather than a moving target.

## Target Files or Areas
- `docs/adr/ADR-002-config-isolation.md`
- `docs/00_governance_03_issue-and-uncertainty-management.md`
- `scripts/eventbus/config.py`
- `scripts/eventbus/app.py`
- `docs/adr/ADR-013-eventbus-authentication-authorization.md`
- `scripts/eventbus/auth.py`

## Required Changes
- Decide whether the EventBus-specific loader is the accepted architecture.
- If accepted, record the exception and rationale in `ADR-002`.
- If not accepted, migrate EventBus to the shared loader without weakening fail-closed checks.
- Update `CI-001` to match the decision.
- Update `ADR-013` implementation status and known deviations.
- Rewrite `EVENTBUS-008` to describe the remaining authorization and audit gaps (not "no authentication middleware exists", once `eventbus02`/`eventbus03` have landed).
- Link each remaining gap to an implementation issue and verification test.

## Constraints
This issue's Required Changes must be performed after `eventbus02`, `eventbus03`, `eventbus05`, and `eventbus09` land — reconciling the documents against a not-yet-implemented state would immediately go stale again.

## Acceptance Criteria
- `ADR-002` defines one authoritative configuration-loading rule for EventBus.
- `CI-001` is either resolved or rewritten as a concrete remaining gap.
- Configuration behavior remains covered by regression tests.
- Documentation distinguishes implemented bearer authentication from incomplete authorization and auditing.
- No active document simultaneously states that the same control is both absent and complete.
- Every completion claim links to executable verification.

## Testing Expectations
Not required for the documentation-reconciliation changes themselves; confirm the regression tests already added by `eventbus02`/`eventbus03`/`eventbus05`/`eventbus09` still pass before updating claims that reference their behavior.

## Documentation Impact
This issue's entire scope is updating `ADR-002`, `ADR-013`, `CI-001`, `CI-005` (cross-reference from `eventbus05`), and `EVENTBUS-008` in `docs/00_governance_03_issue-and-uncertainty-management.md` and `docs/adr/`, once implementation evidence from the dependent issues is available — do not update these documents speculatively ahead of that evidence.

## Out of Scope
- Unrelated refactoring outside the identified behavioral boundary.

## Dependencies
Depends on `eventbus02` (principal-based authentication), `eventbus03` (consumer/topic authorization), `eventbus05` (audit logging, `CI-005` scoping), and `eventbus09` (config validation/role-token policy) landing first, since this issue documents their resulting state rather than a design intent.

## Unresolved Questions
Whether the EventBus-specific configuration loader should be kept as a documented exception to `ADR-002` or migrated to the shared `ConfigLoader` (per `CI-001`) is the central open question this issue itself must resolve during implementation — it is not resolved here.

## AI Implementation Instruction
Do not start this issue until `eventbus02`, `eventbus03`, `eventbus05`, and `eventbus09` are implemented and merged — implementing it earlier risks reconciling documentation against code that is about to change. Keep changes scoped to the named ADR/governance documents; do not modify unrelated ADRs or Known Issue entries. Every claim written into these documents must cite a specific test or code location as evidence, per this document set's own evidence-labeling convention — do not restate an unverified claim as resolved.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-102602
- **Related target files**: docs/adr/ADR-002-config-isolation.md, docs/00_governance_03_issue-and-uncertainty-management.md, scripts/eventbus/config.py, scripts/eventbus/app.py, docs/adr/ADR-013-eventbus-authentication-authorization.md, scripts/eventbus/auth.py
