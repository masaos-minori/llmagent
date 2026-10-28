# Procedure: authorize the (consumer_id, event topic) pair in ACK and NACK before changing delivery state

## Goal

Make the ACK and NACK routes read the event's topic and run the shared decision on the pair before any delivery write (Plan REQ-004).

## Scope

- Modify only `scripts/eventbus/ack_route.py`.
- In scope: the start of `_do_ack` and `nack`, after the existing `consumer_id` presence checks.
- Out of scope: the promotion block of `_nack_and_promote` (another Plan), ack/nack state logic, `app.py`, tests and docs.

## Assumptions

- Row 1 (seq 01) has landed and the `get_event_topic` procedure (seq 05, `scripts/eventbus/event_repo.py`) has been executed first, out of filename order, because this module imports it: `authorize_consumer_access` (new) and `get_event_topic` (new) exist.
- A missing event keeps its existing 404 path, so the pair check runs only when the event exists; the order does not reveal event existence to an unauthorized consumer because an unauthorized `consumer_id` is rejected first by the 403 on the grants check.
- Overlap (compatible): `plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md` also targets `scripts/eventbus/ack_route.py` and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`; it edits the promotion block of `_nack_and_promote` and one transition-table row, which this procedure does not touch. `plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` also targets `scripts/eventbus/app.py` (`_shutdown_lifespan` only).

## Design decisions

- Look up the topic inside `run_with_db_lock`, outside the ACK/NACK write transaction, so a rejected request performs no write.
- Pass `request` into `_do_ack` so audit records keep the request id; `ack_event` already holds it.

## Alternatives considered

- Keep the independent sets and add a second check — rejected: it keeps two sources of truth for the same grant (Plan Design Decision 1).

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

- Add an `authorize_event_pair` (new) helper (new) in this module: `topic = await run_with_db_lock(lambda: get_event_topic(db, event_id))`; when `topic` is not `None`, call `authorize_consumer_access(request, principal, consumer_id, [topic])`; when it is `None`, return and let the existing not-found path run.
- Extend `_do_ack` with a keyword `request` and call the helper after the `consumer_id` presence check and before `_ack_and_offset`; pass `request=request` from `ack_event`.
- In `nack`, call the helper after the `idempotency_key` check and before `_nack_and_promote`; both calls use `_principal`, the principal that the route already receives.
- When `_principal` is `None` (a direct call bypassing the dependency chain) raise HTTP 403 instead of skipping the check.

### Method

Add one helper and two call sites; import the two new symbols from `eventbus.auth` and `eventbus.event_repo`.

### Details

- `app.py` calls `ack_event_route(request, event_id=..., consumer_id=..., _principal=...)`, so `request` is already available in both handlers.
- `nack` currently accepts `event_id` default `""`; the existing 400 for an empty id runs before the new check.
- A concurrent dedup: the lookup and the later write are not one transaction, which is acceptable because a topic never changes after publish.

## Compatibility considerations

- Behavior change: ACK or NACK of an event whose topic is not granted to `consumer_id` now returns 403 instead of succeeding.
- Status codes and bodies for authorized requests are unchanged.

## Security considerations

- Closes the gap where any granted `consumer_id` could ACK or NACK events of topics it is not granted.
- A rejected request writes no delivery or offset state.

## Rollback considerations

Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py tests/eventbus/test_eventbus_ack_endpoint.py -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/ack_route.py`; `uv run ruff check scripts/eventbus/ack_route.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/ack_route.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- ACK and NACK return 403 for another consumer's id or a non-granted event topic and change no delivery state.
- A nonexistent event_id still returns 404.

## Out of Scope

- Promotion logic, dependency wiring (row 4), tests and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-003, REQ-004 (shared decision, pair bound to the event topic)
- **Source issue**: issues/20261027-155843_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-114911
- **Related target files**: scripts/eventbus/ack_route.py
