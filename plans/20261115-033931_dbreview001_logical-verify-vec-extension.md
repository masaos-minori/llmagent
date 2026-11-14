# Plan: Restore verification opens the candidate with the target's extension configuration

## Goal
- Close the residual test gap for the vec0-requiring candidate restore: Issue 001's production fixes were merged upstream mid-batch; the acceptance scenario now needs a regression test.

## Priority
High (Issue Priority; residual scope only)

## Scope
- **In-Scope**: one integration test in `tests/db/test_db_recovery.py` restoring a real staged rag candidate that requires vec0, with the real logical verification.
- **Out-of-Scope**: production changes already merged upstream (`4543c2aa4`); quarantine semantics (`issues/20261114-092850_dbreview003_restore-sidecar-handling.md`).
- **Dependencies**: none.

## Plan-Document Correction

- A `git pull` fast-forward at 2026-11-15 02:59 +0900 (reflog `HEAD@{0}` → `edc79f698`) brought commit `4543c2aa4 feat(db): stage full sidecar filenames and verify candidates before activation` into the tree while this batch was in progress. That commit implements the Issue's Required Changes 1, 2, and 4:
  - `_run_logical_verification(db_path, target)` opens the candidate with an explicit `db_path` (`scripts/db/recovery_verification.py:124-145`); the no-argument `build_db_config()` call and the `run_logical_verification(helper)` entry point no longer exist.
  - The candidate is staged with its full sidecar set and verified before activation (`scripts/db/recovery.py:268-281`, `366-402`); logical-verification gaps map to `action="verification_unavailable"` (`recovery.py:387-402`), tested at `tests/db/test_db_recovery.py:1314-1345`.
  - The drill's bypass fixture (`_run_with_vec_extension` in `tests/db/test_recovery_drill.py`) was removed upstream; Required Change 3's "replace the drill fixture" half is void.
- This plan is therefore corrected from a 3-target production fix to a test-only residual plan. The original target rows are retired with evidence in the Requirement Traceability table.

## Background
From the Source Issue (F-001) and Step 2 re-verification after the pull: every restore-flow test patches `db.recovery._run_logical_verification` (e.g. `tests/db/test_db_recovery.py:837-895`, `1024-1061`); no test exercises a candidate whose consistency checks need the `vec0` shadow table end to end. Issue AC-1 is currently guaranteed only by construction.

## Problem
Residual: the exact failure mode the Issue describes (vec0-requiring candidate unverifiable at restore time) has no passing end-to-end regression test after the upstream fix.

## Reason for Change
A fix for a data-integrity bug reported by an adversarial review should be locked by the test the Issue asked for; otherwise the same regression can silently reappear.

## Implementation Intent
Add one test that builds a real rag candidate DB with a populated `vec0` virtual table (created through the Helper connection so the extension loads the same way the fixed code does), runs `_restore_from_backup` without patching `_run_logical_verification`, and asserts `action == "restored"`.

## Requirements
- `REQ-001`: A regression test exercises a vec0-requiring staged candidate restore end to end and asserts success (`action == "restored"`, `active_db_state="restored"`).

## Implementation Target Files
**Freeze status**: Frozen (corrected rows validated in Step 8b re-run: row exists, requires modification, evidence recorded this cycle, links to a Requirement).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tests/db/test_db_recovery.py | Modify | Add the vec0-requiring candidate e2e restore test; all existing restore tests patch `_run_logical_verification` | REQ-001 / AC-1 | grep over `tests/db/test_db_recovery.py`: `patch("db.recovery._run_logical_verification")` in every `action == "restored"` test (lines 82, 824, 884, 1056, 1457 contexts; checked in Step 2 re-verification) | tests/db/test_db_recovery.py | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/recovery.py | `_restore_from_backup` staging/verification flow the test must not patch | tests/db/test_db_recovery.py / REQ-001 |
| scripts/db/recovery_verification.py | `_run_logical_verification(db_path, target)` is the real stage under test | tests/db/test_db_recovery.py / REQ-001 |
| scripts/db/helper.py | `SQLiteHelper("rag", db_path=...)` loads vec0 from config — used to build the candidate | tests/db/test_db_recovery.py / REQ-001 |

## Acceptance Criteria
- AC-1 (`REQ-001`): the new test passes and exercises a candidate whose consistency checks need the vec shadow table.
- AC-2: `uv run pytest tests/db` stays green.

## Tests
- `REQ-001`: new integration test in `tests/db/test_db_recovery.py`: create the candidate via `SQLiteHelper("rag", db_path=...)` with `CREATE VIRTUAL TABLE ... USING vec0(...)` and a row; corrupt live DB; `_restore_from_backup` with `_run_integrity_check` sequence patched only for the corrupt/healthy transitions; assert `action == "restored"` (AC-1).

## Documentation Impact
None. The `verification_unavailable` vocabulary is already documented upstream.

## Baseline Consistency (Step 5)
| Dimension | Baseline Value | Source (exact command) | Recorded |
|---|---|---|---|
| radon CC target 1 | test-file top B(12); change is test-only | `uv run radon cc tests/db/test_db_recovery.py -s` (run this cycle) | 2026-11-15 |
| vulture target 1 | No `scripts/db` findings repo-wide | `uv run vulture scripts/ --min-confidence 80` (run this cycle) | 2026-11-15 |
| bandit target 1 | 45 low / 0 medium / 0 high | `uv run bandit -r scripts/ -c pyproject.toml` (run this cycle) | 2026-11-15 |
| coverage target 1 | project total 95%; tree clean at recording (no diff lines) | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (run this cycle) | 2026-11-15 |

## Assumptions
- sqlite-vec loads in the test environment (existing rag consistency tests depend on it; checked in Step 3).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | None | — | — | — |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tests/db/test_db_recovery.py | Modify | Low (test-only) | 0 | High (single author, >70%) | not applicable (rsynced) |

## Cross-Plan Target Overlap Scan

- Re-run after correction (`tools/check_plan_target_overlaps.py`, 2026-11-15): `tests/db/test_db_recovery.py` shared with `plans/20261115-035004_dbreview002_partial-activation-rollback.md`. Judgment: **compatible** — this plan adds one success-path e2e test; Plan 002 edits the rollback-failure test at 996-1021 and adds fault injections. Disjoint test functions.

## Design
- Reuse the fixture pattern of `test_wal_shm_sidecars_land_at_final_locations_after_activation` (`tests/db/test_db_recovery.py:1024-1061`) but leave `db.recovery._run_logical_verification` unpatched; the candidate is built through `SQLiteHelper` so vec0 loads via the helper, matching the fixed production path. If the environment cannot load the extension, the test must fail loudly, not skip silently.

## Implementation steps
1. **Phase 1: Residual regression test** (REQ-001; `tests/db/test_db_recovery.py`)
   - [ ] Add the vec0-requiring candidate e2e restore test (REQ-001)
   - [ ] Run `uv run pytest tests/db` and the full suite `-n auto` (AC-2)

### Release units
**Unit**: vec-candidate-test | **Phases**: 1 | **Reason**: test-only; independent of every other plan in this batch.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/db/test_db_recovery.py | Integration e2e restore with a real vec0 candidate | `uv run pytest tests/db/test_db_recovery.py -v` | New test passes; AC-1 scenario asserted |
| tests/db (regression) | Existing suite | `uv run pytest tests/db -v` | No regressions |

## Risks
- **Risk**: sqlite-vec .so unavailable on some test host → **Mitigation**: existing consistency tests already require it; a missing extension must fail the test explicitly.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Residual regression test (tests/db/test_db_recovery.py) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow type**: B (issue-to-plan)
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261114-092848_dbreview001_logical-verify-vec-extension.md (archived to issues/done/)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-033931 (corrected 2026-11-15 after the upstream pull)
- **Related target files**: tests/db/test_db_recovery.py

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target File | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Testing Expectations (vec0-requiring candidate success; residual after upstream fix) | tests/db/test_db_recovery.py | Phase 1 | AC-1 | New e2e test | Pending |

### Retired Requirements (upstream resolution, `4543c2aa4`)
| Original REQ | Original target | Resolution evidence |
|---|---|---|
| Thread config/candidate path through logical verification | scripts/db/recovery_verification.py, scripts/db/recovery.py | `recovery_verification.py:124-145` explicit `db_path`; `recovery.py:268-281`, `366-402` staged candidate verification |
| Replace the drill bypass fixture | tests/db/test_recovery_drill.py | Fixture removed upstream (`_run_with_vec_extension` no longer exists in repo) |
| Map unverifiable candidate to `verification_unavailable` | scripts/db/recovery.py | `recovery.py:387-402`; tests at `tests/db/test_db_recovery.py:1314-1345` |
| Add verification tests | tests/db/test_db_recovery.py | Partially merged upstream; the vec0-requiring success scenario remains — carried as REQ-001 |
