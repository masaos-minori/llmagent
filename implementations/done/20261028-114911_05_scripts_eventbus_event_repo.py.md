# Procedure: add a read helper that returns the topic of an event

## Goal

Add `get_event_topic` (new) next to `get_seq` so the ACK and NACK routes can authorize the pair without a new query shape (Plan REQ-004).

## Scope

- Modify only `scripts/eventbus/event_repo.py`.
- In scope: one new read function.
- Out of scope: callers (row 3), schema changes, tests and docs.

## Assumptions

- `events.topic` is `NOT NULL`, so a returned `None` means the event does not exist.
- Ordering note: `scripts/eventbus/ack_route.py` (seq 03) imports this function although its `seq` is lower than this row's (05); the Plan table order is fixed, so execute this row before seq 03 (`code-implementation` runs a Plan's procedures in filename order, so run this one first by hand).
- Overlap (compatible): `plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md` also targets `scripts/eventbus/ack_route.py` and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`; it edits the promotion block of `_nack_and_promote` and one transition-table row, which this procedure does not touch. `plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` also targets `scripts/eventbus/app.py` (`_shutdown_lifespan` only).

## Design decisions

- Mirror `get_seq`: `conn.execute("SELECT topic FROM events WHERE event_id = ?", (event_id,)).fetchone()`.
- Return `str | None`.

## Alternatives considered

- Reuse `get_seq` and a second query in the route — rejected: it spreads SQL into the route.

## Implementation

### Target file

`scripts/eventbus/event_repo.py`

### Procedure

- Add `get_event_topic(conn, event_id)` (new) after `get_seq`, returning `row["topic"]` when a row exists and `None` otherwise.
- Export it through `eventbus.db` only if `ack_route.py` imports repo functions through that facade; otherwise import from `eventbus.event_repo` directly (verify with `rg "from eventbus" scripts/eventbus/ack_route.py`).

### Method

Add a six-line function modeled on `get_seq`.

### Details

- `get_seq` uses the same row factory (`row["seq"]`), so `row["topic"]` is valid on the shared connection.
- The function runs under `run_with_db_lock` at its call site; it takes no lock itself.

## Compatibility considerations

- Additive function; no caller changes behavior until row 3.

## Security considerations

- A parameterized query; no string interpolation of `event_id`.

## Rollback considerations

Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/event_repo.py`; `uv run ruff check scripts/eventbus/event_repo.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/event_repo.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- `get_event_topic` (new) returns the topic for an existing event and `None` for an unknown id.

## Out of Scope

- Route changes, schema changes.

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
- **Requirement ID**: REQ-004 (event topic lookup for the pair check)
- **Source issue**: issues/20261027-155843_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-114911
- **Related target files**: scripts/eventbus/event_repo.py