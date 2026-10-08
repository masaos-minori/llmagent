# Fix ADR-013 role token model and auth description

## Priority
High

## Summary
Correct ADR-013 so its Consequences stop overstating role separation, authentication is described as implemented (dependency-based role checks, request-ID-only middleware), and /health is stated to need the Monitoring role.

## Background
Source: local investigation notes (memo2.md, ADR-013 section; review findings H09, M24; finding G04 does not apply).

## Problem
- Decision 1 already states that auth_token and admin_token grant every role, but the Consequences still say per-role tokens make the five-role model enforceable, without the operator-only rule or an invariant.
- Verified in code: Decision 1 describes a middleware checking the Authorization header, but attach_auth_middleware() only assigns X-Request-Id; roles are resolved by endpoint dependencies.
- Verified: eventbus_10 states the Monitoring role is required for /health, contradicting the Failure Policy.
- Verified: Decision items are already numbered.
- Assumptions and Scope contain a historical reference to a source issue.

## Reason for Change
Overstated authorization guarantees mislead deployment decisions on token distribution. Decision content changes, so an approval record is required.

## Implementation Intent
- Apply the Assumptions replacement, revised Decision 1 (plus a token-kinds/operator-only statement; keep existing numbering), Consequences and Failure Policy replacements, INV-07, the manual-review Verification item, and revised Known Deviations from memo2.md.

## Target Files or Areas
- `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`
- eventbus_10 under `docs/24_eventbus/` (read-only check of the /health claim)

## Required Changes
- Apply the ADR-013 replacements listed in memo2.md, adapted to the existing numbering and to Decision 1's current text.
- Remove the historical "Issue's Required Changes" wording from Assumptions and Scope.
- Record a new Approval Record in the same change.

## Constraints
- governance_01 ADR Change Protocol applies.
- EVENTBUS-015 must be registered before it is cited.
- No tokens or secrets in the text.

## Acceptance Criteria
- ADR-013 states that auth_token and admin_token grant every role and must stay operator-only.
- Authentication is described as implemented; /health requires the Monitoring role.
- INV-07 and EVENTBUS-015 are recorded; doc checkers pass.

## Testing Expectations
Run the doc checkers listed in `routing.md`, including Known Deviation sync. No code change.

## Documentation Impact
Documentation only: ADR-013 and its Approval Record.

## Out of Scope
- Removing the auth_token requirement or changing roles in code.

## Dependencies
- Depends on the kiupd01 issue (EVENTBUS-015 registration).
- Related: `issues/20261007-154015_ebauthz01_fix-eventbus-authorization-model-for-consumer-tokens.md`.

## Unresolved Questions
- Whether auth_token should stop being mandatory so operation can rely on per-role tokens only (design decision for the ADR owner; this issue documents the current state only).

## AI Implementation Instruction
Document the current behavior only; do not decide the auth_token question. Verify the /health and middleware claims against the eventbus docs before writing. Run the doc checkers before finishing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-094500
- **Related target files**: `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`
