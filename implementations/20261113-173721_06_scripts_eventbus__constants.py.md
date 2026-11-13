## Goal
Delete the three unused column constants `_COL_DLQ_REQUEUE_COUNT`, `_COL_REDISTRIBUTED_FROM`, and `_COL_CONSUMER_ID` and their `__all__` entries from `scripts/eventbus/_constants.py` (REQ-004, REQ-005 / AC-4, AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers are from the 2026-11-13 plan revalidation; locate each passage by its quoted text and skip and report it if it is already correct.
- Verified 2026-11-13: the only user of `_COL_DLQ_REQUEUE_COUNT` is the requeue `UPDATE` being deleted by row 04; `_COL_REDISTRIBUTED_FROM` and `_COL_CONSUMER_ID` have no user in `scripts`, `tests`, `tools`, `docs`, `registry`, or `deploy`.
- Run this document after row 04 (`dlq_repo.py`) so the last `_COL_DLQ_REQUEUE_COUNT` user is gone before the constant is deleted.
- The Plan judges deletion (not rename) as the intent of the Issue's naming request; the acceptance search `rg -n "REDISTRIBUTED" scripts/` is met either way (Plan Corrections).

## Design decisions
- Delete instead of rename: a renamed constant would still have no user (`compatrm001` forbids keeping stale names).

## Alternatives considered
- Keep `_COL_REDISTRIBUTED_FROM` "for future use": rejected — no user exists; the Issue asks for its removal.

## Implementation
### Target file
`scripts/eventbus/_constants.py`

### Procedure
1. Re-run the zero-reference searches first (the Plan Risks mitigation): `rg -n "_COL_DLQ_REQUEUE_COUNT|_COL_REDISTRIBUTED_FROM|_COL_CONSUMER_ID" scripts tests tools docs registry deploy*` — each constant must appear only in `_constants.py` (after row 04 removed the `_COL_DLQ_REQUEUE_COUNT` user). If any other user appears, stop and report.
2. Delete the definitions `_COL_DLQ_REQUEUE_COUNT = "dlq_requeue_count"` (line 13), `_COL_REDISTRIBUTED_FROM = "redelivered_from"` (line 14), and `_COL_CONSUMER_ID = "consumer_id"` (line 17).
3. Delete the matching three entries from `__all__` (lines 24-28 region).

### Method
- Pure deletion; the remaining constants and their `__all__` entries keep order.

### Details
- SQL in other modules spells `redelivered_from` / `consumer_id` as literal column names in their own statements; those are not constant users and are untouched.

## Compatibility considerations
- `_constants.py` is an eventbus-internal module (`lint-imports` eventbus-is-isolated contract unaffected: only names are removed).

## Security considerations
N/A: constant removal only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| AC-4, AC-5 | Search | `rg -n "dlq_requeue_count|_COL_CONSUMER_ID" scripts` and `rg -n "REDISTRIBUTED" scripts/` | No match |
| EventBus suite | Integration | `uv run pytest tests/eventbus` | Pass |
| Changed file | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages`, `uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run python tools/check_module_size.py` | No new finding |

## Completion criteria
- AC-4 and AC-5 searches return nothing; the module imports cleanly.

## Out of Scope
- `ERR_*` constants and all constants with users (Plan Out-of-Scope).

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
- **Requirement ID**: REQ-004, REQ-005 / AC-4, AC-5
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-173721
- **Related target files**: `scripts/eventbus/_constants.py`
