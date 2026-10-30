# Implementation Procedure: dlq.py outbox promotion, worker, reconciliation

## Goal

Rework DLQ promotion in `scripts/eventbus/dlq.py` into a DB-only transaction that commits
`events.dlq_at` and a `dlq_outbox` (new) request atomically, add the outbox consumer
`process_outbox` (new) with durable retry/terminal state, and extend reconciliation with
orphan / interrupted-tmp / mismatch reporting (REQ-002–REQ-007, REQ-009; plan AC-1–AC-5).

## Scope

**In scope:**
- `_shared_promote`, `_shared_promote_single`: remove `_atomic_write`, add outbox insert.
- `process_outbox` (new), `_canonical_record_bytes` (new) idempotence helper, backoff helper.
- Three new `Counter` metrics.
- `reconcile_missing_dlq_files` report extension: `orphans`, `interrupted_tmp` (new), `mismatch`
  (new result keys).

**Out of scope:**
- `archive_dlq_record` (`dlq.py:291-312`, no production caller — untouched, plan Assumption).
- `_atomic_write` (`dlq.py:273-288`) itself, `is_promotable`, `_build_dlq_record`,
  `promote_single` signatures; requeue paths; endpoint contracts.

## Assumptions
- Verified at HEAD `124e340b4`: `_shared_promote` `dlq.py:89-130` (per event: `_atomic_write`
  at 117 → UPDATE `dlq_at` 122-126 → commit; OSError → counter+log+continue at 118-121);
  `_shared_promote_single` `:133-173` (OSError re-raise at 159-161); `sweep_orphans` `:176-190`;
  `reconcile_missing_dlq_files` `:193-249` returning `{checked, rebuilt, failed}`; failure
  `Counter` `:22-25`; `DlqEventRecord` dataclass `:30+`; `_build_dlq_record` `:44`.
- Outbox DDL (rows 01/02) exists in every database this code runs against.

## Design decisions
- Promotion transaction: per event in the sweep, `UPDATE events SET dlq_at=? WHERE event_id=?
  AND dlq_at IS NULL` then `INSERT INTO dlq_outbox (event_id, requested_at, status, attempts)
  VALUES (?,?,'pending',0)` and a single `db.commit()` per event (per-event isolation kept;
  insert runs only when `cur.rowcount == 1` so a racing promotion never duplicates the row).
  `_shared_promote_single` drops the `try/except OSError` + re-raise entirely — no file I/O
  remains in either path (REQ-003, AC-2).
- `process_outbox(db, deadletter_dir, cfg, run_locked) -> dict[str, int]` (new, async):
  `run_locked` (new) is `route_helpers.run_with_db_lock` injected by `app.py` (row 06) — DB reads/
  writes each run in their own locked transaction, file writes run outside any lock hold
  (plan Design; row 06 keeps `dlq.py` free of FastAPI imports).
  Flow: fetch due pending rows (`next_attempt_at` (new) NULL or ≤ now) → for each: build
  `DlqEventRecord` from the event row (same query shape as reconcile) → `_canonical_record_bytes` (new)
  (new) renders the canonical JSON → if destination file exists with byte-identical bytes,
  mark `done` without rewrite (idempotence, double-write risk mitigation) → else
  `_atomic_write` outside the lock → locked write marks `done` (`completed_at=now`) and
  increments the generated counter. `OSError` → locked write records the attempt:
  `attempts+1`, `last_error=str(exc)`, `next_attempt_at = now + min(base * 2**(attempts-1),
  cap_seconds)` from `cfg.outbox_backoff_base_seconds` / `cfg.outbox_backoff_max_seconds`
  (row 07); when `attempts >= cfg.outbox_max_attempts` set status `'failed'` (terminal) and
  increment the terminal counter. One failing artifact never aborts the loop (per-event
  isolation, AC-3). Terminal `failed` rows are never re-fetched (worker skips status≠pending).
- Restart semantics need no repair step: pending rows are simply due on the next cycle (REQ-006).
- New metrics (names fixed here, registered by row 14):
  `eventbus_dlq_outbox_generated_total` (new), `eventbus_dlq_outbox_attempt_failure_total` (new),
  `eventbus_dlq_outbox_failed_total` (new); `eventbus_dlq_file_write_failure_total` kept (reconcile
  rebuilds and worker writes both meter through the existing counter at the `_atomic_write`
  call sites' `except OSError` handlers).
- Reconciliation extension (same function, result dict gains three keys):
  `orphans` — `*.json` files directly in `deadletter_dir` (the `requeued/` subdirectory used
  by `archive_dlq_record` is excluded) whose `event_id` has neither a promoted event row
  (`dlq_at IS NOT NULL`) nor a `done` outbox row; `interrupted_tmp` (new) — lingering
  `.dlq_tmp_*` files (the `tempfile.mkstemp(prefix=".dlq_tmp_")` pattern at `dlq.py:278`;
  count only, never deleted here);
  `mismatch` — promoted events whose file parses but whose canonical fields differ from the
  rebuilt `DlqEventRecord` (compare `seq`, `event_id`, `topic`, `payload`, `producer`,
  `published_at`, `dlq_at`; `consumer_delivery_failure_count` is excluded because the delivery
  table can age after promotion). Missing-file rebuild semantics unchanged (this Plan extends
  `ebdlqrecon002`, never duplicates it).

## Alternatives considered
- Folding file generation into the promotion transaction outside the lock via deferred
  callbacks: rejected — no durable request, contradicts REQ-005 observability.
- Reusing `reconcile_missing_dlq_files` as the outbox worker: rejected — reconcile rebuilds
  from canonical state only and has no attempt/backoff state; the outbox needs its own
  lifecycle rows. Reconcile classifies; the worker generates.

## Implementation
### Target file
`scripts/eventbus/dlq.py`

### Procedure
1. Add the three new `Counter` objects next to the existing one.
2. Rework `_shared_promote` and `_shared_promote_single` to the DB-only two-write
   transaction; delete their `_atomic_write` calls and OSError handling; import the row-04
   repo helpers.
3. Add `_canonical_record_bytes` (new) (orjson dumps with the same key order `_atomic_write`
   uses) and `process_outbox` (new).
4. Extend `reconcile_missing_dlq_files` with the orphan/tmp/mismatch scans and new result keys.

### Method
Behavior rework inside existing functions + additive functions; `sweep_orphans` and
`promote_single` wrappers keep their signatures.

### Details
- `requested_at` (new)/`completed_at` (new) use `now_iso()` like all EventBus timestamps.
- Sweep keeps its `continue`-on-failure isolation; with no file I/O the only failure mode is
  DB errors, which today propagate to `_dlq_loop`'s `except (OSError, sqlite3.Error)` — unchanged.
- The `deadletter_dir` parameter of `_shared_promote`/`_shared_promote_single`/`sweep_orphans`/
  `promote_single` is kept (signature stability for rows 05/06 call sites and existing tests);
  it is unused in the promotion paths themselves — unused parameters raise no ruff finding
  under this repo's selected rules (`pyproject.toml` ruff config).
- The worker must not mutate `events`: `dlq_at` is written only by promotion paths (ADR-006
  INV-13 gating lives in `is_promotable` + the promote `WHERE dlq_at IS NULL`, untouched).
- Artifact content nuance (feeds rows 05/09 tests): after the change the generated file's
  `consumer_delivery_failure_count` is always the `MAX` across consumers computed at
  generation time (the reconcile builder), not the inline NACK-time count `_shared_promote_single`
  used to embed at `dlq.py:156`. `promote_single` keeps its `consumer_failure_count` parameter
  for the promotion log line only.

## Compatibility considerations
- Docs contract flips from "written first" to "committed first, generated durably" — rows
  12/13 land in the same deploy (plan Risk mitigation); until then docs describe the old order.
- `reconcile_missing_dlq_files` return dict gains keys: callers that assert exact dicts
  (tests only today) must be updated — row 09 owns that.

## Security considerations
- `last_error` stores exception text from local OSError only; no secrets in metrics names.
- SQL remains parameterized constant fragments with the repo's `# nosec B608` convention.

## Rollback considerations
- Reverting this file leaves `dlq_outbox` (new) tables unused (harmless); promotion reverts to
  write-first semantics. Roll back rows 03-06 together with rows 05/06 call sites.

## Validation plan
- Row 09 (`test_eventbus_dlq.py`): atomic pair, no inline file write, reconcile fields.
- Row 10 (`test_eventbus_dlq_outbox.py`): commit-then-crash-before-file, crash during tmp
  write (interrupted-tmp detection), monkeypatched `os.replace` raising `OSError` for one
  event among several (isolation + backoff schedule persisted), attempts reaching the bound
  → terminal `failed` persisted and skipped next cycle, restart with pending rows processed
  on next cycle, idempotent re-processing of a matching file.
- `uv run pytest tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_eventbus_dlq_outbox.py`;
  `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `lint-imports`.

## Completion criteria
- AC-1–AC-5 hold under fault injection; no promotion path touches the filesystem; failed
  artifacts are durable, bounded, terminal, and reported.

## Out of Scope
- `_dlq_loop` wiring (row 06), config fields (row 07), ack_route adjustment (row 05), docs (rows 12-14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | DB-only promotion transactions + new counters | Pending | — | — | Plan step 3 |
| 2 | `process_outbox` (new) + idempotence + backoff | Pending | — | — | Plan step 3 |
| 3 | Reconciliation orphan/tmp/mismatch extension | Pending | — | — | Plan step 4 |
| 4 | Run rows 09/10 tests + mypy + lint-imports | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `dlq_outbox` (new) table must exist (rows 01/02 or test-harness schema) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`, `REQ-006`, `REQ-007`, `REQ-009`
- **Source issue**: `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-221254_dlqbox001_dlq-sqlite-outbox.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-103000
- **Related target files**: `scripts/eventbus/dlq.py`
