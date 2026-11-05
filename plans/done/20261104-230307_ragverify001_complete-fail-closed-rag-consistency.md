## Goal
- Make the RAG consistency check fail closed: probe errors, unavailable extension
  state, and unknown counts are reported as verification failures instead of
  healthy zero values, and consumers (recovery drill, recovery verification) act
  on that failure.

## Priority
High

## Scope
- **In-Scope**: fail-closed error propagation in consistency probes, explicit
  verification status in the consistency report contract, failure-aware
  consumption in recovery verification and the recovery drill, error-path tests,
  and the contract documentation update.
- **Out-of-Scope**: changing which consistency dimensions are checked, new
  repair/rebuild features, migration workflow changes, session write-smoke
  redesign (issue `sessmoke001`), physical restore verification
  (issue `sqliterec001`).
- **Dependencies**: `N/A: none` for this Plan's inputs. Downstream consumers:
  `drillmetrics001` builds metrics on this Plan's report contract, and
  `sqliterec001` reuses the logical verification result shape.

## Background
RAG consistency checks run in maintenance commands, startup validation,
document-management workflows, recovery drills, and recovery verification.
Adversarial verification against the current source confirmed all of the issue's
code claims: count probes swallow every `Exception`, schema/FK/embedding probes
share one `try` block, unset probe results are stored as numeric zeros, and
probe errors never become report failures.

## Problem
Three failure mechanisms were confirmed in current code:
1. Silent exception swallowing: the combined FK/embedding/schema fatal-class
   probe in `scripts/db/rag_consistency.py` wraps all three in one `try`
   block ending with `except sqlite3.Error: pass` (L93-L100). A single
   failing probe cancels the other two and leaves their counters at
   healthy-looking zeros, so a missing or broken table reads as a
   consistent report. (`_safe_url_count_query` in
   `scripts/db/rag_consistency_queries.py` intentionally returns `{}` on
   per-query failure; the source issue records this as acknowledged design,
   not a bug to fix.)
2. Zero-as-healthy: unset probe results are stored as numeric zeros
   (`basic.get(...) or 0`, `orphan_docs or 0`), so a failed query looks like a
   healthy zero-mismatch report.
3. Partial-report-as-complete: one failing probe aborts the remaining schema,
   FK, and embedding checks, and the recovery drill treats numeric counts with
   no probe-error state as a consistency pass.

## Reason for Change
Operators and automated workflows currently receive pass results from failed
verification. The report feeds startup validation, recovery drills, and
recovery verification, so a false pass weakens production reliability
guarantees.

## Implementation Intent
Keep the checked dimensions unchanged; change only failure semantics. Probes
report a value or an explicit error. The orchestrator aggregates so that
unverified dimensions never contribute to a healthy result. The report gains an
explicit verification status that consumers branch on, while existing numeric
fields keep their meaning for compatibility.

## Requirements
- `REQ-001`: Probe exceptions and unavailable extension state must propagate to
  the report contract as verification failures.
- `REQ-002`: Zero counts must not be treated as healthy when the underlying
  probe failed or produced an unknown value.
- `REQ-003`: Schema, FK, and embedding checks must continue independently when
  one of them fails.
- `REQ-004`: Recovery drill and recovery verification must consume explicit
  failure states.
- `REQ-005`: Tests must cover probe errors, extension unavailability, partial
  checks, and zero-value ambiguity.
- `REQ-006`: Documentation must describe the verification-failure contract and
  consumer expectations.

## Implementation Target Files
**Freeze status**: Frozen (`issue-to-plan` Step 8 validation passed: every row
exists, requires modification, has repository evidence, and is linked to a Plan
requirement; overlap check recorded below)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/rag_consistency.py | Refactor: fail-closed probe orchestration and aggregation | combined FK/embedding/schema fatal-class probe swallows `sqlite3.Error` (L93-L100), leaving healthy zeros and cancelling the other checks; `_embedding_dimension_issue` renders the 0/1 `dimension_mismatch` flag instead of the expected dimension count | REQ-001, REQ-002 / AC-001, AC-002 | `scripts/db/rag_consistency.py` L90-L101, L337-L346 | tests/db/test_rag_consistency.py | Verified |
| scripts/db/rag_consistency_queries.py | Refactor: per-probe error signatures; independent schema/FK/embedding checks | fatal-class probes (`_check_fk_consistency`/`_check_embedding_dimension`/`_check_schema_recognition`) already propagate `sqlite3.Error`; keep each probe's error distinct from a clean zero so the orchestrator marks the dimension unverified, and distinguish `sqlite-vec` unavailability | REQ-001, REQ-003 / AC-001, AC-003 | `scripts/db/rag_consistency_queries.py` L230-L291 | tests/db/test_rag_consistency.py | Verified |
| scripts/db/models.py | Feature: explicit verification status on `RagConsistencyReport` | report contract has numeric flags/counts only; no way to express "not verified" | REQ-001, REQ-002 / AC-002 | `scripts/db/models.py` L96-L152 (`RagConsistencyReport`) | tests/db/test_rag_consistency.py | Verified |
| scripts/db/recovery_verification.py | Feature: propagate consistency verification failure to `RecoveryResult` | `_verify_rag_logic` passes any report without failure fields through | REQ-004 / AC-004 | `scripts/db/recovery_verification.py` L87-L93, L33-L44 | tests/db/test_recovery_drill.py | Verified |
| tests/db/test_rag_consistency.py | Test: fail-closed contract and error-path regression tests | existing tests do not cover probe-error or unknown-vs-zero cases | REQ-005 / AC-005 | `tests/db/test_rag_consistency.py` (16 tests, no error-injection cases) | tests/db/test_rag_consistency.py | Verified |
| tests/db/test_recovery_drill.py | Test: drill consumes failure-aware report | drill pass path currently ignores unverified dimensions | REQ-004, REQ-005 / AC-004, AC-005 | `tests/db/test_recovery_drill.py` | tests/db/test_recovery_drill.py | Verified |
| docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md | Docs: document the verification-failure contract | section 8 currently documents numeric consistency semantics (`is_consistent` predicate list, `RagConsistencyReport` fields) with no verification-status concept | REQ-006 / AC-006 | section 8 (`db_06_...-maintenance-and-rotation.md` L46-L60) reads the contract today | N/A: docs | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/store_protocols.py | canonical embedding dimension contract (`get_embedding_dims()`) | scripts/db/rag_consistency.py, REQ-001 |
| scripts/agent/services/rag_maintenance_service.py | consumer of `RagConsistencyReport` in maintenance commands | scripts/db/models.py, REQ-004 |
| scripts/agent/startup_validation.py | consumer via `RagMaintenanceService().consistency()` | scripts/db/models.py, REQ-004 |
| scripts/rag/ingestion/document_manager.py | consumer of consistency check results in ingestion workflows | scripts/db/models.py, REQ-004 |
| scripts/db/recovery_drill.py | drill orchestration consuming `_verify_rag_session` results | scripts/db/recovery_verification.py, REQ-004 |
| rules/env.md | embedding contract 1024 dims / 4096 bytes and sqlite-vec path | scripts/db/rag_consistency_queries.py, REQ-001 |

## Acceptance Criteria
- `AC-001` (REQ-001): a probe error or unavailable `sqlite-vec` extension
  produces an explicit failure entry in the consistency report; no probe returns
  a silent empty/zero result on error.
- `AC-002` (REQ-002): dimensions whose probe failed or returned unknown are
  excluded from healthy aggregation, and the report status distinguishes
  "verified healthy" from "not verified".
- `AC-003` (REQ-003): FK, embedding, and schema checks each execute and report
  independently; one failure does not cancel the others.
- `AC-004` (REQ-004): recovery drill and recovery verification treat an
  unverified consistency dimension as a verification failure, not a pass.
- `AC-005` (REQ-005): tests exist for probe error, extension unavailability,
  partial-check, and zero-vs-unknown cases, and they fail if the fail-closed
  behavior regresses.
- `AC-006` (REQ-006): the contract documentation states the new verification
  status and consumer expectations.

## Tests
- `REQ-001`, `REQ-005`: unit tests inject `sqlite3.Error` and extension-load
  failures into each probe and assert explicit failure entries.
- `REQ-002`, `REQ-005`: tests assert that unknown probe values never aggregate
  as healthy zeros and that report status separates verified from unverified.
- `REQ-003`, `REQ-005`: tests assert schema/FK/embedding checks run
  independently when one raises.
- `REQ-004`, `REQ-005`: drill and recovery tests assert a failed verification
  blocks a consistency pass.
- Regression: existing suites for consumers (`tests/agent/`, `tests/rag/`) must
  stay green with the additive contract change.

## Documentation Impact
- Yes. `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` must document
  the verification-failure contract, driven by `REQ-006`. Naming per
  `docs/00_index.md`'s task mapping; this is the RAG write-integrity task doc.

## Assumptions
- The report contract change is additive: existing numeric fields keep their
  meaning, so consumers that only read numbers continue to work.
- All consistency probes are read-only queries and do not take the shared DB
  write lock.
- The embedding dimension contract remains `store_protocols.get_embedding_dims()`
  (1024 dims, 4096 bytes per `rules/env.md`).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Do production operations depend on current numeric severity or zero-count passes? | production consumers: `scripts/agent/startup_reporter.py` renders `rag_counts['FATAL']/['WARNING']/['SKIPPED']` in the readiness summary (L88-L100); `scripts/agent/startup_validation.py` routes on `rag_check.is_consistent` and finding severity (L238-L250); `/session rag-consistency` prints `is_consistent` (`cmd_session.py:152`) | Dependency confirmed. Change is additive: all numeric fields (`fatal_count`, `degraded_count`, per-check counts) and `issues`/`findings` in `RagConsistencyReport` (models.py L96-L152) retain their meaning, so `startup_reporter.py`/`startup_validation.py` work unchanged; the new verification-status field is orthogonal to severity. Fail-closed flips a dimension to unverified only when a probe genuinely errors or `sqlite-vec` is unavailable (a prior masked real problem), so a healthy production DB stays verified/pass. Guardrail: consumer regression suite (`tests/agent/`, `tests/rag/`) must stay green before landing (already in Tests). | False |
| UNK-02 | Should severity become typed enums (blocking / non-blocking / informational) or stay numeric? | consumer preference for enum vs numeric severity | decide at implementation-step Phase 3 against consumer usage; plan recommends keeping numeric severity and adding a separate status field | False |
| UNK-03 | Is a legitimately empty corpus a pass or a failure under the new contract? | intended semantics for empty-corpus deployments | decide during Phase 2 aggregation design; document the decision | False |
| UNK-04 | Is `sqlite-vec` guaranteed loadable in test/CI environments? | `rules/env.md` documents the production extension path only | confirm during the first test run of Phase 1 | False |
| UNK-05 | What does `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` currently promise about consistency semantics? | section 8 (L46-L60) documents `check_rag_consistency`/`is_consistent`/`summarize_issues`/`RagConsistencyReport` as numeric-only; it lists the `_CHECKS` predicates but states no verification-status field | Section 8 already covers the numeric contract; append the verification-failure status semantics (REQ-006) without rewriting existing numeric descriptions | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/rag_consistency.py | Refactor | medium (re-exported via `scripts/db/__init__.py`; maintenance/startup consumers) | 6 commits | 1 | N/A: no deployment file change |
| scripts/db/rag_consistency_queries.py | Refactor | low (db-internal probe layer) | 2 commits | 1 | N/A: no deployment file change |
| scripts/db/models.py | Feature | medium (report contract shared with agent consumers) | 1 commit | 1 | N/A: no deployment file change |
| scripts/db/recovery_verification.py | Feature | medium (drill and recovery consumers) | 1 commit | 1 | N/A: no deployment file change |
| tests/db/test_rag_consistency.py | Test | low | 3 commits | 1 | N/A: tests only |
| tests/db/test_recovery_drill.py | Test | low | N/A | 1 | N/A: tests only |
| docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md | Docs | low | N/A | 1 | N/A: docs only |

## Design
Grounded in Step 3/5 analysis:

- Failure-model mapping: the three confirmed mechanisms map to three design
  commitments. (1) Error propagation: each probe returns its result plus an
  explicit error marker; each fatal-class probe keeps propagating `sqlite3.Error`;
  the orchestrator's combined `try` block (`rag_consistency.py` L93-L100) is
  split into one guarded call per probe so FK, embedding, and schema checks run
  independently and each records its error. (2) Unknown is not zero:
  dimensions whose probe failed or returned unknown are excluded from healthy
  aggregation. (3) Consumer-visible status: `RagConsistencyReport` gains an
  explicit verification status; `scripts/db/recovery_verification.py`
  `_verify_rag_logic` and `_rag_inconsistency_detail` branch on it.
- Dependency graph: probe layer (`rag_consistency_queries.py`) -> orchestrator
  (`rag_consistency.py`) -> report contract (`models.py`) -> recovery consumers
  (`recovery_verification.py`) -> docs. No circular dependency is introduced;
  `uv run lint-imports` currently reports 6 contracts kept, 0 broken.
- Consumer scan (`tools/scan_change_consumers.py`, seeds `check_rag_consistency`
  and `RagConsistencyReport`): affected consumers are
  `scripts/db/__init__.py` (re-export), `scripts/rag/ingestion/document_manager.py`,
  `scripts/agent/commands/cmd_session.py`, `scripts/agent/startup_validation.py`,
  `scripts/agent/services/rag_maintenance_service.py`, and
  `scripts/db/recovery_verification.py`; each is recorded as a target or
  reference row. No consumer outside `scripts/db` reads `dimension_mismatch`
  directly. ADR-citation candidates (`tests/db/test_db_recovery.py`,
  `tests/agent/services/test_rag_index_integrity.py` in `docs/10_adr/`) are not
  modification targets; they join the execution set of Phase 4 verification.
- Path classification signal: 7 target files across 2 modules, 2 tests, and 1
  docs file with a public report contract change — Path B.
- Baselines: `radon cc` average A (2.9), highest B (10) at
  `_build_rag_consistency_report`; `vulture --min-confidence 80` reports no dead
  code in the target files; `bandit` clean; `coverage.xml` exists at repo root
  but diff-cover has no meaningful baseline at Plan time (working tree equals
  `master`) — the implementation phase must establish a real diff base and
  enforce `--fail-under=90`.
- Historical intelligence: the two probe modules have a dense refactor history
  (`drop unreachable URL stage handler`, `split rag consistency reporting into
  per-issue builders`, `classify sqlite read failures`), showing the fail-open
  behavior is deliberate legacy aggregation; the change must be presented as a
  semantic flip, not a cleanup.
- Bug carried from verification: `_embedding_dimension_issue` in
  `scripts/db/rag_consistency.py` passes `expected={report.dimension_mismatch}`
  (a 0/1 flag) instead of the expected dimension count; this Plan corrects it in
  the probe step.

## Implementation steps
1. **Phase 1: Probe-layer error propagation**
   - [ ] Split the combined FK/embedding/schema probe into independent
     guarded calls in `scripts/db/rag_consistency.py`, recording each
     probe's `sqlite3.Error` into `diagnostic_errors` so one failure does
     not cancel the others (REQ-001, REQ-003; scripts/db/rag_consistency.py)
   - [ ] Correct the `_embedding_dimension_issue` display bug: render the
     expected embedding dimension count instead of the 0/1
     `dimension_mismatch` flag (REQ-001; scripts/db/rag_consistency.py)
2. **Phase 2: Fail-closed aggregation**
   - [ ] Aggregate probe results so unverified dimensions never count as
     healthy (REQ-002; scripts/db/rag_consistency.py)
3. **Phase 3: Report contract status field**
   - [ ] Add the explicit verification status to `RagConsistencyReport` while
     keeping numeric fields additive (REQ-001, REQ-002; scripts/db/models.py)
4. **Phase 4: Consumer propagation**
   - [ ] Branch `RecoveryResult` on the verification status in
     `_verify_rag_logic` and `_rag_inconsistency_detail` (REQ-004;
     scripts/db/recovery_verification.py)
   - [ ] Add drill consumption tests (REQ-004, REQ-005; tests/db/test_recovery_drill.py)
5. **Phase 5: Test and documentation completion**
   - [ ] Add error-path and zero-vs-unknown regression tests (REQ-005;
     tests/db/test_rag_consistency.py)
   - [ ] Update the contract documentation (REQ-006;
     docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md)
   - [ ] Deployment validation check: `deploy.sh` copies `scripts/` tree files;
     no new files or config entries are introduced, so no deploy.sh change is
     required — verify with `bash -n deploy.sh` and a deployed-file spot check
     (REQ-006)

### Release units
N/A: no release unit (contract field is additive; each phase is independently verifiable)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/rag_consistency_queries.py | Unit: injected `sqlite3.Error` per probe | `uv run pytest tests/db/test_rag_consistency.py -k "probe or error"` | each probe surfaces an explicit error result; no silent pass |
| scripts/db/rag_consistency.py | Unit: unknown values never aggregate as healthy | `uv run pytest tests/db/test_rag_consistency.py` | failed/unknown dimensions marked unverified |
| scripts/db/models.py | Contract: additive status field | `uv run pytest tests/db/test_rag_consistency.py -k "report or contract"` | numeric fields unchanged; status present |
| scripts/db/recovery_verification.py | Integration: drill/recovery blocked on unverified state | `uv run pytest tests/db/test_recovery_drill.py tests/db/test_db_recovery.py` | consistency pass requires all dimensions verified |
| agent/rag consumers | Regression | `uv run pytest tests/agent/ tests/rag/` | startup validation, maintenance service, document manager green |
| whole repo | Full suite + coverage gate | `uv run pytest --cov --cov-report=xml` then `uv run diff-cover coverage.xml --fail-under=90` | all tests pass; changed-line coverage >= 90% |
| import contract | Static | `uv run lint-imports` | 0 broken contracts |
| static gates | Static | `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy scripts/`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run vulture scripts/ tests/ --min-confidence 80` | clean |

## Risks
- **Risk**: consumers relying on numeric severity see the new status field
  unexpectedly → **Mitigation**: keep numeric fields; add status as an additive
  field; verify all scanned consumers in Phase 4.
- **Risk**: fail-closed status flips existing production checks from pass to
  fail → **Mitigation**: resolve UNK-01 with operations before Phase 3 lands.
- **Risk**: splitting the combined probe changes check ordering or results →
  **Mitigation**: keep per-dimension results identical and test each check
  independently.
- **Risk**: legitimately-empty deployments now report failures where they passed
  before → **Mitigation**: decide UNK-03 in Phase 2 and distinguish
  empty-but-verified from unverified in the contract.
- **Risk**: bus factor 1 on the two most-churned target files → **Mitigation**:
  read existing tests and module docs before editing (Step 3 historical note).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: probe-layer error propagation | Completed | 20261105-184806 | 20261105-184806 | seq 01 (per-probe guards + diagnostics) and seq 02 (query-layer preservation confirmed). |
| 2 | Phase 2: fail-closed aggregation | Completed | 20261105-184806 | 20261105-184806 | Three unverified-flag rules added to `_CHECKS` (seq 05 interlock in `scripts/db/rag_consistency.py`). |
| 3 | Phase 3: report contract status field | Completed | 20261105-184806 | 20261105-184806 | seq 03: `fk_unverified`/`embedding_unverified`/`schema_unverified` added to `RagConsistencyReport`. |
| 4 | Phase 4: consumer propagation | Completed | 20261105-184806 | 20261105-184806 | seq 04 (`_verify_rag_logic` + detail names) and seq 06 (drill `rag_consistency` sub-key). |
| 5 | Phase 5: test and documentation completion | Completed | 20261105-184806 | 20261105-184806 | seq 05/06 tests (incl. tests/deploy interlock), seq 07 doc section 8.1; all four docs checkers pass. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-153113_01_scripts_db_rag_consistency.py.md | 1, 2 | Procedure | Pending | — | — |
| implementations/20261105-153113_02_scripts_db_rag_consistency_queries.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261105-153113_03_scripts_db_models.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261105-153113_04_scripts_db_recovery_verification.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261105-153113_05_tests_db_test_rag_consistency.py.md | 5 | Procedure | Pending | — | — |
| implementations/20261105-153113_06_tests_db_test_recovery_drill.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261105-153113_07_docs_41_db_db_06_api_and_operations-maintenance-and-rotation.md.md | 5 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261104-143443_ragverify001_complete-fail-closed-rag-consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 2026-11-04 23:03 JST
- **Related target files**: scripts/db/rag_consistency.py, scripts/db/rag_consistency_queries.py, scripts/db/models.py, scripts/db/recovery_verification.py, tests/db/test_rag_consistency.py, tests/db/test_recovery_drill.py, docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261105-153113 -->