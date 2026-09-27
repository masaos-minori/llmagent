## Goal

Create `scripts/agent/eventbus_client.py`: an Agent-side HTTP client that publishes events to Event Bus's existing `/publish` endpoint (REQ-001, REQ-002).

## Scope

In scope: a new client module with a publish method, config dataclass, and typed error handling. Out of scope: any Event Bus server-side code; wiring this client into any specific Agent trigger point (UNK-01, deferred to a future decision).

## Assumptions

- Event Bus's `/publish` endpoint's request/response shape and auth header format (confirmed via Reference Files) remain unchanged at implementation time — re-confirm immediately before writing the client, since this is a fast-moving codebase.

## Design decisions

- Follow `scripts/agent/memory/embedding_client.py`'s existing convention: a `@dataclass` config (URL, timeout, auth token), an `httpx.AsyncClient`-based method, and a typed result/error rather than a raised exception on failure — keeps this client consistent with how the Agent already wraps external HTTP dependencies.

## Alternatives considered

- Raising an exception on publish failure instead of a typed result: rejected — inconsistent with `embedding_client.py`'s existing pattern, and would force every future caller to add its own try/except rather than handling a typed error value.

## Implementation

### Target file

`scripts/agent/eventbus_client.py`

### Procedure

1. Re-confirm `scripts/eventbus/publish_route.py::publish()`'s request body shape, response shape, and required auth header (per `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`'s per-role token model) immediately before writing the client.
2. Create a `@dataclass EventBusClientConfig` holding `publish_url`, `timeout`, and the publisher auth token, following `EmbeddingClientConfig`'s shape.
3. Create an `EventBusClient` (or similarly named) class with an async `publish(event: dict) -> EventBusPublishResult` method that POSTs to the configured `publish_url` with the auth header and the event body.
4. On success (2xx), return a typed success result. On failure (network error, non-2xx), return a typed error result (mirroring `EmbeddingResult`/`EmbeddingErrorKind`'s success/error split) — do not raise.

### Method

New module, following an existing local convention (`embedding_client.py`) rather than inventing a new client-shape from scratch.

### Details

- `scripts/eventbus/publish_route.py::publish()` is the exact endpoint this client calls — re-read it first to confirm its current request/response contract before coding against it.
- `docs/10_adr/ADR-013-eventbus-authentication-authorization.md` defines the per-role token header format this client must send.
- No Python-level import of `eventbus.*` modules — this client uses `httpx` over HTTP only; `.importlinter`'s `eventbus-is-isolated` contract (forbidding `eventbus`→`agent` imports) is not implicated by this direction.

## Compatibility considerations

New module, no existing callers — cannot break existing behavior. If Event Bus's `/publish` contract changes in the future, only this one file needs updating.

## Security considerations

The auth token is passed as a config value, not hardcoded — follow `embedding_client.py`'s existing pattern for where the token value itself is sourced (do not add a new secrets-loading mechanism).

## Rollback considerations

New, uncalled file — revert via `git revert` or simple deletion; no other code depends on it yet.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/eventbus_client.py` | Unit | `uv run pytest tests/agent/test_eventbus_client.py -q` | All tests pass, at least 1 collected |
| `scripts/agent/eventbus_client.py` | Static | `uv run ruff check scripts/agent/eventbus_client.py && uv run mypy scripts/agent/eventbus_client.py && uv run lint-imports && uv run bandit -r scripts/agent/eventbus_client.py -c pyproject.toml` | All pass |

## Completion criteria

- The client successfully publishes to a running Event Bus instance and receives a typed success result (AC-1).
- A publish failure is returned as a typed error, not an unhandled exception (AC-2).

## Out of scope

- Wiring this client into any specific Agent trigger point (UNK-01).
- Any change to Event Bus's server-side `/publish` endpoint.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by the sibling procedure for `tests/agent/test_eventbus_client.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no `docs/00_index.md` task-scope row maps this new file |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/done/20260927-115602_eventbus005_implement-agent-to-eventbus-publish-integration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-120356_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-123304
- **Related target files**: scripts/agent/eventbus_client.py
