## Goal
- Make the recovery drill prove that a production-equivalent restored copy is
  logically usable, and report `backup_duration_seconds`, RPO, and RTO as three
  distinct, correctly defined measurements instead of one mislabeled archive
  duration.

## Priority
Medium

## Scope
- **In-Scope**: full RAG consistency verification and read-only session
  consistency verification against the drill's isolated copies, production-
  equivalent plus negative fixtures, the artifact metric rename and precise
  timestamp events, and the runbook metric table update.
- **Out-of-Scope**: changing the consistency checks themselves (`ragverify001`,
  `sessmoke001`) and the recovery path itself (`sqliterec001`); setting RPO/RTO
  objectives (measurement definitions only, per the issue instruction).
- **Dependencies**: this Plan consumes the contracts produced by the two
  preceding Plans.
  - **Depends on**: plans/20261104-230307_ragverify001_complete-fail-closed-rag-consistency.md | phase all | the drill reuses `check_rag_consistency` and must interpret its fail-closed verification status; shared row `tests/db/test_recovery_drill.py`
  - **Depends on**: plans/20261104-230832_sessmoke001_atomic-session-smoke-test.md | phase all | the session verification the drill runs on an isolated copy must be read-only after that Plan's removal

## Background
Adversarial verification confirmed the issue's claims against current source:
- `_verify_rag_session` (`scripts/db/recovery_drill.py` L91-L98) runs only
  `run_integrity_check` and `verify_domain_identity`; no RAG or session
  consistency check is invoked, so FTS, vector, chunk, message, and memory
  relationships are never exercised by a drill.
- `_drill_one_domain` (L155, L185, L193, L211-L214) computes
  `rpo_window = time.time() - drill_start` around the archive step and stores it
  as `rpo_window_seconds` — an elapsed archive duration — while `rto_seconds` is
  measured from a separate `started` timestamp.
- The runbook table (`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
  L177-L178) documents `rpo_window_seconds` as "Gap between `drill_ts` and the
  archive timestamp", which is not what the code measures: the documented
  definition and the implemented measurement already disagree.
- Drill fixtures are minimal DDL constants inside
  `tests/db/test_recovery_drill.py` (L33-L66): `documents`, `sessions`, and the
  workflow/ledger tables only — no FTS, no `chunks_vec`.

## Problem
A logically damaged archive passes the drill whenever `PRAGMA integrity_check`
passes, and the `rpo_window_seconds` field overstates recoverability because it
reports how long archiving took rather than how stale the recovery point is.

## Reason for Change
Recoverability evidence is currently misleading: the drill is the mechanism that
is supposed to prove backups are usable, and its headline metric measures the
wrong thing.

## Implementation Intent
Extend the drill's per-domain verification to the real consistency verifiers
against the isolated copy, build production-equivalent and negative fixtures
from the schema SSOT, and replace the single mislabeled metric with three
explicitly defined measurements backed by recorded event timestamps.

## Requirements
- `REQ-001`: The drill runs full RAG consistency verification on the restored
  rag copy and read-only session consistency verification on the restored
  session copy.
- `REQ-002`: Fixtures carry canonical FTS and vector structures, and negative
  fixtures cover missing FTS rows, missing vectors, orphaned messages, and
  orphaned memories.
- `REQ-003`: The archive elapsed measurement is renamed to
  `backup_duration_seconds`.
- `REQ-004`: RPO is defined as the recovery-point age at the assumed failure
  time, and RTO has exact start and completion events.
- `REQ-005`: Live databases are unchanged in both success and failure paths, and
  a test proves it.
- `REQ-006`: The drill artifact documents the metric definitions and the field
  rename.

## Implementation Target Files
**Freeze status**: Frozen (`issue-to-plan` Step 8 validation passed: every row
exists, requires modification, has repository evidence, and is linked to a Plan
requirement. Overlap with `plans/20261104-230307_ragverify001_complete-fail-closed-rag-consistency.md`
and `plans/20261104-231726_sqliterec001_atomic-fail-closed-sqlite-recovery.md`
on `tests/db/test_recovery_drill.py` and with `plans/20261104-230832_sessmoke001_atomic-session-smoke-test.md`
on `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` is recorded
in Assumptions as a sequencing dependency, not a contradiction.)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/recovery_drill.py | Refactor: consistency verification on isolated copies; metric definitions and artifact event timestamps | `_verify_rag_session` runs only integrity plus identity (L91-L98); `rpo_window_seconds` stores archive elapsed time (L185, L214); only `started`/`drill_start` exist as timing anchors (L155, L193, L211) | REQ-001, REQ-003, REQ-004 / AC-001, AC-003, AC-004 | `scripts/db/recovery_drill.py` L91-L98, L155-L233 | tests/db/test_recovery_drill.py | Verified |
| tests/db/test_recovery_drill.py | Test: production-equivalent and negative fixtures, timestamp-relationship assertions, live-database checksum | fixtures are minimal DDL without FTS or vec (L33-L66); assertions check only `> 0` / `>= 0` (L227-L228); required-key list names `rpo_window_seconds` (L73-L74) | REQ-002, REQ-004, REQ-005 / AC-002, AC-004, AC-005 | `tests/db/test_recovery_drill.py` L33-L66, L73-L74, L227-L228 | tests/db/test_recovery_drill.py | Verified |
| tests/db/test_rag_consistency.py | Test: expose the canonical RAG fixture builders the drill tests reuse for FTS/vector structures | this file already builds canonical RAG fixtures for consistency tests and is the issue's named fixture source | REQ-002 / AC-002 | `tests/db/test_rag_consistency.py` (canonical RAG fixtures, churn 3 commits/30d) | tests/db/test_recovery_drill.py | Verified |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Docs: metric definitions table with the renamed field | L177-L178 documents `rpo_window_seconds` with a definition the code does not implement | REQ-004, REQ-006 / AC-004, AC-006 | `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` L177-L178 | N/A: docs | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/schema_sql.py | DDL SSOT for production-equivalent rag/session fixtures including FTS and `chunks_vec` | tests/db/test_recovery_drill.py, REQ-002 |
| scripts/db/rag_consistency.py | `check_rag_consistency` entry the drill calls on the isolated copy (post-`ragverify001` contract) | scripts/db/recovery_drill.py, REQ-001 |
| scripts/db/session_consistency.py | `check_session_consistency` entry the drill calls; must already be read-only by then | scripts/db/recovery_drill.py, REQ-001 |
| scripts/db/recovery.py | `run_integrity_check`, `verify_domain_identity`, `DbCondition` already imported by the drill (L34) | scripts/db/recovery_drill.py, REQ-001 |
| rules/env.md | `sqlite-vec` extension path and the 1024-dim/4096-byte embedding contract | tests/db/test_recovery_drill.py, REQ-002 |

## Acceptance Criteria
- `AC-001` (REQ-001): the drill's verification dict for `rag` and `session`
  contains consistency-verification results, not only integrity and identity.
- `AC-002` (REQ-002): an archive damaged in a logically valid-but-inconsistent
  way (FTS gap, missing vec rows, orphaned messages, orphaned memory links)
  fails the drill while `PRAGMA integrity_check` still reports ok.
- `AC-003` (REQ-003): the artifact contains `backup_duration_seconds` and no
  longer contains `rpo_window_seconds`.
- `AC-004` (REQ-004): the artifact records the event timestamps
  (`drill_start_ts`, `archive_ts`, `restore_start_ts`, `restore_end_ts` or the
  decided equivalents) so that `rpo_seconds` and `rto_seconds` are derived from
  named events, and tests assert their ordering relationships.
- `AC-005` (REQ-005): a checksum of each live database file is identical before
  and after a drill, in both the passing and the failing fixture cases.
- `AC-006` (REQ-006): the runbook table defines `backup_duration_seconds`, RPO,
  and RTO separately and states the rename.

## Tests
- `REQ-002`, `REQ-001`: negative-fixture tests (one per damage class) written
  before the production change, asserting the drill reports failure.
- `REQ-001`: healthy production-equivalent fixture (canonical FTS and vec
  structures from `scripts/db/schema_sql.py`) passes; where `sqlite-vec` is
  unavailable the drill reports the verification as unavailable rather than
  passed (UNK-02 decides the mechanism).
- `REQ-004`: tests assert `restore_start_ts >= archive_ts`,
  `rto_seconds == restore_end_ts - restore_start_ts` within tolerance, and
  `rpo_seconds == assumed_failure_ts - archive_ts`, replacing the current
  `> 0` / `>= 0` assertions.
- `REQ-005`: live-database checksum test in both success and failure cases.
- Regression: the existing drill artifact keys and ledger assertions stay green
  except where the rename applies.

## Documentation Impact
- Yes. The recovery-and-reference doc under `docs/41_db/` (recovery-and-reference
  task row of `docs/00_index.md`) carries the drill artifact table and must
  state the three metric definitions and the field rename, driven by `REQ-004`
  and `REQ-006`. It is the only drill-documenting file found in `docs/` (a grep
  for the drill outside `db_07` returned nothing).

## Assumptions
- The drill keeps its current isolation model (copy into `tmp_path`-style
  isolated files; live databases are never opened for write) and only gains
  verification depth.
- UNK-01 is resolved (downgraded from `Blocking? = True` during adversarial
  verification): a repo-wide scan shows every `rpo_window_seconds` reference
  resolves to this Plan's own target rows (`scripts/db/recovery_drill.py`,
  `tests/db/test_recovery_drill.py`, the `db_07` runbook table), so the rename to
  `backup_duration_seconds` is self-contained within this release unit and needs
  no external operations confirmation. No compatibility alias is added unless
  operations require one after this change ships.
- Overlap judgment: `tests/db/test_recovery_drill.py` is shared with
  `ragverify001` (Phase 4 drill-consumption tests) and `sqliterec001` (Phase 4
  drill action-value tests); `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
  is shared with `sessmoke001` and `sqliterec001`. This Plan is sequenced after
  all three, and each row is re-verified against the post-predecessor file state
  before editing. The edits touch different artifact fields and different test
  groups, so the designs do not contradict each other.
- RPO/RTO remain measurements, never thresholds; no objective values are
  invented.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Do external consumers (dashboards, cron wrappers, stored artifacts) read `rpo_window_seconds`? | repo-wide scan resolves every in-repo reference to this Plan's own target rows: `scripts/db/recovery_drill.py` (producer), `tests/db/test_recovery_drill.py` (L74, L228), and the `db_07` runbook table (L178); no dashboard, cron wrapper, or external artifact reader outside the repository references it | confirmed by repo-wide grep — all consumers are target rows of this Plan, so the rename is self-contained within this release unit; no external confirmation is required to land it | False |
| UNK-02 | Is `sqlite-vec` loadable in the test/CI environment, and through which helper? | `rules/env.md` documents the production extension path only | confirm in the first Phase 1 test run; add an explicit skip/unavailable state in the artifact rather than a silent pass | False |
| UNK-03 | What are the production RPO and RTO objectives? | none recorded anywhere in the repository | operations decision; out of scope for this Plan (measurements only), carried to the drill metrics documentation | False |
| UNK-04 | Which anonymized production-equivalent fixture set is acceptable as the canonical drill fixture? | no anonymized fixture set exists; `scripts/db/schema_sql.py` is the DDL SSOT | derive from `schema_sql.py` and confirm the derived set during Phase 1 fixture authoring | False |
| UNK-05 | Which timestamp is the "assumed failure time" for RPO — drill start, or a configurable failure timestamp supplied to the drill? | the issue defines RPO as recovery-point age at the assumed failure time without fixing that event | decide in Phase 2; plan default is the recorded `drill_start_ts`, documented explicitly in the runbook | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/recovery_drill.py | Refactor | medium (drill artifact contract; audit output consumed by operators) | 2 commits | 1 | N/A: no deployment file change |
| tests/db/test_recovery_drill.py | Test | low | 2 commits | 1 | N/A: tests only |
| tests/db/test_rag_consistency.py | Test | low | 3 commits | 1 | N/A: tests only |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Docs | low | N/A | 1 | N/A: docs only |

## Design
Grounded in Step 3/5 analysis:

- Verification extension: `_verify_rag_session` gains a consistency stage beside
  integrity and identity — `check_rag_consistency(db)` for `rag` and
  `check_session_consistency(db)` for `session`, each opened with
  `SQLiteHelper(domain, db_path=str(isolated))` exactly as `_verify_workflow`
  and `_verify_eventbus` already do (L103, L121). Verification keys are additive
  in the artifact dict, so existing consumers of `integrity` and
  `required_table_*` keep working. The pass/fail decision uses the post-`ragverify001`
  verification status, so an unverified dimension cannot count as a pass, and
  `artifact["integrity"]`-style aggregation is extended to a
  `verification_ok`-style aggregation instead of silently widening `integrity`.
- Metric definitions: three measurements with named events —
  `backup_duration_seconds` = archive end minus archive start (the value today
  mislabeled as `rpo_window_seconds`); `rpo_seconds` = assumed-failure timestamp
  minus archive completion (staleness of the recovery point, UNK-05 fixes the
  failure event); `rto_seconds` = restore-and-verify completion minus restore
  start (unchanged semantics, now anchored to recorded `restore_start_ts` /
  `restore_end_ts` instead of an unrecorded local variable). Each value is
  derived from timestamps that are themselves written into the artifact, so a
  test can recompute them.
- Fixtures: canonical rag fixtures (documents, chunks, chunks_fts, chunks_vec)
  and session fixtures (sessions, messages, memories, memories_fts,
  memory_links, session_diagnostics) derived from `scripts/db/schema_sql.py`.
  Damage fixtures: delete an FTS row (FTS gap), delete a vec row (missing
  vectors), delete a parent message (orphaned messages), delete a memory
  (orphaned memory links). Each damage case asserts a failing drill against the
  same healthy baseline, proving the failure comes from the damage and not from
  the fixture.
- Consumer scan disposition: the `rpo_window_seconds` consumers found in-repo
  are `scripts/db/recovery_drill.py` (producer), `tests/db/test_recovery_drill.py`,
  and the `docs/41_db/db_07` artifact table — all target rows. No other
  in-repo consumer exists; external usage is UNK-01.
- Path classification signal: 4 target files across 1 module, 2 tests, and 1
  docs file, with a breaking artifact-field rename and a dependency on two other
  Plans' contracts — Path B.
- Baselines: `radon cc scripts/db/recovery_drill.py` average A (3.7); churn low
  (2 commits/30d on both drill files), bus factor 1. `docs/41_db/db_07` L178 is
  evidence that the mislabel has already propagated into documentation, so the
  docs row is not cosmetic.

## Implementation steps
1. **Phase 1: Fixture foundation**
   - [ ] Build production-equivalent rag/session fixtures from the DDL SSOT and
     expose the canonical RAG fixture builders for reuse (REQ-002;
     tests/db/test_recovery_drill.py, tests/db/test_rag_consistency.py)
   - [ ] Add the four damage fixtures as failing-expectation tests before any
     production change (REQ-002; tests/db/test_recovery_drill.py)
2. **Phase 2: Consistency verification in the drill**
   - [ ] Run `check_rag_consistency` on the isolated rag copy and
     `check_session_consistency` on the isolated session copy, and aggregate the
     result into the artifact's verification state (REQ-001; scripts/db/recovery_drill.py)
   - [ ] Fix the assumed-failure timestamp definition for RPO (REQ-004;
     scripts/db/recovery_drill.py)
3. **Phase 3: Metric rename and event timestamps**
   - [ ] Rename `rpo_window_seconds` to `backup_duration_seconds`, add the
     event timestamps, and derive `rpo_seconds` and `rto_seconds` from them
     (REQ-003, REQ-004; scripts/db/recovery_drill.py)
   - [ ] Update the artifact key list, assertions, and timestamp-relationship
     tests, plus the live-database checksum test (REQ-004, REQ-005;
     tests/db/test_recovery_drill.py)
4. **Phase 4: Documentation and full validation**
   - [ ] Update the drill metric table with the three definitions and the rename
     (REQ-006; docs/41_db/db_07_api_and_operations-recovery-and-reference.md)
   - [ ] Deployment validation check: no new files, configs, or service changes;
     `deploy.sh` copies the `scripts/` tree as-is — verify with `bash -n deploy.sh`
     and a deployed-file spot check on `recovery_drill.py` (REQ-006)

### Release units
**Unit**: drill metric rename and assertions | **Phases**: 3 | **Reason**: the artifact field rename in `scripts/db/recovery_drill.py` and the required-key/assertion updates in `tests/db/test_recovery_drill.py` must land in the same change or the drill suite fails in both directions

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/recovery_drill.py | Integration: healthy and damaged production-equivalent copies | `uv run pytest tests/db/test_recovery_drill.py` | damaged copies fail with integrity passing; healthy copy passes |
| scripts/db/recovery_drill.py | Metric derivation: recompute from recorded timestamps | `uv run pytest tests/db/test_recovery_drill.py -k "rpo or rto or duration"` | relationships hold; `rpo_window_seconds` absent |
| tests/db/test_rag_consistency.py | Regression on the reused fixture builders | `uv run pytest tests/db/test_rag_consistency.py` | existing consistency tests stay green |
| live-database isolation | Integration: checksum before/after on success and failure | `uv run pytest tests/db/test_recovery_drill.py -k "live or checksum"` | live database bytes unchanged |
| whole repo | Full suite + coverage gate | `uv run pytest --cov --cov-report=xml` then `uv run diff-cover coverage.xml --fail-under=90` | all tests pass; changed-line coverage >= 90% |
| import contract | Static | `uv run lint-imports` | 0 broken contracts |
| static gates | Static | `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy scripts/`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run vulture scripts/ tests/ --min-confidence 80` | clean |

## Risks
- **Risk**: the artifact rename breaks external consumers → **Mitigation**: UNK-01
  confirmation before Phase 3; keep the rename inside one release unit with the
  test and doc updates.
- **Risk**: deeper verification makes drills slower and flakier (vec extension,
  larger fixtures) → **Mitigation**: fixtures stay schema-realistic but small;
  record an explicit unavailable state instead of failing when `sqlite-vec`
  cannot load.
- **Risk**: a damage fixture fails for the wrong reason and the test proves
  nothing → **Mitigation**: every damage test asserts against the same healthy
  baseline in the same run.
- **Risk**: shared rows with three other Plans on the drill test file and the
  recovery-and-reference doc → **Mitigation**: this Plan is sequenced last of the
  four and re-verifies each row against the post-predecessor state.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: fixture foundation | Completed | 20261105-182000 | 20261105-182000 | STEP: proc 03 (test_rag_consistency.py) archived; canonical RAG fixtures regression-guarded green (65 passed); no fixture change needed (adversarial finding: drill uses schema_sql.py directly, so builder-expose / rag_production_schema would be unused API) |
| 2 | Phase 2: consistency verification in the drill | Completed | 20261105-215555 | 20261105-215555 | STEP: proc 01 (recovery_drill.py) archived |
| 3 | Phase 3: metric rename and event timestamps | Completed | 20261105-215555 | 20261105-215555 | STEP: proc 01 + proc 02 (release unit) archived |
| 4 | Phase 4: documentation and full validation | Completed | 20261105-182000 | 20261105-182000 | STEP: proc 04 (db_07 runbook) archived; docs quality/structure/content-policy/japanese/consistency checkers pass; full suite 11647 passed, 11 skipped, 0 failed |

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
- **Source issue**: issues/20261104-143443_drillmetrics001_strengthen-recovery-drills-and-rpo-rto.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 2026-11-04 23:21 JST
- **Related target files**: scripts/db/recovery_drill.py, tests/db/test_recovery_drill.py, tests/db/test_rag_consistency.py, docs/41_db/db_07_api_and_operations-recovery-and-reference.md

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261105-174750 -->