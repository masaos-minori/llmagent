## Goal
- Make SQLite corruption recovery one atomic, fail-closed protocol: the database
  file and its `-wal`/`-shm` sidecars are handled as one unit, every mandatory
  verification completes on an isolated candidate before activation, failures
  roll back or report an explicit non-serviceable state, and `RecoveryResult`
  describes the state that is actually active.

## Priority
High

## Scope
- **In-Scope**: sidecar path resolution and fail-closed sidecar handling in
  `scripts/db/recovery_restore.py`, candidate-then-activate ordering and rollback
  in `scripts/db/recovery.py`, fail-closed logical verification in
  `scripts/db/recovery_verification.py`, the `RecoveryResult` state contract in
  `scripts/db/models.py`, recovery/drill test updates, and the operations
  documentation update.
- **Out-of-Scope**: backup creation, rotation, and retention; migration safety
  (`dbmigsafe001`); changes to the consistency checks themselves (`ragverify001`,
  `sessmoke001`); automatic recovery for `workflow`/`eventbus` (prohibited by
  ADR-008 and unchanged here).
- **Dependencies**: shared target files with the two already-frozen Plans.
  - **Depends on**: plans/20261104-230307_ragverify001_complete-fail-closed-rag-consistency.md | phase all | shared rows in `scripts/db/models.py` and `scripts/db/recovery_verification.py`, and the logical verifier consumes the RAG consistency report that Plan redefines
  - **Depends on**: plans/20261104-230832_sessmoke001_atomic-session-smoke-test.md | phase all | shared rows in `scripts/db/models.py`, `scripts/db/recovery_verification.py`, and `tests/db/test_db_recovery.py`; the session logical verifier must stay read-only after that Plan's removal

## Background
Adversarial verification confirmed all five claims of the issue against current
source, and located the two areas the issue left unknown:
- `scripts/db/recovery_restore.py` builds sidecar names from `Path.stem`
  (`_quarantine_sidecar_files` L24-L27, `_stage_backup_sidecars` L45-L48, and
  `_stage_restore` step 4a L104): for the production `rag.sqlite` (confirmed by
  `rules/env.md` L71 and the live `/opt/llm/db` layout `rag.sqlite-wal` /
  `rag.sqlite-shm`) the computed names are `rag-wal` / `rag-shm`, so real
  sidecars are never quarantined, never staged, and never moved.
- Quarantine failure (L34-L38) and staged-sidecar move failure (L110-L114) log
  warnings and continue ("proceeding without it").
- `_restore_from_backup` (`scripts/db/recovery.py` L252-L287) activates through
  `os.replace` inside `_stage_restore` (L100) before `_post_restore_failure`
  (L225-L249) runs the integrity re-check and logical verification; a failed
  verification returns a failure result while the unverified file stays active
  and the corrupt original only exists as an archive.
- `_run_logical_verification` (`scripts/db/recovery_verification.py` L111-L129)
  returns `(True, None)` for an unknown target and for `sqlite3.Error`.
- `RecoveryResult.logical_ok` (`scripts/db/models.py` L163) is set only on the
  failure path; the success result (L279-L281) leaves it `None`, so
  `scripts/agent/commands/db_session_ops.py` L80-L84 prints neither a pass nor
  a fail line after a successful restore.
- Recovery CLI entry point located: `/session recover` in
  `scripts/agent/commands/cmd_session.py` L233 ->
  `scripts/agent/commands/db_session_ops.py` `recover()` ->
  `scripts/agent/services/db_maintenance_service.py` `recover_session()` ->
  `db.recovery.recover_corruption()`. There is no process exit-code mapping on
  this path today; no standalone recovery script exists.

## Problem
1. A database can be activated next to stale real sidecars because the code
   looks for names that never exist.
2. Sidecar operation failures are downgraded to warnings and recovery proceeds.
3. Verification runs after activation, and a verification that cannot run is
   reported as success.
4. A failed post-activation verification leaves the unverified database active
   with no rollback, and the result contract misreports the active state to the
   CLI and operators.

## Reason for Change
These defects combine into one atomicity problem on the path that runs exactly
when the database is already damaged. Cosmetic independent fixes would leave the
result semantics inconsistent.

## Implementation Intent
One protocol: stage a complete candidate (database plus sidecars) in a temporary
location, run every mandatory verification on the candidate, activate only a
fully verified file set with a single atomic swap, and on failure either restore
the archived original or report an explicit non-serviceable state. The result
describes the active state, and mandatory verification that cannot run is a
failure.

## Requirements
- `REQ-001`: Resolve target and backup sidecar paths from the full database
  filename (`rag.sqlite-wal`, not `rag-wal`).
- `REQ-002`: Quarantine, copy, rename, and placement failures of WAL/SHM files
  are fatal recovery errors, not warnings.
- `REQ-003`: Physical and logical verification run on the staged candidate
  before activation; an unverified candidate is never activated.
- `REQ-004`: A failure after activation restores the archived original or
  reports an explicit non-serviceable state; a failed rollback is itself
  reported.
- `REQ-005`: `sqlite3.Error` in mandatory logical verification, and an unknown
  target in mandatory verification, return an explicit failure (for example
  `verification_unavailable`) instead of success.
- `REQ-006`: `RecoveryResult` reports `logical_ok` consistently and exposes the
  final active-database state.
- `REQ-007`: Tests cover each fail-closed branch, WAL-mode integration, and
  fault injection, including rollback failure.

## Implementation Target Files
**Freeze status**: Frozen (`issue-to-plan` Step 8 validation passed: every row
exists, requires modification, has repository evidence, and is linked to a Plan
requirement. Overlaps with `plans/20261104-230307_ragverify001_complete-fail-closed-rag-consistency.md`
and `plans/20261104-230832_sessmoke001_atomic-session-smoke-test.md` on
`scripts/db/models.py`, `scripts/db/recovery_verification.py`,
`tests/db/test_db_recovery.py`, and `tests/db/test_recovery_drill.py` are
recorded in Assumptions as sequencing dependencies, not contradictions.)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/recovery_restore.py | Refactor: full-filename sidecar resolution; fail-closed quarantine and sidecar staging | `Path.stem` sidecar naming (L24-L27, L45-L48, L104); quarantine/move failures logged as warnings and ignored (L34-L38, L110-L114) | REQ-001, REQ-002 / AC-001, AC-002 | `scripts/db/recovery_restore.py` L22-L53, L75-L114; production names `rag.sqlite-wal` per `rules/env.md` L71 | tests/db/test_db_recovery.py | Verified |
| scripts/db/recovery.py | Refactor: verify-the-candidate-then-activate ordering, rollback on activation or post-activation failure, consistent `logical_ok` population | `os.replace` activation inside `_stage_restore` (L100) precedes `_post_restore_failure` (L225-L249); success result omits `logical_ok` (L279-L281); `OSError` handler only unlinks the temp file (L283-L287) | REQ-003, REQ-004, REQ-006 / AC-003, AC-004, AC-006 | `scripts/db/recovery.py` L225-L287 | tests/db/test_db_recovery.py | Verified |
| scripts/db/recovery_verification.py | Refactor: mandatory logical verification fails closed | returns `(True, None)` for unknown target and for `sqlite3.Error` (L122-L129) | REQ-005 / AC-005 | `scripts/db/recovery_verification.py` L111-L129 | tests/db/test_db_recovery.py | Verified |
| scripts/db/models.py | Feature: `RecoveryResult` final active-state contract | `logical_ok: bool | None = None` (L163) with no field describing which database is active | REQ-006 / AC-006 | `scripts/db/models.py` L155-L163 | tests/db/test_db_recovery.py | Verified |
| tests/db/test_db_recovery.py | Test: sidecar naming, fail-closed branches, WAL integration, rollback fault injection | existing sidecar tests use a `test.db` file with `test-wal` fixtures (L655-L674), which encodes the wrong naming and masks the defect | REQ-007 / AC-007 | `tests/db/test_db_recovery.py` L370-L503, L643-L674, L1041-L1074 | tests/db/test_db_recovery.py | Verified |
| tests/db/test_recovery_drill.py | Test: drill covers the production-equivalent sidecar layout and the new failure actions | the drill runs `recover_corruption` end to end and currently asserts the old action set | REQ-007 / AC-007 | `tests/db/test_recovery_drill.py` | tests/db/test_recovery_drill.py | Verified |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Docs: restore protocol, result contract, and exclusive-access requirement | L34 documents the staging steps including "quarantine the stale `-wal`/`-shm` sidecars" as they are today | REQ-006, REQ-007 / AC-006 | `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` L34, L69 | N/A: docs | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/commands/cmd_session.py | locates the recovery entry point (`recover` subcommand, L233) and its lack of exit codes | scripts/db/recovery.py, REQ-005 |
| scripts/agent/commands/db_session_ops.py | consumes `result.logical_ok` (L80-L84) and renders the operator-visible outcome | scripts/db/models.py, REQ-006 |
| scripts/agent/services/db_maintenance_service.py | maps `RecoveryResult` to `DbRecoverResult` (L83-L88) | scripts/db/models.py, REQ-006 |
| scripts/agent/services/models.py | service-layer mirror of `logical_ok` (L220) | scripts/db/models.py, REQ-006 |
| scripts/db/rotation.py | imports `DbCondition`, `run_integrity_check`, `verify_domain_identity` from `db.recovery`; must stay import-compatible | scripts/db/recovery.py, REQ-004 |
| scripts/db/__init__.py | re-exports `recover_corruption` (L41, L93) | scripts/db/recovery.py, REQ-006 |
| docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | ADR-008 recovery policy that the new protocol must not contradict | scripts/db/recovery.py, REQ-004 |
| tests/agent/test_wal_backup_security.py | existing WAL-path characterization tests that must stay green | scripts/db/recovery_restore.py, REQ-007 |
| rules/env.md | four-database layout and production sidecar filenames | scripts/db/recovery_restore.py, REQ-001 |

## Acceptance Criteria
- `AC-001` (REQ-001): recovery resolves `rag.sqlite-wal` and `rag.sqlite-shm`;
  no code path computes `rag-wal` or `rag-shm` for that database.
- `AC-002` (REQ-002): no sidecar quarantine, copy, rename, or placement failure
  produces a successful recovery result.
- `AC-003` (REQ-003): a candidate that fails the physical or logical
  verification is never activated; the live database is untouched by the failed
  attempt.
- `AC-004` (REQ-004): a failure after activation either restores the archived
  original or reports an explicit non-serviceable state, and a failed rollback
  is reported as its own action value.
- `AC-005` (REQ-005): a `sqlite3.Error` during mandatory logical verification,
  and an unknown mandatory verification target, return failure
  (`verification_unavailable` or the decided equivalent action value) rather
  than success.
- `AC-006` (REQ-006): after every completed restore `RecoveryResult.logical_ok`
  is `True` or `False` (never `None`), and the result names the active database
  state.
- `AC-007` (REQ-007): negative tests exist for each fail-closed branch before
  the corresponding production branch is changed, and `rag`/`session` coverage
  plus `workflow`/`eventbus` refusal are both exercised.

## Tests
- `REQ-001`, `REQ-007`: sidecar tests using production-equivalent names
  (`rag.sqlite`, `rag.sqlite-wal`, `rag.sqlite-shm`) — replacing the current
  `test.db` / `test-wal` fixtures that mask the naming defect.
- `REQ-002`, `REQ-007`: fault injection for quarantine failure, copy failure,
  rename failure, and permission errors; each asserts a failed result.
- `REQ-003`, `REQ-007`: candidate verification tests proving the live database
  file is byte-identical when the candidate fails verification.
- `REQ-004`, `REQ-007`: rollback tests, including a rollback failure that must
  produce the explicit non-serviceable action.
- `REQ-005`, `REQ-007`: injected `sqlite3.Error` in the logical verifier returns
  the failure action; unknown mandatory target returns the failure action.
- `REQ-006`, `REQ-007`: success-path assertions that `logical_ok` is `True` and
  the active state is reported; existing `is not True` assertions (L370-L503)
  are tightened.
- Integration: WAL-mode databases with production-equivalent schemas via the
  existing fixture helpers; `workflow`/`eventbus` refusal tests stay green.

## Documentation Impact
- Yes. The recovery-and-reference doc under `docs/41_db/` (recovery-and-reference
  task row of `docs/00_index.md`) must document the candidate-then-activate
  protocol, the new action values, and the exclusive-access requirement, driven
  by `REQ-006` and `REQ-007`. ADR-008 itself is not modified: automatic recovery
  for `workflow`/`eventbus` remains prohibited; if the exit-code decision
  (UNK-02) adds a new contract, an ADR amendment note is raised as a follow-up
  work item instead of editing the frozen ADR here.

## Assumptions
- Recovery runs with no other writer on the target database during a restore;
  the exclusive-access mechanism itself is not implemented by this Plan
  (UNK-01) and the Plan documents the requirement instead.
- `RecoveryResult` changes stay additive: existing `success`, `action`,
  `detail`, `dry_run`, and `logical_ok` fields keep their meaning so
  `scripts/db/__init__.py`, `scripts/db/rotation.py`, and the service layer stay
  import-compatible.
- Dry-run behavior stays side-effect-free on live databases.
- Overlap judgment: the four shared rows with `ragverify001` and `sessmoke001`
  are sequenced (this Plan runs third). `models.py` edits touch different data
  classes (`RecoveryResult` vs the two consistency reports);
  `recovery_verification.py` edits touch `_run_logical_verification` while the
  other Plans touch `_verify_rag_logic` and `_session_inconsistency_detail`;
  test-file edits touch different test groups. Each row is re-verified against
  the post-predecessor file state before editing.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | What production service-stop or exclusive-lock mechanism guarantees exclusive file access before a restore? | no stop/lock helper found in `scripts/db/` or the service layer; `/session recover` runs while agent services may be live | operations decision; until resolved, the Plan documents the requirement and keeps ADR-008's operator-intervention posture | True |
| UNK-02 | What is the recovery exit-code contract? The located entry point is the `/session recover` REPL subcommand, which has no exit-code mapping. | no standalone recovery script or exit-code plumbing exists (`cmd_session.py` L233, `db_session_ops.py` `recover()`) | decide with operations: either a new standalone entry script with documented exit codes, or a documented REPL-result contract; the issue's "non-zero CLI exit code" criterion cannot be met by the current path | True |
| UNK-03 | What RTO/RPO objectives apply to recovery? | none recorded in `rules/env.md`, docs, or configs | operations decision; carried forward to `drillmetrics001` | False |
| UNK-04 | Should rollback restore the archived corrupt original, or keep the candidate beside a preserved original? | no operational preference recorded | design decision at Phase 2 with the rollback test written first | False |
| UNK-05 | Is WAL-mode fault injection (locked files, permission errors) reliable in the test environment? | no existing locked-file injection test found in `tests/db/` | prototype in Phase 4; fall back to injected `OSError` mocks if filesystem-level injection is unreliable | False |
| UNK-06 | Should the active database state be a new `RecoveryResult` field or be carried in `action` plus `detail`? | no repo convention recorded for this result type | decide in Phase 3, with the negative test written first; plan recommends one additive field for machine-readable state | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/recovery_restore.py | Refactor | medium (restore staging for both recoverable domains) | 2 commits | 1 | N/A: no deployment file change |
| scripts/db/recovery.py | Refactor | high (recovery entry point for rag/session; imported by rotation and services) | 6 commits | 1 | N/A: no deployment file change |
| scripts/db/recovery_verification.py | Refactor | medium (logical verification for both domains) | 1 commit | 1 | N/A: no deployment file change |
| scripts/db/models.py | Feature | medium (shared contract module) | 1 commit | 1 | N/A: no deployment file change |
| tests/db/test_db_recovery.py | Test | low | 8 commits | 1 | N/A: tests only |
| tests/db/test_recovery_drill.py | Test | low | 2 commits | 1 | N/A: tests only |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Docs | low | N/A | 1 | N/A: docs only |

## Design
Grounded in Step 3/5 analysis:

- One recovery unit: `recovery_restore.py` computes every sidecar path as
  `Path(str(db_path) + suffix)` and `Path(str(backup) + suffix)`. Quarantine,
  copy, and move failures raise instead of logging warnings; `_stage_restore`
  keeps its contract of raising filesystem failures to the caller's cleanup
  handler, and the caller no longer treats a missing sidecar as acceptable.
- Candidate before activation: staging already writes to `temp_restore` and only
  swaps with `os.replace` (L100). The reorder is to run the integrity re-check
  and the logical verification against the staged candidate path before
  `os.replace`, and to stage the candidate's sidecars beside the candidate in
  the temporary directory so the verified unit is the unit that is activated.
- Rollback semantics: the corrupt original is already archived (L92-L94), so a
  post-activation failure restores from that archive; if that restore fails the
  result reports an explicit non-serviceable action and preserves every artifact
  for the operator. Action-value naming and the `UNRESOLVED`-style posture stay
  consistent with the existing `preserved_operator_intervention_required` value.
- Fail-closed verification: `_run_logical_verification` returns `(False, detail)`
  for `sqlite3.Error` and for an unknown mandatory target; the docstring
  rationale ("a verification gap must never block a completed physical restore")
  is inverted by this Plan and must be rewritten, not just patched.
- Result contract: `logical_ok` is populated on every completed path, and one
  additive field names the active database state (`restored`,
  `preserved_original`, `non_serviceable`, or the decided equivalents).
  `scripts/agent/commands/db_session_ops.py` L80-L84 then prints a truthful line
  with no consumer change. Whether the state is a new field or is carried in
  `action` plus `detail` is tracked as UNK-04 alongside the rollback design.
- Consumer scan disposition: candidates from the located call chain
  (`cmd_session.py`, `db_session_ops.py`, `db_maintenance_service.py`,
  `scripts/agent/services/models.py`) and from `scripts/db/rotation.py` /
  `scripts/db/__init__.py` imports are recorded as reference rows: additive
  changes keep them unmodified. `tests/agent/test_wal_backup_security.py` is a
  reference row (path-traversal characterization, unaffected). ADR-008
  (`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`) is a reference row:
  the prohibited-domain policy is unchanged.
- Path classification signal: 7 target files across 3 modules, 2 tests, and 1
  docs file, with a public result-contract change and a high blast-radius entry
  point — Path B.
- Baselines: `radon cc` on the three target modules averages A (3.3);
  `_restore_from_backup` and `_stage_restore` are the structural hotspots
  addressed by this Plan. Churn: `recovery.py` 6 commits and
  `tests/db/test_db_recovery.py` 8 commits in 30 days (high churn), bus factor 1
  — the existing recovery tests must be read fully before editing, and
  `docs/10_adr/adr_02_05_008` documents the recovery-policy intent.
- Masked-defect evidence: `tests/db/test_db_recovery.py` L655-L674 creates
  `test.db` with sidecars named `test-wal`, matching the buggy `Path.stem`
  convention, so current tests pass against the wrong behavior. Fixing the
  naming without also fixing the fixtures would break them; the naming fix and
  the fixture fix are one release unit.

## Implementation steps
1. **Phase 1: Sidecar unit fix**
   - [ ] Resolve all sidecar paths from the full database filename and make
     quarantine/copy/move failures fatal (REQ-001, REQ-002; scripts/db/recovery_restore.py)
   - [ ] Replace the `test.db` / `test-wal` fixtures with
     production-equivalent names before changing the production branch (REQ-007;
     tests/db/test_db_recovery.py)
2. **Phase 2: Candidate verification and activation**
   - [ ] Run physical and logical verification against the staged candidate and
     activate only after both pass (REQ-003; scripts/db/recovery.py,
     scripts/db/recovery_verification.py)
   - [ ] Fail closed on `sqlite3.Error` and unknown mandatory targets (REQ-005;
     scripts/db/recovery_verification.py)
3. **Phase 3: Rollback and result contract**
   - [ ] Restore the archived original on post-activation failure, or report an
     explicit non-serviceable state when rollback fails (REQ-004; scripts/db/recovery.py)
   - [ ] Populate `logical_ok` on every completed path and expose the active
     database state (REQ-006; scripts/db/models.py, scripts/db/recovery.py)
4. **Phase 4: Fault-injection and drill coverage**
   - [ ] Add the fault-injection tests for every fail-closed branch (REQ-007;
     tests/db/test_db_recovery.py)
   - [ ] Extend the drill to the production-equivalent sidecar layout and the
     new action values (REQ-007; tests/db/test_recovery_drill.py)
5. **Phase 5: Documentation and full validation**
   - [ ] Document the protocol, action values, and the exclusive-access
     requirement (REQ-006, REQ-007;
     docs/41_db/db_07_api_and_operations-recovery-and-reference.md)
   - [ ] Deployment validation check: no new files or configs; `deploy.sh`
     copies the `scripts/` tree as-is — verify with `bash -n deploy.sh` and a
     deployed-file spot check on `recovery_restore.py`, `recovery.py`,
     `recovery_verification.py`, `models.py` (REQ-006)

### Release units
**Unit**: sidecar naming and fixtures | **Phases**: 1 | **Reason**: production naming fix and the fixture fix that currently encodes the wrong names must land together or the suite breaks in both directions
**Unit**: contract activation | **Phases**: 2, 3 | **Reason**: verification-before-activation, rollback, and the `RecoveryResult` fields describe one protocol; a partial landing leaves either an unverifiable activation or a result contract that describes a state the code cannot produce

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/recovery_restore.py | Unit: production-equivalent sidecar names + injected `OSError` per operation | `uv run pytest tests/db/test_db_recovery.py -k "sidecar or quarantine or stage"` | no sidecar failure yields a successful result; names match `rag.sqlite-wal` |
| scripts/db/recovery.py | Integration: candidate verification before `os.replace`, rollback paths | `uv run pytest tests/db/test_db_recovery.py -k "restore or rollback"` | unverified candidates are never activated; rollback restores the original |
| scripts/db/recovery_verification.py | Unit: injected `sqlite3.Error`, unknown target | `uv run pytest tests/db/test_db_recovery.py -k "logical"` | failure actions returned instead of `(True, None)` |
| scripts/db/models.py | Contract: additive active-state field, `logical_ok` populated | `uv run pytest tests/db/test_db_recovery.py` | success paths report `True` and the active state |
| recovery drill | Integration | `uv run pytest tests/db/test_recovery_drill.py` | drill exercises the new action set with real sidecar layout |
| import contract | Static | `uv run lint-imports` | 0 broken contracts |
| whole repo | Full suite + coverage gate | `uv run pytest --cov --cov-report=xml` then `uv run diff-cover coverage.xml --fail-under=90` | all tests pass; changed-line coverage >= 90% |
| static gates | Static | `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy scripts/`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run vulture scripts/ tests/ --min-confidence 80` | clean |

## Risks
- **Risk**: making sidecar handling fatal turns previously-successful restores
  into failures in production → **Mitigation**: the previous "success" was an
  unverified activation; sequence after UNK-01 is answered and document the
  behavior change in the runbook.
- **Risk**: rollback itself fails and leaves the database unserviceable →
  **Mitigation**: explicit non-serviceable action value, preserved artifacts, and
  an operator-intervention message consistent with the existing
  `preserved_operator_intervention_required` posture.
- **Risk**: verification against the candidate path diverges from verification
  against the activated path (path-dependent SQL or pragmas) → **Mitigation**:
  integration tests in WAL mode comparing candidate-path and post-activation
  results.
- **Risk**: shared-file conflicts with the `ragverify001` and `sessmoke001`
  Plans → **Mitigation**: strict sequencing and per-row re-verification before
  editing.
- **Risk**: high churn and bus factor 1 on `recovery.py` and its tests →
  **Mitigation**: read the existing 8-commit test suite and ADR-008 before the
  Phase 1 edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: sidecar unit fix | Pending | — | — | |
| 2 | Phase 2: candidate verification and activation | Pending | — | — | |
| 3 | Phase 3: rollback and result contract | Pending | — | — | |
| 4 | Phase 4: fault-injection and drill coverage | Pending | — | — | |
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
- **Source issue**: issues/20261104-143443_sqliterec001_atomic-fail-closed-sqlite-recovery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 2026-11-04 23:17 JST
- **Related target files**: scripts/db/recovery_restore.py, scripts/db/recovery.py, scripts/db/recovery_verification.py, scripts/db/models.py, tests/db/test_db_recovery.py, tests/db/test_recovery_drill.py, docs/41_db/db_07_api_and_operations-recovery-and-reference.md

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.
