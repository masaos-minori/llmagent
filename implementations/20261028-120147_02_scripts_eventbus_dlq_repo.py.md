# Procedure: map the redelivered_from uniqueness violation to already_redelivered

## Goal

Turn an `IntegrityError` that names `events.redelivered_from` into the existing `already_redelivered` result and keep every other integrity error an error (Plan REQ-002).

## Scope

- Modify only `scripts/eventbus/dlq_repo.py`.
- In scope: the `except` clauses of `redeliver_event` and the docstrings that call the pre-check the concurrency guard.
- Out of scope: the pre-insert check itself, the result vocabulary, the HTTP mapping, tests, docs.

## Assumptions

- Ordering note: the tests (row 3) are written first; row 1 (`schema.sql`) has landed so the index exists.
- SQLite reports the violation as `UNIQUE constraint failed: events.redelivered_from`; a collision of the new `event_id` reports `events.event_id` and must still raise (verified on this Python/SQLite build in the planning phase).
- Overlap (compatible): `plans/done/20261028-093931_adrgate005_enforce-adr-evidence-checks.md` (archived, procedures pending) also targets the ADR-006 file; it renames two stale test citations in the Verification table while this procedure edits Implementation Notes only. Any citation added here must resolve to an existing test node once that Plan's node validation is in force.

## Design decisions

- Catch `sqlite3.IntegrityError` before the general `sqlite3.Error` handler, roll back, and discriminate on the column name in the message.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/eventbus/dlq_repo.py`

### Procedure

- Change `except sqlite3.Error:` to two handlers: `except sqlite3.IntegrityError as exc:` that calls `conn.rollback()` and, when `"events.redelivered_from" in str(exc)`, returns `RequeueResult("already_redelivered", True, True, None, None)`, otherwise re-raises; then keep `except sqlite3.Error:` with `conn.rollback()` and `raise`.
- Rewrite the `redeliver_event` docstring paragraph: the existence check classifies the sequential case without a failed insert; the unique index on `redelivered_from` is the concurrency guard.
- Update the `RequeueResult` docstring line for `already_redelivered` to mention both the pre-check and the index.

### Method

Split one handler into two and edit two docstrings.

### Details

- The pre-insert check stays: it avoids a failed `INSERT` in the common case.
- `dlq_route.py` already maps `already_redelivered` to HTTP 409; no change there.

## Compatibility considerations

- No change to statuses or the HTTP mapping.

## Security considerations

- Only the column name from SQLite's own message is inspected; no user input is interpolated.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/dlq_repo.py`; `uv run ruff check scripts/eventbus/dlq_repo.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/dlq_repo.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- The index violation yields `already_redelivered` with the transaction rolled back and the connection usable; an `events.event_id` collision still raises.

## Out of Scope

- Result vocabulary, route code.

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
- **Requirement ID**: REQ-002 (typed result for the database-level conflict)
- **Source issue**: issues/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120147
- **Related target files**: scripts/eventbus/dlq_repo.py
