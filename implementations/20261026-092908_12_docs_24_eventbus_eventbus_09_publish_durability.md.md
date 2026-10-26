## Goal

Document requeue delivery semantics (replay vs immediate broker push) and the side-effect
failure metrics in `docs/24_eventbus/eventbus_09_publish_durability.md` (REQ-001, REQ-002;
Acceptance 1, 5).

## Scope

- Modify only `docs/24_eventbus/eventbus_09_publish_durability.md`.

## Assumptions

- Requeue (`dlq_requeue`, `scripts/eventbus/dlq_route.py`) is delivered through consumer replay
  via the lineage model (`redeliver_event`); it does NOT call `broker.publish()`. This is
  today's behavior and is not currently stated to operators.
- The decision on whether immediate broker notification is required is an owner decision
  (UNK-01), recorded before this row is executed.
- `eventbus_dlq_file_write_failure_total` is introduced by an earlier-seq procedure in this
  Plan (`scripts/eventbus/dlq.py`, seq 05); this doc records its exposition, not its creation.
  (case-2 cross-reference)

## Design decisions

- **Requeue-delivery subsection.** Add a section stating requeue is delivered through consumer
  replay (not immediate broker push), and note the UNK-01 decision on whether immediate broker
  notification should be added.
- **Metrics subsection.** Update the existing Metrics section to record whether the side-effect
  counters (`eventbus_jsonl_append_failure_total`, `eventbus_broker_notify_failure_total`, and
  the new `eventbus_dlq_file_write_failure_total`) are exposed via a `/metrics` endpoint
  (UNK-02 adoption) or documented as intentionally log-only.

## Alternatives considered

- Describing immediate-push delivery: adopt only if UNK-01 selects it; record the current
  replay-based reality regardless.

## Implementation

### Target file

`docs/24_eventbus/eventbus_09_publish_durability.md`

### Procedure

1. Add a "Requeue Delivery Semantics" subsection stating requeue uses consumer replay via the
   lineage model and is not immediate broker push; record the UNK-01 decision.
2. Update the "Metrics" section to state whether the side-effect failure counters are exported
   (UNK-02 adoption) or documented as intentionally log-only; add the new DLQ-file-write
   counter name.

### Method

Additive prose sections; do not alter existing verified content.

## Compatibility considerations

- Docs-only; update Migration Notes per `skills/DESIGN.md` if the doc is referenced elsewhere.

## Security considerations

- N/A: no secrets or tokens documented (INV-05).

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain eventbus` — pass.
- Confirm the requeue/metrics claims match `scripts/eventbus/dlq_route.py` and `dlq.py`.

## Completion criteria

- The doc states replay-based requeue delivery and the side-effect failure metric observability.

## Out of Scope

- Changing requeue to immediate broker push (UNK-01).
- Adding a `/metrics` endpoint (UNK-02; app.py, seq 7).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document requeue delivery semantics + side-effect failure metrics | Pending | — | — | UNK-01 (requeue) / UNK-02 (endpoint) decisions gate the recorded values |
| 2 | Run the documentation checkers (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-01 / UNK-02 recorded; resolution values needed before writing | Classified non-blocking 2026-10-25 | Yes | 20261025 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/done/20261023-154326_eventbus007_side-effects-metrics-health-recovery.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123218_eventbus007_side-effects-metrics-health-recovery.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-092908
- **Related target files**: `docs/24_eventbus/eventbus_09_publish_durability.md`
