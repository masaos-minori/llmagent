## Goal
Remove the unused `deadletter_dir` parameter from the four promotion/sweep functions of `scripts/eventbus/dlq.py` and from their docstrings (REQ-001 / AC-1).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers are from the 2026-11-13 plan revalidation; locate each passage by its quoted text and skip and report it if it is already correct.
- The promotion path has been DB-only since dlqbox001: verified 2026-11-13, none of the four function bodies reads `deadletter_dir` (`_shared_promote` counts promotions from DB rowcounts only). Deleting the parameter changes no behavior.
- `reconcile_missing_dlq_files`, `process_outbox`, `archive_dlq_record`, `_atomic_write`, and `_count_orphan_dlq_files` keep their `deadletter_dir` parameters (Out-of-Scope per the Plan; REQ-006).
- History comments and `(dlqbox001)` docstring references are left for `plans/20261112-122030_rmcompat007_history-comment-sweep.md` (judged compatible in the Plan Assumptions); this document changes only the parameter and its docstring sentences.
- `scripts/eventbus/app.py` and `scripts/eventbus/ack_route.py` are separate target rows (`20261113-173721_03`, `20261113-173721_02`): run those procedures immediately after this one so callers match the new signatures.

## Design decisions
- Delete the parameter instead of keeping the "call-site signature stability" shim — the Plan's Goal forbids signature-stability shims (`compatrm001`).
- Keep each function's other docstring content (dlqbox001 history notes) untouched in this row.

## Alternatives considered
- Rename the parameter with a leading underscore to keep the arity: rejected — the Plan removes it outright (AC-1 asserts the search result).

## Implementation
### Target file
`scripts/eventbus/dlq.py`

### Procedure
1. `def _shared_promote(db: sqlite3.Connection, deadletter_dir: str, max_retry: int) -> int:` (line 115): drop `deadletter_dir`; delete the docstring paragraph "The deadletter_dir parameter is kept for call-site signature stability; the promotion path itself does not touch the filesystem."
2. `def _shared_promote_single(db, deadletter_dir, event_id, consumer_failure_count=None)` (line 151): drop the parameter and its `Args:` line "deadletter_dir: Kept for call-site signature stability; unused here."
3. `def sweep_orphans(db, deadletter_dir, max_retry)` (line 187): drop the parameter; its body call becomes `_shared_promote(db, max_retry)`.
4. `def promote_single(db, deadletter_dir, event_id, consumer_failure_count=None)` (line 328): drop the parameter and its `Args:` line; its body call becomes `_shared_promote_single(db, event_id, consumer_failure_count)`.

### Method
- Text search for `deadletter_dir` inside the four functions; after the edits the only remaining occurrences in the file are in `reconcile_missing_dlq_files`, `process_outbox`, `archive_dlq_record`, `_atomic_write`, and `_count_orphan_dlq_files` (this is AC-1's `rg` result).

### Details
- No body logic changes: promotion counting, rowcount guards, commits, and logging stay byte-identical.
- The module's exported function names are unchanged; only signatures change.

## Compatibility considerations
- Callers updated in the same Plan phase: `ack_route.py:208-215` and `app.py:176`; tests updated by rows 15-18. No external caller exists (Design scan found only these).

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| `scripts/eventbus/dlq.py` | Integration | `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py tests/eventbus/test_eventbus_dlq.py` (after rows 15-18 update the call sites) | Pass |
| AC-1 | Search | `rg -n "deadletter_dir" scripts/eventbus/dlq.py` | Only the five keep-functions match |
| Changed file | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages`, `uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run python tools/check_module_size.py` | No new finding |

## Completion criteria
- AC-1 holds; the four functions and their docstrings carry no `deadletter_dir`; callers and tests compile and pass.

## Out of Scope
- The `deadletter_dir` configuration key, the outbox worker, `reconcile_missing_dlq_files`, and archive behavior (Plan Out-of-Scope).

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
- **Requirement ID**: REQ-001 / AC-1
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-173721
- **Related target files**: `scripts/eventbus/dlq.py`
