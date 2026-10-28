# Procedure: rewire ACK and NACK to the shared decision and keep the subscribe dependency

## Goal

Stop passing the body-bound `topics` through `Depends(require_consumer_identity)` on ACK and NACK and keep subscribe on the shared dependency (Plan REQ-003, REQ-004).

## Scope

- Modify only `scripts/eventbus/app.py`.
- In scope: the `ack_event` and `nack` route handlers' `_identity` dependency and `resolve_subscribe_identity`'s comment.
- Out of scope: `_shutdown_lifespan` and every other route (other Plans), tests and docs.

## Assumptions

- Rows 1 and 3 have landed, so the ACK and NACK routes authorize inside `ack_route.py` and no longer need `_identity`.
- FastAPI exposes the `topics` parameter of `require_consumer_identity` as a request body on the two POST routes (checked against `app.openapi()` during the Plan phase).
- Overlap (compatible): `plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md` also targets `scripts/eventbus/ack_route.py` and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`; it edits the promotion block of `_nack_and_promote` and one transition-table row, which this procedure does not touch. `plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` also targets `scripts/eventbus/app.py` (`_shutdown_lifespan` only).

## Design decisions

- Keep `Depends(require_role(Role.CONSUMER))` for role enforcement; remove only the `_identity` dependency on ACK and NACK.
- `resolve_subscribe_identity` keeps calling `require_consumer_identity` with the query `consumer_id` and `topic`.

## Alternatives considered

- Keep the independent sets and add a second check — rejected: it keeps two sources of truth for the same grant (Plan Design Decision 1).

## Implementation

### Target file

`scripts/eventbus/app.py`

### Procedure

- In `ack_event` and `nack`, delete the `_identity: Principal = Depends(require_consumer_identity)` parameter; keep `_principal`.
- Stop forwarding `_identity` where the handlers call the route functions (they do not forward it today); confirm with `rg "_identity" scripts/eventbus/app.py`.
- Update the comment in `resolve_subscribe_identity` to say the dependency enforces the (consumer_id, topic) grants.

### Method

Delete two dependency parameters and refresh one comment.

### Details

- After the change the OpenAPI schema of `POST /nack` and `POST /events/{event_id}/ack` no longer lists a request body.
- `require_consumer_identity` is still imported for the subscribe dependency; keep the import.

## Compatibility considerations

- The request body that was ignored in practice disappears; no client in `scripts/` sends it.
- Authorization of ACK/NACK still happens, now inside the route (row 3).

## Security considerations

- Removes a caller-supplied `topics` input from the authorization path.

## Rollback considerations

Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py tests/eventbus/test_eventbus_ack_nack.py tests/eventbus/test_eventbus_subscribe.py -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/app.py`; `uv run ruff check scripts/eventbus/app.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/app.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |
| 4 | `uv run python -c "from eventbus.app import app; o=app.openapi(); print('requestBody' in o['paths']['/nack']['post'])"` with `PYTHONPATH=scripts` | Prints False |

## Completion criteria

- ACK and NACK handlers declare no `_identity` dependency and subscribe still resolves identity through the shared dependency.
- OpenAPI shows no request body for the two POST routes.

## Out of Scope

- Shutdown lifespan, DLQ and other routes.

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
- **Requirement ID**: REQ-003, REQ-004 (one shared decision; remove the body-bound topics input)
- **Source issue**: issues/20261027-155843_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-114911
- **Related target files**: scripts/eventbus/app.py
