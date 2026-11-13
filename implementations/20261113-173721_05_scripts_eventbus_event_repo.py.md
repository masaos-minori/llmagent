## Goal
Drop `dlq_requeue_count` from the `fetch_dlq` select in `scripts/eventbus/event_repo.py` so the `/dlq` response no longer carries the removed column (REQ-004 / AC-4).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers are from the 2026-11-13 plan revalidation; locate each passage by its quoted text and skip and report it if it is already correct.
- Verified 2026-11-13: `fetch_dlq` in the target file builds `SELECT seq, event_id, topic, producer, published_at, dlq_requeue_count, dlq_at FROM events WHERE dlq_at IS NOT NULL ORDER BY seq` (lines 124-127); it is the only `/dlq` feed.
- The route layer names no column explicitly, so the removed field disappears from the response with this single select change.
- The Plan Assumption holds: `/dlq` rows come from `fetch_dlq`, so dropping the select column removes the key from the response; documented by row 11 (`eventbus_04`).

## Design decisions
N/A: the Plan fixes the approach for this row.

## Alternatives considered
N/A: single-line select change.

## Implementation
### Target file
`scripts/eventbus/event_repo.py`

### Procedure
1. In `fetch_dlq`, change the fragment `" dlq_requeue_count, dlq_at"` to `" dlq_at"`.

### Method
- One fragment edit; ordering, filter, and pagination logic byte-identical.

### Details
- No other `dlq_requeue_count` reference exists in the file (verified 2026-11-13).

## Compatibility considerations
- API change: `/dlq` item objects lose the `dlq_requeue_count` key (documented in `docs/24_eventbus/eventbus_04_dlq_endpoint.md` by row 11; UNK-02 asks the operator before deploy).

## Security considerations
N/A: no authorization or SQL-injection surface change (static fragment).

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| `/dlq` response | Integration | `uv run pytest tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_eventbus_dlq_pagination.py` (row 15 updates the DLQ tests; pagination tests verified 2026-11-13 to not assert the removed key) | Pass |
| AC-4 | Search | `rg -n "dlq_requeue_count" scripts/eventbus/event_repo.py` | No match |
| Changed file | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages`, `uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run python tools/check_module_size.py` | No new finding |

## Completion criteria
- AC-4: no `dlq_requeue_count` in the select or in any `/dlq` test fixture assertion (after rows 15-17).

## Out of Scope
- `fetch_dlq` callers other than the `/dlq` route (none exist); `dlq_route.py` (reference file).

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
- **Requirement ID**: REQ-004 / AC-4
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-173721
- **Related target files**: `scripts/eventbus/event_repo.py`
