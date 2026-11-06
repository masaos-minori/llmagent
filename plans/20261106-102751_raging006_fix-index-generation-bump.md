# Bump index_generation only when a run actually wrote content

## Goal
- Make the run-level `index_generation` bump fire exactly when at least one URL group wrote
  content in that run, so consumers' cache-invalidation signal stops firing on runs that
  changed nothing.

## Priority
Low

## Scope
- **In-Scope**: guard-condition swap in `RagIngester.ingest_all`; new all-groups-failed
  regression test; new skipped-only characterization test.
- **Out-of-Scope**: cache consumers of `index_generation` in the query path; bump
  granularity (stays per-run); `corpus_identity.py` internals; `TransactionManager`.
- **Dependencies**: coordination with `plans/20261106-095808_raging003_recrawled-chunk-group-poisoning.md`
  (co-targets `scripts/rag/ingestion/ingester.py` in a different region; see Design).

## Background
`ingest_all` bumps via `if results and any(not r.skipped for r in results):
bump_index_generation(db)` (`ingester.py:181-182`). Every failure result shape —
`validation_failure` (`:58-62`), `unexpected_failure` (`:65-73`), `GROUP_VALIDATION_FAILED`
(`:257-273`), all-embed-failed (`:336-342`) — carries `skipped=False` with `n_success=0`, so
a run that wrote nothing still advances the generation. The comment at `:177-180` states the
intent ("advance ... once this run has written new content"); the guard does not implement
it. Equivalence verified in Step 2: `TransactionManager.commit` runs only when
`len(prepared_chunks) > 0 and len(failed_paths) == 0` (`:304`), and there
`n_success = len(prepared_chunks) > 0` (`:327`) — so `sum(r.n_success for r in results) > 0`
is exactly "at least one group wrote content"; mixed-failure groups commit nothing and report
`n_success=0`. `bump_index_generation` is best-effort and never raises
(`corpus_identity.py:235-253`).

## Problem
A run whose every group failed (embedding service down, poisoned groups, unexpected
exceptions) bumps `index_generation` once, invalidating consumer caches for zero content
change and weakening the "content changed" meaning of the counter.

## Reason for Change
The generation counter is the corpus cache-invalidation signal; spurious bumps erode its
semantics (issue Reason for Change).

## Implementation Intent
Replace the guard at `ingester.py:181` with a content-based condition — bump only when the
summed `n_success` across results is greater than zero — keeping the call position (after the
consistency check, outside any per-URL transaction) and the best-effort contract unchanged.

## Requirements
- `REQ-001`: `RagIngester.ingest_all` bumps only when `sum(r.n_success for r in results) > 0`
  (single expression replacing `results and any(not r.skipped for r in results)`; the empty
  `results` list is covered by the same `> 0` test). Call position, best-effort semantics,
  and the run-level comment are preserved (comment reworded to match the new guard).
- `REQ-002`: Tests: new all-groups-failed regression test (embed-failure run and
  group-validation-failure run) asserts `index_generation` equals its pre-run value; new
  skipped-only characterization test (all groups already registered → skipped) asserts no
  bump; existing three tests in `test_ingester_index_generation.py` stay unchanged and green.
- `REQ-003`: `bump_index_generation` (`scripts/rag/corpus_identity.py`) and the bump call
  staying outside any transaction are unchanged (issue Constraints); exactly one bump per
  qualifying run.

## Implementation Target Files
**Freeze status**: Frozen (Step 8b validation passed 20261106-102751 — every row `Verified`).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/ingester.py` | Modify | Swap the bump guard at `:181` to the content-based condition; align the `:177-180` comment | REQ-001, REQ-003; AC-1, AC-2 | Guard `:181-182`; failure-result shapes with `skipped=False`/`n_success=0` at `:58-62`, `:65-73`, `:257-273`, `:336-342`; commit-gate equivalence at `:304`, `:327` (checked in Step 2) | `tests/rag/ingestion/test_ingester_index_generation.py` | Verified |
| `tests/rag/ingestion/test_ingester_index_generation.py` | Modify | Add all-groups-failed regression tests (embed-failure + group-validation-failure) and the skipped-only characterization test | REQ-002; AC-1, AC-3, AC-4 | Only three tests exist today (`:188`, `:222`, `:241`); skipped-only and all-failed runs untested (checked in Step 2) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/corpus_identity.py` | `bump_index_generation` best-effort contract (`:235-253`); unchanged | REQ-003 |
| `scripts/rag/ingestion/ingester.py` (`:304`, `:327` commit gate) | Basis of the `n_success > 0` ⟺ content-written equivalence | REQ-001 rationale |
| `tests/rag/ingestion/test_ingester.py` | Harness patterns (`_make_ingester`, `_FakeSQLiteHelper`, embed-failure mocking) reusable for the new tests; unchanged by this plan | REQ-002 |
| `plans/20261106-095808_raging003_recrawled-chunk-group-poisoning.md` | Co-targets `ingester.py` (group-validation routing region); coordination ordering in Design | REQ-001 sequencing |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002): After a run whose groups all failed, `index_generation` equals its
  pre-run value (covered by tests for both embed-failure and group-validation-failure shapes).
- AC-2 (REQ-001, REQ-003): After a run with at least one successful chunk insert,
  `index_generation` increments exactly once (existing `:188` test stays green).
- AC-3 (REQ-002): A skipped-only run leaves `index_generation` unchanged (new
  characterization test).
- AC-4 (REQ-001..003): `uv run pytest tests/rag/ingestion` passes and changed lines reach the
  `rules/toolchain.md` diff-cover threshold (≥ 90%).

## Tests
- REQ-002 all-failed (embed): one URL group, embedding mocked to fail every chunk →
  `index_generation` unchanged after `ingest_all`.
- REQ-002 all-failed (group validation): one poisoned group (mismatched 9-field signature) →
  `index_generation` unchanged. Note: with the current chunk-payload defect (UNK-01 in the 004
  Plan — `read_chunk_json` rejects ChunkSplitter output), construct the group files directly
  with valid chunk payloads via the `_write_chunk`-style harness rather than ChunkSplitter.
- REQ-002 all-failed (unexpected exception): group raising `sqlite3.Error` →
  `unexpected_failure` → no bump (pins the newly identified instance of the defect).
- REQ-002 skipped-only characterization: group already registered → skip → no bump.
- Characterization: the three existing tests unchanged and green.

## Documentation Impact
N/A. Verified in Step 3: no `docs/` file states when `index_generation` advances
(`docs/21_rag/rag_05_07-rag-index-consistency-checks.md` covers fatal-generation consistency
findings, not the bump guard). No doc change is made.

## Assumptions
- `n_success` remains the authoritative content-written signal: any future path that writes
  content must keep `n_success > 0` for its result (guaranteed today by the commit gate at
  `:304`/`:327`; the equivalence is pinned by a comment note rather than a runtime check).
- Consumer side of `index_generation` needs no coordinated change (issue Out of Scope).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether consumers of `index_generation` (rag-pipeline MCP cache invalidation, query path) tolerate fewer bumps — the fix makes bumps rarer, never wrong-direction | No consumer-side audit performed (out of scope per issue) | Consumer audit is a separate future task; current consumers poll the value, so a rarer bump is strictly safe | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/ingester.py` | Modify | Low | 2 | High (single maintainer) | not applicable (rsynced) |
| `tests/rag/ingestion/test_ingester_index_generation.py` | Modify | Low | 1 | High (single maintainer) | not applicable (rsynced) |

## Design
- Path A classification: one guard expression in one production module plus tests; no
  contract, schema, or cross-module change.
- Guard form decision: `if sum(r.n_success for r in results) > 0:` — chosen over
  `any(r.n_success > 0 for r in results)` because `total_success` is already computed at
  `:184` for the run summary; the Phase-2 edit can reuse a single hoisted `total_success`
  variable computed before the bump (moves `:184` above the bump) so the guard and the log
  line share one computation. Rejected: adding a per-result `wrote_content` flag (new state,
  larger diff, no benefit given the verified equivalence).
- Interaction with the 003 Plan: 003 edits `ingest_url_group`/group-routing regions
  (`:225-342`, `_process_url_groups`) and may add group-result routing; this plan edits only
  the `:181-184` run-level guard region. No semantic contradiction — 003's routed groups
  still return `n_success=0` results, which correctly suppress the bump. Co-target overlap
  flagged by `check_plan_target_overlaps.py`; implement 003 first or rebase this change on
  top (small region, low conflict risk). Dependency path:
  `plans/20261106-095808_raging003_recrawled-chunk-group-poisoning.md`.
- `scan_change_consumers.py` not run: no persisted schema, public API, or shared-constant
  change; `ingest_all`'s public signature and return value are unchanged. Historical
  analysis (Step 3): churn (30d) 2 and 1; single maintainer throughout. Operational check:
  inherited from this batch's `fuser /opt/llm/db/rag.sqlite` (no holders). Persisted schema
  check: N/A — no DDL; `rag_corpus_meta` unchanged.
- Validation quality baseline (Step 5): `radon cc scripts/rag/ingestion/ingester.py` —
  `ingest_all` C(16), `ingest_url_group` C(14), both pre-existing; the guard swap adds no
  branch. Complexity reduction of these two functions is out of scope (unrelated cleanup
  rule). `bandit`/`vulture` on `ingester.py` already clean in this batch's scans.
  `pip-audit` N/A: no dependency change. Diff-cover current number not measured (no code
  change yet); ≥ 90% on changed lines required at implementation per `rules/toolchain.md`.

## Implementation steps
1. **Phase 1: Failing regression tests (RED)**
   - [ ] Add the all-groups-failed (embed / group-validation / unexpected-exception) and
     skipped-only characterization tests to
     `tests/rag/ingestion/test_ingester_index_generation.py` (REQ-002; must fail against the
     current guard before Phase 2, except the skipped-only characterization case)
2. **Phase 2: Guard swap (GREEN)**
   - [ ] Hoist `total_success` above the bump and replace the guard condition at
     `scripts/rag/ingestion/ingester.py:181`; align the `:177-180` comment (REQ-001, REQ-003)
3. **Phase 3: Verification & deploy hand-off**
   - [ ] Run the `rules/toolchain.md` gate sequence on the touched files (pytest targeted +
     `tests/rag/ingestion`, ruff, mypy, lint-imports, bandit, diff-cover ≥ 90%)
   - [ ] Deploy hand-off: after the change is committed and pushed, `scripts/` sync via
     `skills/deploy/SKILL.md` is the user's decision (approval gate) (REQ-001)

### Release units
**Unit**: generation-bump-guard | **Phases**: 1, 2 | **Reason**: Phase 1 adds tests that fail against the current imprecise guard; the suite is green only after Phase 2 swaps the guard, so neither phase validates alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/ingester.py` | Unit + new regression | `uv run pytest tests/rag/ingestion/test_ingester_index_generation.py -v` | All-failed and skipped-only runs leave `index_generation` unchanged; success run bumps exactly once |
| whole `tests/rag/ingestion` | Regression | `uv run pytest tests/rag/ingestion` | All ingestion tests green |
| `scripts/` touched files | Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean, no new findings |
| changed lines | Coverage | `uv run coverage run -m pytest tests/` then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |

## Risks
- **Risk**: a future code path writes content while reporting `n_success=0` → no bump when a
  bump is due → **Mitigation**: equivalence pinned by the Design note and the AC-2 test; any
  change to the commit gate (`:304`) or `n_success` accounting must re-run
  `test_ingester_index_generation.py`.
- **Risk**: guard swap entangles the `total_success` hoist and creates a merge conflict with
  the 003 Plan's edits in the same file → **Mitigation**: edits are confined to the
  `:177-184` region; 003 works in `:225-342`/`_process_url_groups`; implement 003 first or
  rebase (low conflict risk).
- **Risk**: consumers briefly see a staler generation after previously-spurious bumps stop →
  **Mitigation**: intended semantics — the counter resumes meaning "content changed"; UNK-01
  records the consumer tolerance check.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add all-failed + skipped-only tests in `tests/rag/ingestion/test_ingester_index_generation.py` | Pending | — | — | REQ-002 |
| 2 | Guard swap in `scripts/rag/ingestion/ingester.py` | Pending | — | — | REQ-001, REQ-003 |
| 3 | Gate sequence + deploy hand-off | Pending | — | — | REQ-001..003 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-073538_raging006_fix-index-generation-bump.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261106-102751
- **Related target files**: `scripts/rag/ingestion/ingester.py`,
  `tests/rag/ingestion/test_ingester_index_generation.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes bullet 1; guard verified at `ingester.py:181-182`, equivalence verified at `:304`/`:327` (checked in Step 2) | `scripts/rag/ingestion/ingester.py` | Phase 2 | AC-1, AC-2 | Phase 1 all-failed tests | Confirmed by repository evidence |
| REQ-002 | Issue Testing Expectations; coverage gap verified in Step 2 (no skipped-only test exists) | `tests/rag/ingestion/test_ingester_index_generation.py` | Phase 1 | AC-1, AC-3, AC-4 | New regression + characterization tests | Explicit in issue (corrected: skipped-only coverage claimed but absent) |
| REQ-003 | Issue Constraints bullets 1-3; best-effort contract verified at `corpus_identity.py:235-253` (checked in Step 2) | `scripts/rag/ingestion/ingester.py` | Phase 2 | AC-2 | Existing `test_completed_ingest_advances_generation_by_one` + no-raise test | Confirmed by repository evidence |
