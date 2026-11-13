## Goal
Call `sweep_orphans` in the background `_dlq_loop` of `scripts/eventbus/app.py` without `cfg.deadletter_dir` (REQ-001 / AC-1), covering the shutdown-test companion.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers are from the 2026-11-13 plan revalidation; locate each passage by its quoted text and skip and report it if it is already correct.
- Run this document after `20261113-173721_01` (`dlq.py` signature removal).
- `cfg.deadletter_dir` stays passed to `process_outbox` (line 187) and `reconcile_missing_dlq_files` (line 200) — both keep their directory parameter (Plan Out-of-Scope; REQ-006).
- adrrev014's `app.py` procedure is archived in `implementations/done/`; re-read the file before editing anyway (Plan Assumptions).
- The `test_eventbus_shutdown.py` companion qualifies as a companion: it lies under `tests/`, exactly one other target row (`app.py`) names it in `Related Tests`, and its only change is mechanical signature alignment (no test-design decision of its own).

## Design decisions
- None beyond the Plan-fixed call change; the sweep count logging in `_dlq_loop` stays as-is (the returned count is already logged and the Plan adds no new gate here).

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`scripts/eventbus/app.py`

### Procedure
1. In `_dlq_loop`'s `_sweep` closure (line 176), replace `result: int = sweep_orphans(db, cfg.deadletter_dir, cfg.max_retry)` with `result: int = sweep_orphans(db, cfg.max_retry)`.

### Method
- Single-line replacement; no other call in the file names `sweep_orphans` (verified 2026-11-13).

### Details
- Keep the surrounding `asyncio.to_thread(...)` and lock handling byte-identical.

### Companion test files
- `tests/eventbus/test_eventbus_shutdown.py`
  - Procedure: update the two fake signatures `def blocking_sweep_orphans(db: Any, deadletter_dir: str, max_retry: int) -> int:` (lines 67 and 121) to `def blocking_sweep_orphans(db: Any, max_retry: int) -> int:`; their bodies and the `monkeypatch.setattr(eb_app, "sweep_orphans", blocking_sweep_orphans)` targets stay.
  - Validation: `uv run pytest tests/eventbus/test_eventbus_shutdown.py` passes (the lifespan cycle calls the new two-argument `sweep_orphans`).

## Compatibility considerations
- Background behavior is unchanged: the sweep was already DB-only; only the argument list aligns with row 01.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| `app.py` lifespan/loop and shutdown companion | Integration | `uv run pytest tests/eventbus/test_eventbus_shutdown.py` | Pass |
| Changed file | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages`, `uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run python tools/check_module_size.py` | No new finding |

## Completion criteria
- AC-1: the only `sweep_orphans` call passes `(db, cfg.max_retry)`; the shutdown suite passes.

## Out of Scope
- The `deadletter_dir` config key, outbox worker, reconcile, and archive behavior (Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-204923 | 20261113-205554 | Changed: scripts/eventbus/app.py, tests/eventbus/test_eventbus_shutdown.py (companion) |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113-205555 | Targeted run: uv run pytest tests/eventbus/test_eventbus_shutdown.py -q -> 10 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-205555 | 20261113-221853 | Pass: ruff, bandit -ll app.py (no issues). Deferred to cycle 18: mypy, full suite, coverage gate (red intermediate call sites in tests fixed by rows 15-18). Not run: ast-grep (not installed) mypy 0 errors; full suite 12176 passed 1 failed = registry/manifests/eventbus_api.yaml manifest-stale resolved by rows 09+14 regeneration per plan dependency order; diff-cover 100 percent gate 90 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113-205555 | N/A: eventbus docs updates carried by plan rows 09-14 |

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
- **Requirement ID**: REQ-001 / AC-1
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-173721
- **Related target files**: `scripts/eventbus/app.py`, `tests/eventbus/test_eventbus_shutdown.py` (companion)