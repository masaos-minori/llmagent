# Implementation Procedure: scripts/shared/mcp_dedup.py

## Goal

Create the durable dedup store module shared by all MCP server processes: SQLite-backed
state machine `pending → completed / failed` with interrupted classification, result
storage, TTL retention, and validated loading of `config/mcp_dedup.toml` (REQ-002 durable
store; REQ-005 replay-policy building blocks; REQ-006 retry-class lookup; REQ-009 retention).

## Scope

**In scope:**
- `scripts/shared/mcp_dedup.py` (new): store bootstrap, row operations, classification,
  purge, and the `config/mcp_dedup.toml` loader/validator.

**Out of scope:**
- Dispatcher integration (row 04), config file itself (row 10), snapshot builder (row 03).

## Assumptions

- Per UNK-02 (owner decision in the plan): `mcp_dedup.sqlite` stays outside the 4-DB
  inventory and bootstraps via `PRAGMA user_version`, not the dbmig001 registry. Verified
  against `tools/check_db_separation.py`: `_DB_PATH_KEY_RE` matches only the four
  registered `*_db_path` keys and `TABLE_OWNERSHIP` iterates only registered databases, so
  an unregistered standalone store does not trip the checker and no edit to that tool is
  an additional target.
- Result size cap: store `result_json` (new) up to 8000 chars (matching `tool_result_max_llm_chars`
  in `config/agent.toml:62`), above the cap store `result_hash` (new) (SHA-256) only and return
  a sentinel `DispatchResult`-compatible payload decided at row 04. Needs Confirmation of
  the exact cap value/key if operators want it tunable.

## Design decisions

- Store schema (single table `dedup_state` (new)): `idempotency_key TEXT PRIMARY KEY`,
  `tool TEXT NOT NULL`, `args_hash TEXT NOT NULL` (same normalization as the dispatcher's
  `_normalize_args_hash` — reuse via `scripts/mcp_servers/dispatch.py` import is forbidden
  by the layer contract (mcp_servers is above shared); re-implement the hash locally and
  test equality against the dispatcher's output), `state TEXT NOT NULL CHECK(state IN
  ('pending','completed','failed'))`, `created_at REAL NOT NULL`, `updated_at REAL
  NOT NULL`, `result_json TEXT`, `result_hash TEXT`, `snapshot_id TEXT`.
- `PRAGMA user_version = 1` (new) bootstrap on first open; `journal_mode=WAL`,
  `busy_timeout=5000`, `synchronous=NORMAL`; every write is a short `BEGIN IMMEDIATE`
  transaction so concurrent server processes serialize (REQ-002).
- API (all new): `load_dedup_config(path) -> DedupConfig`, `open_dedup_store(cfg)`,
  `record_pending(store, key, tool, args_hash)`, `record_completed(store, key,
  result_json_or_none, snapshot_id)`, `record_failed(store, key)`, `lookup(store, key)
  -> DedupRow | None`, `classify_interrupted(store, now)` (pending rows older than
  `pending_timeout_minutes` (new) are reported interrupted without mutating state),
  `purge_expired(store, now)` deletes `completed`/`failed` rows older than
  `retention_days` (REQ-009), `retry_class(cfg, tool) -> "retryable" | "non_retryable"`.
- Config loader lives here (plan Phase 1 note: "loader/validation lives in the Phase 3
  module"): reads `config/mcp_dedup.toml` with `tomllib`, validates key types/ranges, and
  applies shipped defaults so a missing file still yields the REQ-006 owner classification
  map. `retry_class` (new) map keys are tool names; unknown tool → `non_retryable` (new) (safe default).

## Alternatives considered

- Redis/JSON-file store — rejected: SQLite is the project's only durable substrate and
  WAL + busy_timeout already covers multi-process access (`rules/env.md`).
- Joining the dbmig001 domain registry now — rejected per UNK-02 owner decision;
  adoption path documented in row 14.

## Implementation
### Target file
`scripts/shared/mcp_dedup.py` (new)

### Procedure
1. Module docstring binding REQ-002/REQ-005/REQ-006/REQ-009 semantics and the UNK-02
   standalone decision.
2. Implement `DedupConfig` (new) / `DedupRow` (new) dataclasses, `load_dedup_config` (new), `open_dedup_store` (new).
3. Implement the store schema DDL as a module constant + `user_version` bootstrap.
4. Implement the API functions above.

### Method
`sqlite3` directly (shared layer may not import `db/` internals per `skills/DESIGN.md`
import contract unless an existing shared-module precedent allows it); monotonic-safe
timestamps as `time.time()` (same domain as the dispatcher's `_idem_now`).

### Details
- `lookup` never mutates; classification of interrupted rows is derived at read time via
  `classify_interrupted` (new) so retention/pending windows are observable without state churn.
- All functions are sync (the dispatcher awaits around them only at its own boundary;
  the store keeps transactions short enough not to block the event loop meaningfully —
  Needs Confirmation: wrap in `asyncio.to_thread` if the dispatcher integration (row 04)
  measures loop stalls).

## Compatibility considerations

- Existing `_duplicate_cache` per-process behavior is untouched by this module; row 04
  wires it. `cicd` DB-separation gate unchanged (verified, Assumptions).

## Security considerations

- `result_json` (new) may contain tool output: store is mode-0600 by SQLite default perms on
  `/opt/llm/db/`; do not store masked-field plaintext beyond what the dispatcher already
  produced. Keys are content hashes (row 01) — no secrets stored.

## Rollback considerations

- Deleting the sqlite file is safe (dispatcher falls back to its overlay); reverting the
  commit removes the only writer. No migration dependency (user_version 1 standalone).

## Validation plan

- Row 17 (`tests/shared/test_mcp_dedup.py`, new, test-first): state-machine transitions,
  reopen durability (close + reopen preserves rows), TTL purge, interrupted classification
  boundary, concurrent two-connection write serialization, config validation rejects bad
  types and applies defaults, `retry_class` (new) map per REQ-006 tool list.
- `uv run pytest tests/shared/test_mcp_dedup.py`; `uv run mypy --no-namespace-packages
  scripts/ tests/shared`; `lint-imports`.

## Completion criteria

- A completed row written by one process is readable by a fresh process (REQ-002
  durable-across-restart); over-cap results round-trip as `result_hash` (new) only; purged rows
  disappear only for `completed`/`failed` states; the module has no import above the
  shared layer.

## Out of Scope

- Replay policy decisions and audit wiring (row 04); workflow tables (row 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the store module per Procedure/Method/Details | Pending | — | — | |
| 2 | Land row 17 tests (test-first) before or with this row | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (durable store), `REQ-005` (replay inputs), `REQ-006` (retry classes), `REQ-009` (retention)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: scripts/shared/mcp_dedup.py
