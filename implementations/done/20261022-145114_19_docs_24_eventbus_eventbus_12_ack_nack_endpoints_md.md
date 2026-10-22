## Goal

Rename the NACK response key in `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` from `delivery_failure_count` to `consumer_delivery_failure_count`, matching the renamed response key (`REQ-003`; `REQ-007`; `AC-3`, `AC-7`).

## Scope

Only `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`. `scripts/eventbus/ack_route.py` (row 2) stops returning the legacy `delivery_failure_count` key and returns `consumer_delivery_failure_count` instead; this doc must describe the final key.

## Assumptions

- `scripts/eventbus/ack_route.py` (row 2) maps the new `NackResult.status` to the existing 404/409 outcomes and returns `consumer_delivery_failure_count` (the nacking consumer's per-consumer count) under the new key, plus `dlq_promoted: true` when promoted.
- The ACK response (`event_id`, `acked`, `seq`, `already_acked`) is unaffected.

## Design decisions

- Rename the single key reference in the NACK success description; keep everything else (the state-transition table, the ACK description) unchanged.
- The value semantics are unchanged (it was always the per-consumer count reported under a misleading key), so this is a rename, not a rewrite.

## Alternatives considered

- Rewording the key as "the per-consumer failure count" without the identifier — rejected: the response key is a stable identifier that clients read, and `AC-3` requires the exact key name `consumer_delivery_failure_count`.

## Implementation

### Target file

`docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`

### Procedure

1. In the NACK success description, rename the response key `delivery_failure_count` to `consumer_delivery_failure_count`.
2. Run the docs checkers.

### Method

- Edit the NACK success sentence from:

  > `POST /nack?event_id=<id>&consumer_id=<id>`. Success returns HTTP 200 with `event_id` and `delivery_failure_count`, which is the nacking consumer's per-consumer failure count after this NACK. `dlq_promoted: true` is added when the event was promoted.

  to use the renamed key:

  > `POST /nack?event_id=<id>&consumer_id=<id>`. Success returns HTTP 200 with `event_id` and `consumer_delivery_failure_count`, which is the nacking consumer's per-consumer failure count after this NACK. `dlq_promoted: true` is added when the event was promoted.

### Details

- Evidence in-file: line 40 names `delivery_failure_count` as the NACK response key. No other occurrence of `delivery_failure_count` exists in this document (the state-transition table refers to "the failure count" generically).

## Compatibility considerations

N/A: documentation-only change; no runtime contract is affected.

## Security considerations

N/A: no auth, authorization, or input-handling path is described here beyond what already exists.

## Rollback considerations

N/A: revert the commit that makes this change.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| Docs | Docs checkers | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` | Pass |
| Reference table sync | Check | `generate_reference_table.py --check` | Pass |

## Completion criteria

`docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` reports the NACK response key as `consumer_delivery_failure_count`, names no `delivery_failure_count`, and the docs checkers plus `generate_reference_table.py --check` pass.

## Out of Scope

- Editing any other EventBus document (each is a separate row).
- Changing the NACK response behavior itself (`scripts/eventbus/ack_route.py`, row 2).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename the NACK response key to `consumer_delivery_failure_count` | Completed | 2026-10-22 | 2026-10-22 | |
| 3 | Run the documentation checkers | Completed | 2026-10-22 | 2026-10-22 | check_docs_quality/structure/content_policy, generate_reference_table.py --check all pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-22 | 2026-10-22 | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-007` — update the four EventBus documents to describe only the per-consumer counter, the status outcomes, and the renamed key
- **Source issue**: `issues/20261022-124142_evcounter_decide-event-level-failure-counters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130338_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-145114
- **Related target files**: `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`
