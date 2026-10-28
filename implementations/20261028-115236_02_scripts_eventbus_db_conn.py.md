# Procedure: correct the shutdown-flag docstring and state the counter role

## Goal

Make the `set_shutdown_flag()` docstring match the two-step refusal and state that the active-user counter is observability only (Plan REQ-002, REQ-005).

## Scope

- Modify only `scripts/eventbus/db_conn.py`.
- In scope: the docstrings of `set_shutdown_flag`, `bump_active_db_user` and `release_active_db_user`.
- Out of scope: removing the counter (UNK-01), logic changes, tests and docs.

## Assumptions

- The counter has no reader in `scripts/`; `tests/eventbus/conftest.py` saves and restores it and the generated reference lists the two functions.
- The generated reference quotes only the first docstring line, so first lines stay unchanged.
- Overlap (compatible): `plans/20261028-094217_ebmetrics006_correct-db-timing-health.md` also targets `scripts/eventbus/route_helpers.py` (timing statements around the lock acquisition) and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Metrics section); `plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` (archived) targeted `scripts/eventbus/app.py` (ACK/NACK wiring only). This procedure edits the shutdown re-check, the shutdown state and the Shutdown section.

## Design decisions

- Extend the docstring bodies only; keep the first lines byte-identical so `tools/generate_reference_table.py --check` stays clean.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/eventbus/db_conn.py`

### Procedure

- In `set_shutdown_flag`, after the first line, state that `run_with_db_lock()` refuses new work twice: before queueing and again after a queued worker acquires the lock, and that shutdown serializes through the lock.
- In `bump_active_db_user` and `release_active_db_user`, add one sentence: the counter is observability only and is not consulted by shutdown.

### Method

Docstring-only edit.

### Details

- No code path changes; the first docstring lines used by the API reference are untouched.

## Compatibility considerations

- No behavior change.

## Security considerations

- No security impact.

## Rollback considerations

Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_shutdown.py -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/db_conn.py`; `uv run ruff check scripts/eventbus/db_conn.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/db_conn.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |
| 4 | `uv run python tools/generate_reference_table.py --check`; `uv run python tools/check_docstrings.py` | No drift; docstring format valid |

## Completion criteria

- The three docstrings describe the implemented behavior and the counter role.
- `uv run python tools/generate_reference_table.py --check` and `tools/check_docstrings.py` pass.

## Out of Scope

- Removing the counter, logic changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: REQ-002, REQ-005 (counter role; docstring matches behavior)
- **Source issue**: issues/20261027-155845_ebshutdown002_close-shutdown-admission-race.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115236
- **Related target files**: scripts/eventbus/db_conn.py
