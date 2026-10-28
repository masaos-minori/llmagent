# Enforce pairwise consumer/topic authorization and close the empty-topic subscribe bypass

## Priority
High

## Summary
Make EventBus consumer authorization preserve the configured (consumer_id, topic) relationships instead of collapsing them into two independent sets, and stop an empty `topic` query from widening a topic-restricted consumer's access to all topics.

## Background
Source: `memo-issue.md` Issue 01, re-verified against current source on 2026-10-27.

- `scripts/eventbus/auth.py` (consumer-token branch of the principal builder) accumulates every topic found in `consumer_authorization` values and `topic_authorization` keys into one set, and every consumer ID found in `consumer_authorization` keys and `topic_authorization` values into another. `Principal` carries them as `allowed_consumer_ids` and `allowed_topics`. `Explicit in code`.
- `require_consumer_identity()` checks `consumer_id` against `allowed_consumer_ids` and each requested topic against `allowed_topics` independently. `Explicit in code`.
- `scripts/eventbus/subscribe_route.py` validates only the topics that were requested; with no `topic` query the loop does not run, and an inline comment states "empty topic list means subscribe to all topics". `Explicit in code`. That the broker treats an empty list as "all topics" is `Strongly implied by code` (broker not read in this verification).
- Prior work: `issues/done/20261007-154015_ebauthz01_fix-eventbus-authorization-model-for-consumer-tokens.md` made an empty allow-list deny-all and `issues/done/20260913-143134_eb005_token-topic-map-empty-set-contradiction.md` fixed an empty-set contradiction. Neither covers pairwise preservation or the empty-topic query.

## Problem
- With `consumer-a -> topic-a` and `consumer-b -> topic-b` configured, a token holding both entries is authorized for `consumer-a` with `topic-b` and `consumer-b` with `topic-a`, because the relationship is lost.
- A principal restricted to some topics can subscribe with no `topic` query and receive events of every topic.

## Reason for Change
The authorization is broader than the configuration expresses, which is a security-boundary defect on an authenticated endpoint. No timing constraint makes it more urgent than other High items; severity is driven by the boundary violation.

## Implementation Intent
Represent the grant as explicit (consumer_id, topic) relationships and evaluate subscribe, ACK and NACK through one shared authorization decision, so route handlers do not re-derive authorization after the dependency approved a request. Missing or ambiguous input (for example an empty topic query for a restricted principal) must fail closed or be explicitly narrowed to the authorized topics; the choice is documented. Control-plane credentials must keep receiving no implicit consumer authorization.

## Target Files or Areas
- `scripts/eventbus/auth.py`
- `scripts/eventbus/app.py` (identity dependencies for subscribe, ACK, NACK)
- `scripts/eventbus/subscribe_route.py`
- `scripts/eventbus/ack_route.py`
- `tests/eventbus/` authorization and subscribe tests
- `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` and the current EventBus security/API docs under `docs/24_eventbus/`

## Required Changes
- Replace the independent consumer-ID and topic sets with a structure that keeps (consumer_id, topic) pairs, including when authorization is configured per topic.
- Decide and document how an empty `topic` query behaves for a restricted principal (HTTP 400, HTTP 403, or restriction to the authorized topics) and implement it.
- Route subscribe, ACK and NACK through one shared authorization decision and remove the duplicated partial checks in `subscribe_route.py`.
- Confirm that the real query `consumer_id` is bound into the ACK and NACK authorization path, and fix it if it is not.
- Keep shared and admin credentials from receiving consumer authorization implicitly.
- Keep runtime authorization updates (if any exist) consistent with the pairwise semantics.

## Constraints
- Existing semantics must be preserved: an empty allow-list means deny-all, and consumer tokens without an allow-list are rejected at startup (ebauthz01).
- Unauthorized requests return HTTP 403; documented malformed-input cases return HTTP 400.
- `docs/10_adr/*.md` edits must pass `tools/check_adr_preservation.py`; do not change Decisions or Invariants without owner approval.

## Acceptance Criteria
- Only explicitly configured (consumer_id, topic) pairs are accepted for subscribe, ACK and NACK.
- Omitting the topic cannot expand a restricted consumer's access.
- A control-plane credential cannot subscribe, ACK or NACK as a consumer.
- Implementation, tests, ADR-013 and the EventBus docs describe the same contract.

## Testing Expectations
- Unit and route tests: `consumer-a`/`topic-a` allowed, `consumer-b`/`topic-b` allowed, `consumer-a`/`topic-b` rejected, `consumer-b`/`topic-a` rejected.
- A restricted consumer with no topic query is rejected or restricted per the documented decision.
- A consumer cannot ACK or NACK with another consumer's ID.
- `uv run pytest tests/eventbus`, mypy and ruff on changed files, `tools/check_adr_preservation.py` and the docs checkers for edited docs.

## Documentation Impact
Yes. Record the authorization model (pairwise grant), the empty-topic behavior and the failure status codes in ADR-013 and the EventBus security/API docs. State current behavior only; no history of the old set-based model.

## Out of Scope
- Changing token roles or the credential configuration format beyond what pairwise preservation requires.
- Consumer-ID uniqueness across principals (EVENTBUS-013 area).
- Rate limiting or audit changes.

## Dependencies
N/A: none. No open issue under `issues/` or in-flight plan under `plans/` touches `auth.py`, `subscribe_route.py` or `ack_route.py` (the `ebcompat002` plan touches `ack_route.py` imports only; coordinate if both are implemented).

## Unresolved Questions
- Which behavior is wanted for an empty topic query of a restricted principal: reject (400/403) or narrow to authorized topics? `Needs confirmation` (owner decision).
- Do the ACK and NACK routes already apply the pairwise or consumer-ID check through a dependency, or only a `consumer_id` presence check? `Needs confirmation`: read `app.py` ACK/NACK wiring.
- Is a runtime authorization update path present? `Needs confirmation`: the memo mentions it, not verified here.

## AI Implementation Instruction
Keep changes minimal and limited to authorization. Do not change role definitions or unrelated routes. Preserve deny-all and startup-rejection behavior. If the empty-topic behavior or the ACK/NACK wiring is unclear, stop and report the question instead of choosing silently. Do not implement out-of-scope items.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-155843
- **Related target files**: `scripts/eventbus/auth.py`, `scripts/eventbus/app.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/ack_route.py`, `tests/eventbus/`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/24_eventbus/`
