## Goal

Fix the malformed log line emitted by `ETagManager.update`'s stale-skip branch
(`REQ-001`, `REQ-002`): replace the 3-placeholder / 2-argument `logger.info` call
that raises `TypeError: not enough arguments for format string` on every stale-skip
with a correct call that also names the stored timestamp. Expose the stored timestamp
from the private `_is_stale_update` helper so the skip branch can log it.

## Scope
**Release unit**: etag-log-format-fix (Plan Release units)

## Assumptions
- `_is_stale_update` has a single verified caller (`_incoming_decision`, line :95);
  `update()` is the only production caller of `_is_stale_update`'s result via that
  helper.
- The stored `fetched_at` string is already validated parseable inside
  `_is_stale_update` (parse happens at `:103-128`) before the comparison at `:130`, so
  logging it verbatim is safe.
- `resolve_incoming` (added by the archived `raging002` Plan) shares `_incoming_decision`
  and is pinned by `tests/rag/ingestion/test_ingestion_freshness.py::TestResolveIncomingGuard`;
  its bool contract must be preserved.

## Design decisions
- **`_is_stale_update` returns `str | None`, not `bool`.** Return the stored
  `fetched_at` string when the update is stale (`new_dt < stored_dt`) and `None`
  otherwise. Keep the decision logic, the `InvalidIncomingTimestampError` /
  `InvalidStoredTimestampError` raises, and the single `SELECT fetched_at` read
  unchanged — only the return value changes shape. Rejected: returning a
  `tuple[bool, str | None]` (the bool is redundant with `None`-ness) and
  re-querying `documents.fetched_at` in `update()` (a second DB read for a log line).
- **`update()` drives the skip branch off the returned string.** Replace
  `if not incoming_wins:` with `stored = self._is_stale_update(new_fetched_at); if stored is not None:`.
  This satisfies REQ-001's `if stored is not None:` and supplies the logged value in
  the same single read.
- **Preserve the guards currently in `_incoming_decision`.** The both-None early
  return (no DB read — pinned by `test_both_none_returns_early_no_db_query`) and the
  empty-`new_fetched_at` `ValueError` (pinned by `test_empty_fetched_at_raises_value_error`)
  live in `_incoming_decision` today. Because `update()` now calls `_is_stale_update`
  directly, move these two guards into `update()` BEFORE the `_is_stale_update` call
  in the same order as `_incoming_decision` (verified 20261106: it raises on empty
  `new_fetched_at` at `:91-92` BEFORE the both-None return at `:93-94`, so
  `update(None, None, "")` raises today): empty-string `raise` first, then both-None
  return. The procedure's original reverse order would have silently returned on
  `update(None, None, "")` instead of raising. Do NOT let `_is_stale_update` own
  the empty-string `ValueError` (its existing `if not new_fetched_at: return None`
  guard stays; the raise is an `update()`-level contract).
- **Keep `_incoming_decision`'s bool contract intact for `resolve_incoming`.** Its
  staleness derivation must adapt to the new return type:
  `return self._is_stale_update(new_fetched_at) is None` (True when incoming wins, i.e.
  not stale). `not self._is_stale_update(...)` is also equivalent here because a stale
  return is always a non-empty truthy timestamp, but `is None` is explicit and avoids
  any falsy-string ambiguity. Leave the both-None `return None` and empty-string
  `raise ValueError` clauses exactly as they are.

## Alternatives considered
- Re-querying `documents.fetched_at` in `update()` for the log line: rejected (second
  DB read, violates "single DB read").
- Returning `tuple[bool, str | None]` from `_is_stale_update`: rejected (redundant bool,
  noisier callers).
- Leaving `_is_stale_update` returning `bool` and adding a separate accessor for the
  stored string: rejected (two helpers doing one read; the plan's REQ-001 folds both
  into the return value).

## Implementation
### Target file
- `scripts/rag/ingestion/etag_manager.py`

### Procedure
1. Change `_is_stale_update` signature to `-> str | None` and return the stored
   `fetched_at` string when stale, `None` otherwise.
2. Rewrite `update()` to call `_is_stale_update` directly, guard both-None and
   empty-string before the call, and use `if stored is not None:` as the skip branch
   with the three-argument `logger.info`.
3. Adapt `_incoming_decision`'s staleness expression to `self._is_stale_update(...) is None`
   so `resolve_incoming` keeps its bool contract.

### Method
- In `_is_stale_update`, keep parsing/validation order identical. At the end, replace
  `return new_dt < stored_dt` with:
  ```python
  if new_dt < stored_dt:
      return stored_fetched_at
  return None
  ```
  The `if not stored_fetched_at: return False` clause becomes `return None` (not stale,
  nothing to log) — semantics unchanged (both mean "not skipped").
- In `update()`, replace lines :42-52 with:
  ```python
  if not new_fetched_at:
      raise ValueError("new_fetched_at must be a non-empty string")
  if etag is None and last_modified is None:
      return
  stored = self._is_stale_update(new_fetched_at)
  if stored is not None:
      logger.info(
          "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
          new_fetched_at,
          stored,
          self._doc_id,
          extra={"stage_name": "ingester"},
      )
      return
  self._update_with_freshness(etag, last_modified, new_fetched_at)
  self._log_updated()
  ```
  This preserves the both-None no-DB-read path and the empty-string raise, and emits
  exactly one clean INFO line naming both timestamps and `doc_id`.
- In `_incoming_decision`, change line :95 to
  `return self._is_stale_update(new_fetched_at) is None`.

### Details
- The `logger.info` message string, placeholders (`%s %s ... %d`), argument order
  (`new_fetched_at`, `stored`, `self._doc_id`), and `extra={"stage_name": "ingester"}`
  match REQ-002 exactly and follow the `_log_updated` calling convention (`:155-161`).
- Do not touch `_incoming_decision`'s both-None / empty-string clauses, `_stored_freshness`,
  `_update_with_freshness`, `resolve_incoming`, or the exception classes.
- No schema, public-API, or constant change; `scan_change_consumers.py` is not required
  (private helper, one verified caller path).

## Compatibility considerations
`resolve_incoming` behavior is unchanged (bool contract preserved; covered by
`TestResolveIncomingGuard`). `update()`'s guard decisions, exception types, and the
single-DB-read contract are unchanged. Only the skip-path log line gains its third
argument — an observability fix, not a behavior change (AC-2).

## Security considerations
N/A: no input-handling, network, or credential change. The logged values are the
already-validated incoming and stored timestamps plus the integer `doc_id`; no secret
flows through this line.

## Rollback considerations
Revert the commit to `etag_manager.py`. The change is confined to two private methods
and `update()`'s skip branch; `resolve_incoming`'s adaptation is a one-line expression.

## Validation plan
- Unit + regression (`REQ-003`): new `caplog` test asserts the stale-skip emits exactly
  one INFO record whose `record.getMessage()` formats without raising and contains both
  timestamps and `doc_id` (companion test document).
- Regression: all 9 existing tests in
  `tests/rag/ingestion/test_ingester_etag_guard.py` pass unmodified, including both
  invalid-timestamp subclass tests (AC-2).
- Cross-module regression: `tests/rag/ingestion/test_ingestion_freshness.py::TestResolveIncomingGuard`
  passes (confirms `_incoming_decision` bool contract intact).
- Static gates: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages
  scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll` — clean, no new findings.
- Coverage: changed lines reach ≥ 90% diff-cover (`rules/toolchain.md`).

## Completion criteria
- `_is_stale_update` returns `str | None`; `update()` uses `if stored is not None:` and
  logs three matching arguments.
- The stale-skip emits exactly one clean INFO line with both timestamps and `doc_id`,
  no logging traceback.
- All 9 guard tests and `TestResolveIncomingGuard` pass unmodified.
- Static gates clean; diff-cover ≥ 90% on changed lines.

## Out of Scope
- Guard decision logic, thresholds, and exception types (unchanged).
- `ETagManager` refactoring; timestamp comparison semantics (already datetime-parsed —
  the issue's lexicographic claim was corrected in verification).
- Any documentation (no doc describes this log line — `docs/21_rag/rag_05_03-logging.md`
  lists categories, not this line).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix log format and helper return shape in `scripts/rag/ingestion/etag_manager.py` | Completed | — | 20261106-192106 | REQ-001, REQ-002 guard order corrected during verification (raise-first); _is_stale_update returns str|None; 3-arg log line |
| 2 | Add `caplog` regression test | Completed | — | 20261106-192106 | REQ-003 caplog test added via companion procedure 02 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261106-192106 | full suite 11876 passed; gates Pass; diff-cover 92%; mypy/ruff/bandit/lint-imports clean |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|-------|----------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261106-073538_raging008_etagmanager-stale-log-error.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-103659_raging008_etagmanager-stale-log-error.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-153919
- **Related target files**: `scripts/rag/ingestion/etag_manager.py`