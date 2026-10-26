## Goal

State in the `dlq_requeue` response (`scripts/eventbus/dlq_route.py`) that requeue is delivered
through consumer replay rather than immediate broker push, making delivery unambiguous to
operators (REQ-001; Acceptance 1).

## Scope

- Modify only `scripts/eventbus/dlq_route.py`: `dlq_requeue()` (current lines 49-99).

## Assumptions

- `dlq_requeue()` (lines 49-99) creates a new event row via `redeliver_event` (lineage model)
  and does NOT call `broker.publish()` — requeue is replay-based today; this is just not stated
  to operators.
- The response dict (lines 80-92) is returned to the caller and can carry an extra field.

## Design decisions

- **Delivery field.** Add `"delivery": "replay"` (or `"delivery_method": "consumer_replay"`) to
  the success response (lines 80-92) stating that the requeued event is delivered through
  consumer replay, not immediate broker push (REQ-001; Acceptance 1).

## Alternatives considered

- Adding a full delivery-timing block: rejected — a single scalar field is sufficient and keeps
  the response shape minimal.

## Implementation

### Target file

`scripts/eventbus/dlq_route.py`

### Procedure

1. In `dlq_requeue()`, add a `"delivery"` field to the success `resp` dict (lines 80-92)
   stating replay-based delivery, e.g. `"delivery": "replay"` alongside `"requeued": True`.
2. Keep the audit record (`log_privileged_action`, lines 72-78) and the rest of the response
   unchanged.

### Method

In-place edit of the response dict.

### Details

- The value should reflect the actual mechanism (replay via `redeliver_event`), not an
  immediate-push claim. If the owner decides (UNK-01) that immediate broker notification should
  be added, the field value and mechanism change together — implement the recorded decision.

## Compatibility considerations

- The response gains one field; existing consumers reading `requeued`/`new_event_id` are
  unaffected. Document the field in `docs/24_eventbus/eventbus_09_publish_durability.md`
  (seq 12).

## Security considerations

- N/A: no secrets or tokens in the response (INV-05).

## Rollback considerations

- Revert the commit; the field is removed.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_dlq.py` — assert the requeue response states
  replay-based delivery.
- `uv run pytest tests/eventbus/` — full EventBus suite passes.
- `uv run vulture`, `uv run bandit scripts/eventbus/ -c pyproject.toml`.
- `uv run mypy`, `uv run ruff` on the file.

## Completion criteria

- The `dlq_requeue` response states replay-based delivery.

## Out of Scope

- Changing requeue to immediate broker push (UNK-01 owner decision; would be a larger change).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | State replay-based delivery in the `dlq_requeue` response | Pending | — | — | UNK-01 owner decision gates the value |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-01 (immediate broker notification on requeue) is an owner decision | Classified non-blocking 2026-10-25; response value needs the decision | Yes | 20261025 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/done/20261023-154326_eventbus007_side-effects-metrics-health-recovery.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123218_eventbus007_side-effects-metrics-health-recovery.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-092908
- **Related target files**: `scripts/eventbus/dlq_route.py`
