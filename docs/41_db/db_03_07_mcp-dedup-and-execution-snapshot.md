---
title: "DB Architecture and Schema - MCP Dedup Store and Execution Snapshot Tables"
area: shared
tags:
  - shared
  - db
  - schema
  - mcp-dedup
  - tool-call-state
  - execution-snapshots
  - replay
  - retention
  - ai-reference
related:
  - db_01_architecture_and_schema-overview-and-config.md
  - db_02_architecture_and_schema-schema-reference.md
  - db_03_architecture_and_schema-migration-and-scaling.md
  - db_08_active_databases.md
  - adr_02_05_008_db-six-sqlite-store-separation.md
  - mcp_03_03_transport-and-health.md
  - agent_04_03_state-and-persistence-platform-databases.md
---

# MCP Dedup Store and Execution Snapshot Tables

Operational and failure semantics for the two durable stores introduced by toolexec001 and
renewed by mcpdl002 (lease + identity contract):
the standalone `mcp_dedup.sqlite` dedup store (owned by the shared MCP dispatcher) and
the `tool_call_state` table inside `workflow.sqlite` (owned by
the agent; the former `execution_snapshots` table is retired, see its section). Transport-facing semantics: [mcp_03_03](../22_mcp/mcp_03_03_transport-and-health.md).
Agent-facing semantics: [agent_04_03](../23_agent/agent_04_03_state-and-persistence-platform-databases.md).

## The Standalone `mcp_dedup.sqlite` Store

`mcp_dedup.sqlite` is one of the six SQLite stores: a store outside the four platform domains.
[ADR-008](../10_adr/adr_02_05_008_db-six-sqlite-store-separation.md) separates stores by owner:
this file is owned by the shared MCP dispatcher layer (`scripts/shared/mcp_dedup.py`,
`DedupStore`) and is never opened by the agent, the RAG pipeline, or the MDQ index.
The agent's tool-call view lives in `workflow.sqlite` instead, and the dispatcher never
writes into `mdq.sqlite` or `rag.sqlite`.

Contract details (owned by the `scripts/shared/mcp_dedup*.py` module family; `shared.mcp_dedup`
is the public facade):

- File location: each MCP server process owns its store reference in the `[dedup]` table of
  its own `config/{server}_mcp_server.toml` (ten tables, one shared store). At bootstrap the
  server validates its table with `load_dedup_section()` (`scripts/shared/mcp_dedup_config.py`)
  and injects the typed `DedupStoreConfig` into the dispatcher; there is no shared dedup config
  file and no config discovery. A missing table raises `ConfigMissingError` and a bad value
  raises `ConfigParseError`, both aborting startup before any socket is created. `dedup.db_path`
  is pinned to `dedup_db_dir()/mcp_dedup.sqlite`, where `dedup_db_dir()` is `LLMAGENT_DB_DIR`
  or the default `/opt/llm/db` — the same fallback-literal shape the other platform databases
  use. The contract pins the filename too: the installation marker is directory-scoped.
- Bootstrap and identity stamp: the store creates its canonical tables and indexes on open
  (`scripts/shared/mcp_dedup_schema.py`) and stamps its identity as a three-part handshake:
  a `store_meta` identity row (random `store_uuid` + generation), `PRAGMA user_version = 2`,
  and an external installation marker file (`.mcp_dedup_installed`) next to the database. Automatic
  migration is not supported: a future schema change lands as a new canonical DDL and the file is
  archived and recreated (see Adoption Path below).
- Identity start states: every open classifies the file before any write —
  `first_initialization` (genuinely new; writes the identity stamp), `healthy` (stamp, identity
  row, marker, and canonical fingerprint all agree), or a typed refusal: `lost` (a known
  generation's file is gone), `replaced` (the marker names a different store),
  `legacy_or_unverified` (pre-change shape, no identity row, or a missing marker),
  `schema_mismatch` (fingerprint or `user_version` drift), and `identity_mismatch` (the
  injected config's validated fingerprint drifts from the installed store's identity). Refusals raise
  `DedupStoreError` with the shared archive-and-recreate guidance; nothing is migrated,
  stamped, or repaired automatically. For `identity_mismatch` the recovery is to correct the
  server's `[dedup]` values (never the store file); `resolve_store` remains the operator-runbook
  path for archive-and-recreate.
- Concurrency: WAL journal mode (set only after a successful classification, so refused opens
  stay strictly read-only), `PRAGMA busy_timeout` (default 5000 ms), `synchronous = NORMAL`,
  one held connection guarded by a `threading.Lock`, and every write runs under `BEGIN IMMEDIATE`.
  Cross-process writers rely on the busy timeout; a `sqlite3.Error` rolls back and is re-raised.
- Lease-based state machine: `pending -> completed`, `pending -> failed`, `pending -> interrupted`.
  Each acquisition (`try_acquire_execution`) gives the acquiring caller an `owner_id` and a lease
  (`lease_expires_epoch = now + lease_seconds`). The owner can heartbeat with `renew_lease`.
  Finalization (`record_completed`, `record_failed`, `mark_interrupted`) is owner-conditional:
  a non-owner write, a write to a terminal row, or a heartbeat on an expired or terminal row
  raises `DedupLeaseConflict` and never mutates the row.
- Acquisition vocabulary (the decision `try_acquire_execution` returns, and the dispatcher maps):
  `acquired` (first attempt or a permitted recovery attempt), `replay_completed` (terminal
  completed row with matching snapshot and intact payload), `in_progress` (live lease held by
  another owner), `contract_mismatch` (stored `tool_name`/`args_hash` disagree with the incoming
  call), `reconciliation_required` (expired `pending` lease — classification only, never a new
  owner), `outcome_unknown` (attempt cap reached), `replay_unavailable` (terminal row that
  cannot be safely replayed: completed with a snapshot mismatch or a truncated payload, or failed).
- Terminal immutability: terminal rows are never rewritten. There is no force-reset path; a
  completed row with a different snapshot or a truncated payload refuses re-execution as
  `replay_unavailable` in every retry class. Recovery of an expired `pending` lease requires
  `reconcile_execution` first (audited `pending -> interrupted` transition plus a history entry);
  only then may one reacquisition proceed (`attempt_number + 1`), gated by `dedup.max_attempts`.
  Reacquisition never rewrites the stored snapshot.
- Attempt history: `call_attempt_history` records every decision (attempt, completed, failed,
  reconciled) per key with its attempt number. History entries are deleted by their own
  `recorded_epoch` past the retention cutoff, independently of the parent row's state (see
  retention sweep below); this state-independent rule is recorded as intentional (`U-5`, owner
  decision `D-2`).
- Result size cap: a stored result larger than 8000 serialized characters is replaced by a
  truncated sentinel (`{"truncated": true, "sha256": <full-payload hash>, "preview": <first 1000 chars>}`).
  The preview is built by redacting the serialized text first (bearing tokens, secret query
  parameters, absolute paths), then cutting the redacted text to the preview length, so the
  stored preview is not the first 1000 characters of the raw result.
  A truncated stored payload is never served as a replay result; acquisition reports it as
  `replay_unavailable` (refused), not a fresh attempt.
- Result metadata columns: `dedup_call_state` also carries `result_sha256`, `result_size_bytes`,
  `result_class`, `result_code`, `external_ref`. All five are nullable and are written only at terminal
  finalization. `result_class` is one of `complete` (the serialized result stored in full),
  `secure_reference` (an external reference is recorded), `redacted_preview` (the sentinel), or
  `replay_unavailable` (a failed row, where `result_code` is the error class). `result_sha256` and
  `result_size_bytes` describe the full serialized result whatever the class. These columns record
  facts only: the replay decision table is unchanged, and a row whose stored payload is a truncated
  sentinel is still refused. How the classes reach a caller is described in
  [mcp_02_01](../22_mcp/mcp_02_01_endpoints-and-transport.md).
- Retry classification: the declared `retry_policy` field in each tool's `TOOL_LIST` metadata
  (`shared.tool_metadata.RetryPolicy`) is the sole authority; the dispatcher maps
  `same_logical_call_only`/`reconcile_then_retry` to retryable and everything else, including
  unknown tools, to non-retryable (fail-safe unreplayable). `RETRYABLE_TOOLS` in
  `scripts/shared/tool_constants.py` remains only as reference data, drift-checked against the
  declarations in tests; there is no config-file `[retry_class]` mirror.
- Retention sweep: `purge_expired(retention_days)` deletes terminal rows older than the retention
  window (default 14 days), and separately deletes `call_attempt_history` entries recorded before
  the same cutoff regardless of the parent row's state. States listed in `legal_hold_states`
  (`[dedup]` config entry) are excluded from the sweep. Pending rows are never purged; their
  timeout path is lease classification. The dispatcher purges once per process on first use.
  The per-state eligibility matrix is in the Retention and Capacity Monitoring section below.
- Idempotency key: the key is the caller-supplied logical call id, carried end to end
  (`X-Idempotency-Key` at the transport; the agent passes `context.call_id` through
  `scripts/agent/tool_runner.py::_logical_call_id`). Nothing is derived — the old hash
  derivations collided. A row whose stored `tool_name`/`args_hash` disagree with the incoming
  call is rejected as `idempotency_key_reused` before any dispatch.

Config keys (in the `[dedup]` table of each `config/{server}_mcp_server.toml`): `db_path`
(pinned to the dedup database directory contract above), `retention_days` (14, accepted range
1..365), `pending_timeout_minutes` (10, accepted range 1..1440), `lease_seconds` (30, accepted
range 1..3600), and `max_attempts` (3, accepted range 1..10). Zero, negative, boolean, and
non-integer values are rejected. Every shipped `[dedup]` table sets `pending_timeout_minutes`
explicitly to the default; the key is validated and part of the config fingerprint, and no
server-side code reads it. The table is read once per process at bootstrap and injected as an
immutable `DedupStoreConfig`. The stale-pending timeout that drives classification is
Agent-side only: `pending_timeout_minutes` (10) in `config/agent.toml` via
`AgentConfig.pending_timeout_minutes`.

## `tool_call_state` (workflow.sqlite); `execution_snapshots` retired

The `execution_snapshots` table and the `tool_call_state.snapshot_id` foreign key are never written by any code path and are retired. Fresh databases do not create them; a legacy database that still carries the empty table fails startup under exact fingerprint matching and is archived and recreated by the operator.

Snapshot state is carried in the `execution_snapshot` component map instead
(`scripts/shared/execution_snapshot.py`): five component keys — `deployed_rev`, `git_sha`,
`config_hash`, `schema_versions`, and `dedup`. The `dedup` component is read from the dedup
store identity via a read-only `read_store_identity()` lookup and renders as
`gen=<generation>;schema=<schema-fingerprint>`, or `absent` when the store is unconfigured,
unopenable, or identity-less; building a snapshot never creates or mutates the store.

`tool_call_state` lives in `workflow.sqlite`, defined in the canonical create-path DDL
`db/schema_sql.py` and created at database creation; the fingerprint gate compares the
database shape against that canonical DDL. Column definitions (canonical DDL:
`scripts/db/schema_sql.py::build_workflow_schema_sql`):

- `tool_call_state`: `idempotency_key` (TEXT PK), `task_id` (TEXT NOT NULL),
  `tool` (TEXT NOT NULL), `state` (TEXT NOT NULL, CHECK `pending|completed|failed|interrupted`),
  `retry_class` (TEXT NOT NULL),
  `args_hash` (TEXT NOT NULL, populated by the recording write path; it is the value
  replay-directive reconstruction matches a reissued call against at turn entry),
  `created_at` / `updated_at` (REAL NOT NULL).
- Index: `idx_tool_call_state_task_state` on `tool_call_state(task_id, state)`.

Operational notes:

- Ownership: the agent executor path writes these rows through the `StateStore` facade
  (`scripts/agent/workflow/tool_call_state_ops.py`). `workflow.sqlite` `tool_call_state`
  is the system of record. The dispatcher's `mcp_dedup.sqlite` store is a disposable
  dedup-log cache behind the dispatcher boundary, not a system of record (adrrev008 settled
  the producer-ownership question the archived issue tracked).
- Timestamps: `created_at`/`updated_at` are REAL epoch seconds (wall-clock),
  unlike the ISO-8601 TEXT columns of the older workflow tables.
  Consumers must not assume a single timestamp format across workflow tables
  (see db_02 section 7b).
- The `idempotency_key` column holds the same logical call id the transport carries, so an
  agent row and a dedup-store row for one call can be matched.
- Stale-pending classification: `classify_stale_pending` transitions this task's `pending`
  rows older than the Agent-side `AgentConfig.pending_timeout_minutes` to `interrupted` inside a WHERE-guarded
  UPDATE (idempotent on re-run, same discipline as `recover_stale_attempts`). The rows it
  transitions are surfaced to the next LLM turn as a control message
  (see [agent_04_03](../23_agent/agent_04_03_state-and-persistence-platform-databases.md)).

## Replay Decision Table

What ops reads when a call "wasn't re-run". Branch labels are the shipped `dedup_state`
values on `DispatchResult` and the `error_type` taxonomy in `scripts/mcp_servers/dispatch.py`.
The acquisition statuses behind the branches are listed in the store section above.

| Stored row state | Call condition | Action | Audit tag |
|---|---|---|---|
| no row | any | acquire attempt 1 under the caller's lease; handler runs | `dedup_state=""` (owner-scoped) |
| completed | snapshot matches, stored result present and not truncated | serve cached replay, no handler executed, no side effects | `dedup_state=duplicate_hit` |
| completed | snapshot mismatch, or stored payload is a truncated sentinel | refused; the force-reset path is gone | `is_error`, `error_type=dedup_unreplayable`, `dedup_state=replay_unavailable` |
| pending | live lease held by another owner | refused before dispatch | `is_error`, `error_type=dedup_in_progress`, `dedup_state=in_progress` |
| pending | lease expired, tool `retryable` | `reconcile_execution` (audited `pending -> interrupted`), then one reacquisition (`attempt_number + 1`), handler runs | `dedup_state=replayed` (owner-scoped) |
| pending | lease expired, tool `non_retryable` | refused before dispatch | `is_error`, `error_type=dedup_unreplayable`, `dedup_state=reconciliation_required` |
| interrupted | attempts remain | reacquire with `attempt_number + 1`, handler runs | `dedup_state=replayed` (owner-scoped) |
| interrupted | `dedup.max_attempts` exhausted | tool `retryable`: audited degraded dispatch (overlay-only marker); tool `non_retryable`: refused | `dedup_state=store_error` / `is_error`, `error_type=dedup_unreplayable`, `dedup_state=outcome_unknown` |
| failed | any | refused; terminal rows are immutable | `is_error`, `error_type=dedup_unreplayable`, `dedup_state=replay_unavailable` |
| any | stored `tool_name`/`args_hash` disagree with incoming call | rejected before dispatch | `is_error`, `error_type=idempotency_key_reused` |
| any (store side) | store unavailable or refused open, tool `retryable` | dispatch continues with an audited degraded marker | `dedup_state=store_error` |
| any (store side) | store unavailable or refused open, tool `non_retryable` | fail closed, call refused | `is_error`, `error_type=dedup_store_error`, `dedup_state=store_error` |
| any (store side) | store identity lost/replaced/legacy/mismatch | open refused as `DedupStoreError`; operator resolves via archive-and-recreate | `is_error`, `error_type=dedup_store_error`, `dedup_state=store_error` (non-retryable) / `dedup_state=store_error` (retryable) |

Side notes:

- Only real, successful, non-dry-run results are cached; a dry-run outcome clears the key so
  no replayable state is left behind.
- Expired-pending semantics on the dedup store side are read-time classification
  (`classify_interrupted` in `scripts/shared/mcp_dedup.py`): a lookup reports an old `pending`
  row as `interrupted` without mutating it. An expired lease is never re-authorized without
  the audited `reconcile_execution` step first.
- A finalization that loses ownership (0-row owner-conditional UPDATE) raises
  `DedupLeaseConflict` and is reported as `dedup_state=lease_conflict`; the dispatcher logs it
  and never re-dispatches the call.
- Interrupted rows are never silently re-executed for `non_retryable` tools: the refusal is
  the guarantee, and the operator decides the next step.

## Retention and Capacity Monitoring

Retention eligibility is defined per stored state. The sweep is `purge_expired(retention_days)`
(`scripts/shared/mcp_dedup_ledger.py`, line 551), run at most once per process on first use by
`_purge_once` in `scripts/mcp_servers/dispatch.py`; it deletes rows only and never rewrites a
row's state.

| State or table | Stored status | Retention applies | Rule | Legal hold |
|---|---|---|---|---|
| completed | `completed` | Yes | terminal row past the `retention_days` cutoff on `updated_epoch` | excluded when the state is listed in `legal_hold_states` |
| failed | `failed` | Yes | same terminal rule | same |
| interrupted | `interrupted` | Yes | same terminal rule | same |
| pending (unresolved) | `pending` | No | never swept; its lifecycle is `reconcile_execution` (line 395): an expired lease with attempts remaining becomes `interrupted` through the audited transition, and attempts exhausted is a refusal (outcome unknown) | n/a, no held row can exist in this state |

The three result classifications (`reconciliation_required`, `outcome_unknown`,
`replay_unavailable`) have no stored status; their matrix rows map them to the stored status of
the row they describe (`pending`, or `interrupted` for an interrupted execution) and are
state-conditional definitions applied when those states exist — that vocabulary belongs to the
mcpdl006 plan (`U-6`), and behaviour is asserted only for what is observable.

`call_attempt_history` has no stored state, so its retention cannot be decided by the matrix:
entries are deleted by `recorded_epoch` past the same cutoff regardless of the parent state,
recorded as intentional (`U-5`, owner decision `D-2`). A state-dependent history exception would
need a separate owner approval.

Legal-hold boundary: `legal_hold_states` (new) is an optional `[dedup]` entry listing stored
state names excluded from the sweep; `purge_expired` gains the `AND status NOT IN (...)`
exclusion reading the store's own config. Held rows are reported as held, not as
retained-at-large (`held_past_retention`). Configuration-based only: no schema change, no
fingerprint change (`U-2`).

Capacity fields — the payload contract of `collect_dedup_metrics()` (new), read-only: no write,
no migration, no new service. Published through the health `details` block:

| Field | Meaning |
|---|---|
| `schema_version` | metrics payload contract version |
| `db_path`, `generated_epoch` | store path and read time |
| `row_states` | per-status row counts |
| `pending_overdue` | `pending` rows with `lease_expires_epoch` past the read time |
| `growth_rows_per_hour` | rows created within the last hour |
| `wal_size_bytes` | size of the store's `-wal` file |
| `lock_wait_ms` | elapsed milliseconds to acquire the store lock and run the reads |
| `legal_hold_states` | the configured held states |
| `held_past_retention` | held-state rows past the retention cutoff |
| `rows`, `growth`, `wal` | per-threshold blocks `value`, `threshold`, `status` (`ok`, `warning`, `fail`); present only when the matching `[dedup]` threshold key is set |

Status-only semantics (owner decision `D-6`): a computed status never changes store or
dispatcher behaviour, and threshold values are operator-supplied (`U-1`). The operator criteria
for these fields are in
[agent_10_05](../23_agent/agent_10_05_operations-and-observability-monitoring.md); the payload
shape for the wired servers is in [mcp_02_02](../22_mcp/mcp_02_02_startup-modes-and-health.md);
the key inventory is in [mcp_06_01](../22_mcp/mcp_06_01_configuration-file-inventory.md).

## Adoption Path (Current-Only Policy)

`mcp_dedup.sqlite` bootstraps with its canonical DDL plus the identity stamp (`store_meta`
row, `PRAGMA user_version = 2`, external installation marker) and carries no version ledger or
migration step. A schema change lands as a new canonical DDL in
`scripts/shared/mcp_dedup_schema.py`, and an existing file matching the previous shape is
archived and recreated: the version 2 result-metadata columns were added this way, so a store
created under version 1 is refused as `schema_mismatch` and resolved by the operator runbook.
Recovery for this file is recreating it: the store
is a disposable cache, and a fresh empty store only means the next call of each key runs for
real. Identity refusals (`lost`, `replaced`, `legacy_or_unverified`, `schema_mismatch`) follow
the same operator resolution: archive the file, remove or rename it, and let the next open
stamp a fresh identity (`resolve_store` is the scripted path).

## Keywords

- shared
- db
- mcp_dedup
- tool_call_state
- execution_snapshots
- replay
- retention
