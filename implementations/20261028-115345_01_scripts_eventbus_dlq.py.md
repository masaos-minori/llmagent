# Procedure: count inline promotion failures, isolate sweep failures and correct the sweep docstring

## Goal

Make the inline promotion path increment the file-write failure counter, keep one failing event from blocking the sweep batch, and describe the sweep as the repair path (Plan REQ-003, REQ-005, REQ-007).

## Scope

- Modify only `scripts/eventbus/dlq.py`.
- In scope: `_shared_promote_single`, the loop in `_shared_promote`, and the `sweep_orphans` docstring.
- Out of scope: the DLQ file format, `promote_single`'s signature, `is_promotable`, the NACK route (row 2), tests and docs.

## Assumptions

- Inline and sweep paths run under `run_with_db_lock`, so a failure in one cannot interleave with the other.
- `sqlite3.Error` keeps propagating: a database failure means the database is unhealthy and `_dlq_loop` already logs it.
- Overlap (compatible): `plans/done/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` (archived, procedures pending) also targets `scripts/eventbus/ack_route.py` (authorization at the start of the routes) and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` (Authentication section and error table); this procedure edits only the promotion block of `_nack_and_promote` and one transition-table row.

## Design decisions

- Keep the counter increment next to the `OSError` handler so every path that writes a DLQ file is metered.
- In the sweep, log the failing event id and continue with the next event; the failing event stays live and is retried on the next cycle.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/eventbus/dlq.py`

### Procedure

- In `_shared_promote_single`, wrap the `_atomic_write(deadletter_dir, event_id, record)` call in `try`/`except OSError`: increment `_dlq_file_write_failure_counter` and re-raise.
- In `_shared_promote`, change the `except OSError` branch so it keeps `_dlq_file_write_failure_counter.inc()`, calls `logger.exception("dlq sweep: DLQ file write failed event_id=%s", event_id)` and `continue`s instead of `raise`.
- Rewrite the `sweep_orphans` docstring body: the sweep is the self-healing repair path that promotes events inline promotion left live (a crash, a failed file write); a non-zero return is expected after such a failure and is logged by the caller.
- Keep the first docstring line of `sweep_orphans` unchanged (the generated reference quotes it).

### Method

Two small edits and one docstring rewrite; no new imports (`logger` and the counter already exist in the module).

### Details

- `promote_single` still raises `OSError` to its caller after counting; the NACK route (row 2) converts it to a deferred promotion.
- The sweep now returns the number of events promoted even when some failed; `_dlq_loop` logs a warning for a non-zero value only.

## Compatibility considerations

- A persistent write failure is metered and logged per event; no DLQ file format or location change.

## Security considerations

- No new input or path handling; the same `_atomic_write` is used.

## Rollback considerations

Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_eventbus_dlq_promotion.py tests/eventbus/test_eventbus_publish.py -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/dlq.py`; `uv run ruff check scripts/eventbus/dlq.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/dlq.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |
| 4 | `uv run python tools/generate_reference_table.py --check`; `uv run python tools/check_docstrings.py` | No drift; docstring format valid |

## Completion criteria

- An inline write failure increments the counter and still raises.
- A sweep batch with one failing event promotes the others.
- The `sweep_orphans` docstring no longer says a non-zero count is a bug.

## Out of Scope

- The NACK route, the DLQ file format, requeue logic.

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
- **Requirement ID**: REQ-003, REQ-005, REQ-007 (inline counter, sweep isolation, docstring)
- **Source issue**: issues/20261027-155846_ebdurable003_define-publish-dlq-durability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115345
- **Related target files**: scripts/eventbus/dlq.py
