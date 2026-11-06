# Fix malformed log format in ETagManager's stored-timestamp guard

## Goal
- The stale-update skip branch of `ETagManager.update` emits one clean log line naming the
  incoming timestamp, the stored timestamp, and `doc_id`, instead of a logging-error traceback.

## Priority
Low

## Scope
- **In-Scope**: the skip-branch log call and the private `_is_stale_update` helper's return
  shape (to expose the stored timestamp); a `caplog` regression test.
- **Out-of-Scope**: guard decision logic and exception behavior (unchanged); `ETagManager`
  refactoring; timestamp comparison semantics (already datetime-parsed — the issue's
  lexicographic claim corrected in verification).
- **Dependencies**: sequence after `plans/20261106-094942_raging002_etag-updated-before-reingestion.md`
  (co-targets `etag_manager.py`; 002 explicitly lists this log fix as its out-of-scope
  counterpart).

## Background
`update()` logs `"skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d"`
with only `new_fetched_at` and `self._doc_id` — 3 placeholders, 2 args
(`etag_manager.py:47-52`). Reproduction confirms
`TypeError: not enough arguments for format string` inside logging on every stale-skip
(`etag_manager.py:46` → `_is_stale_update` returns True when parsed `new_dt < stored_dt`,
`:57-90`; stored value fetched at `:73-76` and never exposed to `update()`). The 9 tests in
`tests/rag/ingestion/test_ingester_etag_guard.py` assert DB behavior only; none validate the
log line. Verified against HEAD `bdb9bed66` in Step 2 of this cycle.

## Problem
Every stale-skip of a data-integrity guard produces a `--- Logging error ---` traceback
instead of the intended operator-visible explanation, polluting `ingest.log` and undermining
trust in the guard's observability.

## Reason for Change
Broken log output in a data-integrity guard path (issue Reason for Change).

## Implementation Intent
Make the private helper report the stored timestamp it already read, and pass three matching
arguments to the existing `logger.info` call. Guard logic, thresholds, and exception types are
untouched.

## Requirements
- `REQ-001`: `_is_stale_update` returns the stored `fetched_at` string when the update is
  stale and `None` otherwise (replacing the bool return; same decision logic, same
  `InvalidIncomingTimestampError` / `InvalidStoredTimestampError` behavior, same single DB
  read). `update()` uses `if stored is not None:` as the skip branch. The helper stays
  private; its only caller is `update()` (verified in Step 2 — no test calls it directly).
- `REQ-002`: The skip-branch log call becomes
  `logger.info("skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d", new_fetched_at, stored_fetched_at, self._doc_id, extra={"stage_name": "ingester"})`
  — 3 placeholders, 3 args, preserving the message intent and the `%`-arg + `extra` calling
  convention used elsewhere in the file (`_log_updated`, `:104-110`).
- `REQ-003`: Regression test in `tests/rag/ingestion/test_ingester_etag_guard.py` using
  `caplog`: trigger the stale-skip, assert exactly one record at INFO, its
  `record.getMessage()` formats without raising, and the rendered text contains both
  timestamps and the `doc_id`; existing 9 tests unchanged and green.

## Implementation Target Files
**Freeze status**: Frozen (Step 8b validation passed 20261106-103659 — every row `Verified`).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/etag_manager.py` | Modify | Change `_is_stale_update` return shape to expose the stored timestamp; fix the skip-branch `logger.info` args | REQ-001, REQ-002; AC-1, AC-2 | Broken call at `:47-52` (3 placeholders vs 2 args, reproduced in Step 2); stored value local to `:73-76`; comparison at `:90`; calling convention at `:106-109` (checked in Step 2) | `tests/rag/ingestion/test_ingester_etag_guard.py` | Verified |
| `tests/rag/ingestion/test_ingester_etag_guard.py` | Modify | Add the `caplog` log-formatting regression test | REQ-003; AC-1 | 9 existing tests assert DB behavior only; no `caplog` anywhere (checked in Step 2) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/logger.py` | `Logger` wraps stdlib logging — confirms `caplog` captures its records and `%`-arg formatting happens at render time | REQ-003 |
| `scripts/rag/ingestion/document_manager.py` | Only production caller chain reaching `update()` (skip path); behavior unchanged | REQ-001 scope confirmation |
| `plans/20261106-094942_raging002_etag-updated-before-reingestion.md` | Co-targets `etag_manager.py` (adds `resolve_incoming`, leaves `update()` unchanged); ordering in Design | Dependencies |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002, REQ-003): Triggering the stale-skip emits exactly one clean INFO
  line naming both timestamps and `doc_id`, with no logging error (covered by the `caplog`
  test).
- AC-2 (REQ-001): Guard decisions are unchanged — the 9 existing tests pass unmodified,
  including the two invalid-timestamp exception tests.
- AC-3 (REQ-001..003): `uv run pytest tests/rag/ingestion/test_ingester_etag_guard.py` and
  `uv run pytest tests/rag/ingestion` pass; changed lines reach the `rules/toolchain.md`
  diff-cover threshold (≥ 90%).

## Tests
- REQ-003 new: stale-skip via `update("etag-old", ..., older_ts)` with a stored newer
  `fetched_at` → `caplog` holds exactly one INFO record for the guard logger;
  `record.getMessage()` returns a string containing the incoming ts, the stored ts, and
  `doc_id=` without raising.
- Characterization: all 9 tests in `test_ingester_etag_guard.py` unchanged and green (they
  already cover stale-skip DB behavior, empty `fetched_at`, both None early return, Z-suffix
  datetime comparison, and both invalid-timestamp subclasses).

## Documentation Impact
N/A: no documentation describes this log line (issue statement confirmed by Step 3 scan —
`docs/21_rag/rag_05_03-logging.md` lists log categories, not this line).

## Assumptions
- The stored timestamp string is safe to log verbatim (it is already validated parseable
  before the comparison at `:81-88`).
- `Logger` records reach pytest `caplog` as ordinary stdlib records (its other log lines are
  already the `%`-arg + `extra` shape used repo-wide); confirmed by reading
  `scripts/shared/logger.py` at implementation start if needed.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | N/A: no unknowns remain; the lexicographic question was resolved in verification (comparison is datetime-parsed) | — | — | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/etag_manager.py` | Modify | Low | 0 | High (single maintainer) | not applicable (rsynced) |
| `tests/rag/ingestion/test_ingester_etag_guard.py` | Modify | Low | 1 | High (single maintainer) | not applicable (rsynced) |

## Design
- Path A classification: one log call plus one private helper return-shape change in one
  module, plus a test; no contract change.
- Helper-shape decision — `_is_stale_update(new_fetched_at) -> str | None` (stored timestamp
  when stale, `None` otherwise): chosen over (a) re-querying `documents.fetched_at` in
  `update()` (second DB read for a log line — rejected) and (b) returning a
  `tuple[bool, str | None]` (bool redundant with None-ness; rejected as noisier). Public API
  (`update()`) signature is unchanged; the helper is private with a single verified caller.
- Interaction with the 002 Plan: 002 adds `ETagManager.resolve_incoming` and removes the
  pre-commit `update()` call from `DocumentManager.handle_existing_document` while explicitly
  leaving `update()` behavior unchanged; this plan fixes only `update()`'s log line and the
  private helper. No semantic contradiction; same-file co-target — implement 002 first, then
  this plan rebases cleanly (both edit disjoint regions). Dependency path:
  `plans/20261106-094942_raging002_etag-updated-before-reingestion.md`.
- `scan_change_consumers.py` not run: no persisted schema, public API, or shared-constant
  change; the private-helper return change has one verified caller. Historical analysis
  (Step 3): churn (30d) 0 (module) / 1 (test file); single maintainer
  (8+1 commits, one spelling variant). Operational check: inherited from this batch's
  `fuser /opt/llm/db/rag.sqlite` (no holders). Persisted schema check: N/A — no DDL; the
  guard's DB reads are unchanged.
- Validation quality baseline (Step 5): `radon cc` on the module — max B (file is small; no
  C-or-worse grade); `bandit -q -c pyproject.toml` and `vulture --min-confidence 80` on the
  file — clean in this batch's scans of the ingestion package. `pip-audit` N/A: no dependency
  change. Diff-cover current number not measured; ≥ 90% on changed lines required at
  implementation per `rules/toolchain.md`.

## Implementation steps
1. **Phase 1: Failing regression test (RED)**
   - [ ] Add the `caplog` stale-skip log-format test to
     `tests/rag/ingestion/test_ingester_etag_guard.py` (REQ-003; must fail against current
     code before Phase 2)
2. **Phase 2: Log fix (GREEN)**
   - [ ] Change `_is_stale_update` to return `str | None` and pass three args to the
     skip-branch `logger.info` (`scripts/rag/ingestion/etag_manager.py`) (REQ-001, REQ-002)
3. **Phase 3: Verification & deploy hand-off**
   - [ ] Run the `rules/toolchain.md` gate sequence on the touched files (pytest targeted +
     `tests/rag/ingestion`, ruff, mypy, lint-imports, bandit, diff-cover ≥ 90%)
   - [ ] Deploy hand-off: after the change is committed and pushed, `scripts/` sync via
     `skills/deploy/SKILL.md` is the user's decision (approval gate) (REQ-001)

### Release units
**Unit**: etag-log-format-fix | **Phases**: 1, 2 | **Reason**: Phase 1 adds a test that fails against the current malformed log call; the suite is green only after Phase 2 fixes the format, so neither phase validates alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/etag_manager.py` | Unit + new regression | `uv run pytest tests/rag/ingestion/test_ingester_etag_guard.py -v` | Stale-skip emits one clean INFO line with both timestamps and doc_id; no logging error |
| whole `tests/rag/ingestion` | Regression | `uv run pytest tests/rag/ingestion` | All ingestion tests green, including the 9 unchanged guard tests |
| `scripts/` touched files | Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean, no new findings |
| changed lines | Coverage | `uv run coverage run -m pytest tests/` then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |

## Risks
- **Risk**: helper return-shape change alters skip/update decisions → **Mitigation**: decision
  logic and exception paths are copy-fixed; the 9 unchanged characterization tests pin every
  branch, including stale/non-stale and both invalid-timestamp subclasses (AC-2).
- **Risk**: `caplog` may not capture the module-level `Logger` instance → **Mitigation**:
  `Logger` wraps stdlib logging (Reference Files); if capture requires propagation config in
  the test, use the same pattern already used by other repo tests that assert log output.
- **Risk**: same-file conflict with the 002 Plan → **Mitigation**: disjoint regions
  (`resolve_incoming` new method vs `update()`/`_is_stale_update`); implement 002 first.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `caplog` regression test | Completed | — | 20261106-192234 | REQ-003 |
| 2 | Fix log format and helper return shape in `scripts/rag/ingestion/etag_manager.py` | Completed | — | 20261106-192234 | REQ-001, REQ-002 |
| 3 | Gate sequence + deploy hand-off | Completed | — | 20261106-192234 | REQ-001..003 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261106-153919_01_scripts_rag_ingestion_etag_manager.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261106-153919_02_tests_rag_ingestion_test_ingester_etag_guard.py.md` | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-073538_raging008_etagmanager-stale-log-error.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261106-103659
- **Related target files**: `scripts/rag/ingestion/etag_manager.py`,
  `tests/rag/ingestion/test_ingester_etag_guard.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Constraints "No behavior change to the guard logic"; stored-value locality verified at `etag_manager.py:73-76` (checked in Step 2) | `scripts/rag/ingestion/etag_manager.py` | Phase 2 | AC-2 | 9 unchanged characterization tests | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes bullet 1; broken call verified at `:47-52` and reproduced in Step 2 | `scripts/rag/ingestion/etag_manager.py` | Phase 2 | AC-1 | New `caplog` test | Confirmed by repository evidence |
| REQ-003 | Issue Testing Expectations; absence of log-line validation verified in Step 2 | `tests/rag/ingestion/test_ingester_etag_guard.py` | Phase 1 | AC-1, AC-3 | New `caplog` test | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261106-153919 -->