# Fix ADR-006 INV-12 contradiction and INV-10 scope

## Priority
Medium

## Summary
Rewrite ADR-006 INV-12 so it no longer contradicts the At-Least-Once rule (INV-07), state the real scope of INV-10, add EVENTBUS-014 to Known Deviations, and number the delivery rules.

## Background
Source: local investigation notes (memo2.md, ADR-006 section; review findings H11, G05, G04).

## Problem
- INV-12 says an event is not redelivered when ACK persistence fails, which contradicts INV-07 (duplicates allowed, loss not allowed).
- INV-10 is enforced only on GET /subscribe, but its text implies broader coverage (EVENTBUS-013).
- Known Deviations lacks EVENTBUS-014.
- A Review Trigger duplicates what is now a Known Issue.

## Reason for Change
- An invariant that contradicts another invariant cannot be verified.
- The intent behind INV-12 is unconfirmed (see Unresolved Questions), so the change alters Decision content and needs an approval record.

## Implementation Intent
- Interpret INV-12 as "a failed ACK is not treated as success: offset and delivery state do not advance, and the event stays eligible for redelivery".
- Apply the numbered delivery rules (11a to 11e), revised INV-10 to INV-12, revised Known Deviations, and delete the EVENTBUS-013 Review Trigger as memo2.md specifies.

## Target Files or Areas
- `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

## Required Changes
- Replace the delivery rules in Decision Details with the numbered version.
- Replace INV-10, INV-11, INV-12.
- Replace Known Deviations (EVENTBUS-008, 011, 012, 013, 014).
- Remove the Review Trigger "Consumer ID exclusivity must also be enforced on ACK and NACK (EVENTBUS-013)".
- Record a new Approval Record in the same change.

## Constraints
- governance_01 ADR Change Protocol applies because Decision content changes.
- Cited Known Issue IDs must exist in governance_03 Part 1.

## Acceptance Criteria
- No invariant in ADR-006 contradicts INV-07.
- Known Deviations include EVENTBUS-014 and the removed Review Trigger no longer appears.
- A new Approval Record exists; doc checkers pass.

## Testing Expectations
Run the doc checkers listed in `routing.md`, including Known Deviation sync and ADR structure checks. No code change.

## Documentation Impact
Documentation only: ADR-006 Decision Details, Invariants, Known Deviations, Review Triggers, and the Approval Record.

## Out of Scope
- Fixing EVENTBUS-013 or EVENTBUS-014 in code.
- Editing ADR-013.

## Dependencies
- Related: `issues/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`, `issues/20261007-154015_ebauthz01_fix-eventbus-authorization-model-for-consumer-tokens.md`.
- adr-index lists this ADR; see the adridx01 issue.

## Unresolved Questions
- Whether the original intent of INV-12 was "do not redeliver" or the revised interpretation. Confirmation by the ADR owner is required before the ADR is finalized as Accepted.

## AI Implementation Instruction
Do not finalize the ADR as Accepted without the owner's confirmation of the INV-12 interpretation; stop and ask. Edit only the listed sections.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-094450
- **Related target files**: `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
