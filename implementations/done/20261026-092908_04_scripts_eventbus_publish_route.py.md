## Goal

Confirm the two existing side-effect failure counters in `scripts/eventbus/publish_route.py`
are the exported set for REQ-002; no code change is required here unless UNK-02 adopts a
`/metrics` endpoint that needs them registered explicitly.

## Scope

- Read-only confirmation of `scripts/eventbus/publish_route.py`: `_jsonl_append_failure_counter`
  (line 25) and `_broker_notify_failure_counter` (line 30). No modification unless UNK-02
  requires it.

## Assumptions

- The two counters are module-level `prometheus_client.Counter` instances in the default
  registry, so they are exposed automatically by any `/metrics` endpoint that registers the
  default registry (see seq 7, app.py).
- The DLQ-file-write-failure counter lives in `scripts/eventbus/dlq.py` (seq 5), not here.

## Design decisions

- **No change.** The two existing counters are the side-effect failure set REQ-002 names; they
  export with the default registry. Record in `docs/24_eventbus/eventbus_09_publish_durability.md`
  (seq 12) that they are observable (or documented log-only if UNK-02 declines an endpoint).

## Alternatives considered

- Adding a third counter here: rejected — the DLQ-file-write counter belongs in `dlq.py`
  (seq 5), where the write happens.

## Implementation

### Target file

`scripts/eventbus/publish_route.py`

### Procedure

1. Confirm `_jsonl_append_failure_counter` (line 25) and `_broker_notify_failure_counter`
   (line 30) are the only side-effect failure counters in this module and both live in the
   default Prometheus registry.
2. Make no code change unless UNK-02 explicitly requires registering these counters at a
   custom `/metrics` route outside the default registry.

### Method

Read-only verification; no edit expected.

### Details

- If UNK-02 adopts an endpoint that uses a non-default registry, register these two counters
  there and note it — otherwise leave this file untouched.

## Compatibility considerations

- N/A: no change.

## Security considerations

- N/A: counters carry no token values (INV-05).

## Rollback considerations

- N/A: no change.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_publish.py` if present; otherwise confirm the two
  counters increment on the fault paths already covered.
- `uv run mypy`, `uv run ruff` if any change is made (expected: none).

## Completion criteria

- The two existing counters are confirmed as the exported side-effect set; no unrequested
  change is introduced.

## Out of Scope

- The DLQ-file-write-failure counter (dlq.py, seq 5).
- Adopting a `/metrics` endpoint (UNK-02; app.py, seq 7).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the two existing side-effect counters are the exported set | Pending | — | — | No change expected unless UNK-02 requires it |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/done/20261023-154326_eventbus007_side-effects-metrics-health-recovery.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123218_eventbus007_side-effects-metrics-health-recovery.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-092908
- **Related target files**: `scripts/eventbus/publish_route.py`
