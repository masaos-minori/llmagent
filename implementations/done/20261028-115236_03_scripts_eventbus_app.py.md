# Procedure: clear app.state.db after the shutdown close

## Goal

Set `app.state.db` to `None` after `_shutdown_lifespan` closes the connection so a later `get_db` raises its explicit error (Plan REQ-003).

## Scope

- Modify only `scripts/eventbus/app.py`.
- In scope: the `try`/`finally` that closes the connection in `_shutdown_lifespan`.
- Out of scope: the ACK/NACK wiring and routes (another Plan), the sweep loop, tests and docs.

## Assumptions

- Applied only if `uv run pytest tests/eventbus` stays green (UNK-02); if a test reads `app.state.db` after the lifespan exits, drop this change and record why.
- `_shutdown_lifespan` guards its close with `if app.state.db`, so the change makes a second call a no-op.
- Overlap (compatible): `plans/20261028-094217_ebmetrics006_correct-db-timing-health.md` also targets `scripts/eventbus/route_helpers.py` (timing statements around the lock acquisition) and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Metrics section); `plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` (archived) targeted `scripts/eventbus/app.py` (ACK/NACK wiring only). This procedure edits the shutdown re-check, the shutdown state and the Shutdown section.

## Design decisions

- Assign inside the existing `finally`, before `lock.release()`, so no worker can see a half-closed reference after the lock is released.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/eventbus/app.py`

### Procedure

- Change the close block to `try: app.state.db.close()` / `finally: app.state.db = None; lock.release()`.
- Run `uv run pytest tests/eventbus -q` before moving on; a failure that reads `app.state.db` after shutdown means REQ-003 is dropped for this Plan.

### Method

Two-line edit in one block; no import changes.

### Details

- `get_db(request)` and `app_get_db(app)` already raise `RuntimeError` when the state is missing, so no helper changes are needed.
- `lifespan()` startup sets `app.state.db = open_db(...)` again, so a second lifecycle starts clean.

## Compatibility considerations

- Any code that still holds a reference to the closed connection is unchanged; only the shared attribute is cleared.

## Security considerations

- Prevents use of a closed connection through the shared state.

## Rollback considerations

Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_shutdown.py tests/eventbus/test_eventbus_health.py tests/eventbus/test_admin_topics_authorization.py -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/app.py`; `uv run ruff check scripts/eventbus/app.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/app.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- After `_shutdown_lifespan`, `app.state.db` is `None` and the full eventbus suite passes.

## Out of Scope

- Other routes, lifespan startup, the sweep loop.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-153121 | 20261028-153121 | Full suite: 1 unrelated failure (test_dlq_list_snapshot_consistent_during_promotion, count/fetch race against a separate writer connection under 16 min load; passes alone and in tests/eventbus) |
| 2 | Add or update tests per Validation plan | Completed | 20261028-153121 | 20261028-153121 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-153121 | 20261028-153121 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-153121 | 20261028-153121 |  |

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
- **Requirement ID**: REQ-003 (later access fails explicitly)
- **Source issue**: issues/20261027-155845_ebshutdown002_close-shutdown-admission-race.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115236
- **Related target files**: scripts/eventbus/app.py