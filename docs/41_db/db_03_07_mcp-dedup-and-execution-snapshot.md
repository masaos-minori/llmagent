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
  - adr_02_05_008_db-sqlite-4db-separation.md
  - mcp_03_03_transport-and-health.md
  - agent_04_03_state-and-persistence-platform-databases.md
---

# MCP Dedup Store and Execution Snapshot Tables

Operational and failure semantics for the two durable stores introduced by toolexec001:
the standalone `mcp_dedup.sqlite` dedup store (owned by the shared MCP dispatcher) and
the `tool_call_state` table inside `workflow.sqlite` (owned by
the agent; the former `execution_snapshots` table is retired, see its section). Transport-facing semantics: [mcp_03_03](../22_mcp/mcp_03_03_transport-and-health.md).
Agent-facing semantics: [agent_04_03](../23_agent/agent_04_03_state-and-persistence-platform-databases.md).

## The Standalone `mcp_dedup.sqlite` Store

`mcp_dedup.sqlite` is a fifth database file outside the original four-database set.
[ADR-008](../10_adr/adr_02_05_008_db-sqlite-4db-separation.md) separates stores by owner:
this file is owned by the shared MCP dispatcher layer (`scripts/shared/mcp_dedup.py`,
`DedupStore`) and is never opened by the agent, the RAG pipeline, or the MDQ index.
The agent's tool-call view lives in `workflow.sqlite` instead, and the dispatcher never
writes into `mdq.sqlite` or `rag.sqlite`.

Contract details (all owned by `scripts/shared/mcp_dedup.py`):

- File location: the config file is resolved through `resolve_config_dir()` (overridable with
  `LLMAGENT_CONFIG_DIR`), like every other config consumer. The store database is `dedup.db_path` in
  `config/mcp_dedup.toml`, default `/opt/llm/db/mcp_dedup.sqlite` — the same fallback-literal shape the
  other platform databases use. A missing config file raises `ConfigMissingError`; bad values raise
  `ConfigParseError`.
- Bootstrap: the store creates its own table and indexes on open (`CREATE TABLE IF NOT EXISTS`),
  stamps `PRAGMA user_version = 1` as its current schema-shape marker. There is no migration
  registry: the former migration machinery was removed by the compatrm001 plan, so a future
  schema change to this file
  lands as a new canonical DDL and the file is archived and recreated (see Adoption Path below).
- Concurrency: WAL journal mode, `PRAGMA busy_timeout` (default 5000 ms), `synchronous = NORMAL`,
  one held connection guarded by a `threading.Lock`, and every write runs under `BEGIN IMMEDIATE`.
  Cross-process writers rely on the busy timeout; a `sqlite3.Error` rolls back and is re-raised.
- State machine: `pending -> completed`, `pending -> failed`, `pending -> interrupted`.
  Terminal states never regress; `record_pending` refreshes only `pending`/`interrupted` rows
  unless called with `force=True` (the dispatcher uses force only for the policy-allowed fresh
  attempt on a snapshot-mismatched completed row).
- Result size cap: a stored result larger than 8000 serialized characters is replaced by a
  truncated sentinel (`{"truncated": true, "sha256": <full-payload hash>, "preview": <first 1000 chars>}`).
  A truncated stored payload is never served as a replay result; it triggers a fresh attempt.
- Retry classification: `[retry_class]` in `config/mcp_dedup.toml` maps live tool names to
  `retryable` / `non_retryable`. Unknown tools default to `non_retryable` (fail-safe unreplayable).
- Retention sweep: `purge_expired(retention_days)` deletes terminal rows older than the retention
  window (default 14 days). Pending rows are never purged; their timeout path is classification.
  The dispatcher purges once per process on first use.
- Idempotency key: `sha256` over `(method, tool_name, args, uid)` via `derive_idempotency_key`
  (shared by the transport layer; see mcp_03_03). A row whose stored `tool_name`/`args_hash`
  disagree with the incoming call is rejected as `idempotency_key_reused` before any dispatch.

Config keys (all in `config/mcp_dedup.toml`): `dedup.db_path`, `dedup.retention_days` (14),
`dedup.pending_timeout_minutes` (10), and the `[retry_class]` map. The same timeout value is
the source for the agent-side stale-pending classification in `workflow.sqlite`. The config file is
read once per process: after the first successful load the parsed config is cached until the service
restarts, and a failed load is not cached.

## `tool_call_state` (workflow.sqlite); `execution_snapshots` retired

The `execution_snapshots` table and the `tool_call_state.snapshot_id` foreign key were never written by any code path and are retired (wfaudit010). Fresh databases no longer create them; a legacy database that still carries the empty table fails startup under exact fingerprint matching and is archived and recreated by the operator.

`tool_call_state` lives in `workflow.sqlite`, defined in the canonical create-path DDL
`db/schema_sql.py` and created at database creation. (Historical note: it was originally
added by a per-database migration step that the compatrm001 plan later removed;
fresh-created databases and the removed step produced byte-identical shapes, which is what the
fingerprint gate compares against.) Column definitions (canonical DDL:
`scripts/db/schema_sql.py::build_workflow_schema_sql`):

- `tool_call_state`: `idempotency_key` (TEXT PK), `task_id` (TEXT NOT NULL),
  `tool` (TEXT NOT NULL), `state` (TEXT NOT NULL, CHECK `pending|completed|failed|interrupted`),
  `retry_class` (TEXT NOT NULL),
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
- The `idempotency_key` column holds the same derived key the transport computes, so an
  agent row and a dedup-store row for one call can be matched (producer-side key identity
  is the open item in the follow-up issue above).
- Stale-pending classification: `classify_stale_pending` transitions this task's `pending`
  rows older than `dedup.pending_timeout_minutes` to `interrupted` inside a WHERE-guarded
  UPDATE (idempotent on re-run, same discipline as `recover_stale_attempts`). The rows it
  transitions are surfaced to the next LLM turn as a control message
  (see [agent_04_03](../23_agent/agent_04_03_state-and-persistence-platform-databases.md)).

## Replay Decision Table

What ops reads when a call "wasn't re-run". Branch labels are the shipped `dedup_state`
values on `DispatchResult` and the `error_type` taxonomy in `scripts/mcp_servers/dispatch.py`.

| Stored row state | Call condition | Action | Audit tag |
|---|---|---|---|
| completed | snapshot matches, stored result present and not truncated | serve cached result, no handler executed, no side effects | `dedup_state=duplicate_hit` |
| completed | snapshot mismatch, or stored payload is a truncated sentinel | fresh attempt under the same key (`record_pending` with force) | `dedup_state=snapshot_mismatch` / `result_truncated` |
| pending / failed / interrupted | tool is `retryable` | re-dispatch the same key (interrupted past the timeout is the canonical case) | `dedup_state=replayed` |
| pending / failed / interrupted | tool is `non_retryable` | refuse the call before dispatch; no handler runs | `is_error`, `error_type=dedup_unreplayable`, `dedup_state=unreplayable` |
| any | store unavailable, tool `retryable` | dispatch continues without dedup protection | `dedup_state=store_error` |
| any | store unavailable, tool `non_retryable` | fail closed, call refused | `is_error`, `error_type=dedup_store_error`, `dedup_state=store_error` |
| any | stored `tool_name`/`args_hash` disagree with incoming call | rejected before dispatch | `is_error`, `error_type=idempotency_key_reused` |

Side notes:

- Only real, successful, non-dry-run results are cached; a dry-run outcome clears the key so
  no replayable state is left behind.
- Expired-pending semantics on the dedup store side are read-time classification
  (`classify_interrupted` in `scripts/shared/mcp_dedup.py`): a lookup reports an old `pending`
  row as `interrupted` without mutating it. The store-side dispatcher currently replays fresh
  `pending` rows per the retry class above; the workflow-side timeout transition is the
  `classify_stale_pending` UPDATE described above.
- Interrupted rows are never silently re-executed for `non_retryable` tools: the refusal is
  the guarantee, and the operator decides the next step.

## Adoption Path (Current-Only Policy)

`mcp_dedup.sqlite` bootstraps with `CREATE TABLE IF NOT EXISTS` + `PRAGMA user_version`
and carries no version ledger or migration step: the per-database migration mechanism
established by dbmig001 was removed by the compatrm001 plan. A future schema change to this file lands as a new canonical DDL in
`scripts/shared/mcp_dedup.py`, and an existing file matching the previous shape is archived
and recreated. Until such a change, recovery for this file is recreating it: the store is a
disposable cache, and a fresh empty store only means the next call of each key runs for real.

## Keywords

- shared
- db
- mcp_dedup
- tool_call_state
- execution_snapshots
- replay
- retention
