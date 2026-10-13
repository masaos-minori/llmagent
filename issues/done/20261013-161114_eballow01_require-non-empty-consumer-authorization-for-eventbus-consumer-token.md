# Require non-empty consumer authorization for the EventBus CONSUMER token

## Priority
Medium

## Summary
The EventBus `CONSUMER`-role token is unrestricted across every `consumer_id` when
`consumer_authorization` and `topic_authorization` in `config/eventbus.toml` are both
empty, because `_populate_token_maps()` in `scripts/eventbus/auth.py` assigns
`allowed_consumer_ids=None` ("any consumer_id") instead of denying all. This is the
residual gap tracked as `EVENTBUS-008` in the governance known-issue ledger. Fix the
fail-open so an empty mapping means "deny all" (or fails closed at startup), and cover
it with a test.

## Background
`EVENTBUS-008` is recorded in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
as `open` / `Medium` / `design-gap`. Its source is `scripts/eventbus/auth.py`; its
related documents are `ADR-013` (consumer-topic authorization, INV-02) and
`ADR-006` (ACK/NACK token binding, INV-10), both of which rely on the CONSUMER token
being restricted to its allowlist.

`eventbus03` (`issues/done/20260914-102317_eventbus03_consumer-topic-authorization-ack-nack.md`)
introduced the fail-closed consumer/topic authorization model across subscribe, ACK, and
NACK. It is consumed, but it did not close the specific empty-mapping case:
`_populate_token_maps()` still treats an empty `consumer_authorization`/`topic_authorization`
pair as "no restriction" rather than "deny all", so `EVENTBUS-008` remains open.

## Problem
With `consumer_token` configured and both `consumer_authorization` and `topic_authorization`
present but empty, startup does not reject the configuration and the resolved
`Principal.allowed_consumer_ids` is `None`. `require_consumer_identity()` then never rejects
a `consumer_id`, so the CONSUMER token can act as any `consumer_id`. This is a fail-open at a
trust boundary driven purely by configuration.

## Reason for Change
An empty authorization mapping is most naturally read as "no one is authorized", but the
current code reads it as "everyone is authorized". Any operator who clears the allowlist
(or ships an empty mapping) silently disables consumer-identity enforcement without a
startup error, and the ACK/NACK binding of `ADR-006` INV-10 and the topic restriction of
`ADR-013` INV-02 both depend on that enforcement. The gap is a genuine code/config mismatch
that contradicts the fail-closed intent documented in `ADR-013`.

## Implementation Intent
Change how an empty `consumer_authorization`/`topic_authorization` pair is interpreted for
the `CONSUMER` role only. Prefer one of the two resolution targets from `EVENTBUS-008`:
- deny all consumers when both mappings are empty (resolve to an empty allowlist that
  rejects every `consumer_id`), or
- reject an empty `consumer_authorization` at startup when `consumer_token` is configured
  (extend the existing missing-config check), or
- represent the three states (unrestricted, deny-all, explicit allowlist) with distinct
  values so "empty" resolves to deny-all rather than unrestricted.

Do not change the interpretation for other roles. Keep the work scoped to the empty-mapping
case; do not alter the union-apply behavior for non-empty mappings.

## Target Files or Areas
- `scripts/eventbus/auth.py` (`_populate_token_maps()`, `require_consumer_identity()`)
- `config/eventbus.toml` schema / validation for `consumer_authorization` / `topic_authorization`
- `tests/eventbus/test_eventbus_auth.py`

## Required Changes
- Make an empty `consumer_authorization` and empty `topic_authorization` resolve to deny-all
  for the CONSUMER role (or fail closed at startup), instead of `allowed_consumer_ids=None`.
- Ensure `require_consumer_identity()` rejects every `consumer_id` under the deny-all state.
- Add a test asserting a CONSUMER token with empty mappings cannot use any `consumer_id`.
- Add a test asserting a CONSUMER token with a non-empty mapping still restricts to its
  allowlist (regression).
- Update the `EVENTBUS-008` ledger entry to reflect the new status once fixed.

## Constraints
- Preserve the intentional superuser behavior of `auth_token` and `admin_token`
  (`allowed_consumer_ids=None`), which is by design, not a defect.
- Preserve backward compatibility of the single/shared-token deployment model.
- Do not change the union-apply semantics for non-empty mappings.
- Keep fail-closed startup validation consistent with the existing missing-config check.

## Acceptance Criteria
- A `consumer_token` with empty `consumer_authorization` and `topic_authorization` is either
  rejected at startup or denied every `consumer_id`; it is never unrestricted.
- A `consumer_token` with a non-empty mapping is restricted to the union of its allowlist.
- `auth_token` and `admin_token` remain unrestricted (superuser behavior unchanged).
- The deny-all / deny-every-`consumer_id` path is covered by an automated test.

## Testing Expectations
Unit tests under `tests/eventbus/test_eventbus_auth.py` covering: empty mappings → deny-all
(or startup rejection), non-empty mapping → allowlist enforced, and superuser tokens →
unchanged. Run the EventBus test suite plus static analysis and type checks.

## Documentation Impact
After the fix, update the `EVENTBUS-008` entry in
`docs/00_governance/governance_03_issue-and-uncertainty-management.md` to record the
resolution (or keep it open with corrected wording if the chosen resolution differs).
`ADR-013` and `ADR-006` Known Deviations references to `EVENTBUS-008` should be re-checked
against the resolved state.

## Out of Scope
- Changing the unrestricted behavior of `auth_token` / `admin_token` (superuser, by design).
- Altering the union-apply behavior for non-empty mappings.
- Other roles' authorization (`PUBLISHER`, `OPERATOR`, `MONITORING`, `ADMIN`).
- Rewriting unrelated DB or broker logic beyond the empty-mapping interpretation.

## Dependencies
- Related to `eventbus03` (`issues/done/20260914-102317_eventbus03_consumer-topic-authorization-ack-nack.md`),
  which established the fail-closed consumer/topic model but left this empty-mapping gap
  open. Re-verify against current source after that work.
- Depends on the config schema for `consumer_authorization` / `topic_authorization` being
  reachable at startup validation time (to be confirmed during implementation).

## Unresolved Questions
- Which resolution target to adopt: deny-all at runtime, or reject an empty mapping at
  startup? These have different operational implications (silent deny vs. loud misconfiguration).
- Whether an explicitly empty mapping should be distinguished from a missing key, or treated
  identically.
- Whether the shared/single-token deployment model depends on the CONSUMER token being
  unrestricted when only `auth_token` is set (confirm no regression before changing).

## AI Implementation Instruction
Only change the interpretation of an empty `consumer_authorization`/`topic_authorization`
pair for the `CONSUMER` role in `scripts/eventbus/auth.py`. Do not touch `auth_token` /
`admin_token` superuser behavior, the union-apply path for non-empty mappings, or any other
role. Choose one resolution target (deny-all or startup rejection) and document it; do not
introduce a third interpretation. Add unit tests for the empty-mapping, non-empty-mapping,
and superuser cases. Stop and report if the single-token deployment model cannot be
confirmed safe to change.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261013-161114
- **Related target files**: scripts/eventbus/auth.py, config/eventbus.toml, tests/eventbus/test_eventbus_auth.py
