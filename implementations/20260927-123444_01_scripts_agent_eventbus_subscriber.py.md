## Goal

Create `scripts/agent/eventbus_subscriber.py`: an Agent-side SSE client that opens Event Bus's existing subscribe/replay stream, handles disconnection/reconnection, and surfaces failures without crashing (REQ-001, REQ-002, REQ-003).

## Scope

In scope: a new streaming-client module with reconnection handling respecting the one-connection-per-`consumer_id` constraint. Out of scope: any Event Bus server-side code; the Agent-side event-dispatch mechanism (UNK-01, deferred).

## Assumptions

- Event Bus's SSE stream format and `ConsumerAlreadyConnectedError` trigger condition (confirmed via Reference Files) remain unchanged at implementation time — re-confirm immediately before writing the client.

## Design decisions

- No existing Agent-side SSE consumption pattern exists to reuse (confirmed via `rg` — zero matches for `text/event-stream`/`StreamingResponse`/`aiter_lines` under `scripts/agent/`), so the streaming loop is new implementation. Surrounding conventions (config dataclass, typed error surface) still follow `scripts/agent/memory/embedding_client.py` for consistency.
- Reconnection uses a fresh `consumer_id` per connection attempt rather than waiting to confirm the prior connection's closure — simpler, avoids a closure race. Confirm during implementation whether Event Bus tracks any other consumer-scoped state (beyond the connection slot) that this approach would reset unexpectedly.

## Alternatives considered

- Waiting for confirmation of the prior connection's closure before reusing the same `consumer_id`: rejected as the primary approach — requires a way to detect closure from the client side that Event Bus's API does not obviously expose; a fresh-`consumer_id`-per-attempt approach avoids this entirely, at the cost of the trade-off noted in Design decisions.

## Implementation

### Target file

`scripts/agent/eventbus_subscriber.py`

### Procedure

1. Re-confirm `scripts/eventbus/subscribe_route.py::subscribe()`'s exact SSE event format and `scripts/eventbus/broker.py::ConsumerAlreadyConnectedError`'s trigger condition (line 64) immediately before writing the client.
2. Create a `@dataclass EventBusSubscriberConfig` (subscribe URL, timeout, consumer token), following `EmbeddingClientConfig`'s shape.
3. Create a subscriber class with an async generator method that opens the SSE stream via `httpx`'s streaming support and yields parsed events.
4. Implement reconnection: on stream disconnection, generate a fresh `consumer_id` and reconnect, per the Design decision above.
5. Wrap stream-level errors in a typed result/exception distinct from a raised, uncaught exception, so a caller can log and continue rather than crash.

### Method

New streaming-consumer module; no local convention to directly reuse for the streaming loop itself (per Design decisions), though surrounding config/error conventions follow `embedding_client.py`.

### Details

- `scripts/eventbus/subscribe_route.py` and `scripts/eventbus/replay_route.py` (`format=sse`) are the two candidate endpoints — confirm which one this client should use (subscribe is the live-stream path; replay is the catch-up/historical path) before finalizing which one this module targets. Default to `subscribe_route.py` per the Issue's own framing ("SSE subscribe"), using `replay` only if `subscribe` proves unsuitable during implementation.
- `ConsumerAlreadyConnectedError` (line 64) is the correctness constraint reconnection logic must respect.
- No Python-level import of `eventbus.*` modules — HTTP-only client, same finding as the EVENTBUS-005 procedure.

## Compatibility considerations

New module, no existing callers — cannot break existing behavior.

## Security considerations

The consumer auth token is passed as a config value, not hardcoded — follow `embedding_client.py`'s existing pattern.

## Rollback considerations

New, uncalled file — revert via `git revert` or deletion.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/eventbus_subscriber.py` | Unit | `uv run pytest tests/agent/test_eventbus_subscriber.py -q` | All tests pass, at least 1 collected |
| `scripts/agent/eventbus_subscriber.py` | Static | `uv run ruff check scripts/agent/eventbus_subscriber.py && uv run mypy scripts/agent/eventbus_subscriber.py && uv run lint-imports && uv run bandit -r scripts/agent/eventbus_subscriber.py -c pyproject.toml` | All pass |

## Completion criteria

- The client opens the SSE stream and yields received events (AC-1).
- Simulated disconnection is followed by successful reconnection without `ConsumerAlreadyConnectedError` (AC-2).
- A stream failure is surfaced without crashing the process (AC-3).

## Out of scope

- The Agent-side event-dispatch mechanism (UNK-01).
- Any change to Event Bus's server-side SSE/subscribe/replay logic.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-141518 | 20260927-141518 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260927-141518 | 20260927-141518 | Covered by the sibling procedure for `tests/agent/test_eventbus_subscriber.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-141518 | 20260927-141518 | ruff/pyright/lint-imports/bandit clean (mypy still blocked repo-wide by the same pre-existing tool_constants.py issue). Full suite: 38 pre-existing failures confirmed unrelated (none reference eventbus_subscriber; failure set differs from prior cycle's run, consistent with concurrent session's ongoing WIP), 7944 passed including this module's 5 new tests |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-141518 | 20260927-141518 | N/A: no `docs/00_index.md` task-scope row maps this new file |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/done/20260927-115629_eventbus006_implement-agent-eventbus-sse-subscribe-integration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-120532_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-123444
- **Related target files**: scripts/agent/eventbus_subscriber.py