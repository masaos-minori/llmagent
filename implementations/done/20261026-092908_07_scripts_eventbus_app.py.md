## Goal

Register the metrics exposition route in `scripts/eventbus/app.py` under the existing
loopback + bearer-auth model — but only if UNK-02 adopts a `/metrics` endpoint. If counters are
documented as log-only, make no change here.

## Scope

- Modify `scripts/eventbus/app.py` only if UNK-02 adopts an endpoint: register a `/metrics`
  route (conditional). No change if counters stay log-only.

## Assumptions

- Other routes apply a loopback + bearer-auth model; a new `/metrics` route inherits that
  contract (plan Assumptions).
- Registering the default registry via `generate_latest` exposes the two existing side-effect
  counters (publish_route.py) and the new DLQ-file-write counter (dlq.py) automatically.
- `eventbus008` also edits `app.py` (REQ-0 tag classification at lines 25,26,249,267) —
  comment-only, sequenced after this behavioral plan; additive, no contradiction.

## Design decisions

- **Conditional route.** If UNK-02 adopts an endpoint, register `/metrics` under the existing
  loopback + auth model using `generate_latest` from `prometheus_client`; the default registry
  (including the side-effect and DLQ counters) is exposed automatically.
- **No endpoint.** If UNK-02 declines, leave `app.py` untouched and document the counters as
  intentionally log-only (seq 12).

## Alternatives considered

- A public `/metrics` route: rejected — expands the auth/loopback surface (Risk in the plan);
  restrict to the existing loopback + auth model with owner sign-off (UNK-02).

## Implementation

### Target file

`scripts/eventbus/app.py`

### Procedure

1. Proceed only if UNK-02 is decided to adopt an endpoint. Register a `/metrics` route that
   returns `generate_latest(REGISTRY)` (default registry), placed alongside the other route
   registrations, applying the same loopback + bearer-auth guard used by other routes.
2. Confirm the two existing side-effect counters and the new DLQ-file-write counter export with
   the default registry (no per-counter registration needed).
3. If UNK-02 declines, make no change.

### Method

Additive route registration under the existing auth/loopback model; no new symbols.

### Details

- Reuse the existing loopback + bearer-auth pattern rather than introducing a new guard.
- Coordinate with `eventbus008` (comment-only edits to `app.py`) — implement this behavioral
  change first, then the comment cleanup.

## Compatibility considerations

- A `/metrics` route adds an endpoint; document it in `docs/24_eventbus/eventbus_10_health_endpoint.md`
  (seq 13). If not adopted, no compatibility impact.

## Security considerations

- If adopted, `/metrics` must respect the loopback + bearer-auth model so metrics are not
  exposed publicly (plan Risk). No token values are emitted in the counters (INV-05, REQ-007).

## Rollback considerations

- Revert the commit; the route is removed.

## Validation plan

- If a route is added: `uv run pytest tests/eventbus/test_eventbus_app_isolation.py` — confirm
  the route respects loopback + auth.
- `uv run pytest tests/eventbus/` — full EventBus suite passes.
- `uv run mypy`, `uv run ruff` on the file.

## Completion criteria

- If UNK-02 adopts an endpoint, `/metrics` is registered under the loopback + auth model and
  exports the side-effect and DLQ counters; otherwise `app.py` is unchanged.

## Out of Scope

- Choosing whether to adopt an endpoint (UNK-02 owner decision).
- Registering a non-default registry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Register `/metrics` under loopback + auth model (only if UNK-02 adopts) | Pending | — | — | UNK-02 owner decision gates whether any change is made |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-02 (metrics endpoint adoption) is an owner decision | Classified non-blocking 2026-10-25; adoption decision needed before any edit | Yes | 20261025 |

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
- **Related target files**: `scripts/eventbus/app.py`
