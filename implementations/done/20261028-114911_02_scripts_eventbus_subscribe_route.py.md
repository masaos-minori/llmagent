# Procedure: remove the duplicated checks from the subscribe route and apply the narrowed topic list

## Goal

Make `subscribe` rely on the shared decision and use the effective topic list for both live delivery and replay (Plan REQ-002, REQ-003).

## Scope

- Modify only `scripts/eventbus/subscribe_route.py`.
- In scope: the `_identity`, `REQ-011`, `REQ-012` and `REQ-013` check blocks and the use of `topic` for `broker.subscribe` and the replay query.
- Out of scope: resume-position logic, Last-Event-ID handling, SSE generation, tests and docs.

## Assumptions

- Row 1 (`scripts/eventbus/auth.py`) has landed: `effective_topics` (new, created by row 1) and the pairwise `Principal` exist when this procedure runs.
- `resolve_subscribe_identity` in `app.py` has already called `require_consumer_identity` for the requested topics before `subscribe` runs.
- Overlap (compatible): `plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md` also targets `scripts/eventbus/ack_route.py` and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`; it edits the promotion block of `_nack_and_promote` and one transition-table row, which this procedure does not touch. `plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` also targets `scripts/eventbus/app.py` (`_shutdown_lifespan` only).

## Design decisions

- Keep only the "Missing consumer_id" HTTP 400 for a principal with grants; drop the re-derived consumer_id and topic membership checks (the dependency already enforced them).
- Compute `topic = effective_topics(_principal, consumer_id, topic)` once, before the Last-Event-ID handling, so `broker.subscribe(list(topic), ...)` and the replay SQL use the same list.

## Alternatives considered

- Reject an omitted topic with 400/403 — rejected as the default by the Plan (UNK-01); it would break the default subscriber configuration.

## Implementation

### Target file

`scripts/eventbus/subscribe_route.py`

### Procedure

- Delete the `if isinstance(_identity, Principal):` block and the `REQ-011` and `REQ-013` blocks, including the comment "empty topic list means subscribe to all topics".
- Keep the `REQ-012` fail-closed 400 for a missing `consumer_id` when `_principal.consumer_grants` is non-empty.
- Import `effective_topics` from `eventbus.auth`; call it right after the missing-`consumer_id` check and rebind `topic`.
- When the narrowed list is empty (a consumer with no grants reached here only if the dependency was bypassed), raise HTTP 403 rather than subscribing to all topics.

### Method

Delete the duplicated blocks and add one rebind of `topic`; the replay query already branches on `if topic:`, so a non-empty narrowed list takes the filtered branch.

### Details

- Verified: `broker.subscribe(list(topic), consumer_id=consumer_id)` treats `[]` as all topics, so the rebind must happen before that call.
- `_identity` stays in the signature (the `app.py` wrapper passes it) but is no longer read; leave the parameter to avoid a signature change in this row.

## Compatibility considerations

- A subscribe request without `topic` from a restricted consumer now receives only its granted topics instead of all topics (the behavior change this Plan requires).
- `scripts/agent/eventbus_subscriber.py` sends `topic` only when configured; with the default `topics=None` it keeps working inside the granted set.

## Security considerations

- Removes a bypass: an omitted topic can no longer widen access.
- 403 for an empty narrowed list keeps the endpoint fail-closed.

## Rollback considerations

Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_subscribe.py tests/eventbus/test_eventbus_replay_subscribe.py -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/subscribe_route.py`; `uv run ruff check scripts/eventbus/subscribe_route.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/subscribe_route.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- `subscribe_route.py` contains no consumer_id or topic membership check of its own.
- Live delivery and replay both use the narrowed list when `topic` is omitted.

## Out of Scope

- Authorization model changes (row 1), ACK/NACK routes, tests and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-130500 | 20261028-130500 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261028-130500 | 20261028-130500 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-130500 | 20261028-130500 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-130500 | 20261028-130500 |  |

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
- **Requirement ID**: REQ-002, REQ-003 (omitted-topic narrowing, one shared decision)
- **Source issue**: issues/20261027-155843_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-114911
- **Related target files**: scripts/eventbus/subscribe_route.py