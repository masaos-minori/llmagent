## Goal

Evaluate and, once the governing decision is made, implement `REQ-002` in
`scripts/eventbus/dlq.py`: decide DLQ promotion from the **per-consumer** failure count
instead of the shared `events.delivery_failure_count`, so one faulty consumer cannot
exhaust the shared DLQ budget before other consumers process the event (`EVENTBUS-012`).

## Scope

Modifies `scripts/eventbus/dlq.py` only. Heavily cross-row: the concrete change depends
on (a) the per-event vs per-consumer DLQ-unit decision resolved in the `ADR-006` row
(`REQ-006`), and (b) where the per-consumer failure count physically lives
(`consumer_delivery` vs the `events` table), also decided by the `REQ-002` / ADR-006
decision. See Design decisions.

## Assumptions

- Promotion gating currently lives in two places: `_shared_promote` (sweep, gated on
  `delivery_failure_count >= max_retry`) and `ack_route._nack_and_promote` (inline,
  gated on the returned failure count). This row owns the `dlq.py` side only.
- The per-consumer count is `consumer_delivery_failure_count`; it is currently
  incremented per `(event, consumer)` NACK but its storage location and promotion use
  are unresolved (see Current state).

## Current state (adversarial verification)

- `_shared_promote` (lines 47-70): sweeps `events WHERE delivery_failure_count >= ?`
  using the **shared** lifetime counter. No consumer dimension.
- `_shared_promote_single` (lines 73-100): promotes any non-DLQ'd event by `event_id`
  with **no** failure-count gate at all; the inline gate lives in `ack_route.py`.
- `promote_single` / `sweep_orphans` (lines 117-114): thin public wrappers.
- `consumer_delivery_failure_count` is incremented by `nack_event()` but is NOT used
  for promotion. Its column currently lives on the `events` table (schema.sql line 17),
  i.e. it still accumulates across consumers — the very defect `REQ-002` targets.

## Design decisions

- **This row cannot be safely implemented until the per-event vs per-consumer DLQ-unit
  decision is made.** The source issue explicitly defers it: "decide in ADR-006 whether
  the DLQ unit is per event or per consumer." Do not guess.
- If the decision is **per-consumer**: promotion must compare the
  `consumer_delivery_failure_count` for the specific `(consumer_id, event_id)` against
  `max_retry`, not the shared `delivery_failure_count`. That requires the inline gate
  in `ack_route._nack_and_promote` to pass `consumer_id` and read the per-consumer
  count, and the sweep in `_shared_promote` to group by consumer. Coordinate with the
  `ack_route.py` and `ADR-006` rows.
- If the decision is **per-event**: promotion stays on `delivery_failure_count` and
  `REQ-002` reduces to documenting/confirming current behavior — no `dlq.py` change.
- The per-consumer count's storage (events table vs `consumer_delivery`) must be
  settled together with the above; moving it touches the schema rows and
  `delivery_repo.py`.

## Alternatives considered

- Changing `_shared_promote` to filter on `consumer_delivery_failure_count` alone —
  rejected without the per-event/per-consumer decision: the sweep has no single
  `consumer_id`, so a per-consumer predicate is undefined for a global sweep.

## Implementation

### Target file

`scripts/eventbus/dlq.py`

### Procedure

1. **BLOCKED** on the ADR-006 per-event vs per-consumer decision. Do not edit until it
   is recorded in the `ADR-006` row.
2. If **per-consumer**: gate promotion on the per-consumer count. For the inline path,
   ensure `promote_single` receives `consumer_id` and the caller passes the
   `consumer_delivery_failure_count` for that `(consumer_id, event_id)`; for the sweep
   path, group `_shared_promote` by `consumer_id` and apply `max_retry` per consumer.
3. If **per-event**: no change required; record the confirmation in the Validation plan.

### Method

- Read `ack_route._nack_and_promote` to see how the inline gate currently reads the
  failure count and whether `consumer_id` is available at that call site.
- Confirm the physical location of `consumer_delivery_failure_count` (events table vs
  `consumer_delivery`) after the schema rows land.
- Lint and test: `ruff`, `mypy --no-namespace-packages`, `bandit`, `lint-imports`, then
  targeted `pytest tests/eventbus/`.

### Details

- Do not hardcode column names; read them from `_constants.py`.
- Preserve the atomic write-before-DB-update ordering in `_atomic_write` /
  `_shared_promote_single`.

## Compatibility considerations

- Any signature change to `promote_single` ripples to `ack_route._nack_and_promote`
  (coordinate via the `ack_route.py` row).

## Security considerations

- Promotion gating affects availability (when events leave the active queue); the
  per-consumer boundary prevents one misbehaving consumer from a denial-of-service on
  others. Parameterized SQL throughout.

## Rollback considerations

- Revert to the shared-counter predicate; restore the pre-change `promote_single`
  signature if added.

## Validation plan

- Per-consumer: consumer A repeatedly NACKs while consumer B processes the same event;
  B must NOT be sent to the DLQ by A's NACKs (`REQ-002`).
- Per-event (if decided): confirm existing promotion behavior unchanged.
- `ruff`, `mypy --no-namespace-packages`, `bandit`, `lint-imports`.

## Completion criteria

- Promotion is gated on the failure-count source dictated by the ADR-006 decision.
- If per-consumer: one consumer's NACKs do not advance another consumer's DLQ timer.

## Out of scope

- The per-event vs per-consumer decision itself (`ADR-006` row, `REQ-006`).
- Moving `consumer_delivery_failure_count` between tables (schema rows + `delivery_repo.py`).
- The inline gate in `ack_route._nack_and_promote` (`ack_route.py` row) — coordinate only.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement REQ-002 promotion change in dlq.py | Completed | 2026-10-10 | 2026-10-10 | Landed in commit 4b58334a0 (fix: gate DLQ promotion on per-consumer failure count), bundled with the ack_route.py inline-gate and delivery_repo.py changes. Current dlq.py gates promotion on per-consumer `consumer_delivery_failure_count` via `_all_attempted_consumers_exceeded`; shared `delivery_failure_count` ignored. Adversarial-verified against committed source. |
| 2 | Add or update tests per Validation plan | Completed | 2026-10-10 | 2026-10-10 | `TestReq002PerConsumerDlqPromotion` (3 tests) in `tests/eventbus/test_eventbus_ack_nack.py` covers the completion criterion (consumer A's NACKs must not advance consumer B's DLQ timer). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-10 | 2026-10-10 | ruff format/check clean, mypy clean, lint-imports contracts kept, bandit 0 High / 0 Medium (3 Low), pytest 340 passed / 1 skipped. |
| 4 | Update documentation | Completed | 2026-10-10 | 2026-10-10 | Updated `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` to reflect per-consumer promotion gating (was stale shared-counter claims). quality/structure/content_policy/japanese checkers pass. |

### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | REQ-002 DLQ-promotion source depends on the per-event vs per-consumer decision deferred to ADR-006 | Yes | 2026-10-09 | ADR-006 now decides per-consumer (commit 4a24dd3c1). Implementation landed in commit 4b58334a0 (bundled with the ack_route.py inline-gate and delivery_repo.py changes); see Execution Status notes. |

### Work Items Created

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-071937
- **Related target files**: `scripts/eventbus/dlq.py`
