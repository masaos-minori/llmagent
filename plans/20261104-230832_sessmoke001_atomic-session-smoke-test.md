## Goal
- Make session consistency verification read-only: replace the mutating
  insert/commit/delete write smoke test in `scripts/db/session_consistency.py`
  with a read-only probe of the same tables, so drills, recovery checks, and
  repeated validations never add or delete temporary rows.

## Priority
High

## Scope
- **In-Scope**: a read-only replacement probe in `scripts/db/session_consistency.py`,
  the `SessionConsistencyReport` field contract update, the matching trigger
  change in `scripts/db/recovery_verification.py`, test updates, and the
  documentation correction in the recovery/reference doc.
- **Out-of-Scope**: RAG (non-session) consistency changes beyond what the shared
  report contract requires (covered by `ragverify001`), physical restore
  behavior (covered by `sqliterec001`), drill metric changes (covered by
  `drillmetrics001`), any new write-capability feature.
- **Dependencies**: sequencing dependency on `plans/20261104-230307_ragverify001_complete-fail-closed-rag-consistency.md`
  — both Plans modify `scripts/db/models.py` and
  `scripts/db/recovery_verification.py`.
  - **Depends on**: plans/20261104-230307_ragverify001_complete-fail-closed-rag-consistency.md | phase all | shared target rows in `scripts/db/models.py` and `scripts/db/recovery_verification.py`; this Plan's rows must be re-verified against the code state left by that Plan before editing

## Background
Session consistency checks run in startup validation, maintenance commands,
session workflows, recovery verification, and recovery drills. The current
session check mutates data: `_check_write_smoke_test` inserts a throwaway
`session_diagnostics` row, commits it, looks it up, deletes it, and commits
again. Adversarial verification confirmed every claim of the issue against
`scripts/db/session_consistency.py` L75-L105.

## Problem
1. The consistency check performs data changes during verification, which is
   unsafe to run automatically during drills, incident verification, and
   repeated checks (L86-L99: INSERT, COMMIT, DELETE, COMMIT).
2. Repeated execution leaves audit noise and residue risk in
   `session_diagnostics`: cleanup selects only the newest `kind='smoke'` row,
   so an interrupted run can leave rows behind.
3. Operators and tests treat the mutating probe as a health signal
   (`write_smoke_test_ok`), which conflates verification with data insertion.

## Reason for Change
Verification paths must not mutate production data. The recovery drill and
recovery verification invoke this check repeatedly, and the smoke test's
side effects undermine both the audit trail and the drill's read-only guarantee.

## Implementation Intent
Remove the mutating probe and its report field. The repository already has the
read-only coverage the replacement needs: `session_diagnostics` is probed with
`SELECT COUNT(*)` at `scripts/db/session_consistency.py` L174-L179 into
`session_diagnostics_readable`, and `_check_read_smoke_test` covers the read
path. Deleting the write group therefore replaces the mutating smoke with the
existing read-only probes instead of adding a new one. Keep every other session
rule untouched.

## Requirements
- `REQ-001`: Session consistency verification must not insert, commit, delete,
  or otherwise mutate data.
- `REQ-002`: Drills and recovery checks must verify session health through the
  read-only probe.
- `REQ-003`: Session health checks must cover the existing `session_diagnostics`
  table through the read-only probes that already exist in the module.
- `REQ-004`: Tests must prove the session logic path runs without data mutation.
- `REQ-005`: Report semantics must distinguish verified read-only health from
  unverified or failed checks.
- `REQ-006`: Documentation must state the read-only session verification
  contract.

## Implementation Target Files
**Freeze status**: Frozen (`issue-to-plan` Step 8 validation passed: every row
exists, requires modification, has repository evidence, and is linked to a Plan
requirement; overlap with `plans/20261104-230307_ragverify001_complete-fail-closed-rag-consistency.md`
on `scripts/db/models.py` and `scripts/db/recovery_verification.py` is recorded
in Assumptions as a sequencing dependency, not a contradiction)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/session_consistency.py | Refactor: delete `_check_write_smoke_test` and its check group; keep the existing read-only probes | L75-L105 INSERT/COMMIT/DELETE/COMMIT inside the check; L187-L191 write group; L221 gate reads `write_smoke_test_ok is not False`; L174-L179 already provide the read-only `session_diagnostics` probe | REQ-001, REQ-003 / AC-001, AC-003 | `scripts/db/session_consistency.py` L75-L105, L174-L179, L187-L191, L201, L221 | tests/db/test_session_consistency.py | Verified |
| scripts/db/models.py | Refactor: remove the `write_smoke_test_ok` field from `SessionConsistencyReport` | public contract claims a write test that no longer exists | REQ-005 / AC-005 | `scripts/db/models.py` L175-L177 (`session_diagnostics_readable`, `read_smoke_test_ok`, `write_smoke_test_ok`) | tests/db/test_session_consistency.py | Verified |
| scripts/db/recovery_verification.py | Refactor: `_session_inconsistency_detail` trigger update | L81 triggers on `report.write_smoke_test_ok is False` | REQ-002 / AC-002 | `scripts/db/recovery_verification.py` L63-L84 | tests/db/test_db_recovery.py | Verified |
| tests/db/test_session_consistency.py | Test: read-only probe behavior and no-mutation assertion | current tests assert `write_smoke_test_ok is True` (L124, L152) | REQ-004 / AC-004 | `tests/db/test_session_consistency.py` L124, L152 | tests/db/test_session_consistency.py | Verified |
| tests/db/test_db_recovery.py | Test: trigger-semantics tests after the write-smoke trigger removal | fixture and trigger tests reference `write_smoke_test_ok` (L891, L1041-L1074) | REQ-004 / AC-004 | `tests/db/test_db_recovery.py` L891, L1041-L1074 | tests/db/test_db_recovery.py | Verified |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Docs: replace "write smoke test" wording with the read-only contract | L69 documents "a write smoke test (both)" | REQ-006 / AC-006 | `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` L69 | N/A: docs | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/rag_consistency_queries.py | the existing read-smoke pattern to mirror (`_check_read_smoke_test`, COUNT-only reads) | scripts/db/session_consistency.py, REQ-001 |
| scripts/db/rag_consistency.py | shows how read smoke feeds the report without mutation (L111) | scripts/db/session_consistency.py, REQ-001 |
| scripts/db/schema_sql.py | `session_diagnostics` table definition and columns for the read probe | scripts/db/session_consistency.py, REQ-003 |
| scripts/agent/services/rag_maintenance_service.py | consumer of `SessionConsistencyReport` in maintenance commands | scripts/db/models.py, REQ-005 |
| scripts/agent/startup_validation.py | consumer of session consistency at startup | scripts/db/models.py, REQ-005 |

## Acceptance Criteria
- `AC-001` (REQ-001): running `check_session_consistency()` performs no INSERT,
  UPDATE, DELETE, or COMMIT; a row-count snapshot before and after the check is
  identical.
- `AC-002` (REQ-002): recovery verification and drills still flag session
  verification failures through the remaining rules (`session_diagnostics_readable`,
  `read_smoke_test_ok`, `diagnostic_errors`) after the write-smoke trigger is
  removed.
- `AC-003` (REQ-003): the read-only probes (`SELECT COUNT(*) FROM
  session_diagnostics` at L174-L179 and `_check_read_smoke_test`) remain the
  session health path, and no INSERT/DELETE remains in the module.
- `AC-004` (REQ-004): tests assert the whole session consistency path leaves the
  database byte-identical (no residue rows), and the recovery trigger tests
  cover the removed write-smoke entry.
- `AC-005` (REQ-005): `SessionConsistencyReport` no longer contains a field that
  claims a write test; verified read-only health (`session_diagnostics_readable`,
  `read_smoke_test_ok`), failure (`False` on those flags or non-empty
  `diagnostic_errors`), are distinguishable without a write probe.
- `AC-006` (REQ-006): the recovery/reference documentation describes the
  read-only session verification contract.

## Tests
- `REQ-001`, `REQ-004`: a characterization test snapshots `session_diagnostics`
  row count and contents before and after `check_session_consistency()` and
  asserts equality; a spy asserts no INSERT/DELETE statement is executed.
- `REQ-003`, `REQ-005`: probe tests confirm `session_diagnostics_readable` and
  `read_smoke_test_ok` still report the healthy/missing-table/read-failure states
  after the write group is deleted.
- `REQ-002`: recovery verification tests (`tests/db/test_db_recovery.py`)
  updated for the removed `write_smoke_fail` entry keep the remaining trigger
  semantics (`None` means "not run" for other fields stays intact).
- Regression: `tests/agent/` session/maintenance tests stay green with the
  field removal.

## Documentation Impact
- Yes. The recovery/reference doc (`docs/41_db/`, recovery-and-reference task
  row of `docs/00_index.md`) must state that session verification is read-only,
  driven by `REQ-006`.

## Assumptions
- The write smoke test has no functional purpose beyond probing write
  capability; no code path depends on the throwaway row surviving the check.
- The removal keeps the existing `session_diagnostics_readable` and
  `read_smoke_test_ok` semantics unchanged; no other rule is touched.
- Overlap judgment: `scripts/db/models.py` and `scripts/db/recovery_verification.py`
  are shared with `plans/20261104-230307_ragverify001_complete-fail-closed-rag-consistency.md`.
  The edits touch different report classes (`SessionConsistencyReport` vs
  `RagConsistencyReport`) and different functions (`_session_inconsistency_detail`
  vs `_verify_rag_logic` / `_rag_inconsistency_detail`); they are sequenced
  (ragverify001 first) rather than run concurrently, and this Plan's rows are
  re-verified against the post-ragverify001 file state.
- The issue's claim that `scripts/db/session_schema.py` provides a `session_id`
  helper is disconfirmed: no such file or function exists in the repository; the
  requirement is dropped as not applicable.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Do production monitoring or operational scripts read `write_smoke_test_ok` outside this repository? | consumer scan covers repo code and tests only; external dashboards/scripts unknown | confirm with operations before the field removal lands | True |
| UNK-02 | Is any write-capability signal required from consistency checks after the removal (e.g., a separate explicit write-check command)? | the issue mandates removal but does not state whether ops need a replacement signal | default is removal without replacement; add a separate explicit check only if operations confirm the need | False |
| UNK-03 | Do drill audit artifacts or stored reports serialize `write_smoke_test_ok` in a way readers depend on? | drill audit artifact schema for this field not yet confirmed | inspect the drill audit artifact writer during Phase 2 | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/session_consistency.py | Refactor | medium (maintenance/startup/recovery consumers) | 1 commit | 1 | N/A: no deployment file change |
| scripts/db/models.py | Refactor | medium (shared report contract module) | 1 commit | 1 | N/A: no deployment file change |
| scripts/db/recovery_verification.py | Refactor | medium (drill and recovery consumers) | 1 commit | 1 | N/A: no deployment file change |
| tests/db/test_session_consistency.py | Test | low | 1 commit | 1 | N/A: tests only |
| tests/db/test_db_recovery.py | Test | low | 1 commit | 1 | N/A: tests only |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Docs | low | N/A | 1 | N/A: docs only |

## Design
Grounded in Step 3/5 analysis:

- Replacement design: delete the write group. The read-only coverage the issue
  asks for already exists in the same module: `SELECT COUNT(*) FROM
  session_diagnostics` at L174-L179 (feeds `session_diagnostics_readable`) and
  `_check_read_smoke_test` (feeds `read_smoke_test_ok`). Deleting
  `_check_write_smoke_test` and its group (L187-L191) leaves a verification path
  that touches only reads, with no new probe to maintain.
- Contract change: remove `SessionConsistencyReport.write_smoke_test_ok`
  (`scripts/db/models.py` L177) and the matching rule term in `is_consistent`
  (session_consistency.py L221) and the matching entry in
  `_session_inconsistency_detail` (recovery_verification.py L66, L81). These are
  the only in-repo logic consumers; they move in the same unit as the removal
  (UNK-01 gates external consumers).
- Scan candidates disposition (`tools/scan_change_consumers.py --seed
  write_smoke_test_ok`): in-repo consumers
  `scripts/db/session_consistency.py`, `scripts/db/models.py`,
  `scripts/db/recovery_verification.py`, `tests/db/test_session_consistency.py`,
  `tests/db/test_db_recovery.py` — all recorded as target rows.
  ADR-citation candidates (`tests/db/test_db_recovery.py` citations in
  `docs/10_adr/adr_01_index.md` and `docs/10_adr/adr_02_05_008`) are not
  modification targets; they join the Phase 5 execution set.
- Path classification signal: 6 target files across 2 modules, 2 tests, and 1
  docs file with a public report field removal — Path B. The issue's proposed
  3-file target list is corrected: the mutating probe lives in
  `session_consistency.py`, not `rag_consistency.py` (RAG already has a
  read-only smoke), so `scripts/db/rag_consistency.py` is `not affected: its
  smoke probe is already read-only (rag_consistency.py L111)`.
- Baselines: `radon cc scripts/db/session_consistency.py` average A (4.6) —
  `_check_write_smoke_test` itself is the most complex block and is being
  replaced, so no hotspot remains; churn low (1 commit/30d per file), bus
  factor 1.
- Historical note: `check_session_consistency`'s docstring itself documents the
  mutation ("All queries are read-only except the write smoke test"), and
  `docs/41_db/db_07` repeats it — the change removes a documented exception
  rather than an accidental one.

## Implementation steps
1. **Phase 1: Remove the mutating probe**
   - [ ] Delete `_check_write_smoke_test` and its check group (REQ-001, REQ-003;
     scripts/db/session_consistency.py)
2. **Phase 2: Report contract**
   - [ ] Remove the `write_smoke_test_ok` field from `SessionConsistencyReport`
     and the matching `is_consistent` term (REQ-005; scripts/db/models.py,
     scripts/db/session_consistency.py)
3. **Phase 3: Consumer propagation**
   - [ ] Remove the `write_smoke_fail` entry from `_session_inconsistency_detail`
     and its docstring note (REQ-002; scripts/db/recovery_verification.py)
4. **Phase 4: Tests**
   - [ ] Add the no-mutation characterization test and probe-state tests
     (REQ-004; tests/db/test_session_consistency.py)
   - [ ] Update the recovery trigger/fixture tests for the removed entry
     (REQ-004; tests/db/test_db_recovery.py)
5. **Phase 5: Documentation and full validation**
   - [ ] Update the recovery/reference doc wording (REQ-006;
     docs/41_db/db_07_api_and_operations-recovery-and-reference.md)
   - [ ] Deployment validation check: no new files, configs, or service changes;
     `deploy.sh` copies the `scripts/` tree as-is — verify with `bash -n deploy.sh`
     and a deployed-file spot check (REQ-006)

### Release units
**Unit**: session report contract removal | **Phases**: 1, 2, 3 | **Reason**: removing the field from `scripts/db/models.py` leaves `scripts/db/session_consistency.py` and `scripts/db/recovery_verification.py` referencing a contract member that no longer exists until all three phases land together

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/session_consistency.py | Unit: probe states (healthy/missing/read-error) + no-mutation snapshot | `uv run pytest tests/db/test_session_consistency.py` | identical row counts before/after; no INSERT/DELETE executed |
| scripts/db/models.py | Contract: field removal | `uv run pytest tests/db/test_session_consistency.py -k "report or contract"` | no write-claim field remains |
| scripts/db/recovery_verification.py | Integration: remaining trigger semantics unchanged | `uv run pytest tests/db/test_db_recovery.py -k "session"` | remaining failure and not-run cases behave as before |
| ADR-cited recovery tests | Integration | `uv run pytest tests/db/test_db_recovery.py` | all cited recovery tests pass |
| whole repo | Full suite + coverage gate | `uv run pytest --cov --cov-report=xml` then `uv run diff-cover coverage.xml --fail-under=90` | all tests pass; changed-line coverage >= 90% |
| import contract | Static | `uv run lint-imports` | 0 broken contracts |
| static gates | Static | `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy scripts/`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run vulture scripts/ tests/ --min-confidence 80` | clean |

## Risks
- **Risk**: removing the write probe loses a write-capability signal operators
  may rely on → **Mitigation**: resolve UNK-01/UNK-02 with operations; the
  remaining read probes still detect a missing or unreadable `session_diagnostics`.
- **Risk**: the field removal breaks external consumers → **Mitigation**: UNK-01
  confirmation before Phase 2; the removal is a single coordinated unit (release
  unit Phases 1-3).
- **Risk**: concurrent edits with the `ragverify001` Plan on `models.py` and
  `recovery_verification.py` conflict → **Mitigation**: strict sequencing
  (ragverify001 first) and row re-verification before editing.
- **Risk**: a COUNT-only probe becomes trivially true on an empty database →
  **Mitigation**: keep the existing required-tables check as the existence
  guarantee and document that the probe verifies readability, not content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: read-only probe | Pending | — | — | |
| 2 | Phase 2: report contract | Pending | — | — | |
| 3 | Phase 3: consumer propagation | Pending | — | — | |
| 4 | Phase 4: tests | Pending | — | — | |
| 5 | Phase 5: documentation and full validation | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261104-143443_sessmoke001_atomic-session-smoke-test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 2026-11-04 23:08 JST
- **Related target files**: scripts/db/session_consistency.py, scripts/db/models.py, scripts/db/recovery_verification.py, tests/db/test_session_consistency.py, tests/db/test_db_recovery.py, docs/41_db/db_07_api_and_operations-recovery-and-reference.md

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.
