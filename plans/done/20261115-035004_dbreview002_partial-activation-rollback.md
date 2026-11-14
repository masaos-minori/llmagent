## Goal
- Make any failure after the candidate swap begins trigger the same rollback and explicit state reporting as post-activation verification failures, so the live path never holds an unverified candidate silently.

## Priority
High

## Scope
- **In-Scope**: activation-state tracking inside `_activate_candidate`; rollback of a partially-completed activation (database file plus already-moved sidecars); explicit `active_db_state` on every activation-failure result; `_cleanup_staged` made non-raising; per-step fault-injection tests; documentation of the changed action/state mapping.
- **Out-of-Scope**: logical verification and the vec extension problem (`issues/20261114-092848_dbreview001_logical-verify-vec-extension.md`, already planned/frozen); sidecar quarantine semantics beyond what rollback needs (`issues/20261114-092850_dbreview003_restore-sidecar-handling.md`).
- **Dependencies**: Coordinate with `issues/20261114-092850_dbreview003_restore-sidecar-handling.md` (same functions).
  - **Depends on**: issues/20261114-092850_dbreview003_restore-sidecar-handling.md | phase all | reverse-direction coordination only: 003 edits `_restore_from_backup`/`_activate_candidate` and must be implemented after this Plan lands.

## Plan-Document Correction (re-verification after mid-batch pull)

- A `git pull` fast-forward at 2026-11-15 02:59 +0900 (reflog → `edc79f698`; recovery restructure commit `4543c2aa4`) landed mid-batch. All claims of this plan were re-verified against the post-pull tree and hold: `_activate_candidate` non-atomic (`recovery.py:284-295`), `activated` set post-call (`404-405`), guarded handler (`424-443`, check at 427, state-less `_failure` at 443), unguarded `_cleanup_staged` call at 426, `error`/`non_serviceable` in the handler's rollback-failure branch (`436-442`) while the helper already reports `rollback_failed` (`310-325`, tested at `tests/db/test_db_recovery.py:965-991`), and neither rollback path removes moved sidecars (`315`, `431`).
- Refined test target: exactly one existing test asserts the handler's rollback-failure vocabulary — `tests/db/test_db_recovery.py:996-1021`, assert at 1020. The other `action == "error"` assertions (108, 120, 132, 1432, 1477) belong to non-rollback paths and stay unchanged.

## Background
From the Source Issue (F-002, re-confirmed on second adversarial pass). In `_restore_from_backup` (`scripts/db/recovery.py:336-443`) the flag `activated = True` is assigned only after `_activate_candidate` returns (lines 404-405). `_activate_candidate` (lines 284-295) performs `os.replace(temp_restore, db_path)` then `shutil.move`s each staged sidecar; an `OSError` after the replace leaves the unverified candidate live while the `except OSError` handler (lines 424-443) skips its rollback branch (guarded by `activated`, line 427) and returns `_failure("error", str(e), dry_run)` with `active_db_state=None` (line 443). `_cleanup_staged` (lines 298-302, called unguarded at 374, 395, 426) can itself raise and escape the handler. Issue reproduction (workflow target, patched `_activate_candidate`): live DB contained the backup's table; result `action="error"`, `active_db_state=None`. Step 3 confirms existing tests (`tests/db/test_db_recovery.py:959-1015`) exercise only failures after `_activate_candidate` returned (post-activation re-check injection), never a failure inside it.

## Problem
The fail-closed restore contract (an unverified file must never be the live database; every result names the live state) is violated on the in-activation failure path: the candidate stays live and the caller receives a state-less `error`.

## Reason for Change
`recover_corruption` consumers (`scripts/agent/services/db_maintenance_service.py`, `scripts/agent/services/rag_maintenance_service.py`, both `from db.recovery import recover_corruption`, checked in Step 3) branch on `action`/`active_db_state` to decide operator follow-up; a state-less `error` on the most dangerous path defeats that. Post-pull re-verification: the drill no longer calls `_restore_from_backup` (grep of `scripts/db/recovery_drill.py` for `_restore_from_backup|recover_corruption` is empty; it runs its own isolated restore) — the drill is a docs/impact reader only, not an activation consumer.

## Implementation Intent
Track the swap at the moment it begins (inside `_activate_candidate`) rather than after the call returns, reuse the existing rollback helper so activation-failure paths report the same `rollback_failed`/`non_serviceable` and `preserved_original` vocabulary as verification-failure paths, remove sidecars the partial activation already moved, and make staged-file cleanup log-and-continue.

## Requirements
- `REQ-001`: `_activate_candidate` records swap-start before `os.replace` and records each sidecar move as it completes, so `_restore_from_backup`'s `except OSError` handler knows a partial activation happened (replaces the post-call `activated` flag).
- `REQ-002`: When a partial activation is rolled back, sidecars already moved to their live names are removed so the restored original never inherits candidate `-wal`/`-shm` files.
- `REQ-003`: Activation-failure results state the live DB explicitly: successful rollback → `active_db_state="preserved_original"`; rollback failure → `action="rollback_failed"` with `active_db_state="non_serviceable"` (replaces the handler's state-less `error`/`non_serviceable` reporting, `recovery.py:436-443`).
- `REQ-004`: `_cleanup_staged` tolerates and logs per-file `OSError` and never raises out of `_restore_from_backup` (all three call sites: lines 374, 395, 426).
- `REQ-005`: Fault-injection tests at each `_activate_candidate` step (after `os.replace`, after the first sidecar move) assert live-file content and reported state; `_cleanup_staged` failure no longer escapes.
- `REQ-006`: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` action/state mapping is updated to cover `rollback_failed` on in-activation failures (per the Issue's Documentation Impact condition — the set of reported outcomes changes: `active_db_state` is now always populated on the handler path and `rollback_failed` appears in a new situation).

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b: every row exists, requires modification, has supporting evidence recorded this cycle, and links to a Requirement).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/recovery.py | Modify | `_restore_from_backup` (flag + handler lines 364, 404-405, 424-443), `_activate_candidate` (284-295), `_cleanup_staged` (298-302), `_rollback_or_non_serviceable` (305-333, gains sidecar removal) | REQ-001..REQ-004 / AC-1, AC-2, AC-3 | `recovery.py:404-405` flag-after-call, `:427` guarded rollback, `:443` state-less failure (checked in Step 2) | tests/db/test_db_recovery.py | Verified |
| tests/db/test_db_recovery.py | Modify | No test injects failure inside `_activate_candidate`; existing handler tests assert `action == "error"` for rollback failure (`:996+`, assert at offset 1020: `result.action == "error"`) and must be updated to the new vocabulary | REQ-003, REQ-005 / AC-1, AC-2, AC-3 | grep of `tests/db/test_db_recovery.py` shows injection only at `_post_restore_failure`/`copy2` points (checked in Step 3) | tests/db/test_db_recovery.py | Verified |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Modify | Documents the recovery action/state contract (lines 65-66: pre/post-activation failure semantics, `active_db_state` enumeration); the changed action mapping must be reflected | REQ-006 / AC-4 | `scan_change_consumers.py --seed rollback_failed` returned this file as the direct docs consumer (checked in Step 3) | docs consistency checker `tools/check_docs_consistency.py --domain db` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/recovery_restore.py | `_stage_restore` defines what `staged` holds (candidate path + quarantined sidecar copies) and what a partial activation can have moved | scripts/db/recovery.py / REQ-001, REQ-002 |
| scripts/db/models.py | `RecoveryResult` field semantics (`action`, `active_db_state`) — fields unchanged | scripts/db/recovery.py / REQ-003 |
| scripts/agent/services/db_maintenance_service.py | Consumer branching on `action`/`active_db_state`; confirms no consumer depends on the state-less `error` shape | scripts/db/recovery.py / REQ-003 |
| scripts/agent/services/rag_maintenance_service.py | Same consumer check | scripts/db/recovery.py / REQ-003 |
| scripts/db/recovery_drill.py | Post-pull: no longer calls `_restore_from_backup`/`recover_corruption`; read only to confirm no drill coupling to the activation result shape | scripts/db/recovery.py / REQ-001 |
| docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | ADR-008 recovery matrix and test-citation table; checked, not modified: its state enumeration (`restored`/`preserved_original`/`non_serviceable`) stays accurate — Step 3 consumer scan found only the test-citation table, no exclusivity claim invalidated | scripts/db/recovery.py / REQ-006 |
| tests/db/test_db_maintenance.py | Imports `recover_corruption` and asserts action values; regression check target, no edit expected | scripts/db/recovery.py / REQ-003 |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-003`): A forced `OSError` after `os.replace` inside `_activate_candidate` restores the archived original and the result has `active_db_state="preserved_original"`.
- AC-2 (`REQ-003`): If that rollback also fails, the result is `action="rollback_failed"` with `active_db_state="non_serviceable"`.
- AC-3 (`REQ-004`): A failing `_cleanup_staged` unlink no longer raises out of `_restore_from_backup`; it is logged and the flow still returns a `RecoveryResult`.
- AC-4 (`REQ-002`, `REQ-005`, `REQ-006`): After a partial-activation rollback, no candidate `-wal`/`-shm` remains at live names; `uv run pytest tests/db` passes; `uv run python tools/check_docs_consistency.py --domain db` is clean.

## Tests
- `REQ-005`: in `tests/db/test_db_recovery.py`, patch `shutil.move` to raise `OSError` after a real `os.replace` (workflow target, tmp dirs) and assert the live file bytes are the archived original and `active_db_state="preserved_original"` (AC-1); patch `os.replace` so the handler's rollback replace fails and assert `rollback_failed`/`non_serviceable` (AC-2).
- `REQ-002`: sidecar variant — stage one sidecar, let the second `shutil.move` fail, assert the first moved sidecar is removed on rollback and candidate bytes never persist at live names (AC-4).
- `REQ-004`: patch `Path.unlink` (or the staged path) to raise `OSError`; assert `_restore_from_backup` returns a result instead of raising (AC-3).
- `REQ-003`: update the one existing test asserting `action == "error"` for handler rollback failure — `test_os_error_after_activation_with_failed_rollback_reports_non_serviceable` (`:996-1021`, assert at 1020) — to the new vocabulary (AC-2). The `action == "error"` assertions at 108, 120, 132 (condition dispatch), 1432 (`os.replace` itself fails: no swap, no rollback), and 1477 (dry_run dispatch) belong to non-rollback paths and stay unchanged (checked this cycle).
- Suite gate: `uv run pytest tests/db`, then full suite `-n auto`.

## Documentation Impact
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (named via `docs/00_index.md` task mapping) must state the new handler behavior (REQ-006): `rollback_failed` on in-activation rollback failure and always-populated `active_db_state` on that path. ADR-008 needs no edit: Step 3 consumer scan showed its state enumeration and test-citation table stay accurate; update only if the docs checker fails after the code change.

## Assumptions
- Keeping the single atomic `os.replace` of the DB file (Issue Constraint) is compatible with tracking the swap via a mutable activation holder passed into `_activate_candidate` (judgment call during analysis).
- `corrupt_archive` exists once `_stage_restore` completed AND the live DB existed at staging time (the copy is made inside `_stage_restore`, `recovery_restore.py:96-98`, only when `db_path.exists()`); the handler's `corrupt_archive.exists()` guard stays as the rollback precondition, not the activation indicator (checked in Step 3 re-verification). A partial activation with no archived original cannot roll back; it must report `rollback_failed`/`non_serviceable`, matching the Issue's Required Changes.
- No production consumer branches on the state-less `error` shape specifically (checked by reading both service consumers in Step 3); if a consumer is found later to require it, that is a Plan-Document Correction, not a silent exception.
- At recording time no process holds `/opt/llm/db/rag.sqlite` or `/opt/llm/db/session.sqlite` (`fuser` returned no users, exit 1, checked in Step 3); operational inspection reflects the dev host only.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether an external cron/backup job ever invokes `recover_corruption` with `dry_run` expectations tied to the old state-less `error` on handler paths | `rg` over `deploy/`, `init.d/`, `tools/`, `config/` found no external invocations of `recover_corruption` (checked in Step 3), but host cron outside the repo cannot be excluded | Operator confirms host cron/systemd timers before rollout; deploy step includes a service-restart check | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/recovery.py | Modify | High (restore state machine; `recover_corruption` services, `scripts/db/__init__.py` export) | 9 | High (single author, >70%) | not applicable (rsynced) |
| tests/db/test_db_recovery.py | Modify | Low (test-only) | 0 | High (single author, >70%) | not applicable (rsynced) |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Modify | Low (docs) | 0 | High (single author, >70%) | not applicable (rsynced) |

## Cross-Plan Target Overlap Scan

- Result: 1 finding (`tools/check_plan_target_overlaps.py`, 2026-11-15): `tests/db/test_db_recovery.py` targeted by both this plan and `plans/20261115-033931_dbreview001_logical-verify-vec-extension.md`.
- Re-run after Plan 003 was added (2026-11-15): 3 findings total — this plan + Plan 003 also share `scripts/db/recovery.py` and `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`. Judgment: **sequencing** — Plan 003 lands after this plan (its dependency row) and builds on the activation-holder shapes this plan introduces.
- Judgment (vs Plan 001): **compatible**. Plan 001 edits the happy-path test (`test_recovery_backup_and_restore`, staging-dir/sidecar assertions); this plan edits the rollback-failure test (~lines 1010-1024, action vocabulary) and adds new test functions. Disjoint test functions, no contradicting designs. Note for the implementer: this plan's new failure tests need a WAL sidecar on the source DB — the same fixture pattern Plan 001 introduces for the happy path.
- Update after Plan 001 procedures were generated (2026-11-15): Plan 001's actual test edits are **add-only** new functions appended after `test_wal_shm_sidecars_land_at_final_locations_after_activation` (its procedure `implementations/20261115-075008_2_...md`); it does not edit `test_recovery_backup_and_restore`. The disjoint-functions judgment is unchanged; 001's e2e vec fixtures run with `_run_logical_verification` unpatched, while 002's failure tests keep patching it — different fixtures, no conflict.
- Update after Plan 009 froze (same tool, 2026-11-15): `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` is now shared by 4 plans (002+003+004+009). Judgment: **compatible sections** — 009 edits only section 12 (drill artifacts and the `rto_seconds` row); 002/003/004 own the restore/probe sections. Batch order 002 → 003 → 004 → 009; no contradiction.
- Update after Plan 008 froze (same tool, 2026-11-15): `docs/41_db/db_07...` now 5 plans (002+003+004+009+008); `scripts/db/recovery.py` now 4 plans (002+003+004+008). Judgment: **compatible sections** — 008 edits only the name-construction lines (`recovery.py:359-361`) and section-12 lifecycle text; 002's holder/rollback region is untouched. 008 is last in the fixed batch order 001→008; no contradiction.

## Design
- **Activation tracking**: replace the post-call `activated` flag with a mutable holder (small dataclass or dict passed to `_activate_candidate`) that `_activate_candidate` flips **after `os.replace` returns and before the first sidecar move**, appending each successfully moved sidecar to. `os.replace` is atomic: if it raises, no swap happened and the holder stays unset, so the handler does not roll back and `corrupt_archive` is never consumed on a replace failure (existing test `:1424-1436` stays unchanged). The holder flip sits inside `_activate_candidate` between the replace and the moves, matching the Issue's Required Changes bullet 1 ("before or inside"). Alternatives rejected: (a) setting a caller-side flag before calling `_activate_candidate` — would claim a swap that `os.replace` itself might not have performed, producing spurious rollbacks that also destroy the quarantine of the original's sidecars; (b) splitting `_activate_candidate` into replace + moves at the call site — enlarges `_restore_from_backup` and duplicates the swap contract.
- **Rollback reuse**: extend `_rollback_or_non_serviceable` with an optional `moved_sidecars` iterable (default empty keeps current behavior for post-activation verification failures) that unlinks moved sidecars (log-and-continue) before swapping the archived original back; the `except OSError` handler calls the same helper so both failure families report identical vocabulary (REQ-003), replacing the duplicated inline rollback in the handler (`recovery.py:427-442`).
- **Action vocabulary**: `rollback_failed` already exists in the contract (ADR-008 test-citation table and `db_07` contract, per consumer scan); the handler path adopting it is a documented change (Issue Constraint honored: documented reason = consistent state reporting), and the Issue's AC-2 explicitly requires it.
- **Consumer scan record** (`scan_change_consumers.py --seed rollback_failed`, Step 3): docs candidates → `docs/41_db/db_07` (target row REQ-006), `docs/10_adr/adr_02_05_008...` and `docs/10_adr/adr_01_index.md` (reference-only: test-citation tables, not invalidated); test candidates → `tests/db/test_db_recovery.py` (target row); services consumers of `recover_corruption` → `not affected: they branch on action/state strings that remain in the documented vocabulary, verified by reading both files in Step 3`.
- **Architecture check** (Step 3): `recovery.py` imports only `db.*`, `pathlib`, `os`, `shutil`, `sqlite3`, `logging`; `lint-imports` contracts reported 6 kept / 0 broken this cycle; no new import edges planned.

## Implementation steps
1. **Phase 1: Activation tracking and non-raising cleanup** (REQ-001, REQ-004; `scripts/db/recovery.py`)
   - [ ] Pass a mutable activation holder into `_activate_candidate`; set swap-started before `os.replace` and record each completed sidecar move (REQ-001)
   - [ ] Rewrite the `except OSError` handler to branch on swap-started instead of the post-call `activated` flag (REQ-001)
   - [ ] Make `_cleanup_staged` unlink per file inside `try/except OSError` with a log (REQ-004)
2. **Phase 2: Unified rollback and reporting** (REQ-002, REQ-003; `scripts/db/recovery.py`)
   - [ ] Extend `_rollback_or_non_serviceable` with optional moved-sidecar removal (unlink candidates at live names, log-and-continue) (REQ-002)
   - [ ] Handler uses the helper for activation failures: `preserved_original` on success, `rollback_failed`/`non_serviceable` on rollback failure (REQ-003)
3. **Phase 3: Fault-injection tests** (REQ-003, REQ-005; `tests/db/test_db_recovery.py`)
   - [ ] Add after-replace, after-first-sidecar-move, rollback-failure, and cleanup-failure injections asserting live bytes and reported state (REQ-005)
   - [ ] Update the one existing test asserting `action == "error"` on handler rollback failure (`:996-1021`) to the new vocabulary (REQ-003)
4. **Phase 4: Documentation, validation & deployment hand-off** (REQ-006; `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`)
   - [ ] Update the recovery action/state mapping in `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (REQ-006)
   - [ ] Run `uv run pytest tests/db`, full suite `-n auto`, ruff, mypy (CI form), bandit `-ll`, `lint-imports`, `tools/check_docs_consistency.py --domain db` (AC-4)
   - [ ] diff-cover on the branch diff reaches 90% per `rules/toolchain.md`
   - [ ] Deployment hand-off to `skills/deploy/SKILL.md` after commit+push; deploying is the user's decision (REQ-003)

### Release units
**Unit**: activation-rollback-reporting | **Phases**: 1, 2, 3 | **Reason**: the handler action change (`error` → `rollback_failed` on rollback failure) breaks existing test assertions until the Phase 3 test updates land; Phases 1-2 alone leave `tests/db` red, so they cannot each be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/recovery.py | Unit fault injection per activation step; integration via `recover_corruption` | `uv run pytest tests/db/test_db_recovery.py -v` | AC-1..AC-3 behaviors asserted; live bytes verified against archived original |
| scripts/db/recovery.py (regression) | Existing restore/rollback tests | `uv run pytest tests/db -v` | Existing flows unchanged except the documented handler vocabulary |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Docs consistency | `uv run python tools/check_docs_consistency.py --domain db` | No findings |
| scripts/db/recovery.py (radon) | Complexity guard | `uv run radon cc scripts/db/recovery.py -s` | Baseline top `_restore_from_backup` C(13); change must not add a new C — extract the handler rollback into the shared helper (already Phase 2) |
| scripts/ (vulture) | Dead-code baseline | `uv run vulture scripts/ --min-confidence 80` (run this cycle) | No `scripts/db` findings in baseline; new helper usage keeps `_rollback_or_non_serviceable` referenced from both call sites |
| scripts/ (bandit) | Security baseline | `uv run bandit -r scripts/ -c pyproject.toml` (run this cycle) | Baseline 45 low / 0 medium / 0 high; `-ll` gate stays clean |
| branch diff | Coverage gate | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (baseline run this cycle; then with `--fail-under=90`) | Baseline recorded this cycle: total project coverage 95%, tree clean at recording (no diff lines); future branch diff must reach 90% |

## Risks
- **Risk**: the handler now reports `rollback_failed` where services previously saw `error`, changing service-side log/alert interpretation → **Mitigation**: vocabulary is already in the documented contract; REQ-006 updates docs; UNK-01 records the external-cron check before rollout.
- **Risk**: removing candidate sidecars during rollback could delete a live sidecar belonging to the original if staging semantics change later (Issue 003) → **Mitigation**: only unlink paths recorded as moved by `_activate_candidate`; 003 sequences after this Plan and must re-verify the same invariant.
- **Risk**: swallowing `_cleanup_staged` OSError hides leftover temp artifacts → **Mitigation**: log each failure at ERROR level; retention/cleanup of `.tmp_` leftovers is explicitly covered by `issues/20261114-092857_dbreview008_artifact-retention-gaps.md`.
- **Risk**: concurrent edits with Plan 001 (verification stage) and Issue 003 (sidecar semantics) in the same function family → **Mitigation**: execution order fixed in the batch plan (001 → 002 → 003); Step 8b overlap check recorded as sequencing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Activation tracking and non-raising cleanup (scripts/db/recovery.py) | In Progress | — | — | Procedure generated: implementations/20261115-080732_1 |
| 2 | Unified rollback and reporting (scripts/db/recovery.py) | In Progress | — | — | Procedure generated: implementations/20261115-080732_1 (Phases 1-2, same file) |
| 3 | Fault-injection tests (tests/db/test_db_recovery.py) | In Progress | — | — | Procedure generated: implementations/20261115-080732_2 |
| 4 | Documentation, validation & deployment hand-off (docs/41_db/db_07_api_and_operations-recovery-and-reference.md) | In Progress | — | — | Procedure generated: implementations/20261115-080732_3 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261115-080732_1_scripts_db_recovery.py.md | 1 | Procedure | Created | — | — |
| implementations/20261115-080732_2_tests_db_test_db_recovery.py.md | 3 | Procedure | Created | — | — |
| implementations/20261115-080732_3_docs_41_db_db_07_api_and_operations-recovery-and-reference.md.md | 4 | Procedure | Created | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261114-092849_dbreview002_partial-activation-rollback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-035004
- **Related target files**: scripts/db/recovery.py, tests/db/test_db_recovery.py, docs/41_db/db_07_api_and_operations-recovery-and-reference.md

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target File | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem bullets 1-2; Required Changes bullet 1 | scripts/db/recovery.py | Phase 1 | AC-1 | Phase 3 after-replace injection | Verified by test (Issue ad hoc) + confirmed in Step 2 code reading |
| REQ-002 | Required Changes bullet 2 | scripts/db/recovery.py | Phase 2 | AC-4 | Phase 3 sidecar-variant test | Explicit in code (Step 2) |
| REQ-003 | Required Changes bullet 3; Acceptance Criteria 1-2 | scripts/db/recovery.py | Phase 2 | AC-1, AC-2 | Phase 3 assertions incl. updated existing tests | Explicit in code (Step 2) |
| REQ-004 | Problem bullet 4; Required Changes bullet 4 | scripts/db/recovery.py | Phase 1 | AC-3 | Phase 3 cleanup-failure injection | Explicit in code (Step 2) |
| REQ-005 | Testing Expectations | tests/db/test_db_recovery.py | Phase 3 | AC-1, AC-2, AC-3, AC-4 | Phase 3 tests themselves | Verified by test (gap confirmed in Step 3) |
| REQ-006 | Documentation Impact | docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Phase 4 | AC-4 | `check_docs_consistency.py --domain db` | Explicit in code (Step 3 consumer scan) |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261115-080732 -->