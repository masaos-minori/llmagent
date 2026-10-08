# Fix EventBus authorization model for consumer tokens

## Priority
Medium

## Summary
Make the EventBus authorization model fail closed: every consumer token must map to an explicit set of allowed consumer IDs, an empty allow-list always means "deny all", and all-role tokens are operator-only.

## Background
Source: local investigation notes (memo1.md, ISSUE-07), consolidating EVENTBUS-008, EVENTBUS-013 and three earlier findings. ADR-013 INV-02 requires fail-closed; ADR-006 INV-10 concerns concurrent use of one Consumer ID.

## Problem
- Without `consumer_authorization`, a CONSUMER token has `allowed_consumer_ids=None` (no restriction) and can act as any consumer ID (EVENTBUS-008).
- `auth_token` is mandatory (`get_auth_token()`) and grants all roles with no consumer-ID restriction, so an all-powerful token always exists; `admin_token` also grants all roles, contradicting eventbus_02's "role tokens only for their own role".
- The meaning of an empty allow-list is inverted between code paths: `ack_route.py` uses truthiness (empty = unrestricted) while `require_consumer_identity()` uses `is not None` (empty = deny all).
- ACK/NACK cannot prevent several principals from using the same Consumer ID (EVENTBUS-013, ADR-006 INV-10).
- `_do_ack()` keeps a debug log at WARNING that prints principal information.

## Reason for Change
- "No allow-list means allow all" is fail-open and violates ADR-013 INV-02.
- A mandatory all-role token defeats least privilege regardless of role-token granularity.
- One concept with opposite meanings per location yields configurations that do not match intent and cannot be security-reviewed.
- ACK can arrive after a subscription disconnects, so binding INV-10 to an open subscription would reject legitimate ACKs; what must be prevented is a different principal using the same consumer ID, which token-to-consumer-ID binding achieves.
- The debug log leaks authentication information at WARNING.

## Implementation Intent
- Token to allowed consumer-ID set must always be explicit and fail closed.
- All-role tokens are for operators only and are not distributed to consumers (stated as a design rule).
- An empty allow-list consistently means deny all.

## Target Files or Areas
- `scripts/eventbus/auth.py`, `ack_route.py`, `scripts/eventbus/app.py` (to be read), `config/eventbus.toml`
- ADR-006 (INV-10), ADR-013, eventbus_02

## Required Changes
- Reject, at startup configuration validation, a `consumer_token` configured without `consumer_authorization`.
- Unify allow-list checks to `is not None` plus membership in both ACK and NACK in `ack_route.py`.
- Document `auth_token` / `admin_token` as operator-only in ADR-013; if feasible, remove the requirement for `auth_token` so role tokens alone can start the service.
- Revise ADR-006 INV-10 to "a consumer ID may be used only by the principal bound to it by token", with its scope stated.
- Remove the debug WARNING log in `_do_ack()`.

## Constraints
- Fail closed on every ambiguity; no change to authentication of unrelated roles.
- Do not log token fingerprints at WARNING.

## Acceptance Criteria
- A consumer token without an allow-list is rejected at startup (test).
- An empty allow-list denies ACK, NACK, and subscribe (tests).
- ADR-006, ADR-013, and eventbus_02 match the implementation.

## Testing Expectations
- Unit and route tests for auth decisions; config validation test; ruff, mypy, targeted pytest.

## Documentation Impact
Update ADR-006, ADR-013, eventbus_02 and the Known Issue ledger (EVENTBUS-008, EVENTBUS-013 until fixed).

## Out of Scope
- ACK/NACK state management (separate issue); DLQ model.

## Dependencies
- Works well together with the ACK/NACK state-management issue (same files).

## Unresolved Questions
- Whether `_principal` is actually passed into ACK/NACK handlers (confirm in `scripts/eventbus/app.py`; if not, ACK authorization is not enforced).
- Whether the production `config/eventbus.toml` sets allow-lists.

## AI Implementation Instruction
Fail closed everywhere. Confirm the `_principal` question before changing ACK authorization. Do not broaden any token's permissions.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-154015
- **Related target files**: `scripts/eventbus/auth.py`, `scripts/eventbus/ack_route.py`, `config/eventbus.toml`
