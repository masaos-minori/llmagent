# Plan: correct pagination consistency claims and the DLQ index test (ebpage003)

## Goal
- Make the DLQ pagination test state the request-local consistency the API actually provides, and rewrite the DLQ index regression test so it examines the canonical schema and the real production SQL without ever creating an index.

## Priority
Medium

## Scope
- **In-Scope**:
  - Re-word `tests/eventbus/test_eventbus_dlq_pagination.py` to the request-local contract and add a concurrent-mutation test matching it (explicit synchronization, no sleeps).
  - Rewrite `tests/eventbus/test_eventbus_dlq_index.py`: schema-shape assertions (fail on a missing canonical index, never `CREATE INDEX`), a separate plan assertion over the exact SQL `fetch_dlq()`/`count_dlq()` execute (captured via `sqlite3.Connection.set_trace_callback`), and a fixed publish (publisher token, asserted success).
  - State the pagination consistency boundary in the DLQ and replay endpoint docs.
- **Out-of-Scope**: a cross-page snapshot mechanism (cursor/token/expiry) — not chosen; DLQ response shape and ordering unchanged; production query text unchanged; keyset pagination; other query-plan tests.
- **Dependencies**: The archived Plans `plans/done/20261028-093155_ebdurable003_*` and `plans/done/20261028-094441_ebdlqunique007_*` have all procedures implemented (`implementations/` top level is empty), so none of this Plan's files carries an active procedure row. No ordering required against sibling Plans in `plans/`: this Plan's doc rows are `eventbus_04_dlq_endpoint.md` and `eventbus_11_replay_endpoint.md`; ebdlqrecon002 edits `eventbus_03_dlq_operations.md` (different files).

## Background
`dlq_list()` in `scripts/eventbus/dlq_route.py` computes `total` (`count_dlq`) and the page (`fetch_dlq`) inside one `run_with_db_lock` acquisition: consistency is request-local; two HTTP requests share no cursor or snapshot token. `tests/eventbus/test_eventbus_dlq_pagination.py` (docstring at lines 145-155) claims two sequential requests "must come from one consistent snapshot" — a cross-request guarantee the API does not provide. `tests/eventbus/test_eventbus_dlq_index.py::test_dlq_query_uses_index` creates `idx_events_dlq_at` when absent (line 58-59), so it cannot fail on the schema regression it exists to catch, and its EXPLAIN runs on a synthetic query (`ORDER BY dlq_at DESC`) that is not `fetch_dlq()`'s SQL. The test publishes with the shared `auth_token` (control-plane roles only) and ignores the response; verified in this cycle that such a publish returns 403.

Verified planner facts (throwaway database from canonical `schema.sql`, 2026-10-28):
- `count_dlq`'s SQL (`SELECT COUNT(*) ... WHERE dlq_at IS NOT NULL`) plans as `SEARCH events USING COVERING INDEX idx_events_dlq_seq`.
- `fetch_dlq`'s SQL (`... ORDER BY seq LIMIT ? OFFSET ?`) plans as `SCAN events` (seq is rowid order, so no sort and no DLQ index is used). A rewritten test that asserts "the index is used" on the page query would assert something false.

## Problem
One test names a guarantee the API does not provide; the index regression test self-repairs the regression it should catch and examines a different query from production, giving false assurance about the DLQ read path.

## Reason for Change
Testability and an ambiguous public contract. No outage, not time-sensitive; Medium.

## Implementation Intent
Adopt the recommended request-local contract (matches the code; UNK-01 records the owner decision as non-blocking for this direction). Tests assert what is true: per-response consistency of `total` and `items`, and a plan assertion over the exact production SQL captured at execution time. The page-query plan fact (`SCAN events`, no temp B-tree sort) and the count-query fact (`COVERING INDEX idx_events_dlq_seq`) are each asserted separately; the schema-shape half of the test pins `idx_events_dlq_at` and `idx_events_dlq_seq` presence and fails when a canonical index is dropped in a throwaway database. Docs state the boundary as current behavior.

## Requirements
- `REQ-001`: `tests/eventbus/test_eventbus_dlq_pagination.py` no longer describes two independent requests as one snapshot; its wording states request-local consistency, and it adds a concurrent-mutation test with explicit synchronization (no sleeps) that asserts the chosen contract (each response is internally consistent; a page pair taken across a mutation is not claimed to be).
- `REQ-002`: `tests/eventbus/test_eventbus_dlq_index.py` never executes `CREATE INDEX` or any DDL beyond what `open_db`/`schema.sql` applies; it fails when `idx_events_dlq_at` or `idx_events_dlq_seq` is absent from the examined database, including a negative test that drops an index in a throwaway database and asserts the detection fails.
- `REQ-003`: The plan assertion runs `EXPLAIN QUERY PLAN` on the exact SQL strings captured from production `fetch_dlq()` and `count_dlq()` execution via `set_trace_callback`, asserting the verified facts: the count statement uses `idx_events_dlq_seq`; the page statement uses no temporary B-tree sort. Schema-shape assertions and plan assertions stay separate test cases.
- `REQ-004`: The index test's data setup publishes with a publisher-role token and asserts the publish succeeded (no ignored 403).
- `REQ-005`: The DLQ endpoint doc states the per-response consistency boundary and the replay endpoint doc phrases its single-lock guarantee as per-response (removing the word "snapshot"), current behavior only.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 2026-10-29: all target rows Verified; `tools/check_workitem_structure.py` clean; `tools/check_plan_target_overlaps.py` findings reviewed as documented sequencing dependencies).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tests/eventbus/test_eventbus_dlq_pagination.py | Re-word to request-local contract; add concurrent-mutation test | Snapshot wording claims a nonexistent guarantee | REQ-001; AC-1, AC-5 | Docstring lines 145-155 "one consistent snapshot"; two sequential requests | The rewritten tests themselves | Verified |
| tests/eventbus/test_eventbus_dlq_index.py | Rewrite: no DDL, schema-shape + real-SQL plan assertions, fixed publish | Self-repairing CREATE INDEX and synthetic query give false assurance | REQ-002, REQ-003, REQ-004; AC-2, AC-3, AC-4 | Lines 58-59 CREATE INDEX; lines 63-67 synthetic SQL; line 32/48 shared-token publish (verified 403) | The rewritten tests themselves | Verified |
| docs/24_eventbus/eventbus_04_dlq_endpoint.md | State per-response consistency boundary | Pagination docs state envelope and bounds but not the consistency boundary | REQ-005; AC-6 | Lines 31-32 describe limit/offset and envelope only | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| docs/24_eventbus/eventbus_11_replay_endpoint.md | Replace "consistent snapshot" wording with per-response wording | Current wording names a snapshot mechanism that does not exist across requests | REQ-005; AC-6 | Line 68: "form a consistent snapshot" | `tools/check_docs_consistency.py --domain eventbus` | Verified |

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/eventbus/dlq_route.py | Shows `total` and page computed in one `run_with_db_lock` acquisition — the definition of the request-local boundary; not modified (no snapshot mechanism chosen) | REQ-001, REQ-005 |
| scripts/eventbus/event_repo.py | Source of the exact SQL for `fetch_dlq` (line ~118) and `count_dlq` (line ~141); not modified | REQ-003 |
| scripts/eventbus/schema.sql | Canonical index definitions `idx_events_dlq_at`, `idx_events_dlq_seq`; not modified | REQ-002 |
| tests/eventbus/test_eventbus_replay_pagination.py | Checked for the same snapshot wording; verified none present, so it requires no modification | REQ-001 scope check |
| scripts/eventbus/auth.py | Publisher token semantics for the fixed publish fixture | REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001): no test in `tests/eventbus` calls independent requests "one snapshot"; the DLQ pagination test's wording matches the request-local contract.
- AC-2 (REQ-002): the index test contains no `CREATE INDEX`; removing `idx_events_dlq_at` or `idx_events_dlq_seq` from the examined schema makes it fail (proved by the throwaway-drop negative test).
- AC-3 (REQ-003): plan assertions execute on SQL captured from the production functions, and both verified planner facts are asserted.
- AC-4 (REQ-004): the index test's setup publish asserts a 2xx response.
- AC-5 (REQ-001): the concurrent-mutation test passes deterministically with explicit synchronization, no sleeps.
- AC-6 (REQ-005): both endpoint docs state the per-response boundary; `tools/check_docs_consistency.py --domain eventbus` and `tools/check_docs_structure.py` pass.

## Tests
- REQ-001: reworded response-local consistency test plus a concurrent-mutation test (mutation thread synchronized via `threading.Event`/barrier against the two requests).
- REQ-002: schema-shape test on a database opened through `open_db` (canonical schema) and a negative test that drops each canonical index in a throwaway copy and asserts the test path reports failure.
- REQ-003: capture production SQL with `set_trace_callback` during `fetch_dlq()`/`count_dlq()` calls, then EXPLAIN the captured statements; assert covering-index use for the count and absence of a temp B-tree sort for the page.
- REQ-004: fixture gains `publisher_token`; publish asserted 200 with that token.
- Suite: `uv run pytest tests/eventbus`; ruff and mypy on changed test files.

## Documentation Impact
Yes, small: the EventBus DLQ endpoint document and the replay endpoint document (per `docs/00_index.md` task mapping for EventBus endpoint reference docs) state the per-response consistency boundary for REQ-005. Current behavior only.

## Assumptions
- The request-local contract is adopted (the issue's recommended option, matching the code). If the owner later chooses cross-page snapshots, that is a new Plan: the frozen table here has no `dlq_route.py`/`event_repo.py` rows.
- SQLite's planner choices for these two statements are stable enough at the project's SQLite version to assert as facts; they were verified in this cycle and the assertions are phrased around plan features (covering index used / no temp sort), not exact opcodes.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Owner confirmation of the request-local pagination contract (vs cross-page snapshot) | Owner decision | The Plan adopts the issue's recommended request-local option; if the owner objects before implementation, stop and re-scope (a snapshot mechanism would add production rows and a new Plan) | False |
| UNK-02 | Whether asserting "no temp B-tree sort" for the page query is durable across SQLite upgrades | Version-pinned SQLite behavior beyond this cycle | Verified 2026-10-28 on the project SQLite; procedure writes the assertion with a comment citing the verified plan output; revisit only on a SQLite version bump | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tests/eventbus/test_eventbus_dlq_pagination.py | Reword + new test | Tests only; 12 recent commits — collision-prone file | 12 | 2 | N/A: test file is not deployed |
| tests/eventbus/test_eventbus_dlq_index.py | Test rewrite | Tests only | 1 | 1 | N/A: test file is not deployed |
| docs/24_eventbus/eventbus_04_dlq_endpoint.md | One boundary sentence | Docs only | 0 | N/A (single-author doc; treat as 1) | N/A: docs are deployed read-only if changed |
| docs/24_eventbus/eventbus_11_replay_endpoint.md | Wording fix | Docs only | 3 | 1 | N/A: docs are deployed read-only if changed |

## Design
- Contract definition: request-local — `total` and `items` are read under one `run_with_db_lock` acquisition; two requests may observe different states. Tests must assert per-response internal consistency only.
- Index test split into three cases: (1) schema shape — `open_db` database contains both canonical DLQ indexes and `user_version` matches; (2) negative shape — copy of the database with one index dropped (throwaway) makes the shape check fail; (3) plan — production functions executed against the test database with `set_trace_callback` capturing the exact SQL, EXPLAIN asserting the verified facts. No DDL in the test.
- Concurrent-mutation test for pagination: publish/nack a row from a worker thread synchronized with the request sequence; each response is asserted internally consistent (`len(items)` matches `total`-bounded window) rather than claiming cross-request stability.
- Fixture token fix: `publisher_token` added to the config so the publish is authorized; assert response status.

## Implementation steps

1. **Phase 1: Index test rewrite**
   - [ ] Rewrite `tests/eventbus/test_eventbus_dlq_index.py` per the Design (REQ-002, REQ-003, REQ-004; tests/eventbus/test_eventbus_dlq_index.py)
2. **Phase 2: Pagination test reword and extension**
   - [ ] Re-word `tests/eventbus/test_eventbus_dlq_pagination.py` to the request-local contract (REQ-001; tests/eventbus/test_eventbus_dlq_pagination.py)
   - [ ] Add the synchronized concurrent-mutation test (REQ-001; tests/eventbus/test_eventbus_dlq_pagination.py)
3. **Phase 3: Docs**
   - [ ] Add the per-response consistency boundary to the DLQ endpoint doc and rephrase the replay doc's snapshot sentence (REQ-005; docs/24_eventbus/eventbus_04_dlq_endpoint.md, docs/24_eventbus/eventbus_11_replay_endpoint.md)
4. **Phase 4: Verification**
   - [ ] `uv run pytest tests/eventbus`, ruff and mypy on changed files, `tools/check_docs_consistency.py --domain eventbus`, `tools/check_docs_structure.py` on the changed docs (REQ-001..REQ-005; all rows)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_dlq_index.py | Unit + negative regression (drop-index) | `uv run pytest tests/eventbus/test_eventbus_dlq_index.py` | Shape and plan cases pass; drop-index negative case proves failure detection |
| tests/eventbus/test_eventbus_dlq_pagination.py | Integration with explicit synchronization | `uv run pytest tests/eventbus/test_eventbus_dlq_pagination.py` (repeat 3x) | Deterministic, no sleeps |
| tests/eventbus (whole suite) | Suite run | `uv run pytest tests/eventbus` | Baseline 411 passed, 1 skipped plus new tests, no new skips |
| docs/24_eventbus/eventbus_04_dlq_endpoint.md, docs/24_eventbus/eventbus_11_replay_endpoint.md | Docs consistency + structure | `uv run python tools/check_docs_consistency.py --domain eventbus`; `uv run python tools/check_docs_structure.py` | Clean |

## Risks
- **Risk**: asserting today's SQLite plan output breaks on a SQLite upgrade → **Mitigation**: assertions target plan features (covering index present in plan / no temp sort), UNK-02 records the version coupling.
- **Risk**: the concurrent-mutation test is flaky → **Mitigation**: explicit synchronization primitives required by the test design (AC-5), same pattern required in ebdlqrecon002.
- **Risk**: owner later wants snapshot semantics → **Mitigation**: contract choice recorded in UNK-01; adopting it now matches the code and the issue's recommendation; a snapshot choice is a new Plan, not an edit of this one.

## Validation Quality Analysis
Baseline (2026-10-28, pre-implementation, saved under `.opencode/verification/`):
- radon: no production file is touched; `dlq_route.py` baseline A (2.0), `event_repo.py` baseline A (3.71). Gate: vacuous unless an implementation step drifts into production files — frozen table has no production row, so any such drift must stop and return to the owner (snapshot choice).
- vulture: unchanged production files; baseline in `vulture_20261028.txt`. Test-only rewrite must leave no unused helpers in the rewritten test files.
- bandit: baseline 3 findings (B101 in untouched files) in `bandit_20261028.json`; gate — no new finding.
- diff-cover: TOTAL 91% baseline; `dlq_route.py` 100%, `event_repo.py` 89% (unchanged). Production lines are not modified, so the incremental gate is vacuous; the rewritten tests must keep `fetch_dlq`/`count_dlq` exercised.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite index test (REQ-002..REQ-004) | In Progress | — | — |  |
| 2 | Pagination reword (REQ-001) | In Progress | — | — |  |
| 3 | Concurrent-mutation test (REQ-001) | In Progress | — | — |  |
| 4 | Endpoint docs boundary wording (REQ-005) | In Progress | — | — |  |
| 5 | Full verification (REQ-001..REQ-005) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261029-094100_01_tests_eventbus_test_eventbus_dlq_pagination.py.md | 2, 3 | Procedure | Pending | — | — |
| implementations/20261029-094100_02_tests_eventbus_test_eventbus_dlq_index.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261029-094100_03_docs_24_eventbus_eventbus_04_dlq_endpoint.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261029-094100_04_docs_24_eventbus_eventbus_11_replay_endpoint.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261028-122307_ebpage003_pagination-contract-dlq-index.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-231631
- **Related target files**: `tests/eventbus/test_eventbus_dlq_pagination.py`, `tests/eventbus/test_eventbus_dlq_index.py`, `docs/24_eventbus/eventbus_04_dlq_endpoint.md`, `docs/24_eventbus/eventbus_11_replay_endpoint.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Background bullet 2; lines 145-155 wording | tests/eventbus/test_eventbus_dlq_pagination.py | Phase 2 | AC-1, AC-5 | Reworded tests + concurrent-mutation test | Explicit in issue |
| REQ-002 | Issue Background bullet 3; test lines 58-59 | tests/eventbus/test_eventbus_dlq_index.py | Phase 1 | AC-2 | Drop-index negative test | Explicit in issue |
| REQ-003 | Issue Background bullet 4; verified planner facts (this cycle) | tests/eventbus/test_eventbus_dlq_index.py | Phase 1 | AC-3 | set_trace_callback plan assertions | Derived from confirmed evidence |
| REQ-004 | Issue Background bullet 5 (publish ignored; verified 403) | tests/eventbus/test_eventbus_dlq_index.py | Phase 1 | AC-4 | Asserted publish with publisher token | Confirmed by repository evidence |
| REQ-005 | Issue Required Changes bullet 5; doc line 68 read | docs/24_eventbus/eventbus_04_dlq_endpoint.md | Phase 3 | AC-6 | check_docs_consistency run | Explicit in issue |
| REQ-005 | Issue Target Files; replay doc line 68 | docs/24_eventbus/eventbus_11_replay_endpoint.md | Phase 3 | AC-6 | check_docs_consistency run | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261029-094100 -->