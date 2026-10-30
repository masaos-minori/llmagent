## Goal
- Replace the synchronous, lock-held DLQ file write in EventBus promotion with an SQLite outbox: commit `events.dlq_at` and a `dlq_outbox` request in one transaction, generate the derived JSON file in the existing background loop with persisted failure and retry state, and extend reconciliation to report orphaned, interrupted, and mismatched artifacts.

## Priority
Medium

## Scope
- **In-Scope**:
  - Decision record: the owner adopted the outbox design on 2026-10-29 (Step 7b answer); this Plan implements the outbox, not the lighter alternative.
  - `dlq_outbox` table written in the same transaction as the `events.dlq_at` update (inline NACK promotion and sweep promotion).
  - File generation moved out of the DB-lock critical section into the existing `_dlq_loop` background worker; idempotent completion, per-artifact isolation, persisted failure detail, bounded retry with backoff, terminal `failed` state.
  - Reconciliation extended to report orphan files (file without a promoted row), interrupted `.dlq_tmp_*` files, and content mismatches; missing-file rebuild already exists (`ebdlqrecon002`, landed).
  - Shutdown behavior preserved: outbox work is part of `app.state.dlq_task` and joins before the shared connection closes.
  - Schema change lands through the dbmig001 migration framework (registered `eventbus` migration step + baseline update).
  - Config knobs for retry policy in `scripts/eventbus/config.py` + `config/eventbus.toml`.
- **Out-of-Scope**:
  - Changing the promotion rule (ADR-006 INV-13), the requeue transaction, or the DLQ endpoint contracts.
  - Outboxing requeue/archive file operations (see Assumptions; `archive_dlq_record` in `scripts/eventbus/dlq.py:291-312` has no production caller today — confirmed by absence search across `scripts/`).
  - JSONL event archive reconciliation.
  - Unrelated refactoring or formatting-only changes.
- **Dependencies**:
  - Hard order: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` Phases 1–2 (framework + `scripts/eventbus/migrations.py` + `schema.py` lookup) must be implemented before this Plan's Phase 2; the `dlq_outbox` schema step is the first registered `eventbus` migration. Overlap rows flagged by `check_plan_target_overlaps.py` (`scripts/eventbus/schema.sql`) are this dependency, sequenced, not contradictory designs.
  - `ebdlqrecon002` procedures are archived in `implementations/done/20261029-085348_*` and their `reconcile_missing_dlq_files` landed in `scripts/eventbus/dlq.py:193-249`; this Plan extends, never duplicates it.
  - `ebaudit005` landed (`implementations/done/20261029-115727_*`); audit calls in `scripts/eventbus/dlq_route.py` are untouched by this Plan.
  - Active implementations `implementations/20261029-130401_*` touch `tests/eventbus/test_eventbus_restart_resume.py`, `test_eventbus_requeue_edge_cases.py`, `test_admin_topics_authorization.py` — no target-file overlap, but rebase against current `HEAD` before implementing (EventBus churn is high: `ack_route.py` 11, `app.py` 9, `dlq.py` 8, `schema.sql` 8 commits/30d).

## Background
Re-verified against `HEAD c5a8285dd` on 2026-10-29 (after the tree reorganization `f7f7616f3`; all cited paths are in the tracked tree). Today's order in `scripts/eventbus/dlq.py`: `_atomic_write` runs before the `events.dlq_at` update in both promotion paths (`_shared_promote:89-130` sweep, `_shared_promote_single:133-173` inline), all while the shared DB lock is held; a failed write only increments `eventbus_dlq_file_write_failure_total` and logs (`dlq.py:118-121`), and inline failure re-raises to `ack_route.py:213` which defers to the sweep. `ack_route.py:166-221` runs `_nack_and_promote` through `run_with_db_lock`. No outbox concept exists anywhere in `scripts/eventbus/`, `tests/eventbus/`, `docs/24_eventbus/` (absence re-verified 2026-10-29). The background worker exists: `app.py:80` creates `app.state.dlq_task = _dlq_loop(app)` (`app.py:139-158`, 60s cadence, `sweep_orphans` each cycle); shutdown (`app.py:95-136`) stops the task, joins in-flight work, and acquires the DB lock before closing (`ebshutdown002` sequence). `ebdlqrecon002` landed `reconcile_missing_dlq_files` (`dlq.py:193-249`; today called only from `tests/eventbus/test_eventbus_dlq.py`, not yet from the production startup path — this Plan wires its extension into the loop). Authority model in docs: SQLite `events.dlq_at` is authoritative, the JSON file is derived (`docs/24_eventbus/eventbus_03_dlq_operations.md:120`, `eventbus_09_publish_durability.md:21-23`). `scripts/eventbus/schema.sql` stamps `PRAGMA user_version = 3` (line 45).

## Problem
DLQ file I/O inside the DB-lock critical section stretches the lock for every promotion and sweep cycle, and a failed artifact generation leaves no durable record — only a counter and a log line. Orphaned and content-mismatched files are not reported by any reconciliation (`ebdlqrecon002` rebuilds missing files only).

## Reason for Change
The outbox takes file I/O out of the lock-held transaction and makes artifact generation observable, durable, and retryable. The owner confirmed outbox adoption on 2026-10-29 (issue UNK-01 resolved), with `ebdlqrecon002` already landed as the precursor the issue required.

## Implementation Intent
Keep SQLite canonical and the DLQ file derived. Promotion becomes a DB-only transaction: `events.dlq_at` update + `dlq_outbox` pending row commit atomically, so a committed DLQ state always implies a durable generation request. The existing `_dlq_loop` consumes pending outbox rows outside the write transaction (still under `run_with_db_lock` for DB steps, file writes outside it), marks completion idempotently, and persists attempts/backoff/last error with a terminal `failed` state. The docs-03 "written first" ordering contract flips to "committed first, generated durably"; reconciliation reports orphaned, interrupted, and mismatched artifacts in addition to rebuilding missing ones. Promotion rules, requeue, endpoints, and the shutdown sequence stay as today.

## Requirements
- `REQ-001`: Decision recorded: outbox adopted over the lighter alternative (owner 2026-10-29); rationale captured in this Plan.
- `REQ-002`: `dlq_outbox` table committed in the same transaction as `events.dlq_at` for both inline and sweep promotion; one row per artifact request.
- `REQ-003`: Promotion paths perform no file I/O while the DB lock is held.
- `REQ-004`: Background worker generates files from committed pending rows; completion is idempotent (re-processing never duplicates canonical state or overwrites a completed artifact non-idempotently).
- `REQ-005`: Failed generation persists failure detail (`attempts`, `last_error`, `next_attempt_at`) with bounded retry and backoff, then terminal `failed`; one failed artifact never blocks others (per-event isolation preserved).
- `REQ-006`: Outbox processing resumes safely after restart: pending rows are processed on the next cycle with no extra repair step.
- `REQ-007`: Reconciliation reports orphaned files (present without a promoted row), interrupted `.dlq_tmp_*` files, and content mismatches, in addition to the existing missing-file rebuild.
- `REQ-008`: Shutdown joins in-flight outbox work before closing the shared connection; the `ebshutdown002` one-lock-guarded close sequence is unchanged.
- `REQ-009`: Preserved behavior: NACK success independent of file creation, ADR-006 INV-13 promotion gating, requeue transaction, DLQ endpoint contracts, fail-closed reporting of file-system failures.
- `REQ-010`: The schema change lands only through the dbmig001 migration framework (registered step + baseline), never an ad-hoc `CREATE TABLE` against an existing database.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed on 2026-10-29: every row exists-or-is-new-with-evidence, is linked to a Plan requirement, and is `Verified`; `check_workitem_structure.py` reports no findings. `check_plan_target_overlaps.py` flags no new pair; the sequenced dependency on `plans/20261029-214108_dbmig001_*` for `scripts/eventbus/schema.sql` and `scripts/eventbus/migrations.py` is recorded in both plans' Dependencies — dbmig001 lands first. Re-verified 2026-10-29 against `HEAD c5a8285dd`: evidence anchors and churn re-checked against current source; no target-file row changes.)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/schema.sql` | Add `dlq_outbox` DDL (event_id PK/FK, requested_at, status, attempts, last_error, next_attempt_at, completed_at) and stamp the new baseline `PRAGMA user_version` (the version after the dbmig001 ledger step) | New outbox contract for `eventbus.sqlite` | REQ-002, REQ-010 | `scripts/eventbus/schema.sql:3-45` tables + `PRAGMA user_version = 3`; dbmig001 sequenced before this row | `tests/eventbus/test_eventbus_dlq_outbox.py`, `tests/db/test_eventbus_schema_equivalence.py` | Verified |
| `scripts/eventbus/migrations.py` | Register the `dlq_outbox` forward migration step (previous version → new baseline) via the dbmig001 framework | Issue Required Changes: schema change via the migration framework; file created by dbmig001 Phase 2 | REQ-010 | `plans/20261029-214108_*` Phase 2 creates this registry; dependency sequenced | `tests/eventbus/test_eventbus_migrations.py` | Verified |
| `scripts/eventbus/dlq.py` | Rework `_shared_promote`/`_shared_promote_single` to commit `dlq_at` + outbox row with no file I/O; add outbox consumption (`process_outbox`): generate via `_atomic_write` outside the write transaction, idempotent completion, attempts/backoff/`last_error`, terminal `failed`; extend reconciliation with orphan/tmp/mismatch reporting; new outbox metrics | Core behavior change; all promotion and reconciliation logic lives here | REQ-002–REQ-007, REQ-009 | `dlq.py:89-130`, `:133-173`, `:176-190`, `:193-249`, `:273-288`, failure counter `:22-25` | `tests/eventbus/test_eventbus_dlq.py`, `tests/eventbus/test_eventbus_dlq_outbox.py` | Verified |
| `scripts/eventbus/dlq_repo.py` | Outbox row operations: pending fetch ordered by `next_attempt_at`, mark done/failed, terminal counts, mismatch/orphan query helpers | Repo module already owns DLQ requeue data access (`redeliver_event:43`) | REQ-002, REQ-004, REQ-005, REQ-007 | `dlq_repo.py:23-43` | `tests/eventbus/test_eventbus_dlq_outbox.py` | Verified |
| `scripts/eventbus/ack_route.py` | `_nack_and_promote` keeps INV-13 gating but the promote step becomes DB-only (no file I/O, no OSError deferral needed for file failure; NACK independence preserved via transaction) | Inline promotion runs under `run_with_db_lock` today | REQ-003, REQ-009 | `ack_route.py:166-221` (`_nack_and_promote`, OSError at 213, `run_with_db_lock` at 221) | `tests/eventbus/test_eventbus_dlq.py` (inline promotion), `tests/eventbus/test_eventbus_ack_nack.py` | Verified |
| `scripts/eventbus/app.py` | `_dlq_loop` calls the outbox consumption step each cycle after the sweep; shutdown sequence unchanged (task join already covers it) | The background worker exists here; outbox rides the same task so `ebshutdown002` join semantics hold | REQ-004, REQ-006, REQ-008 | `app.py:80` (`dlq_task`), `app.py:139-158` (`_dlq_loop`), `app.py:95-136` (shutdown/join/lock-then-close) | `tests/eventbus/test_eventbus_shutdown.py`, `tests/eventbus/test_eventbus_dlq_outbox.py` | Verified |
| `scripts/eventbus/config.py` | Add validated config fields: outbox max attempts, backoff base/interval cap | Project rule: retry policy is config, not hardcoded | REQ-005 | `config.py:82`, `:224-236`, `:337` existing field/validator pattern | `tests/eventbus/test_eventbus_config.py` | Verified |
| `config/eventbus.toml` | Ship defaults for the new outbox retry fields | Deployed config boundary for EventBus | REQ-005 | `config/eventbus.toml:6` already carries `deadletter_dir` | `tests/deploy/` config validation | Verified |
| `tests/eventbus/test_eventbus_dlq.py` | Extend: promotion commits `dlq_at` + outbox atomically; no file written inline; reconciliation report fields | Issue Testing Expectations | REQ-002, REQ-003, REQ-007 | Existing file, incl. reconcile tests at 759-913 | — | Verified |
| `tests/eventbus/test_eventbus_dlq_outbox.py` | New: fault injection at each crash point (commit-then-crash-before-file, crash during tmp write, one failing artifact among several, restart with pending rows, terminal `failed` state persisted) | Issue Testing Expectations (crash-window coverage) | REQ-004–REQ-006, REQ-009 | New module | — | Verified |
| `tests/eventbus/test_eventbus_shutdown.py` | Extend: shutdown with in-flight outbox generation joins before close; no post-close DB use | Issue Acceptance Criteria (shutdown criterion) | REQ-008 | Existing file (ebshutdown002 sequence) | — | Verified |
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | Replace the "written first" ordering contract with committed-first + durable outbox generation; state retry/backoff, terminal `failed`, reconciliation report classes (missing rebuilt / orphan / interrupted tmp / mismatch) | Doc currently states file-first authority semantics | REQ-004–REQ-007, REQ-009 | `eventbus_03_dlq_operations.md:120`, `:140` authority + reconcile text | docs checkers | Verified |
| `docs/24_eventbus/eventbus_09_publish_durability.md` | Update derived-artifact failure semantics: committed DLQ state always implies a durable generation request; failures recorded durably | Doc states the current file-first guarantee | REQ-004, REQ-009 | `eventbus_09_publish_durability.md:21-23` authority model | docs checkers | Verified |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Document new outbox metrics and config fields in the EventBus reference | Reference doc must match shipped surface; `generate_reference_table.py --check` gate | REQ-005, REQ-009 | Reference table regenerated by `tools/generate_reference_table.py` (CI runs `--check`) | `uv run python tools/generate_reference_table.py --check` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/dlq.py` | Issue instruction: read before editing; all promotion/reconcile paths change here | `scripts/eventbus/dlq.py` row |
| `scripts/eventbus/ack_route.py` | Issue instruction: NACK independence semantics to preserve | `scripts/eventbus/ack_route.py` row |
| `scripts/eventbus/app.py` | `_dlq_loop` + shutdown/join sequence to reuse, not re-implement | `scripts/eventbus/app.py` row |
| `implementations/done/20261029-085348_01_scripts_eventbus_dlq.py.md` | Issue instruction: do not duplicate `ebdlqrecon002` reconciliation | `scripts/eventbus/dlq.py` row |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | INV-13 promotion gating must stay unchanged (Out-of-Scope constraint); `:162`, `:184` | REQ-009 |
| `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` | Framework API, ledger, and baseline-version sequencing this Plan depends on | REQ-010 |
| `scripts/eventbus/schema.py` | Startup fail-closed version validation stays; only registered migration changes it (dbmig001) | REQ-010 |
| `config/eventbus.toml` + `scripts/eventbus/config.py` | Config boundary for retry knobs | REQ-005 |
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | Issue instruction: current DLQ operational contract | docs rows |

## Acceptance Criteria
- AC-1 (REQ-002, REQ-009): Every committed DLQ state can regenerate its file repeatedly without duplicate canonical state; the outbox row and `dlq_at` commit atomically.
- AC-2 (REQ-003, REQ-009): No promotion path performs file I/O while the DB lock is held; a file-system failure never undoes or misreports a committed NACK or DLQ transition.
- AC-3 (REQ-004, REQ-006): Outbox processing resumes safely after restart (pending rows processed on next cycle); one failed artifact does not block unrelated artifacts.
- AC-4 (REQ-005): Generation failures leave a persisted record with attempt count, error detail, next-attempt schedule, and terminal `failed` state after the configured bound.
- AC-5 (REQ-007): Reconciliation rebuilds missing files (existing) and reports orphaned, interrupted-temp, and content-mismatched artifacts.
- AC-6 (REQ-008): Shutdown joins in-flight outbox work before the shared connection closes; `ebshutdown002` ordering preserved.
- AC-7 (REQ-010): The schema change appears only as a registered migration plus updated baseline; no ad-hoc DDL against existing databases.

## Tests
- Crash-window fault injection (issue Testing Expectations): commit-then-crash-before-file, crash during tmp write, per-event filesystem failure among several events, restart with pending rows, shutdown with in-flight worker — each written to fail before the change and pass after.
- Extension of `tests/eventbus/test_eventbus_dlq.py` (promotion transaction, reconciliation report fields) and `tests/eventbus/test_eventbus_shutdown.py` (join semantics).
- Migration path: `dlq_outbox` step applies to a v-baseline db with data preserved (runs in `tests/eventbus/test_eventbus_migrations.py`, dbmig001-owned harness).
- Suite commands: `uv run pytest tests/eventbus`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run python tools/check_db_separation.py`, `uv run python tools/generate_reference_table.py --check`.

## Documentation Impact
Yes. `docs/24_eventbus/eventbus_03_dlq_operations.md` (outbox lifecycle, ordering contract, retry/terminal behavior, reconciliation report classes), `docs/24_eventbus/eventbus_09_publish_durability.md` (derived-artifact durability), `docs/24_eventbus/eventbus_08_reference_api.md` (metrics/config surface) are target rows. Task mapping follows `docs/00_index.md` EventBus spec entries. Docs state operational behavior and failure semantics only (`skills/DESIGN.md` Docs content policy).

## Assumptions
- The outbox covers DLQ **generation** only (promotion + rebuild requests). Requeue keeps its current transaction and file handling; `archive_dlq_record` (`dlq.py:291-312`) has no production caller today and is untouched. (Issue UNK-03 partial resolution; owner can extend.)
- Operator surface for permanently failed artifacts is the reconciliation report plus Prometheus metrics and logs; no new admin endpoint in this Plan (owner-revisable).
- Retry policy defaults: bounded attempts (default 5) with exponential backoff clamped to a max interval, configurable via `config/eventbus.toml`; exact numbers validated in the procedure step.
- Baseline `user_version` numbering follows whatever version dbmig001 lands for the ledger table; this Plan registers the immediately following step. Cross-plan sequencing is recorded in both plans.
- Inline promotion remains "inline": the DLQ transition (canonical state) still happens synchronously on NACK; only the derived file becomes asynchronous. INV-13 semantics unchanged.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether requeue/archive file operations should later join the outbox | No owner decision on record | Assumption: out of scope; revisit if owner requests | False |
| UNK-02 | Exact retry numbers (attempts, backoff base/cap) | No operational data on write-failure rates | Defaults in config, tuned after first drills/production observation | False |
| UNK-03 | Whether failed-artifact visibility should gain an admin endpoint in `dlq_route.py` | Issue left "operator surface" open; no requirement yet | Assumption: reports + metrics only; separate issue if needed | False |
| UNK-04 | Non-target test-file edits ride on implementation rows: `tests/eventbus/test_eventbus_migrations.py` (outbox-step cases, procedure row 02) and `tests/eventbus/test_eventbus_config.py` (retry-knob cases, procedure row 07) are Related-Tests entries in the target table but have no rows of their own (the migrations test module is created by dbmig001 row 15) | Frozen table contains no rows for these files | Disclosed in the procedure docs; Needs confirmation that these supporting test edits are acceptable without table rows | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/dlq.py` | Core promotion/reconcile/worker rework | All EventBus DLQ paths | 8 | High (single author) | Synced by `rsync scripts/`; service restart required |
| `scripts/eventbus/ack_route.py` | Promotion step becomes DB-only | NACK endpoint behavior | 11 | High (single author) | Synced by `rsync scripts/`; restart |
| `scripts/eventbus/app.py` | Loop gains outbox step | EventBus lifecycle | 9 | High (single author) | Synced by `rsync scripts/`; restart |
| `scripts/eventbus/schema.sql` | New table + version bump | Startup schema validation, fingerprint, dbmig001 ledger sequencing | 9 | High (single author) | Synced by `rsync scripts/` |
| `scripts/eventbus/dlq_repo.py` | New outbox row operations | DLQ data access | 8 | High (single author) | Synced by `rsync scripts/` |
| `scripts/eventbus/config.py` + `config/eventbus.toml` | New validated fields | EventBus config validation | — | High (single author) | `config/` sync per deploy checklist |
| `tests/eventbus/*` (dlq, outbox new, shutdown) | Extension + new module | EventBus suite runtime | 5–45 | High (single author) | Synced by `rsync tests/` |
| `docs/24_eventbus/eventbus_03/08/09` | Operational contract updates | EventBus docs + reference table | 22 / — / 6 | High (single author) | N/A: docs only |

## Design
- `dlq_outbox` table (per `eventbus.sqlite`): `event_id TEXT PRIMARY KEY REFERENCES events(event_id)`, `requested_at TEXT NOT NULL`, `status TEXT NOT NULL CHECK(status IN ('pending','done','failed'))`, `attempts INTEGER NOT NULL DEFAULT 0`, `last_error TEXT`, `next_attempt_at TEXT`, `completed_at TEXT`. One row per promotion request; `done` rows are kept as the durable generation record (reconcile uses them to classify orphans/mismatches).
- Promotion transaction (`_shared_promote`, `_shared_promote_single`): select promotable rows → `UPDATE events SET dlq_at` + `INSERT INTO dlq_outbox (…, status='pending')` in one transaction per event (sweep) or single commit (inline); no `_atomic_write` call remains in these paths. Sweep keeps per-event isolation.
- Outbox consumption (`process_outbox`, called from `_dlq_loop` after `sweep_orphans` each cycle): fetch `pending` rows where `next_attempt_at` is NULL or past; for each, rebuild the `DlqEventRecord` from the event row (same builder as reconcile), `_atomic_write` outside the DB lock hold for the completion write, then a short locked transaction marks `done`/`failed` (attempts increment, `last_error`, backoff `next_attempt_at` on OSError). Idempotent: existing destination file with matching content → mark `done` without rewrite; terminal `failed` rows are skipped by the worker and reported by reconciliation and metrics.
- Reconciliation extension (`reconcile_missing_dlq_files` + new report fn): keep missing-file rebuild; add counts for files present with no `dlq_at` row and no `done` outbox row (orphans), stale `.dlq_tmp_*` files, and content mismatch (file JSON vs rebuilt record comparison of canonical fields). Result dict gains `orphans`, `interrupted_tmp`, `mismatch` counts.
- Metrics: keep `eventbus_dlq_file_write_failure_total`; add outbox attempt/terminal counters (names fixed in the procedure step, registered in the reference table).
- Shutdown: outbox runs inside `app.state.dlq_task`; the existing cancel+join+lock-before-close sequence (`app.py:95-136`) covers it unchanged — a mid-cycle file write completes or aborts on its own; the DB completion write is a locked transaction that shutdown ordering already serializes.
- Failure semantics flip documented in docs: pre-change guarantee "committed DLQ row implies file existed at commit"; post-change "committed DLQ row implies a durable outbox request that the worker will fulfill or report as failed". The fail-closed rule (never hide a file-system failure) is satisfied by the persisted failure record rather than by write-first ordering.

## Implementation steps
1. **Phase 1: Decision record + tests-first contracts**
   - [ ] Record the outbox decision in this Plan (done above; REQ-001) and write failing-first contract tests for the new promotion transaction (`tests/eventbus/test_eventbus_dlq.py`) (REQ-002, REQ-003)
2. **Phase 2: Schema via migration framework** (gated on dbmig001 Phases 1–2 implemented)
   - [ ] Add `dlq_outbox` DDL to `scripts/eventbus/schema.sql` baseline and register the forward migration step in `scripts/eventbus/migrations.py` (REQ-002, REQ-010; those rows)
3. **Phase 3: Outbox core**
   - [ ] Implement outbox row operations in `scripts/eventbus/dlq_repo.py` (REQ-002, REQ-004, REQ-005)
   - [ ] Rework `_shared_promote`/`_shared_promote_single` to the two-writes-one-transaction path and implement `process_outbox` with retry/backoff/terminal state in `scripts/eventbus/dlq.py` (REQ-003–REQ-006, REQ-009)
   - [ ] Adjust `_nack_and_promote` in `scripts/eventbus/ack_route.py` to the DB-only promotion (REQ-003, REQ-009)
   - [ ] Wire `process_outbox` into `_dlq_loop` in `scripts/eventbus/app.py` (REQ-004, REQ-006, REQ-008)
   - [ ] Add validated retry config in `scripts/eventbus/config.py` + `config/eventbus.toml` (REQ-005)
   - [ ] New `tests/eventbus/test_eventbus_dlq_outbox.py` fault-injection suite incl. restart and terminal-failure cases (REQ-004–REQ-006)
4. **Phase 4: Reconciliation reporting**
   - [ ] Extend reconciliation in `scripts/eventbus/dlq.py` with orphan/interrupted-tmp/mismatch reporting (REQ-007)
   - [ ] Extend `tests/eventbus/test_eventbus_dlq.py` reconciliation tests and `tests/eventbus/test_eventbus_shutdown.py` in-flight-join test (REQ-007, REQ-008)
5. **Phase 5: Verification**
   - [ ] Run `uv run pytest tests/eventbus`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run python tools/check_db_separation.py`, `uv run python tools/generate_reference_table.py --check`; confirm service restart plan for the deployed EventBus (port 8015, DB held by pid at deploy time) (all REQ)
6. **Phase 6: Documentation**
   - [ ] Update `docs/24_eventbus/eventbus_03_dlq_operations.md`, `eventbus_09_publish_durability.md`, `eventbus_08_reference_api.md` (REQ-004–REQ-007, REQ-009)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/dlq.py`, `scripts/eventbus/dlq_repo.py` | Unit + crash-point fault injection (tmpfs/monkeypatched `os.replace`) | `uv run pytest tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_eventbus_dlq_outbox.py` | Atomic commit pair; pending→done/failed lifecycle; isolation holds |
| `scripts/eventbus/ack_route.py` | Integration via TestClient | `uv run pytest tests/eventbus` | NACK success independent of file state; INV-13 unchanged |
| `scripts/eventbus/app.py`, shutdown | Integration with in-flight worker | `uv run pytest tests/eventbus/test_eventbus_shutdown.py` | Join before close; no closed-connection use |
| `scripts/eventbus/schema.sql`, `scripts/eventbus/migrations.py` | Migration apply against data-bearing v-baseline | `uv run pytest tests/eventbus/test_eventbus_migrations.py tests/db/test_eventbus_schema_equivalence.py` | `dlq_outbox` appears; rows preserved; fingerprint matches |
| `scripts/eventbus/config.py` | Unit incl. invalid values | `uv run pytest tests/eventbus/test_eventbus_config.py` | Retry knobs validated |
| Cross-cutting | Architecture + docs gates | `lint-imports`; `uv run python tools/check_db_separation.py`; `uv run python tools/generate_reference_table.py --check` | No import-contract breach; reference table current |
| Type/quality | Static | `uv run mypy --no-namespace-packages scripts/ tests/eventbus` | Clean |

## Risks
- **Risk**: The ordering flip weakens the "file exists at commit" guarantee ops may rely on. **Mitigation**: outbox row is the durable promise; docs-03/09 updated in the same change; reconciliation reports close the visibility gap. Landing docs and code in one deploy.
- **Risk**: Running EventBus service holds `/opt/llm/db/eventbus.sqlite` (confirmed 2026-10-29: pid holds the file, listener on port 8015). **Mitigation**: migration + deploy sequence stops the service first; restart verified via the deploy checklist.
- **Risk**: High EventBus churn (`ack_route.py` 11/30d) and active implementations (`20261029-130401_*`) editing neighboring EventBus tests. **Mitigation**: rebase against current `HEAD` before each phase; run `check_plan_target_overlaps.py` again at procedure generation.
- **Risk**: dbmig001 slippage blocks Phase 2 (REQ-010 gate). **Mitigation**: Phase 1 (tests-first contracts) and Phase 3 repo/worker code can proceed against a test-harness schema; only the deployed-schema step waits. Never ad-hoc DDL against the live DB.
- **Risk**: Worker and reconcile double-writing the same artifact. **Mitigation**: idempotent completion rule (matching file present → mark done) + tests for concurrent-cycle overlap.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Decision record + tests-first contracts | In Progress | — | — |  |
| 2 | Phase 2: Schema via migration framework | In Progress | — | — | Gated on dbmig001 Phases 1–2 |
| 3 | Phase 3: Outbox core | In Progress | — | — |  |
| 4 | Phase 4: Reconciliation reporting | In Progress | — | — |  |
| 5 | Phase 5: Verification | Pending | — | — |  |
| 6 | Phase 6: Documentation | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | dbmig001 framework not yet implemented (planning-order dependency, not a design conflict) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261030-103000_01_scripts_eventbus_schema.sql.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261030-103000_02_scripts_eventbus_migrations.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261030-103000_03_scripts_eventbus_dlq.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-103000_04_scripts_eventbus_dlq_repo.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-103000_05_scripts_eventbus_ack_route.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-103000_06_scripts_eventbus_app.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-103000_07_scripts_eventbus_config.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-103000_08_config_eventbus.toml.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-103000_09_tests_eventbus_test_eventbus_dlq.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261030-103000_10_tests_eventbus_test_eventbus_dlq_outbox.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-103000_11_tests_eventbus_test_eventbus_shutdown.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261030-103000_12_docs_24_eventbus_eventbus_03_dlq_operations.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261030-103000_13_docs_24_eventbus_eventbus_09_publish_durability.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261030-103000_14_docs_24_eventbus_eventbus_08_reference_api.md.md` | 6 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261029-221254
- **Related target files**: `scripts/eventbus/schema.sql`, `scripts/eventbus/migrations.py`, `scripts/eventbus/dlq.py`, `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/app.py`, `scripts/eventbus/config.py`, `config/eventbus.toml`, `tests/eventbus/test_eventbus_dlq.py`, `tests/eventbus/test_eventbus_dlq_outbox.py`, `tests/eventbus/test_eventbus_shutdown.py`, `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_09_publish_durability.md`, `docs/24_eventbus/eventbus_08_reference_api.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Unresolved Questions (owner decision 2026-10-29) | (recorded in this Plan) | Phase 1 | — | Plan record | Confirmed by owner decision |
| REQ-002 | Required Changes | `scripts/eventbus/schema.sql` | Phase 2 | AC-1 | `tests/eventbus/test_eventbus_dlq_outbox.py` | Explicit in issue |
| REQ-002 | Required Changes | `scripts/eventbus/dlq.py` | Phase 3 | AC-1 | `tests/eventbus/test_eventbus_dlq.py` | Explicit in issue |
| REQ-002 | Required Changes | `scripts/eventbus/dlq_repo.py` | Phase 3 | AC-1 | `tests/eventbus/test_eventbus_dlq_outbox.py` | Derived from confirmed evidence |
| REQ-003 | Problem (lock-held I/O); Required Changes | `scripts/eventbus/dlq.py` | Phase 3 | AC-2 | Contract tests (no inline file write) | Explicit in issue |
| REQ-003 | Required Changes | `scripts/eventbus/ack_route.py` | Phase 3 | AC-2 | `tests/eventbus/test_eventbus_dlq.py` | Explicit in issue |
| REQ-004 | Required Changes (worker, idempotent) | `scripts/eventbus/dlq.py` | Phase 3 | AC-3 | `tests/eventbus/test_eventbus_dlq_outbox.py` | Explicit in issue |
| REQ-004 | Required Changes | `scripts/eventbus/app.py` | Phase 3 | AC-3 | `tests/eventbus/test_eventbus_shutdown.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes (persisted failure/retry) | `scripts/eventbus/dlq.py` | Phase 3 | AC-4 | Fault-injection tests | Explicit in issue |
| REQ-005 | Constraints/config boundary | `scripts/eventbus/config.py`, `config/eventbus.toml` | Phase 3 | AC-4 | `tests/eventbus/test_eventbus_config.py` | Derived from confirmed evidence |
| REQ-006 | Acceptance Criteria (restart) | `scripts/eventbus/app.py` | Phase 3 | AC-3 | Restart fault-injection test | Explicit in issue |
| REQ-007 | Required Changes (orphan/mismatch) | `scripts/eventbus/dlq.py` | Phase 4 | AC-5 | Reconciliation tests | Explicit in issue |
| REQ-008 | Required Changes (shutdown) | `scripts/eventbus/app.py` | Phase 3 | AC-6 | `tests/eventbus/test_eventbus_shutdown.py` | Explicit in issue |
| REQ-009 | Constraints | `scripts/eventbus/ack_route.py` | Phase 3 | AC-2 | NACK independence regression | Explicit in issue |
| REQ-009 | Constraints (ADR-006 INV-13) | `scripts/eventbus/dlq.py` | Phase 3 | AC-1 | Promotion-semantics regression | Explicit in issue |
| REQ-010 | Dependencies (dbmig001) | `scripts/eventbus/migrations.py` | Phase 2 | AC-7 | `tests/eventbus/test_eventbus_migrations.py` | Explicit in issue |
| REQ-010 | Dependencies | `scripts/eventbus/schema.sql` | Phase 2 | AC-7 | `tests/db/test_eventbus_schema_equivalence.py` | Derived from confirmed evidence |
| REQ-009 | Documentation Impact | `docs/24_eventbus/eventbus_03_dlq_operations.md` | Phase 6 | AC-2 | Docs checkers | Explicit in issue |
| REQ-004 | Documentation Impact | `docs/24_eventbus/eventbus_09_publish_durability.md` | Phase 6 | AC-3 | Docs checkers | Explicit in issue |
| REQ-005 | Documentation Impact | `docs/24_eventbus/eventbus_08_reference_api.md` | Phase 6 | AC-4 | `generate_reference_table.py --check` | Derived from confirmed evidence |