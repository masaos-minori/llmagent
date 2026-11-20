# Plan: Rebuild the MCP dedup ledger as an atomic owner lease with store identity

## Goal
- Replace the MCP dedup store's lookup-then-record ledger with atomic execution ownership (one typed acquisition, renewable owner lease, immutable terminal evidence, append-only attempt history) and give the store a verifiable identity created at initialization, so exactly one caller owns a logical call at a time and a lost, replaced, legacy, or unverified store blocks side-effecting calls until an operator resolves the state.

## Priority
High

## Scope
- **In-Scope**:
  - Atomic acquisition operation (`try_acquire_execution()`) replacing the separate `lookup` + `record_pending` pattern; removal of the `record_pending(force=True)` path from the store and from all production callers.
  - `owner_id`, `lease_expires_epoch`, `attempt_number` columns; owner-conditional heartbeat and finalization that require exactly one updated row.
  - Lease expiry as a reconciliation trigger only; separate `interrupted` and `failed` recovery classification.
  - Terminal-row and snapshot immutability in code and SQL predicates; append-only attempt-history table.
  - Store identity: store UUID + generation + schema fingerprint + configuration fingerprint created at initialization, `PRAGMA user_version` stamp, external installation marker written atomically; open-time classification into first initialization / healthy / lost / replaced / legacy-or-unverified / schema mismatch; side-effecting calls rejected in every state but the first two.
  - `resolve_lost_store()` replaced by an operator resolution that records the decision and issues a new generation; `touch()` recovery removed.
  - Dedup store identity/schema fingerprint added to the execution compatibility data (`execution_snapshot`).
  - Registration of `mcp_dedup` in `tools/check_db_separation.py` and in the generated `registry/manifests/db_schema_versions.yaml` manifest.
  - New configuration keys (`lease_seconds`, `max_attempts`) in `config/mcp_dedup.toml` with loader validation.
  - Deployment initialization handling (`deploy/init_db.sh`) and documentation reconciliation (state machine, start states, operator resolution, stale `derive_idempotency_key` and `PRAGMA user_version = 1` claims).
  - Concurrency (100-caller, multi-connection), loss/replacement/legacy/mismatch identity tests written test-first.
- **Out-of-Scope**:
  - Dispatcher integration beyond adopting the new store API (heartbeat task, structured tool results, dispatcher-level fail-closed rule redesign) — filed as mcpai001.
  - Logical call id format and Agent-side approval-grant contracts (mcpdl001, archived); retention-capacity monitoring (mcpdl005); reconciliation/result-replay control API (mcpdl004); config isolation (mcpdl003); two-layer failure verification (mcpdl006).
  - Any change to ADR-008 or ADR-004 decision text and any ADR approval statement (governance constraint: maintainer approval only).
  - Migration registries for the four platform databases; the dedup store follows archive-and-recreate, not migration.
- **Dependencies**: The logical call id format (mcpdl001) has already landed (`scripts/agent/tool_runner.py::_logical_call_id`, `X-Idempotency-Key` transport header); this Plan builds on it. This Plan blocks mcpai001, mcpdl003, mcpdl004, mcpdl005, and mcpdl006 (sequencing note; each blocked item names this Plan's state vocabulary and store API as its precondition).
  - **Depends on**: issues/done/20261120-115840_mcpdl001_approval-grant-intent.md | phase all | The store's key space and the `mcpdl001` logical-call-id contract must exist before the lease columns and acquisition result vocabulary are defined.

## Background
Source: consolidated MCP deduplication two-layer defense backlog (`memo-issue.md`, Issue 2), storage half of mcpai001. The store is classified by ADR-008 as a disposable cache (recreated after loss, non-retryable tools rejected until an operator resolves the state), and ADR-004 registers the MCP-001 exception (retryable tools proceed overlay-only when the store is unavailable, lost, or freshly recreated) and the MCP-002 exception (post-open write failure is warning-only). Current code implements a partial version: `DedupStore.__init__` detects a lost store only via an out-of-band sentinel written by `resolve_lost_store()`, open-time validation compares only the table shape, and `dispatch.py` implements the fail-open overlay fallback and the lost-store refusal. Step 2 verification confirmed the issue's core claims against current source and corrected its stale references (nonexistent doc paths, no "xfail 30 days" policy, both claimed ADR conflicts already resolved in current ADR text — see Verification findings in Design).

## Problem
- `lookup` and `record_pending` are separate `BEGIN IMMEDIATE` transactions, so two concurrent callers can both observe no active row and both execute the same side-effecting handler.
- `record_pending(force=True)` resets a terminal row to pending (clearing `result_json`, resetting `created_epoch`/`updated_epoch`), destroying reconciliation evidence and allowing the same logical call to execute again; a zero-row finalization update passes silently.
- No identity marker is written at normal initialization, so a deleted or replaced database cannot be distinguished from a first start; `resolve_lost_store()`'s `touch()` creates an empty file that hides the loss.
- The store's own schema version is invisible to the execution-identity snapshot (`_DB_PATH_KEYS` covers only rag/session/workflow), and the store is not registered in `tools/check_db_separation.py` or `registry/manifests/db_schema_versions.yaml`.
- `DedupStore.__init__` raises a raw `RuntimeError` on a table-shape mismatch, which escapes `dispatch.py`'s audited fail-open/fail-closed `store_error` taxonomy (it catches only `sqlite3.Error`/`OSError`/`ConfigMissingError`/`ConfigParseError`).

## Reason for Change
Duplicate execution of external side effects is a correctness and data-integrity risk. Ownership without identity would still let all evidence vanish, and identity without atomic ownership would only preserve an unsafe ledger, so both change the same schema in one rollout.

## Implementation Intent
One transaction atomically acquires an attempt for a logical call; only the current owner heartbeats or finalizes; an expired lease requires reconciliation and never authorizes a retry by itself; terminal rows and their original snapshots are immutable and further attempts go to an attempt-history table. A store UUID and generation are created at successful initialization with the schema and configuration fingerprints, and an external installation marker is written atomically at the same moment. Each open is classified as first initialization, healthy, lost, replaced, legacy or unverified, or schema mismatch, and side-effecting calls are rejected in every state but the first two. Resolution is an explicit operator action that issues a new generation; creating an empty file is never a recovery. Retryability is a property of a known recovery procedure, not of the transport.

## Requirements
- `REQ-001`: `scripts/shared/mcp_dedup.py` exposes `try_acquire_execution(key, tool_name, args_hash, snapshot_json, owner_id)` that performs row lookup, classification, and ownership acquisition in one `BEGIN IMMEDIATE` transaction and returns a typed acquisition result (`acquired`, `replay_completed`, `in_progress`, `reconciliation_required`, `outcome_unknown`, `contract_mismatch`, `replay_unavailable`); no SQLite transaction is held open during handler execution; `record_pending`'s `force=True` parameter and the `lookup`-then-`record_pending` caller pattern are removed.
- `REQ-002`: The ledger row carries `owner_id`, `lease_expires_epoch`, and `attempt_number`; heartbeat and finalization (`record_completed`/`record_failed`/`mark_interrupted`) are owner-conditional, require exactly one updated row (`WHERE key=? AND status='pending' AND owner_id=?`), and raise a typed ownership-conflict error otherwise; a zero-row update is never a success.
- `REQ-003`: Lease expiry alone only marks the row for reconciliation (never re-authorizes execution); `interrupted` (lease-expired, outcome unknown) and `failed` (handler errored with a finalized owner write) are separate recovery classifications; `classify_interrupted` uses lease state rather than only `created_epoch`.
- `REQ-004`: Terminal rows (`completed`/`failed`/`interrupted`) and their `snapshot_json` are immutable in code and SQL; further attempts on the same key append a row to an append-only `call_attempt_history` table (key, attempt_number, owner, outcome, detail, recorded_epoch); the terminal row's original snapshot is never rewritten.
- `REQ-005`: At first initialization the store creates a `store_meta` identity row (store UUID, generation, schema fingerprint, configuration fingerprint), stamps `PRAGMA user_version = 1`, and atomically writes the external installation marker co-located with the DB file, all as one creation sequence.
- `REQ-006`: Every open classifies the start state (first initialization / healthy / lost / replaced / legacy-or-unverified / schema mismatch) from marker presence, DB presence, identity row validity, and fingerprints; a pre-change database (no identity, `user_version = 0`) is legacy-or-unverified, not healthy and not a first start; side-effecting calls are rejected in every state but first initialization and healthy; shape-mismatch failures surface as the typed `store_error` taxonomy instead of a raw `RuntimeError`.
- `REQ-007`: `resolve_lost_store()` is replaced by an operator resolution operation that records the resolution decision (generation rollover recorded in the new store's identity and in a durable log line), issues a new generation, and removes the `touch()` empty-file recovery; creating an empty file alone never resolves.
- `REQ-008`: `scripts/shared/execution_snapshot.py` includes the dedup store's identity component (store generation + schema fingerprint) in the execution compatibility data so a snapshot comparison detects a dedup-store swap.
- `REQ-009`: `tools/check_db_separation.py` registers `mcp_dedup` (path key `db_path` from `config/mcp_dedup.toml`, table ownership for the new ledger tables); `tools/generate_reference_table.py` emits a `mcp_dedup` entry in `registry/manifests/db_schema_versions.yaml` (regenerated, never hand-edited).
- `REQ-010`: `config/mcp_dedup.toml` gains `[dedup] lease_seconds` and `[dedup] max_attempts` keys with loader-side validation bounds (defaults in the loader; unknown values rejected).
- `REQ-011`: `deploy/init_db.sh` deterministically initializes the dedup store through the shared loader path (identity + marker created at deploy time) instead of relying on lazy first-use creation.
- `REQ-012`: Documentation reconciles to the new contract: ownership/lease state machine, store identity and start states, operator resolution runbook, archive-and-recreate rollout, and removal of stale `derive_idempotency_key` and unstamped-`user_version` claims.

## Implementation Target Files
**Freeze status**: Frozen (set to `Frozen` only once `issue-to-plan` Step 8's
Implementation Target Files Validation passes — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/shared/mcp_dedup.py | Store core | Rewrite `_SCHEMA`/`_INDEXES`/`_CANONICAL_DDL` (ledger columns `owner_id`, `lease_expires_epoch`, `attempt_number`; `store_meta` and `call_attempt_history` tables; ledger table renamed `dedup_call_state`); replace `lookup`/`record_pending` with `try_acquire_execution`; owner-conditional heartbeat/finalization; delete `force=True`; identity stamping and start-state classification; operator resolution replacing `resolve_lost_store`/`touch()`; typed `store_error` surfacing; new config keys | REQ-001..REQ-007, REQ-010; AC-1..AC-6 | issue evidence lines 310 (`record_pending`), 318-323 (force reset), 390 (`lookup`), 453-470 (`resolve_lost_store` + `touch()`), 52-77 (`_SCHEMA`, `_CANONICAL_DDL`, `DEDUP_SENTINEL_NAME`); verified against current file 2026-11-21 | tests/shared/test_mcp_dedup.py; tests/shared/test_mcp_dedup_concurrency.py; tests/shared/test_mcp_dedup_identity.py | Verified |
| scripts/mcp_servers/dispatch.py | Caller adoption | Replace `lookup` + pending-write + `force` call sites with `try_acquire_execution` + owner-scoped finalize; map new start states to the existing `store_error` taxonomy (`dedup_store_error` refusal for non-retryable, audited overlay-only `store_error` for retryable per ADR-004 MCP-001); keep overlay cache and per-key `args_hash` reuse rejection | REQ-001, REQ-002, REQ-006; AC-1, AC-6 | dispatch.py:289-315 (lost-store refusal), 313-329 (`lookup` failure fallback), 331-343 (reuse rejection), 160-179 (`_dedup_context` fail-open) | tests/mcp_servers/test_mcp_dispatch.py; tests/mcp_servers/conftest.py | Verified |
| scripts/shared/execution_snapshot.py | Compatibility data | Add the dedup store identity component (generation + schema fingerprint) to the snapshot build and `_DB_PATH_KEYS` so a dedup-store swap is visible in snapshot comparison | REQ-008; AC-7 | execution_snapshot.py `_DB_PATH_KEYS` covers only rag/session/workflow (verified 2026-11-21) | tests/shared/test_execution_snapshot.py | Verified |
| config/mcp_dedup.toml | Configuration | Add `[dedup] lease_seconds` and `[dedup] max_attempts` keys alongside `db_path`/`retention_days` | REQ-010; AC-8 | config/mcp_dedup.toml `[dedup]` currently holds only `db_path` and `retention_days` (verified 2026-11-21) | tests/shared/test_mcp_dedup.py (loader tests) | Verified |
| tools/check_db_separation.py | Validator registration | Register `mcp_dedup` in `TABLE_OWNERSHIP` (new ledger table names) and extend `_DB_PATH_KEY_RE` (or an equivalent explicit registration) to cover the `db_path` key in `config/mcp_dedup.toml` | REQ-009; AC-9 | tools/check_db_separation.py:55 (`TABLE_OWNERSHIP`, four DBs only), :111 (`_DB_PATH_KEY_RE = ^(rag\|session\|workflow\|eventbus)_db_path$`) | tests/tools/test_check_db_separation.py | Verified |
| tools/generate_reference_table.py | Generator source | Emit a `mcp_dedup` schema-version manifest entry (canonical DDL source + user_version stamp) from the store module | REQ-008, REQ-009; AC-9 | registry/manifests/db_schema_versions.yaml holds no `mcp_dedup` entry today; generator sources are `scripts/db/config.py`, `config/agent.toml`, `scripts/eventbus/schema.sql` (generate_reference_table.py:55) | tools/generate_reference_table.py --check (see Validation plan) | Verified |
| registry/manifests/db_schema_versions.yaml | Generated manifest | Regenerate with `tools/generate_reference_table.py` so the manifest contains the new `mcp_dedup` entry (generated file: never hand-edit) | REQ-009; AC-9 | Manifest file has no `mcp_dedup` row (verified 2026-11-21) | tools/generate_reference_table.py --check | Verified |
| deploy/init_db.sh | Deployment initialization | Initialize the dedup store (identity row, user_version stamp, installation marker) deterministically at deploy time via the shared loader, and verify creation; operator-resolution step documented there | REQ-005, REQ-007, REQ-011; AC-5, AC-10 | deploy/init_db.sh contains no dedup/mcp references today (grep 2026-11-21); deploy.sh:153-154 copies `config/mcp_dedup.toml` | tests/deploy/ scripts execution (see Validation plan) | Verified |
| tests/shared/test_mcp_dedup.py | Test suite | Rewrite ledger tests for acquisition/finalize/lease/attempt history; update the `TestFingerprintGate` pin from `PRAGMA user_version == 0` to the stamped identity; adapt `TestLostOrRecreatedDetection`, `TestReopenDurability`, `TestTtlPurge` to the identity/marker scheme | REQ-001..REQ-005; AC-1..AC-5 | TestFingerprintGate pins `PRAGMA user_version == 0` (verified 2026-11-21); file already exercises `resolve_lost_store` | this file | Verified |
| tests/shared/test_mcp_dedup_concurrency.py | New test file (New file; directory tests/shared exists) | Test-first: one key under 100 concurrent async callers acquires exactly once; multi-connection and multi-process ownership; heartbeat vs stale recovery; finalization vs recovery race; process-kill-during-dispatch scenario | REQ-001..REQ-003; AC-1..AC-3 | New file per issue Target Files; must be shown failing on current code before store changes land (issue AI Implementation Instruction) | this file | Verified |
| tests/shared/test_mcp_dedup_identity.py | New test file (New file; directory tests/shared exists) | Loss and replacement matrix: DB-only deletion, marker-only deletion, DB replacement (different store UUID), legacy pre-change DB fixture, schema mismatch, first initialization, operator resolution generation rollover | REQ-005..REQ-007; AC-4, AC-5 | New file per issue Target Files; must be shown failing on current code before store changes land | this file | Verified |
| tests/mcp_servers/test_mcp_dispatch.py | Dispatcher tests | Adapt `test_store_error_retryable_proceeds_non_retryable_fails_closed` and `test_lost_store_non_retryable_refused_retryable_proceeds` to the acquisition API and new start states; add replaced/legacy-state refusal cases | REQ-001, REQ-006; AC-1, AC-4, AC-5 | test names cite REQ-001/REQ-002 and the lost-store contract today (verified 2026-11-21) | this file | Verified |
| tests/mcp_servers/conftest.py | Fixture | Build fixtures through the new initialization path (identity + marker) instead of raw table creation | REQ-005 | conftest.py:46 imports `DedupConfig, DedupStore` and seeds store fixtures directly | consumed by tests/mcp_servers/* | Verified |
| tests/shared/test_execution_snapshot.py | Snapshot tests | Update the component-shape and mismatch pins (`COMPONENT_KEYS` equality test at :88-95) for the added dedup component | REQ-008; AC-7 | test pins `set(snap) == set(COMPONENT_KEYS)` (test_execution_snapshot.py:88-97) | this file | Verified |
| tests/db/test_schema_validation_per_database.py | Schema-drift tests | Update the `mcp_dedup` drift-harness expectations for the new multi-table canonical shape and identity stamp | REQ-004, REQ-008, REQ-009; AC-9 | test_schema_validation_per_database.py:42-43, 161-219 pin `_CANONICAL_DDL` and a `DedupStore` entry for the current single-table shape | this file | Verified |
| tests/tools/test_check_db_separation.py | Validator tests | Add registration cases: `mcp_dedup` path-key check for `config/mcp_dedup.toml` `db_path` and ownership of the new ledger tables | REQ-009; AC-9 | tests/tools/test_check_db_separation.py:60-67 exercises the four-DB path-key rules only | this file | Verified |
| docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md | Canonical store doc | Rewrite schema/config/decision sections for the lease + identity design; remove the stale `derive_idempotency_key` derivation claim (:69); make the `PRAGMA user_version = 1` claim true; add the lost/replaced/legacy/mismatch branches to the Replay Decision Table; remove the dangling follow-up-issue reference (:108) | REQ-012; AC-11 | db_03_07:69 (`derive_idempotency_key` claim; no such function exists in `scripts/`), :108 (stale follow-up citation), user_version claim vs code that never stamps (verified 2026-11-21) | docs checker (see Validation plan) | Verified |
| docs/41_db/db_08_active_databases.md | Operator reference | Update the `mcp_dedup.sqlite` section (schema authority line :69, lifecycle) with identity, lease columns, start-state semantics, and the operator-resolution runbook (sentinel/marker handling, generation rollover, archive-and-recreate) | REQ-007, REQ-011, REQ-012; AC-10, AC-11 | db_08:65-85 documents the store as `CREATE TABLE IF NOT EXISTS tool_call_state` with no identity/operator procedure; neither `resolve_lost_store` nor the sentinel is documented anywhere in `docs/` (rg 2026-11-21) | docs checker | Verified |
| docs/41_db/db_01_architecture_and_schema-overview-and-config.md | Store overview | Update the disposable-store paragraph describing the ledger (table name, lease/identity columns, recreation semantics) | REQ-012; AC-11 | db_01:36 describes "the dispatcher's `tool_call_state` dedup ledger ... recreated after loss" | docs checker | Verified |
| docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md | Migration policy | Update the dedup rows to the identity-gated rule: legacy/unverified stores are rejected, recreation issues a new generation | REQ-006, REQ-012; AC-11 | db_03:68, :76, :87 state "recreated empty" with no identity/legacy gate | docs checker | Verified |
| docs/22_mcp/mcp_03_03_transport-and-health.md | Transport/dedup doc | Update the durable-dedup state description to the new acquisition vocabulary and start states; fix the deterministic-key claim (:38 `derive_idempotency_key`) to the logical-call-id contract | REQ-006, REQ-012; AC-11 | mcp_03_03:38 (`derive_idempotency_key(method, tool_name, args, uid)` claim), :51-59 (dedup states) | docs checker | Verified |
| docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md | Agent tool-execution doc | Fix the two stale key-derivation claims to the logical-call-id contract (no `derive_idempotency_key` exists in `scripts/`) | REQ-012; AC-11 | agent_06_01:81 and :99 cite `shared/http_transport.py::derive_idempotency_key`; `rg derive_idempotency_key scripts/` returns no definition (verified 2026-11-21) | docs checker | Verified |
| docs/23_agent/agent_10_05_operations-and-observability-monitoring.md | Monitoring doc | Update the dedup-degradation observability row (new WARNING markers for lease conflicts, reconciliation_required, replaced/legacy refusal) to the new taxonomy | REQ-006, REQ-012; AC-11 | agent_10_05:30 observability row cites the current WARNING set and the db_03_07 Replay Decision Table | docs checker | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | ADR-008 Decision Details 22-24 and the disposable-cache classification are the governing contract (archive-and-recreate, no migration, fail-closed until operator resolution); the Plan must not contradict or rewrite it | scripts/shared/mcp_dedup.py; REQ-005..REQ-007 |
| docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md | Registered exceptions MCP-001 (retryable overlay-only `store_error`, covering lost or freshly recreated) and MCP-002 (post-open write failure warning-only) define dispatcher degradation semantics | scripts/mcp_servers/dispatch.py; REQ-006 |
| scripts/agent/tool_runner.py | Supplies the caller-supplied idempotency key via `_logical_call_id` (:153, :191, :366); a key producer that must keep working against the new acquisition API | scripts/mcp_servers/dispatch.py; REQ-001 |
| scripts/agent/tool_audit.py | Writes `execution_snapshot_json` into audit payloads (:281); the added dedup component flows through it unchanged | scripts/shared/execution_snapshot.py; REQ-008 |
| scripts/shared/schema_fingerprint.py | `assert_matches` contract used for open-time validation and fingerprint inputs | scripts/shared/mcp_dedup.py; REQ-006 |
| scripts/db/schema_sql.py | Prior art for `owner_id` / `lease_expires_at` lease columns in the workflow `attempts` table and the 9-state workflow `tool_call_state` (name-similarity boundary: distinct database) | scripts/shared/mcp_dedup.py; REQ-002 |
| scripts/shared/tool_constants.py | `RETRYABLE_TOOLS` is the owner classification mirrored by `config/mcp_dedup.toml [retry_class]` | config/mcp_dedup.toml; REQ-010 |
| scripts/agent/production_config_validator.py | Registers the dedup config path (:177) for startup validation; its expectations must keep passing with the new keys | config/mcp_dedup.toml; REQ-010 |
| scripts/mcp_servers/server.py | Transport layer that forwards `X-Idempotency-Key`; key contract unchanged by this Plan | scripts/mcp_servers/dispatch.py; REQ-001 |
| tests/shared/test_http_transport.py | Contains a historical docstring mention of `derive_idempotency_key` (:13); residual mention is handled by the mcpai012 documentation sweep, not this Plan | docs/22_mcp/mcp_03_03_transport-and-health.md; REQ-012 |
| deploy/deploy.sh | Copies `config/mcp_dedup.toml` (:153-154); confirms the deploy copy path needs no change | deploy/init_db.sh; REQ-011 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-002): Exactly one caller acquires a new logical call under concurrency (100-caller test); a non-owner cannot heartbeat or finalize; an old owner cannot finalize after recovery; every finalization path asserts exactly one updated row.
- `AC-2` (REQ-002, REQ-004): Terminal states cannot regress: `try_acquire_execution` never resets a terminal row, no `force` parameter exists, and a zero-row update raises a typed ownership-conflict error rather than passing silently.
- `AC-3` (REQ-003): Only an expired lease can become `interrupted`; expiry produces `reconciliation_required` and never grants retry permission; `failed` is only produced by an owner-finalized handler error.
- `AC-4` (REQ-005, REQ-006): Deleting the DB after normal operation is detected as `lost`; replacing the DB (different store UUID) is detected as `replaced`; deleting only the installation marker is detected (marker-state asymmetry classified); a legacy pre-change DB is classified `legacy_or_unverified`.
- `AC-5` (REQ-006, REQ-007): `lost`, `replaced`, `legacy_or_unverified`, and `schema_mismatch` block side-effecting calls (non-retryable refused with `dedup_store_error`; retryable degraded per the retained MCP-001 exception pending the owner decision in UNK-03); operator resolution records the decision, issues a new generation, and an empty file alone does not resolve.
- `AC-6` (REQ-001): No production caller invokes a force reset or a lookup-plus-record pattern (static check: `rg` shows no `record_pending`/`force` call sites outside the store's own removed API; enforced by tests/mcp_servers/test_mcp_dispatch.py fixtures).
- `AC-7` (REQ-008): Execution snapshots built before and after a dedup-store generation rollover are unequal on the dedup component.
- `AC-8` (REQ-010): `config/mcp_dedup.toml` carries `lease_seconds` and `max_attempts`; the loader rejects out-of-range or unknown values.
- `AC-9` (REQ-009): `tools/check_db_separation.py` reports ownership/path-key coverage for `mcp_dedup`, and `tools/generate_reference_table.py --check` shows a `mcp_dedup` row in `registry/manifests/db_schema_versions.yaml`.
- `AC-10` (REQ-011): `deploy/init_db.sh` creates the store with identity row, `user_version = 1` stamp, and installation marker in one deterministic run.
- `AC-11` (REQ-012): The documentation targets above describe the acquisition vocabulary, start states, lease columns, identity, and operator resolution; the docs checker reports no stale claims for the changed docs.

## Tests
- `REQ-001/002/003` (test-first, AC-1..AC-3): tests/shared/test_mcp_dedup_concurrency.py — 100 concurrent async callers on one key (exactly one `acquired`), multi-connection (separate sqlite3 connections), multi-process (subprocess claim race), heartbeat-extends-lease vs stale-recovery, finalize-vs-recovery race, kill-during-dispatch leaves an expired pending row that only becomes `reconciliation_required`. Written and confirmed failing against current code before the store rewrite lands.
- `REQ-005/006/007` (AC-4/AC-5): tests/shared/test_mcp_dedup_identity.py — first initialization, DB-only deletion (lost), marker-only deletion, DB replacement with foreign identity (replaced), legacy fixture DB (no identity row, `user_version = 0`), schema mismatch (drifted shape), operator resolution generation rollover, empty-file-only non-resolution.
- `REQ-001/002/004` (AC-1/AC-2): tests/shared/test_mcp_dedup.py — rewritten acquisition/finalization matrix (owner vs non-owner, terminal immutability, attempt-history append), updated fingerprint gate (`user_version == 1`), TTL purge of terminal rows only, lease-expiry reconciliation classification.
- `REQ-001/006` (AC-1/AC-5/AC-6): tests/mcp_servers/test_mcp_dispatch.py — adapted store_error/refusal tests plus replaced-state and legacy-state refusal cases.
- `REQ-008` (AC-7): tests/shared/test_execution_snapshot.py — updated `COMPONENT_KEYS` shape and per-component mismatch tests.
- `REQ-009` (AC-9): tests/db/test_schema_validation_per_database.py and tests/tools/test_check_db_separation.py — new dedup rows/cases.
- Determinism: concurrency tests use fixed seeds and bounded timeouts; mark repo-scan/slow tests per repository test policy.

## Documentation Impact
Yes (REQ-012). Target docs are named via `docs/00_index.md`'s Document References by Task
table rows — "DB layer spec (schema, ops, known issues)" (canonical store doc, operator
reference, migration policy, store overview), "MCP server implementation" (dispatch/transport
semantics), and the Agent tool-execution and operations-observability rows — matching the
`Implementation Target Files` documentation rows. The ADR rows (disposable-cache classification,
registered exceptions) are Reference Files only: this Plan changes no ADR text and writes no
approval statements (governance constraint from the issue's Constraints).

## Assumptions
- The production dedup store does not currently exist on disk: `ls /opt/llm/db/` (2026-11-21) shows no `mcp_dedup.sqlite`, so archive-and-recreate rollout has no live data to preserve in this environment.
- The `tool_call_state` name collision is cross-database only: the workflow database's 9-state `tool_call_state` (`scripts/db/schema_sql.py`) and the dedup ledger are distinct tables in distinct files; `TABLE_OWNERSHIP` is keyed per database, but its name-lookup helpers (`next((d for d, t in TABLE_OWNERSHIP.items() if name in t) ...)`, tools/check_db_separation.py:153,166) become ambiguous if two databases own the same table name — hence the ledger table rename to `dedup_call_state` (Design D-6, UNK-07).
- `dispatch_tool` remains the only side-effecting-call gatekeeper; the in-process `_duplicate_cache` overlay stays as a second layer (two-layer defense).
- Existing archived decisions stay binding: ADR-008 disposable-cache/archive-and-recreate and ADR-004 MCP-001/MCP-002 exceptions are carried forward unchanged unless the owner decides UNK-02/UNK-03.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Heartbeat interval and lease duration values, and where the installation marker lives under deployment mounts (issue Unresolved Questions) | No maintainer value decision recorded | Land with configurable defaults (`lease_seconds` default sized above observed handler maxima, marker co-located with the DB file at `db_path`); values configurable per REQ-010; maintainer confirms values at review | False |
| UNK-02 | Whether immutable terminal evidence and attempt history are consistent with the ADR-008 disposable-cache classification if evidence must outlive the cache (issue Unresolved Questions) | ADR-008 amendment requires maintainer approval; none exists | Plan keeps attempt history inside the same disposable store (bounded by the store's own retention), so no ADR change is implied; if evidence must outlive the store, that is an ADR-008 change filed separately with approval — do not pre-write it | False |
| UNK-03 | Whether retryable tools also fail closed after store loss, removing the ADR-004 MCP-001 overlay-only exception (owner decision, issue Unresolved Questions) | Owner decision | Implement the exception exactly as currently registered in ADR-004:249; an owner decision to remove it is a separate governance change | False |
| UNK-04 | Final state vocabulary for downstream issues (review_required / replay_unavailable / outcome_unknown) (issue Unresolved Questions) | Downstream issues (mcpai001, mcpdl004, mcpdl006) have no adopted vocabulary yet | This Plan decides it (Design D-5: acquisition-result vocabulary; `review_required` rejected in favor of `reconciliation_required`); downstream issues adopt it as their precondition | False |
| UNK-05 | Whether the current dispatcher already serializes acquisition in-process (issue Unresolved Questions: confirm by the concurrency test before changing storage) | No concurrency evidence yet | Phase 1 first step runs tests/shared/test_mcp_dedup_concurrency.py against current code and records the observed failure mode; storage change proceeds regardless because cross-process ownership is out of the overlay's scope | False |
| UNK-06 | Manifest requirement for `mcp_dedup` in `registry/manifests/db_schema_versions.yaml` (issue Target Files marks it Needs confirmation) | Generator currently has no dedup source; manifest semantics for disposable stores undefined | REQ-009 adds the entry because the store now has a stamped schema version; if the maintainer decides disposable stores stay out of the manifest, REQ-009's manifest half is amended via plan amend | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/shared/mcp_dedup.py | Store rewrite (schema, API, identity) | All MCP side-effecting dispatch paths; dispatcher, tests, validators | 7 | 2 | No deploy.sh change (store DB created by init_db.sh; config copy unchanged) |
| scripts/mcp_servers/dispatch.py | Caller adoption | All MCP tool calls through the dispatcher | 6 | 2 | None |
| scripts/shared/execution_snapshot.py | Added snapshot component | tool_audit payloads, snapshot comparison tests | 3 | 2 | None |
| config/mcp_dedup.toml | New keys | Config validation paths | 4 | 2 | deploy.sh:153-154 copy already covers the file; no change needed |
| tools/check_db_separation.py | New registration branch | CI gate for all DB configs | 11 | 2 | None |
| tools/generate_reference_table.py | New manifest source | Generated registry manifest | 8 | 2 | None |
| registry/manifests/db_schema_versions.yaml | Regenerated row | Manifest consumers (docs tables, checkers) | N/A (generated) | N/A | None |
| deploy/init_db.sh | New store init step | Production initialization path | 7 | 2 | init_db.sh is invoked after deploy.sh; new dedup step runs there |
| tests/shared/test_mcp_dedup.py | Suite rewrite | Dedup regression coverage | 6 | 2 | None |
| tests/shared/test_mcp_dedup_concurrency.py | New file | Concurrency regression coverage | N/A (new) | N/A | None |
| tests/shared/test_mcp_dedup_identity.py | New file | Identity regression coverage | N/A (new) | N/A | None |
| tests/mcp_servers/test_mcp_dispatch.py | Test adaptation | Dispatcher behavioral contracts | 6 | 2 | None |
| tests/mcp_servers/conftest.py | Fixture change | All mcp_servers suite fixtures | 2 | 2 | None |
| tests/shared/test_execution_snapshot.py | Pin update | Snapshot contracts | 2 | 1 | None |
| tests/db/test_schema_validation_per_database.py | Dedup harness update | Per-DB schema drift coverage | 2 | 1 | None |
| tests/tools/test_check_db_separation.py | New cases | Validator contracts | 0 | 1 | None |
| docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md | Canonical doc rewrite | Docs-vs-code consistency gate | 8 | 2 | None |
| docs/41_db/db_08_active_databases.md | Operator runbook | Operational procedure correctness | 3 | 2 | None |
| docs/41_db/db_01_architecture_and_schema-overview-and-config.md | Overview paragraph | Store classification docs | 9 | 2 | None |
| docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md | Migration policy rows | Schema policy docs | 16 | 2 | None |
| docs/22_mcp/mcp_03_03_transport-and-health.md | Dedup/transport section | MCP transport docs | 9 | 2 | None |
| docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md | Key-derivation claims | Agent tool-execution docs | 8 | 2 | None |
| docs/23_agent/agent_10_05_operations-and-observability-monitoring.md | Observability row | Monitoring docs | 3 | 2 | None |

## Design
Verification findings (Step 2, against current source 2026-11-21):
- The issue's stale references were confirmed and mapped to current locations: `docs/70_testing/01_test_strategy.md`, `docs/30_module_map/04_shared.md`, `docs/40_runbooks/*`, `docs/41_db/db_03_07` equivalents are `docs/41_db/db_03_07_*`, `docs/22_mcp/mcp_03_01_*`/`mcp_03_03_*`, `docs/40_shared/*`, `docs/90_deployment/*`; no "xfail expires after 30 days" policy exists (the constraint is `skills/python-test-and-fix/SKILL.md:23`).
- Both claimed ADR conflicts are already resolved in current ADR text: ADR-004:249 (MCP-001 retryable overlay-only `store_error`, explicitly covering "lost, or freshly recreated") and :250 (MCP-002 post-open write failure warning-only); ADR-008:141 (disposable cache; after recreation non-retryable tools are rejected until an operator resolves the state). The Plan therefore records them as superseded-governance, changes no ADR, and writes no approval statements.
- The lost-store sentinel gate already exists in code and tests (`DedupStore.__init__` `lost_or_recreated`; `resolve_lost_store()` writing `.mcp_dedup_resolved`), but nothing in `docs/` or `deploy/` documents the sentinel or `resolve_lost_store` — a real documentation gap confirmed by `rg`.
- `mcp_dedup` is absent from `tools/check_db_separation.py` (path-key regex `^(rag|session|workflow|eventbus)_db_path$`; config key is `db_path`) and from `registry/manifests/db_schema_versions.yaml`.
- Doc/code divergences confirmed: db_03_07 claims a `PRAGMA user_version = 1` stamp (code never stamps; the test pins `user_version == 0`); db_03_07:69, mcp_03_03:38, and agent_06_01:81/99 claim a `derive_idempotency_key(method, tool_name, args, uid)` derivation, while the key is caller-supplied (`X-Idempotency-Key` from `context.call_id`; `scripts/agent/tool_runner.py::_logical_call_id`); the function exists nowhere in `scripts/`.
- `DedupStore.__init__`'s shape-mismatch `RuntimeError` escapes `dispatch.py::_dedup_context`'s caught exception set, bypassing the audited taxonomy.
- Validation baseline: radon flags `load_dedup_config` at C(18) and `dispatch_tool` at F(44); bandit clean on the three subject files; vulture lists the soon-to-be-removed `mark_interrupted`/`classify_interrupted`/`resolve_lost_store` as currently unused outside tests.

Consumer-scan dispositions (`tools/scan_change_consumers.py` seeds `scripts/shared/mcp_dedup.py`, `DedupStore`, `record_pending`, `resolve_lost_store`, `DEDUP_SENTINEL_NAME`, `purge_expired`, `tool_call_state`, `snapshot_json`):
- Target rows: all rows above (store, dispatcher, snapshot, config, validators, generator+manifest, deploy init, tests, docs).
- Reference rows: `scripts/agent/tool_runner.py`, `scripts/agent/tool_audit.py`, `scripts/agent/production_config_validator.py`, `scripts/mcp_servers/server.py`, `scripts/shared/schema_fingerprint.py`, `scripts/shared/tool_constants.py`, `scripts/db/schema_sql.py`, `deploy/deploy.sh` — read-only consumers confirmed unaffected by the API change (they call no removed method; deploy copy is file-level).
- `scripts/agent/workflow/tool_call_state_ops.py`, `scripts/agent/workflow/workflow_engine.py` (seed `tool_call_state`): not affected — they operate on the workflow database's distinct `tool_call_state` table (`scripts/db/schema_sql.py`); only the table-name similarity was confirmed, no shared code path.
- `docs/10_adr/*` ADR citation rows (adr-test-citation candidates): governance references only; handled as Reference Files (no ADR edits).

Design decisions:
- D-1 (atomic claim): acquisition is one `BEGIN IMMEDIATE` transaction: read row (if any), classify, and either insert the pending row with owner + lease or return the non-acquisition result. Handler execution happens outside any open transaction; ownership is maintained by lease renewal, not by holding the write lock.
- D-2 (leases and identity): `owner_id` is a per-call acquisition nonce; heartbeat (`renew_lease`) extends `lease_expires_epoch` only while `status='pending' AND owner_id` matches; expiry alone yields `reconciliation_required` (the row becomes `interrupted` with outcome-unknown semantics) and never authorizes execution — a further attempt requires an explicit reconciliation/acquisition path gated by `max_attempts`.
- D-3 (immutable terminal evidence): terminal rows are write-once; SQL finalization statements are `UPDATE ... WHERE status='pending' AND owner_id=?` and the code raises `DedupLeaseConflict` on 0-row results; repeat attempts append to `call_attempt_history` instead of touching the ledger row; `purge_expired` deletes only terminal rows and history older than `retention_days` (reconciliation of UNK-02: history lives in the same disposable store, so no new persistence class is introduced).
- D-4 (identity and start states): `store_meta` single-row identity (store UUID, generation, schema fingerprint, config fingerprint, created_epoch) + `PRAGMA user_version = 1` stamp + external installation marker file written atomically at creation; open-time classification: first_initialization (no DB, no marker), healthy (DB + valid identity + matching fingerprints), lost (marker present, DB absent), replaced (DB present with foreign store UUID), legacy_or_unverified (DB present without identity row or with `user_version = 0`), schema_mismatch (fingerprint drift). Operator resolution: validates the state, archives the old file (`<path>.corrupt-<ts>` style archive consistent with ADR-008 Decision 22), creates a new generation, records the decision durably (log line + new identity's generation counter); `touch()` recovery removed.
- D-5 (vocabulary, resolving UNK-04): acquisition results `acquired | replay_completed | in_progress | reconciliation_required | outcome_unknown | contract_mismatch | replay_unavailable`; ledger states remain `pending | completed | failed | interrupted`; error taxonomy keeps `dedup_store_error`. `review_required` is not adopted.
- D-6 (table rename): the dedup ledger table is renamed `dedup_call_state` at recreation to avoid a cross-database ownership-name collision with the workflow database's `tool_call_state` in `tools/check_db_separation.py`'s name-lookup helpers (:153, :166); the old name disappears with the recreated store (no migration per ADR-008 Decision 22).
- D-7 (dispatcher mapping): new start states map onto the existing taxonomy — non-retryable tools refused (`dedup_store_error`) in `lost`/`replaced`/`legacy_or_unverified`/`schema_mismatch`; retryable tools degrade overlay-only with the audited `store_error` marker (ADR-004 MCP-001 unchanged); store-unavailable-open path additionally catches the typed identity errors so the `RuntimeError` leak is closed; MCP-002 warning-only behavior switches from `RuntimeWarning` to a structured `logger.warning`.
- D-8 (snapshot compatibility): `execution_snapshot` gains a `dedup` component (store generation + schema fingerprint) making the snapshot 4-component; `tool_audit` payloads carry it unchanged.
- Rollout (no migration): existing incompatible databases are rejected by the shape/fingerprint/identity gate; rollout is archive-and-recreate. Production currently has no dedup store file, so the rollout is a clean first initialization after deploy.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`. Phases that land together in one commit cannot be validated alone: declare them
as a unit; `N/A` is only for a Plan whose every phase passes validation alone.

1. **Phase 1: Test-first evidence (no production change)**
   - [ ] Write tests/shared/test_mcp_dedup_concurrency.py and tests/shared/test_mcp_dedup_identity.py; run them against current code and record the confirmed failing behaviors (double-acquire, force-reset evidence loss, loss indistinguishable from first start) (REQ-001..REQ-003, REQ-005..REQ-007; UNK-05 answer recorded in Execution Status notes).
2. **Phase 2: Store core and identity**
   - [ ] Rewrite scripts/shared/mcp_dedup.py: new `_SCHEMA`/`_INDEXES`/`_CANONICAL_DDL` (`dedup_call_state`, `store_meta`, `call_attempt_history`), `try_acquire_execution`, owner-conditional `renew_lease`/`record_completed`/`record_failed`/`mark_interrupted` with 1-row assertions, `force=True` removal, identity stamping, start-state classification, typed error types, operator resolution replacing `resolve_lost_store`/`touch()`, retention-scoped purge (REQ-001..REQ-007).
   - [ ] Add `lease_seconds` and `max_attempts` to config/mcp_dedup.toml and the loader validation in scripts/shared/mcp_dedup.py (REQ-010).
   - [ ] Add the dedup component to scripts/shared/execution_snapshot.py (REQ-008).
3. **Phase 3: Dispatcher, validators, deployment, and tests co-landing**
   - [ ] Adopt the acquisition API in scripts/mcp_servers/dispatch.py (remove lookup+pending+force patterns; map start states to `dedup_store_error`; structured store-write warnings) (REQ-001, REQ-006).
   - [ ] Register `mcp_dedup` in tools/check_db_separation.py and add the manifest source in tools/generate_reference_table.py; regenerate registry/manifests/db_schema_versions.yaml (REQ-009).
   - [ ] Add the dedup store initialization step to deploy/init_db.sh (REQ-011).
   - [ ] Update tests/shared/test_mcp_dedup.py, tests/mcp_servers/test_mcp_dispatch.py, tests/mcp_servers/conftest.py, tests/shared/test_execution_snapshot.py, tests/db/test_schema_validation_per_database.py, tests/tools/test_check_db_separation.py to the new contract; Phase 1 tests must now pass (REQ-001..REQ-009; AC-1..AC-10).
4. **Phase 4: Documentation reconciliation**
   - [ ] Update docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md, docs/41_db/db_08_active_databases.md, docs/41_db/db_01_architecture_and_schema-overview-and-config.md, docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md, docs/22_mcp/mcp_03_03_transport-and-health.md, docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md, docs/23_agent/agent_10_05_operations-and-observability-monitoring.md per the new contract and the stale-claim list in Design (REQ-012; AC-11).

### Release units
**Unit**: dedup-lease-identity-rollover | **Phases**: 2, 3 | **Reason**: the new DDL and store API break `dispatch.py`, the per-database schema-drift harness, the fixtures, and the checkers until they land in the same change; validating Phase 2 alone runs against callers still using `lookup`+`record_pending` and the single-table canonical shape.
**Unit**: docs-sync | **Phases**: 3, 4 | **Reason**: the canonical docs and the docs-vs-code consistency checker must not validate a release whose docs describe removed APIs (`record_pending(force=True)`, `derive_idempotency_key`, unstamped `user_version`) while Phase 2/3 have already removed them.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/mcp_dedup.py | Unit + concurrency | `uv run pytest tests/shared/test_mcp_dedup.py tests/shared/test_mcp_dedup_concurrency.py tests/shared/test_mcp_dedup_identity.py` | All pass; Phase 1 failures confirmed before Phase 2 |
| scripts/mcp_servers/dispatch.py | Integration | `uv run pytest tests/mcp_servers/` | store_error/refusal matrix passes with new start states; no lookup+record pattern remains (`rg -n "record_pending\|force=True" scripts/` → store-internal only, then none) |
| scripts/shared/execution_snapshot.py | Unit | `uv run pytest tests/shared/test_execution_snapshot.py` | 4-component pins pass; dedup component mismatch detected |
| tools/check_db_separation.py, tests/tools/test_check_db_separation.py | Gate | `uv run python tools/check_db_separation.py` | Exit 0 with `mcp_dedup` registered |
| tools/generate_reference_table.py, registry/manifests/db_schema_versions.yaml | Generator drift | `uv run python tools/generate_reference_table.py --check` | Manifest-vs-source check passes with a `mcp_dedup` row |
| scripts/db harness | Schema drift | `uv run pytest tests/db/test_schema_validation_per_database.py` | New multi-table canonical shape validated for `mcp_dedup` |
| deploy/init_db.sh | Script integration | `uv run pytest tests/deploy/` + sandboxed `bash deploy/init_db.sh` against a temp DB dir | Store created with identity, stamp, marker |
| Full static gate | Static | `uv run ruff check`, `uv run mypy`, `uv run python tools/check_workitem_structure.py`, import-contract gate per `rules/toolchain.md` | Clean on changed files |
| Whole suite | Regression | `uv run pytest` (plus CI sequence per `rules/toolchain.md`) | No regressions |
| docs targets | Docs gate | Applicable `docs/` checker per `routing.md` Tools → "When to run which tool" | No stale claims in the changed docs |

## Risks
- **Risk**: SQLite `BEGIN IMMEDIATE` serializes writers but cross-process correctness depends on `busy_timeout` and single-writer semantics → **Mitigation**: multi-connection and multi-process tests in Phase 1/3 pin the guarantee; acquisition transactions stay short (no handler execution inside); explicit `timeout` on connect.
- **Risk**: DDL change forces archive-and-recreate; live evidence is discarded → **Mitigation**: ADR-008 disposable-cache semantics already accept this; production currently has no store file (confirmed 2026-11-21), so rollout is a clean creation; the archive-and-recreate operator procedure is documented in db_08 before deploy.
- **Risk**: `dispatch_tool` already sits at cyclomatic complexity F(44); adopting a richer acquisition vocabulary could grow it → **Mitigation**: extract the dedup decision into a module-level helper in dispatch.py; radon must not worsen (validation gate).
- **Risk**: The 100-caller concurrency test can become a slow/flaky suite member → **Mitigation**: bounded fixed-duration test with seeded scheduling, no real sleeps beyond one short lease; classify per repository slow-test policy.
- **Risk**: The new snapshot component changes audit payload shape consumed downstream (tool_audit JSON) → **Mitigation**: additive component only; tool_audit writes the payload blob without key assumptions (confirmed read-only consumer); tests pin the payload passthrough.
- **Risk**: Governance drift: immutable evidence/attempt history could be read as contradicting ADR-008 disposable-cache wording, and the MCP-001 exception stays contentious (UNK-02/UNK-03) → **Mitigation**: Plan implements current ADR text unchanged, writes no approval statements, and stops to report rather than resolve a conflict if implementation reveals a genuine contradiction (issue AI Implementation Instruction).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| Phase 1 | Test-first evidence (concurrency + identity) | Pending | — | — | Records the UNK-05 answer |
| Phase 2 | Store core and identity (mcp_dedup.py, config keys, snapshot) | Pending | — | — | |
| Phase 3 | Dispatcher, validators, deployment, tests | Pending | — | — | Co-lands with Phase 2 as release unit dedup-lease-identity-rollover |
| Phase 4 | Documentation reconciliation | Pending | — | — | Release unit docs-sync |

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
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261121-083728
- **Related target files**: scripts/shared/mcp_dedup.py, scripts/mcp_servers/dispatch.py, scripts/shared/execution_snapshot.py, config/mcp_dedup.toml, tools/check_db_separation.py, tools/generate_reference_table.py, registry/manifests/db_schema_versions.yaml, deploy/init_db.sh, tests/shared/test_mcp_dedup.py, tests/shared/test_mcp_dedup_concurrency.py, tests/shared/test_mcp_dedup_identity.py, tests/mcp_servers/test_mcp_dispatch.py, tests/mcp_servers/conftest.py, tests/shared/test_execution_snapshot.py, tests/db/test_schema_validation_per_database.py, tests/tools/test_check_db_separation.py, docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md, docs/41_db/db_08_active_databases.md, docs/41_db/db_01_architecture_and_schema-overview-and-config.md, docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md, docs/22_mcp/mcp_03_03_transport-and-health.md, docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md, docs/23_agent/agent_10_05_operations-and-observability-monitoring.md — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; Evidence (:310,:390) | scripts/shared/mcp_dedup.py | Phase 2 | AC-1, AC-2, AC-6 | tests/shared/test_mcp_dedup_concurrency.py; tests/shared/test_mcp_dedup.py | Planned |
| REQ-001 | Target Files or Areas | scripts/mcp_servers/dispatch.py | Phase 3 | AC-1, AC-6 | tests/mcp_servers/test_mcp_dispatch.py | Planned |
| REQ-002 | Required Changes 2 | scripts/shared/mcp_dedup.py | Phase 2 | AC-1..AC-3 | tests/shared/test_mcp_dedup_concurrency.py | Planned |
| REQ-002 | Required Changes 2 | tests/mcp_servers/conftest.py | Phase 3 | AC-1 | tests/mcp_servers/conftest.py fixtures | Planned |
| REQ-003 | Required Changes 3 | scripts/shared/mcp_dedup.py | Phase 2 | AC-3 | tests/shared/test_mcp_dedup.py lease tests | Planned |
| REQ-004 | Required Changes 4 | scripts/shared/mcp_dedup.py | Phase 2 | AC-2 | tests/shared/test_mcp_dedup.py immutability tests | Planned |
| REQ-004 | Required Changes 4 | tests/db/test_schema_validation_per_database.py | Phase 3 | AC-9 | tests/db/test_schema_validation_per_database.py | Planned |
| REQ-005 | Required Changes 6; Implementation Intent | scripts/shared/mcp_dedup.py | Phase 2 | AC-4, AC-5 | tests/shared/test_mcp_dedup_identity.py | Planned |
| REQ-005 | Target Files (deployment initialization) | deploy/init_db.sh | Phase 3 | AC-10 | tests/deploy/ + sandboxed init_db.sh run | Planned |
| REQ-006 | Required Changes 7; Constraints (no tolerant start) | scripts/shared/mcp_dedup.py | Phase 2 | AC-4, AC-5 | tests/shared/test_mcp_dedup_identity.py | Planned |
| REQ-006 | Required Changes 7 | scripts/mcp_servers/dispatch.py | Phase 3 | AC-5 | tests/mcp_servers/test_mcp_dispatch.py | Planned |
| REQ-006 | Target Files or Areas | docs/22_mcp/mcp_03_03_transport-and-health.md | Phase 4 | AC-11 | docs checker | Planned |
| REQ-006 | Observability of new states | docs/23_agent/agent_10_05_operations-and-observability-monitoring.md | Phase 4 | AC-11 | docs checker | Planned |
| REQ-007 | Required Changes 8 | scripts/shared/mcp_dedup.py | Phase 2 | AC-5 | tests/shared/test_mcp_dedup_identity.py rollover tests | Planned |
| REQ-007 | Operator runbook gap (rg 2026-11-21) | docs/41_db/db_08_active_databases.md | Phase 4 | AC-10, AC-11 | docs checker | Planned |
| REQ-008 | Required Changes 4 (execution compatibility) | scripts/shared/execution_snapshot.py | Phase 2 | AC-7 | tests/shared/test_execution_snapshot.py | Planned |
| REQ-009 | Target Files (manifest); check_db_separation evidence :55,:111 | tools/check_db_separation.py | Phase 3 | AC-9 | tests/tools/test_check_db_separation.py | Planned |
| REQ-009 | Target Files (generated manifest) | tools/generate_reference_table.py | Phase 3 | AC-9 | generate_reference_table.py --check | Planned |
| REQ-009 | Target Files (generated manifest) | registry/manifests/db_schema_versions.yaml | Phase 3 | AC-9 | generate_reference_table.py --check | Planned |
| REQ-010 | Unresolved Questions (lease values) | config/mcp_dedup.toml | Phase 2 | AC-8 | tests/shared/test_mcp_dedup.py loader tests | Planned |
| REQ-011 | Target Files (deployment initialization) | deploy/init_db.sh | Phase 3 | AC-10 | tests/deploy/ | Planned |
| REQ-012 | Documentation Impact | docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md | Phase 4 | AC-11 | docs checker | Planned |
| REQ-012 | db_01:36 store description | docs/41_db/db_01_architecture_and_schema-overview-and-config.md | Phase 4 | AC-11 | docs checker | Planned |
| REQ-012 | db_03:68,76,87 recreation rows | docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md | Phase 4 | AC-11 | docs checker | Planned |
| REQ-012 | agent_06_01:81,99 stale key-derivation claims | docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md | Phase 4 | AC-11 | docs checker | Planned |
| REQ-001..REQ-007 | Testing Expectations | tests/shared/test_mcp_dedup.py | Phase 3 | AC-1..AC-5 | this file | Planned |
| REQ-001..REQ-003 | AI Implementation Instruction (test-first) | tests/shared/test_mcp_dedup_concurrency.py | Phase 1 | AC-1..AC-3 | this file (failing first) | Planned |
| REQ-005..REQ-007 | AI Implementation Instruction (loss/replacement) | tests/shared/test_mcp_dedup_identity.py | Phase 1 | AC-4, AC-5 | this file (failing first) | Planned |
| REQ-001, REQ-006 | Testing Expectations (dispatcher) | tests/mcp_servers/test_mcp_dispatch.py | Phase 3 | AC-1, AC-5, AC-6 | this file | Planned |
| REQ-005 | Fixture initialization path | tests/mcp_servers/conftest.py | Phase 3 | AC-5 | tests/mcp_servers suite | Planned |
| REQ-008 | Component pins (:88-97) | tests/shared/test_execution_snapshot.py | Phase 3 | AC-7 | this file | Planned |
| REQ-009 | Validator cases | tests/tools/test_check_db_separation.py | Phase 3 | AC-9 | this file | Planned |
