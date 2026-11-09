# Complete the EventBus configuration, persistence, and observability specifications

## Priority
Medium

## Summary
Define every EventBus table, configuration key, endpoint, and failure mode in an ADR or a referenced specification (the outbox table, the required-key list, `GET /replay`, `/subscribe` replay from the start), remove an obsolete NACK failure row, and expose the failures that the fail-closed design depends on through `/health`.

## Background
- Source: `memo-issue.md` items M-07 and L-01, re-checked against current source on 2026-11-09.
- `Explicit in code`: `scripts/eventbus/schema.sql` defines the `dlq_outbox` table and its status index. `Documentation only`: a search of `docs/10_adr/*.md` found no mention of `dlq_outbox`, so ADR-006 and ADR-008 do not cover it (consistent with the memo). `Needs confirmation`: the memo's claim that the manual deletion procedure assumes no foreign keys.
- `Explicit in documentation` (`docs/10_adr/adr_02_01_002_platform-config-isolation.md`): ADR-002 now describes the actual loading mechanism (EventBus loads through the shared loader without `restrict_to()`, with a path override via `EVENTBUS_CONFIG_PATH`); the required-key row lists a small fixed set of keys and does not list `authz_max_ttl_seconds` or the `outbox_*` keys (memo confirmed for the key table; the loading-mechanism claim is stale). `Needs confirmation`: the ADR-013 Out of Scope text about moving to ConfigLoader.
- `Explicit in documentation` (`docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`): the NACK table still has "Initial NACK, inline DLQ file write failed". `Needs confirmation` whether that path still exists in code.
- `Explicit in code`: `scripts/eventbus/subscribe_route.py` takes `since_seq` with default `0`, so an omitted value and an explicit `0` are indistinguishable. `Documentation only`: ADR-006 does not mention `/replay`; `eventbus_11_replay_endpoint.md` exists.
- `Explicit in code`: `scripts/eventbus/health_route.py` reports capacity-only degraded reasons (`subscribers_at_capacity`, `lock_wait_high`, `query_duration_high`) with HTTP 503, and `eventbus_10_health_endpoint.md` says the body reports DLQ sweep task state, broker counters, and lock metrics. No outbox status appears in the health route (search for "outbox" found nothing). `Needs confirmation`: the "metered" wording for persistent outbox failures and the absence of a metrics endpoint.

## Problem
- A table, several configuration keys, and the `/replay` endpoint exist without an authoritative specification, so their behavior can change unnoticed.
- A documented failure row refers to a path that may no longer exist, and reviewers will look for a failure mode that is gone.
- Persistent outbox failures are not visible in `/health`, although fail-closed behavior depends on operators noticing them; capacity-only reasons return 503, which makes status-code monitoring raise false alarms.

## Reason for Change
- Unspecified behavior and unobservable failure modes are review risks on a security-relevant service.

## Implementation Intent
- Every EventBus table, configuration key, endpoint, and failure mode is defined by an ADR or a referenced specification, and every failure that a guarantee depends on is observable through `/health`.
- Prefer documenting current behavior; change code only for the observability items and a possible `/subscribe` full-replay option.

## Target Files or Areas
- `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
- `docs/24_eventbus/eventbus_10_health_endpoint.md`, `docs/24_eventbus/eventbus_11_replay_endpoint.md`, `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md`
- `scripts/eventbus/health_route.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/schema.sql` (read-only reference)
- `tests/eventbus/`

## Required Changes
- Describe the actual config loading mechanism consistently in ADR-002 and ADR-013, decide whether to apply `restrict_to()`, and complete the required-key table (`authz_max_ttl_seconds`, the `outbox_*` keys).
- Add `dlq_outbox` to ADR-006 (Scope, Data Ownership) and ADR-008; make the manual deletion procedure foreign-key-safe, or prohibit manual deletion in ADR-006.
- Delete the obsolete NACK state row after confirming the path no longer exists in code.
- Add the `/replay` contract (offsets are not changed; Operator only) to ADR-006, and either make full replay possible on `/subscribe` or document why it is not.
- Add a count of permanently failed outbox rows and the result and time of the last sweep to `/health`, with matching degraded reasons. Return 200 with `status: degraded` for capacity-only reasons, or document the monitoring rule. Update `eventbus_10`.

## Constraints
- Do not change authorization behavior (EventBus authorization issue in this batch).
- Health response changes must keep liveness and readiness semantics (`health_route.py` documents that a capacity-only reason does not change them).
- ADR amendments need approval records (governance-ledger issue); the implementer must not fabricate approvals.
- Documents follow the docs content policy: no config values, no implementation-location mappings.

## Acceptance Criteria
- Every EventBus table and configuration key is covered by an ADR or a referenced specification.
- A test with failed outbox rows shows them in `/health`.
- `/replay` and the `/subscribe` replay behavior are specified in ADR-006.
- `check_adr_authority.py`, `check_adr_structure.py`, `check_docs_consistency.py --domain eventbus`, `check_db_separation.py`, and `generate_reference_table.py --check` pass.

## Testing Expectations
- New `tests/eventbus/` tests for the `/health` outbox and sweep reporting and for the status-code rule; `uv run pytest tests/eventbus -v`; the full validation sequence from `rules/toolchain.md` if code changes.
- Documentation checkers listed above.

## Documentation Impact
- ADR-002, ADR-006, ADR-008, ADR-013, and `eventbus_10` / `eventbus_11` / `eventbus_12` / `eventbus_03` change: state intent, data ownership, failure behavior, and monitoring rules.

## Out of Scope
- Authorization generations, credentials, and consumer grants (EventBus authorization issue in this batch).
- Route handler structure (EventBus route handler issue in this batch).
- Adding a metrics endpoint unless the maintainer decides it is required.

## Dependencies
- Depends on: `issues/20261109-112739_adrrev006_eventbus-future-decision.md` and `issues/20261109-112952_adrrev010_eventbus-authz-harden.md`.

## Unresolved Questions
- `Needs confirmation`: whether the inline DLQ file write path still exists; the foreign-key assumption in the manual deletion procedure; the ADR-013 Out of Scope text.
- Maintainer decision: whether `/subscribe` should support replay from the start, and whether a metrics endpoint is wanted.

## AI Implementation Instruction
- Start from current code and `schema.sql`; document what exists before changing behavior.
- Do not change authorization or role behavior.
- Do not write approval records on a maintainer's behalf.
- Write documentation in English and follow the docs content policy; do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-113152
- **Related target files**: `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/24_eventbus/eventbus_10_health_endpoint.md`, `docs/24_eventbus/eventbus_11_replay_endpoint.md`, `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md`, `scripts/eventbus/health_route.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/dlq_repo.py`
