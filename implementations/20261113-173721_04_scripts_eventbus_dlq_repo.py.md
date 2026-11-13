## Goal
Reduce `RequeueResult` in `scripts/eventbus/dlq_repo.py` to `status`, `new_event_id`, `new_seq`, and remove the `dlq_requeue_count` update and its constant import (REQ-003, REQ-004 / AC-3, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers are from the 2026-11-13 plan revalidation; locate each passage by its quoted text and skip and report it if it is already correct.
- Verified 2026-11-13: `RequeueResult` (lines 24-39) carries `original_event_exists` and `already_redelivered`, both derived from `status` at the five construction points (`dlq_repo.py:82,102,103,119,124`); `dlq_route.py` references neither field; only `tests/eventbus/test_eventbus_requeue_edge_cases.py:574` reads `already_redelivered` (row 17 updates it).
- The adrrev014 procedure for this file is archived (`implementations/done/20261112-072954_01_scripts_eventbus_dlq_repo.py.md`); its read-only terminal-failure count addition is already in the current source — re-read the file before editing and do not disturb that region.
- The `already_redelivered` status string and the IntegrityError → status mapping stay (Plan Requeue design).

## Design decisions
- The status string `"already_redelivered"` remains the single carrier of that fact; the duplicate boolean fields are deleted rather than renamed (AC-3 requires exactly three fields).
- The `UPDATE events SET dlq_requeue_count = dlq_requeue_count + 1 ...` statement is deleted outright — the requeue fact is already persisted as the descendant row (`redelivered_from` lineage), so the counter repeated it (Goal: each fact once).

## Alternatives considered
- Keep `original_event_exists` for API callers: rejected — no reader exists (consumer scan, Plan Design; AC-4 search).

## Implementation
### Target file
`scripts/eventbus/dlq_repo.py`

### Procedure
1. Delete `_COL_DLQ_REQUEUE_COUNT,` from the `_constants` import block (line 16).
2. In `class RequeueResult` (line 24): delete the fields `original_event_exists: bool` and `already_redelivered: bool` (lines 38-39) and the docstring lines describing them (including the `already_redelivered` bullet at line 31); keep `status`, `new_event_id`, `new_seq`.
3. Update every `RequeueResult(...)` construction to the three remaining positional arguments (verified construction points: lines 82 and 119 use `RequeueResult("already_redelivered", True, True, None, None)` → `RequeueResult("already_redelivered", None, None)`; the success and `not_in_dlq` constructions drop their two boolean arguments).
4. Delete the counter `UPDATE events SET {_COL_DLQ_REQUEUE_COUNT} = ...` statement (line 89) from the requeue transaction; the descendant INSERT and the rowcount/IntegrityError handling stay.

### Method
- After the edits, `rg -n "dlq_requeue_count|original_event_exists" scripts/eventbus/dlq_repo.py` returns nothing (AC-3/AC-4 partial).

### Details
- Keep the `# nosec B608` suppression context only where a formatted SQL fragment remains; the deleted statement's suppression goes with it.
- `redeliver_event` keeps its transaction, the unique `redelivered_from` index race mapping, and rollback semantics byte-identical.

## Compatibility considerations
- `dlq_route.py` (reference file, unchanged) maps `status` only; the HTTP 409 texts for `already_redelivered`/`not_in_dlq` are unchanged (ADR-006 requeue paragraph already names them).
- Test assertion updates are carried by row 17 (`20261113-173721_17_tests_eventbus_test_eventbus_requeue_edge_cases.py.md`).

## Security considerations
N/A: no new dynamic SQL; the removed formatted fragment went with the deleted statement.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| Requeue repository | Integration | `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py` (after row 17) | Pass |
| AC-3 | Search | field list of `RequeueResult` in the file | Exactly `status`, `new_event_id`, `new_seq` |
| Changed file | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages`, `uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run python tools/check_module_size.py` | No new finding |

## Completion criteria
- AC-3 holds; no `dlq_requeue_count` write remains in the requeue transaction; requeue tests pass.

## Out of Scope
- The schema column itself (`schema.sql`, row 08) and the `/dlq` select (row 05); `dlq_route.py` (reference only).

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
- **Requirement ID**: REQ-003, REQ-004 / AC-3, AC-4
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-173721
- **Related target files**: `scripts/eventbus/dlq_repo.py`
