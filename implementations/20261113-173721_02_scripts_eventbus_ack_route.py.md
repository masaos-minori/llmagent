## Goal
In the `/nack` handler of `scripts/eventbus/ack_route.py`, call `promote_single` without the directory argument and delete the unreachable `except OSError` block (REQ-001, REQ-002 / AC-1, AC-2).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers are from the 2026-11-13 plan revalidation; locate each passage by its quoted text and skip and report it if it is already correct.
- Verified 2026-11-13: the `try` at lines 210-216 wraps only `dlq.is_promotable` and `dlq.promote_single`, both DB-only since dlqbox001 (`promote_single` never touches the filesystem); no OSError source remains in the wrapped calls, so the handler cannot run (Plan Background).
- Run this document after `20261113-173721_01` (`dlq.py` signature removal) so the new call arity exists.
- The `from eventbus.dlq import is_promotable, promote_single  # noqa: PLC0415` deferred import (line 208) stays.
- `scripts/eventbus/dlq_route.py` reads no duplicate `RequeueResult` field (Plan correction) and is untouched.

## Design decisions
- Delete the whole `except OSError` / `logger.exception("nack: inline DLQ promotion failed, deferred to sweep event_id=%s", ...)` / `promoted = False` block instead of narrowing it to `sqlite3.Error`: the Plan (REQ-002) removes the handler because the path is unreachable; a genuine DB failure then propagates as a 500 instead of a false "deferred to sweep" claim.

## Alternatives considered
- Keep the handler narrowed to `sqlite3.Error`: rejected — it would re-introduce a "deferred to sweep" path the sweep no longer needs to cover (promotion is atomic).

## Implementation
### Target file
`scripts/eventbus/ack_route.py`

### Procedure
1. In `_nack_and_promote` (handler `POST /nack`, line 137), replace the block

   ```python
   try:
       promoted = is_promotable(
           db, event_id, cfg.max_retry
       ) and promote_single(
           db, cfg.deadletter_dir, event_id, consumer_failure_count
       )
   except OSError:
       logger.exception(
           "nack: inline DLQ promotion failed, deferred to sweep event_id=%s",
           event_id,
       )
       promoted = False
   ```

   with

   ```python
   promoted = is_promotable(db, event_id, cfg.max_retry) and promote_single(
       db, event_id, consumer_failure_count
   )
   ```

### Method
- Single contiguous replacement; keep the surrounding `consumer_failure_count` gate and REQ-002 comments unchanged.

### Details
- `cfg.deadletter_dir` remains used elsewhere in the module only through `cfg`; no local variable references it after this edit (verified 2026-11-13: none existed).

## Compatibility considerations
- Response shape unchanged (`consumer_delivery_failure_count`, optional `dlq_promoted`). The only semantic change is that a promotion-path exception now propagates instead of being swallowed — acceptable because the Plan proves it unreachable (AC-2).
- Test replacement is carried by row 16 (`20261113-173721_16_tests_eventbus_test_eventbus_dlq_promotion.py.md`).

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| `/nack` handler | Integration | `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py tests/eventbus/test_eventbus_dlq.py` (after rows 15-16) | Pass |
| AC-2 | Search | `rg -n "OSError" scripts/eventbus/ack_route.py` | No match inside the `/nack` handler |
| Changed file | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages`, `uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run python tools/check_module_size.py` | No new finding |

## Completion criteria
- AC-1 and AC-2 hold; promotion on `/nack` is a single DB-only expression.

## Out of Scope
- The `/ack` handler and other `OSError` uses in the file that wrap real filesystem or audit code (Plan AC-2 limits the search to the `/nack` handler).

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
- **Requirement ID**: REQ-001, REQ-002 / AC-1, AC-2
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-173721
- **Related target files**: `scripts/eventbus/ack_route.py`
