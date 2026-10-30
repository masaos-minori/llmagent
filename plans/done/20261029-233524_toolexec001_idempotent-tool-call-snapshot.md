# Idempotent Tool Calls With Execution Snapshots

Status: Draft
Created: 2026-10-29

Task classification: Path B (Medium feature: cross-module contract change, new durable
storage, migration work, restart-behavior semantics). Path B workflow applied
(`skills/issue-to-plan/workflow-path-b.md`).

## Goal
Make MCP tool-call dedup durable and replay-aware: deterministic content-derived
idempotency keys, a persistent dedup store that survives server-process restarts, execution
snapshots recorded at call start, and explicit replay rules for interrupted calls
(retryable replays as a new turn; non-retryable is never auto-retried).

## Priority
P1. The dedup gap is an active correctness hole: a server-process restart silently re-dispatches
side-effecting calls, and the reserved audit snapshot field is permanently null.

## Scope
In scope:
- Deterministic `X-Idempotency-Key` derivation in the HTTP transport layer.
- Durable dedup store (`/opt/llm/db/mcp_dedup.sqlite`) enforced at the shared
  `dispatch_tool` entry point used by every MCP server process, replacing the per-process
  in-memory `_duplicate_cache` as the source of truth.
- Execution-snapshot builder (`/opt/llm/DEPLOYED_REV` + git SHA + `config/*.toml` hashes +
  schema versions) recorded in dispatch audit and the existing `tool_audit` snapshot fields.
- Workflow-side tool-call lifecycle state (`pending`/`completed`/`failed`) in
  `workflow.sqlite` landed through the dbmig001 migration framework.
- Per-tool `retry_class` config (`retryable` / `non_retryable`) with the owner's initial
  classification.
- Replay semantics: snapshot match + retryable → replay the same key as a new turn;
  snapshot mismatch → fresh attempt; non-retryable → surfaced as unreplayable, never
  auto-retried.
- Retention/TTL cleanup for dedup rows.
- Tests (unit + integration) and docs updates listed below.

Out of scope:
- Per-server dedup inside individual MCP servers. Every server-side tool execution enters
  the shared `dispatch_tool` (`scripts/mcp_servers/dispatch.py:152`) imported by each server
  process, so one durable store behind that shared entry covers all dispatch-capable
  servers without N-fold code; server modules stay unchanged.
- EventBus ACK/NACK idempotency semantics (owned by ADR-006; already durable).
- Tool-loop guard behavior (`scripts/agent/tool_loop_guard.py`; owned by the toolhint001
  plan `plans/20261029-215111_*`).
- Local subprocess tools that bypass HTTP dispatch (`scripts/shared/web_search.py`); they
  are classified non-retryable and never auto-replayed.
- Operator replay UI or admin endpoints.

## Background
- `scripts/mcp_servers/dispatch.py:102` keeps `_duplicate_cache: dict[str, dict[str, Any]]`,
  the only dedup store: in-memory, per-process, wiped on restart. `dispatch_tool`
  (`dispatch.py:152`) is a library imported by each MCP server process (e.g.
  `scripts/mcp_servers/file/write_server.py:30,209`; also read/delete/git/github/cicd/
  rag_pipeline/web_search servers), so every server holds its own cache. A completed-call
  hit (`:125-128`) returns the cached result; a pending record for a crashed in-flight call
  is only noted as a duplicate attempt (`:190-201`) and never resolved.
- `scripts/shared/http_transport.py:170-186` `build_auth_context` generates the fallback
  `X-Idempotency-Key` as `f"{http_method}:{tool_name}:{uuid.uuid4()}"` — random per call.
- `scripts/agent/tool_audit.py:159` accepts `execution_snapshot=None` and `:188` always
  writes `"execution_snapshot_json": None`; no producer exists repo-wide.
- `scripts/db/schema_sql.py:172-214` workflow tables include `tasks.idempotency_key`
  UNIQUE (`:179`), a durable task-level anchor; `scripts/agent/workflow/idempotency_ops.py:14-29`
  (`begin_stage_if_new`, `record_processed_event`) dedups stage events only.
- `deploy.sh` already writes `/opt/llm/DEPLOYED_REV` (source SHA + `config/config.toml` +
  `config/agent.toml` hashes), the natural snapshot seed.

## Problem
Idempotency is process-local and keys are random. After any server-process or agent
restart:
re-issuing an identical call produces a new key, so a previously completed side-effecting
call (file write, git action, github action) can execute a second time, and an interrupted
in-flight call cannot be distinguished from a fresh call. Replay decisions therefore cannot
depend on what code/config was running when the call first started.

## Reason for Change
The issue (`issues/20261029-104503_toolexec001_*`) requires: deterministic keys, a durable
dedup store, snapshot-at-call-start semantics, and a defined interrupted-call replay
policy. The audit schema already reserves snapshot fields (toolaudit002/003 landed), so the
missing piece is the producer plus the durable store.

## Implementation Intent
- Make call identity a function of call content so identity survives process boundaries.
- Make the dedup state durable in a shared store behind the single `dispatch_tool` entry
  point every server process traverses.
- Bind each dispatch attempt to the execution snapshot so replay is decided by snapshot
  equality, not blind retry.
- Keep existing dispatcher fast paths and audit behavior, with the durable store as their
  backing truth.

## Requirements
- `REQ-001`: Deterministic key: `build_auth_context` fallback becomes
  `sha256(method + tool_name + canonical-JSON(args) + uid)` formatted to fit the existing
  house pattern `^[A-Za-z0-9_-]{1,64}$` (`scripts/shared/auth_base.py:315`); a
  caller-supplied key still takes precedence.
- `REQ-002`: Durable store `scripts/shared/mcp_dedup.py` over `/opt/llm/db/mcp_dedup.sqlite`
  (WAL, busy timeout, short transactions, `PRAGMA user_version` bootstrap; safe for
  concurrent access from multiple server processes): states `pending` → `completed` /
  `failed`; completed rows return the stored result (size-capped; over-cap stores a result
  hash only); a `pending` row older than `mcp_pending_timeout_minutes` is classified
  interrupted. The module loads and validates its settings from a new
  `config/mcp_dedup.toml` via the shared config loader.
- `REQ-003`: `dispatch_tool` replaces `_duplicate_cache` (which today exists per server
  process) as truth: completed hit (kept as a per-process fast-path overlay fed from the
  store) reads from the durable store; the duplicate-attempt audit path (`:190-201`) is
  preserved; store writes never span the backend call.
- `REQ-004`: Snapshot builder `scripts/shared/execution_snapshot.py`: reads
  `/opt/llm/DEPLOYED_REV` (tolerantly; missing → `unknown`), git commit SHA, hashes of all
  `config/*.toml`, and schema versions; equality test defined per component; recorded in the
  dispatch audit record and serialized into `tool_audit` `execution_snapshot_json`.
- `REQ-005`: Replay policy at the store lookup: `completed` + snapshot match → return
  stored result; `completed` + snapshot mismatch → allow a fresh attempt (new dispatch,
  audited as `snapshot_mismatch`); `interrupted` + `retryable` → replay the same key
  (re-execution); `interrupted` + `non_retryable` → refuse auto-replay, record
  `dedup_state=unreplayable`, and surface the status into the turn context.
- `REQ-006`: `retry_class` is config-declared per tool in `config/mcp_dedup.toml` with
  defaults fixed by the owner classification: dispatch-capable HTTP tools retryable
  (file_write, file_delete, git, github, mdq, rag_pipeline); external-side-effect tools
  non-retryable (shell, web_search).
- `REQ-007`: Workflow lifecycle: new `tool_call_state` and `execution_snapshots` tables in
  `workflow.sqlite` land only via the dbmig001 migration framework (registered step +
  baseline), never ad-hoc DDL.
- `REQ-008`: Interrupted calls replay as a new turn: turn entry detects pending
  `tool_call_state` rows for the task and injects a control message so the LLM re-issues
  the call under the same key; non-retryable pending rows surface as an unreplayable status
  message instead.
- `REQ-009`: Retention: completed/failed rows older than `mcp_dedup_retention_days` are
  purged by an opportunistic sweep inside `dispatch_tool` (at most one sweep per process
  per configured interval); interrupted detection uses the pending timeout at read time.
- `REQ-010`: Preserved behavior: caller-supplied keys, dispatcher auth/authz flow, tool
  audit contract (toolaudit003 wiring), `tasks.idempotency_key` semantics (task UUID stays;
  new tool-call key is content-derived and separate).

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed on 2026-10-29: every row exists-or-is-new-with-evidence, is linked to a Plan requirement, and is `Verified`; all modified-file paths re-confirmed against `HEAD c5a8285dd` (test/module paths corrected during drafting: `workflow_engine.py` not `executor.py`; `tests/shared/test_http_transport.py`, `tests/shared/test_tool_executor_routing.py`, `tests/mcp_servers/test_mcp_dispatch.py`, `tests/agent/workflow/test_workflow_engine.py`; no `test_http_transport_detailed.py` or `test_dispatcher_integration.py` exists). Architecture fact corrected during drafting: `dispatch_tool` is a shared library entry imported by each MCP server process (e.g. `file/write_server.py:209`), not a standalone daemon; the durable store is therefore multi-process shared. `check_workitem_structure.py` reports no findings. `check_plan_target_overlaps.py` adds one pair: `scripts/db/schema_sql.py` shared with Frozen Plan `plans/20261029-214108_dbmig001_*` — sequenced in both plans (dbmig001 ledger DDL lands first; this Plan's Phase 4 registers its step through that framework). Two further pairs with Frozen Plan `plans/20261029-215111_toolhint001_*`: `scripts/agent/llm_turn_runner.py` and `tests/agent/test_llm_turn_runner.py` — designs verified non-conflicting (toolhint001 changes guard wiring for unavailable tool results; this Plan adds pending-call control-message injection at turn entry; distinct wiring points in the runner). whichever lands first, the other rebases.)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/http_transport.py` | Deterministic fallback key in `build_auth_context` | REQ-001 core behavior change | REQ-001, REQ-010 | `http_transport.py:170-186` uuid4 fallback | `tests/shared/test_http_transport.py`, `tests/shared/test_tool_executor_routing.py` | Verified |
| `scripts/shared/mcp_dedup.py` | New durable dedup store module + validated loading of `config/mcp_dedup.toml` | Dedup must survive restart and be shared across all server processes | REQ-002, REQ-005, REQ-006, REQ-009 | New module; no `mcp_dedup` name repo-wide (0 hits); shared-layer placement matches `scripts/shared/mcp_config.py` precedent (import contract: shared layer usable by both agent and servers) | `tests/shared/test_mcp_dedup.py` | Verified |
| `scripts/shared/execution_snapshot.py` | New snapshot builder/comparator | Snapshot-at-call-start + replay equality decision | REQ-004, REQ-005 | New module; `deploy.sh` writes `/opt/llm/DEPLOYED_REV` | `tests/shared/test_execution_snapshot.py` | Verified |
| `scripts/mcp_servers/dispatch.py` | `dispatch_tool` swaps `_duplicate_cache` truth to the durable store; records snapshot in audit; applies replay policy; opportunistic retention sweep | `dispatch_tool` is the shared entry point every server process uses | REQ-003, REQ-005, REQ-009 | `dispatch.py:152` `dispatch_tool`, `:102`, `:125-128`, `:156-215`, `:190-201`, audit region `:227-240`; server call site example `scripts/mcp_servers/file/write_server.py:209` | `tests/mcp_servers/test_mcp_dispatch.py` | Verified |
| `scripts/agent/tool_audit.py` | Serialize the populated snapshot + dedup state | Fields exist (`:159`, `:188`) but no producer | REQ-004 | `tool_audit.py:159`, `:188` | `tests/agent/test_tool_audit.py` (toolaudit003 tests exist) | Verified |
| `scripts/db/schema_sql.py` | Add `tool_call_state` + `execution_snapshots` DDL to workflow tables | Workflow lifecycle persistence | REQ-007, REQ-008 | `schema_sql.py:172-214` tables, `:25` `WORKFLOW_SCHEMA_VERSION` | `tests/db/` migration harness (dbmig001-owned) | Verified |
| `scripts/agent/workflow/state_store.py` | Task-scoped tool-call state read/write helpers | Turn entry needs pending-call detection | REQ-008 | `state_store.py` owns workflow persistence per `docs/23_agent/agent_04_03_*:71` | `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_state_store.py` | Verified |
| `scripts/agent/workflow/workflow_engine.py` | Pending-call detection + replay-as-new-turn control injection | Turn execution semantics live here | REQ-008 | `scripts/agent/workflow/workflow_engine.py` turn/stage flow (`idempotency_ops.py` stage hooks) | `tests/agent/workflow/test_workflow_engine.py` | Verified |
| `scripts/agent/llm_turn_runner.py` | Propagate the control message into the turn context | Hand-off point between executor and LLM | REQ-008 | `llm_turn_runner.py:62` chain entry | `tests/agent/test_llm_turn_runner.py` | Verified |
| `config/mcp_dedup.toml` | New: shipped defaults for `db_path`, `retention_days`, `pending_timeout_minutes`, and the `retry_class` map (owner classification) | Project rule: policy is config, not hardcoded; follows the existing per-concern `config/` file pattern (`eventbus.toml`, `*_mcp_server.toml`) | REQ-002, REQ-006, REQ-009 | `config/` layout verified; loaded via `scripts/shared/config_loader.py` from the `mcp_dedup.py` row | `tests/shared/test_mcp_dedup.py` config-validation cases | Verified |
| `docs/22_mcp/mcp_03_03_transport-and-health.md` | Document deterministic key + durable dedup at dispatcher | Transport contract doc must match shipped behavior | REQ-001–REQ-003, REQ-005 | Current transport/idempotency text | docs checkers | Verified |
| `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` | Document snapshot recording + dedup states in the trace | Tracing doc covers the audit record | REQ-004 | Existing tracing pipeline doc | docs checkers | Verified |
| `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Update `:71` key statement + new workflow tables | Current text states task-key UUID semantics only | REQ-007, REQ-010 | `agent_04_03_*:71` verified text | docs checkers | Verified |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | New: both workflow tables, mcp_dedup bootstrap, retention, replay decision table | DB docs domain for new stores | REQ-002, REQ-007, REQ-009 | New file; `docs/41_db/` domain layout | docs checkers | Verified |
| `tests/shared/test_http_transport.py` | Adapt key assertions to determinism; add cross-process determinism test | Existing suite covers the transport/key behavior | REQ-001 | Existing file | — | Verified |
| `tests/shared/test_tool_executor_routing.py` | Adapt `X-Idempotency-Key` propagation assertions | Existing suite asserts current header behavior | REQ-001 | `test_tool_executor_routing.py` asserts `X-Idempotency-Key` | — | Verified |
| `tests/shared/test_mcp_dedup.py` | New: state machine, reopen durability, TTL purge, interrupted classification | Regression coverage for the new store | REQ-002, REQ-005, REQ-009 | New module | — | Verified |
| `tests/shared/test_execution_snapshot.py` | New: build/equality/mismatch per component, missing DEPLOYED_REV | Regression coverage | REQ-004 | New module | — | Verified |
| `tests/mcp_servers/test_mcp_dispatch.py` | Durable-dedup integration cases (completed hit after reopen, replay refuse/allow) replacing `_duplicate_cache` fixture assumptions | Existing integration surface for `dispatch_tool` | REQ-003, REQ-005 | Existing file; tests isolate `dispatch.py._duplicate_cache` (`:14`, `:101-108`, `:136`) | — | Verified |
| `tests/agent/workflow/test_workflow_engine.py` | Pending detection + replay-as-new-turn integration | Turn semantics regression | REQ-008 | Existing file | — | Verified |
| `tests/agent/test_llm_turn_runner.py` | Control-message propagation | Turn semantics regression | REQ-008 | Existing file | — | Verified |

Total target files: 21.

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/dispatch.py` | Issue instruction: read before editing; cache/audit paths to preserve | `scripts/mcp_servers/dispatch.py` row |
| `scripts/shared/http_transport.py` | Key generation site; auth context contract | `scripts/shared/http_transport.py` row |
| `scripts/agent/tool_audit.py` | Reserved snapshot fields + toolaudit003 wiring (`TOOL_AUDIT_ENABLED`, `:46-51`) | `scripts/agent/tool_audit.py` row |
| `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` | Migration framework API/ledger this plan's Phase 4 depends on | REQ-007 |
| `scripts/shared/auth_base.py` | House key pattern `:315` the new key must fit | REQ-001 |
| `deploy.sh` | DEPLOYED_REV format the snapshot builder reads (tolerantly; deploy.sh unchanged by this plan) | REQ-004 |
| `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Current task-key semantics to preserve | REQ-010 |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Workflow-engine ownership of retry/idempotency (`:150`, `:277`) | REQ-008 |

## Acceptance Criteria
- AC-1 (REQ-001): Identical (method, tool, args, uid) produces the identical key in two
  fresh processes; any payload difference produces a different key; caller-supplied keys
  unchanged.
- AC-2 (REQ-002, REQ-003): A completed call's result is retrievable from the durable store
  after the server process that executed it restarts (the store is shared across server
  processes); the duplicate-attempt audit path still fires.
- AC-3 (REQ-005): A pending row past the timeout is classified interrupted; replay is
  allowed only for retryable tools with a matching snapshot; snapshot mismatch yields a
  fresh audited attempt; non-retryable interrupted calls are recorded unreplayable and are
  never re-dispatched automatically.
- AC-4 (REQ-004): Every dispatch attempt records a snapshot (or explicit `unknown`) in the
  audit record; `tool_audit` `execution_snapshot_json` is populated when provided.
- AC-5 (REQ-008): A turn crash leaves a pending `tool_call_state` row; the next turn
  detects it and re-issues the call as a new turn under the same key (integration-verified
  with mocked transport).
- AC-6 (REQ-009): Rows past retention are purged; completed results are not purged early.
- AC-7 (REQ-007): New tables appear only via a registered dbmig001 migration + updated
  baseline; fresh init and upgrade both converge; existing rows preserved.

## Tests
- Unit: key determinism (incl. cross-process), snapshot build/equality/mismatch/unknown,
  dedup state machine, TTL purge, interrupted classification, config validation (invalid
  values fail loudly), retry_class default map.
- Integration: dispatcher completed-hit after simulated reopen; interrupted replay allowed
  for retryable and refused for non-retryable; pending detection → control message → same
  key re-issue (mocked transport); retention sweep in the dispatcher loop.
- Migration: workflow v-baseline → new version with data preserved (dbmig001 harness).
- Regression: existing transport/dispatcher/audit/workflow suites stay green with adapted
  assertions.
- Suite commands: `uv run pytest tests/shared tests/mcp_servers tests/agent`,
  `uv run pytest` (full), `uv run mypy --no-namespace-packages scripts/ tests/`,
  `uv run python tools/check_db_separation.py`, `uv run lint-imports` (import-boundary
  contract).

## Documentation Impact
Yes. `docs/22_mcp/mcp_03_03_transport-and-health.md` (key derivation, durable dedup),
`docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` (snapshot + dedup states in the
trace), `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` (key
semantics + new tables), and new `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
are target rows per `docs/00_index.md` task mapping. Docs describe operational behavior
and failure semantics only (`skills/DESIGN.md` Docs content policy).

## Assumptions
- All MCP server processes that call `dispatch_tool` share `mcp_dedup.sqlite` as readers
  and writers; WAL + busy timeout + short transactions make multi-process access safe, and
  no lock is ever held across a backend tool execution. Verify per-server process count at
  implementation time.
- Same-process, same-turn identical repeated calls (e.g., two identical `file_read` in one
  turn) keep current per-attempt behavior; dedup semantics apply across attempts/processes
  for the same key. This preserves existing LLM-visible behavior.
- rag_pipeline is retryable (read-only, dispatch-capable). Confirm during Phase 1 config
  review.
- Result storage cap defaults to reuse `tool_result_max_llm_chars` (8000); over-cap
  completed rows store a result hash and allow re-execution for retryable tools.
- `/opt/llm/DEPLOYED_REV` may be missing on dev machines; snapshot `unknown` behaves as
  mismatch (fresh attempt) and is logged.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Exact hash input set (uid vs username vs auth context) for per-user dedup | No existing precedent for content-derived keys | Fix at Phase 2: `method + tool_name + canonical-JSON(args) + uid`; document in transport doc | False |
| UNK-02 | Whether `mcp_dedup.sqlite` joins the dbmig001 domain registry later | Owner chose standalone file for now | Bootstrap via `PRAGMA user_version`; record adoption path in `db_03_07` doc | False |
| UNK-03 | Whether existing servers log or compare idempotency keys internally | Server-side code not audited key-by-key; no validator found repo-wide | Grep per-server usage during Phase 2; keys are opaque passthrough today | False |
| UNK-04 | Retention default value (days) | No operational data on replay windows | Config default 14 days, tuned after observation | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/http_transport.py` | Key derivation | All HTTP MCP calls | 7 | High (single author) | Synced by `rsync scripts/`; agent + MCP server restarts |
| `scripts/mcp_servers/dispatch.py` | Dedup cutover + snapshot + sweep | All dispatch-capable tool calls (every server process importing `dispatch_tool`) | 5 | High (single author) | Synced; MCP server restarts |
| `scripts/shared/mcp_dedup.py`, `scripts/shared/execution_snapshot.py` | New modules | New surface only | — | High (single author) | Synced |
| `scripts/agent/tool_audit.py` | Snapshot serialization | Tool audit records | 5 | High (single author) | Synced |
| `scripts/db/schema_sql.py` | 2 new tables via migration | Workflow DB init/upgrade; dbmig001 ledger sequencing | 11 | High (single author) | Synced; `init_db.sh` path unchanged for fresh installs |
| `scripts/agent/workflow/state_store.py`, `workflow_engine.py`, `llm_turn_runner.py` | Pending detection + replay turn | Agent turn lifecycle | 2 / 1 / 4 | High (single author) | Synced; agent restart |
| `config/mcp_dedup.toml` | New shared dedup/retry config file | MCP server config loading | — | High (single author) | `config/` sync per deploy checklist |
| `tests/` (transport, dispatcher, new shared modules, workflow) | Extension + 2 new modules | Test suite runtime | varies | High (single author) | Synced by `rsync tests/` |
| `docs/22_mcp/*`, `docs/23_agent/*`, `docs/41_db/*` | Contract + schema docs | Docs gates | varies | High (single author) | N/A: docs only |

## Design
- Key derivation (`http_transport.build_auth_context` fallback):
  `mcp:` + `sha256(method|tool_name|canonical_json(args)|uid)` hex truncated to fit the
  `^[A-Za-z0-9_-]{1,64}$` house pattern. Caller-supplied keys bypass derivation unchanged.
  Canonical JSON: sorted keys, no whitespace, UTF-8.
- `mcp_dedup.sqlite` schema (bootstrapped by the module, `PRAGMA user_version = 1`):
  `dedup(key TEXT PRIMARY KEY, tool_name TEXT NOT NULL, uid TEXT NOT NULL, request_hash
  TEXT NOT NULL, snapshot_id TEXT, status TEXT NOT NULL CHECK(status IN
  ('pending','completed','failed')), result_json TEXT, result_hash TEXT, attempts INTEGER
  NOT NULL DEFAULT 0, created_at TEXT NOT NULL, completed_at TEXT)`. WAL mode, short
  transactions, busy timeout; shared by all `dispatch_tool` server processes (multi-writer,
  serialized by WAL).
- `dispatch_tool` flow: lookup by key → policy decision per REQ-005 → on dispatch: upsert
  `pending` (short transaction, released before backend call) → backend call → upsert
  `completed`/`failed` (+ snapshot_id, result or result_hash). The existing in-process
  completed dict may remain as a read-only overlay cache fed from the store. An
  opportunistic sweep inside `dispatch_tool` (at most once per process per
  `mcp_dedup_retention_days / 24` interval) purges expired rows and logs counts.
- Snapshot: `{deployed_rev, git_sha, config_hashes: {name: sha256}, schema_versions:
  {workflow: N, eventbus: M}}` stored per attempt in the audit record and in
  `execution_snapshots` (workflow.sqlite) keyed by snapshot_id. Equality = field-wise
  comparison; `unknown` deployed_rev never equals a concrete snapshot.
- Workflow tables (via dbmig001 workflow-domain registered step, version 1 → 2):
  `execution_snapshots(snapshot_id TEXT PRIMARY KEY, deployed_rev TEXT, git_sha TEXT,
  config_hashes_json TEXT, schema_versions_json TEXT, created_at TEXT NOT NULL)` and
  `tool_call_state(key TEXT PRIMARY KEY, tool_name TEXT NOT NULL, task_id INTEGER
  REFERENCES tasks(task_id) NULL, snapshot_id TEXT REFERENCES execution_snapshots NULL,
  state TEXT NOT NULL CHECK(state IN ('pending','completed','failed','unreplayable')),
  created_at TEXT NOT NULL, completed_at TEXT)`. Dedup store stays the transport-level
  truth; `tool_call_state` is the turn-level lifecycle view written by the workflow layer
  keyed by the same deterministic key.
- Replay-as-new-turn: at turn entry, `workflow_engine.py` queries `tool_call_state` pending rows
  for the task; if a retryable row exists, a control message ("prior attempt of tool call
  X was interrupted; replay permitted: re-issue with key K") is injected into the turn
  context via `llm_turn_runner.py`; the LLM re-issues and the deterministic key lands on
  the same dedup row. Non-retryable rows inject "unreplayable: manual action required" and
  mark `state='unreplayable'`.
- Retention: `mcp_dedup_retention_days` purge of `completed`/`failed` rows; `pending` rows
  past `mcp_pending_timeout_minutes` flip to interrupted semantics at read time (no
  mutation needed) and their `tool_call_state` counterparts are consumed by the replay
  path once, then marked.

## Implementation steps
1. **Phase 1: Config + snapshot contracts**
   - [ ] Create `config/mcp_dedup.toml` with validated defaults + retry_class map (REQ-006, REQ-002, REQ-009); loader/validation lives in the Phase 3 module
   - [ ] Implement `scripts/shared/execution_snapshot.py` + `tests/shared/test_execution_snapshot.py` (REQ-004)
2. **Phase 2: Key determinism** (independently shippable)
   - [ ] Deterministic fallback key in `scripts/shared/http_transport.py`; adapt `tests/shared/test_http_transport.py` and `tests/shared/test_tool_executor_routing.py`; add cross-process determinism test (REQ-001, REQ-010)
   - [ ] Grep per-server key usage to confirm passthrough (UNK-03)
3. **Phase 3: Durable dedup at the dispatcher**
   - [ ] Implement `scripts/shared/mcp_dedup.py` (incl. `config/mcp_dedup.toml` loader/validation) + `tests/shared/test_mcp_dedup.py` (REQ-002, REQ-005, REQ-006, REQ-009)
   - [ ] Cutover `scripts/mcp_servers/dispatch.py`: store-backed lookup/policy/snapshot recording; preserve completed fast path + duplicate-attempt audit; extend `tests/mcp_servers/test_mcp_dispatch.py` (REQ-003, REQ-005)
   - [ ] Populate audit snapshot + dedup state; `scripts/agent/tool_audit.py` serialization + tests (REQ-004)
4. **Phase 4: Workflow lifecycle tables** (gated on dbmig001 Phases 1–2 implemented)
   - [ ] `tool_call_state` + `execution_snapshots` DDL + registered migration step via dbmig001 harness in `scripts/db/schema_sql.py` (REQ-007)
5. **Phase 5: Turn semantics**
   - [ ] Pending detection + replay-as-new-turn in `scripts/agent/workflow/state_store.py`, `workflow_engine.py`, control message in `llm_turn_runner.py`; `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_llm_turn_runner.py` (REQ-008)
6. **Phase 6: Verification + documentation**
   - [ ] Full validation sequence (Tests section); staging check: restart dispatcher between identical calls and confirm completed-hit without re-execution; kill mid-call and confirm next-turn replay
   - [ ] Update `docs/22_mcp/mcp_03_03_*`, `docs/22_mcp/mcp_06_06_*`, `docs/23_agent/agent_04_03_*`; write `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` (Documentation Impact)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/http_transport.py` | Unit + cross-process determinism | `uv run pytest tests/shared/test_http_transport.py tests/shared/test_tool_executor_routing.py` | Stable keys; supplied keys preserved |
| `scripts/shared/mcp_dedup.py` | Unit, reopen durability, TTL, interrupted classification | `uv run pytest tests/shared/test_mcp_dedup.py` | Full state machine incl. restart |
| `scripts/shared/execution_snapshot.py` | Unit per component + missing DEPLOYED_REV | `uv run pytest tests/shared/test_execution_snapshot.py` | Equality/mismatch/unknown semantics |
| `scripts/mcp_servers/dispatch.py` | Integration (TestClient, simulated reopen, retry/non-retry mix) | `uv run pytest tests/mcp_servers/test_mcp_dispatch.py` | REQ-003/005 hold; fast path + audit preserved |
| `scripts/db/schema_sql.py` (new tables) | Migration fresh-init + upgrade with data | dbmig001 harness (`tests/db/`) | v2 tables present; rows preserved |
| `scripts/agent/workflow/*`, `llm_turn_runner.py` | Integration with mocked transport | `uv run pytest tests/agent/workflow/test_workflow_engine.py tests/agent/test_llm_turn_runner.py` | Replay-as-new-turn; unreplayable surfaced |
| Cross-cutting | Architecture + DB separation gates | `uv run lint-imports`; `uv run python tools/check_db_separation.py` | No import-contract breach; new DB declared (see Risks) |
| Type/quality | Static | `uv run mypy --no-namespace-packages scripts/ tests/` | Clean |

## Risks
- **Risk**: Deterministic keys collapse intentional identical repeated calls within one
  live turn. **Mitigation**: same-process same-turn behavior stays as today
  (`dispatch.py:190-201` path preserved); durable dedup governs cross-attempt/cross-process
  identity only. Covered by AC-1/AC-2 tests.
- **Risk**: Dedup store failure stalls all tool calls. **Mitigation**: WAL + busy timeout +
  short transactions; on store error: non-retryable tools fail closed, retryable read-type
  tools dispatch with an audited `dedup_store_error` marker. Never block silently.
- **Risk**: `schema_sql.py` (churn 11/30d) and dispatcher edits collide with active
  implementations `20261029-130401_*` and `20261029-135744_*`. **Mitigation**: Phase 4 lands
  strictly after dbmig001; rebase each phase against current `HEAD`; rerun
  `check_plan_target_overlaps.py` at procedure generation.
- **Risk**: `scripts/agent/llm_turn_runner.py` and `tests/agent/test_llm_turn_runner.py` are
  also targeted by Frozen Plan `plans/20261029-215111_toolhint001_*`. **Mitigation**: distinct
  wiring points (guard wiring vs. turn-entry control-message injection); sequenced in both
  plans — whichever lands first, the other rebases before its runner phase.
- **Risk**: Snapshot mismatch storms after routine config edits turn every completed call
  into a fresh attempt. **Mitigation**: mismatch only changes replay choice, never blocks
  execution; per-attempt snapshot in audit makes storms visible.
- **Risk**: `check_db_separation.py` may flag the new `mcp_dedup.sqlite` as an undeclared
  cross-domain DB. **Mitigation**: register the new path in the tool's domain config as
  part of Phase 3 (config-only change to the checker's declared paths).
- **Risk**: Key-shape change breaks any receiver comparing keys. **Mitigation**: UNK-03
  grep gate in Phase 2 before Phase 3 ships; Phase 2 is independently shippable and
  reversible.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Config + snapshot contracts | In Progress | — | — |  |
| 2 | Phase 2: Key determinism | In Progress | — | — | Independently shippable |
| 3 | Phase 3: Durable dedup at the dispatcher | In Progress | — | — |  |
| 4 | Phase 4: Workflow lifecycle tables | In Progress | — | — | Gated on dbmig001 Phases 1–2 |
| 5 | Phase 5: Turn semantics | In Progress | — | — |  |
| 6 | Phase 6: Verification + documentation | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | dbmig001 framework not yet implemented (planning-order dependency, not a design conflict) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261030-102825_01_scripts_shared_http_transport.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261030-102825_02_scripts_shared_mcp_dedup.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-102825_03_scripts_shared_execution_snapshot.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261030-102825_04_scripts_mcp_servers_dispatch.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-102825_05_scripts_agent_tool_audit.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-102825_06_scripts_db_schema_sql.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261030-102825_07_scripts_agent_workflow_state_store.py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261030-102825_08_scripts_agent_workflow_workflow_engine.py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261030-102825_09_scripts_agent_llm_turn_runner.py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261030-102825_10_config_mcp_dedup.toml.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261030-102825_11_docs_22_mcp_mcp_03_03_transport-and-health.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261030-102825_12_docs_22_mcp_mcp_06_06_end-to-end-tool-call-tracing.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261030-102825_13_docs_23_agent_agent_04_03_state-and-persistence-platform-databases.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261030-102825_14_docs_41_db_db_03_07_mcp-dedup-and-execution-snapshot.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261030-102825_15_tests_shared_test_http_transport.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261030-102825_16_tests_shared_test_tool_executor_routing.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261030-102825_17_tests_shared_test_mcp_dedup.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-102825_18_tests_shared_test_execution_snapshot.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261030-102825_19_tests_mcp_servers_test_mcp_dispatch.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-102825_20_tests_agent_workflow_test_workflow_engine.py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261030-102825_21_tests_agent_test_llm_turn_runner.py.md` | 5 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261029-233524
- **Related target files**: `scripts/shared/http_transport.py`, `scripts/shared/mcp_dedup.py`, `scripts/shared/execution_snapshot.py`, `scripts/mcp_servers/dispatch.py`, `scripts/agent/tool_audit.py`, `scripts/db/schema_sql.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/llm_turn_runner.py`, `config/mcp_dedup.toml`, `docs/22_mcp/mcp_03_03_transport-and-health.md`, `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`, `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`, `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `tests/shared/test_http_transport.py`, `tests/shared/test_tool_executor_routing.py`, `tests/shared/test_mcp_dedup.py`, `tests/shared/test_execution_snapshot.py`, `tests/mcp_servers/test_mcp_dispatch.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_llm_turn_runner.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (deterministic keys) | `scripts/shared/http_transport.py` | Phase 2 | AC-1 | `tests/shared/test_http_transport.py` | Explicit in issue |
| REQ-002 | Required Changes (durable store; owner storage decision) | `scripts/shared/mcp_dedup.py` | Phase 3 | AC-2 | `tests/shared/test_mcp_dedup.py` | Explicit in issue + owner decision |
| REQ-003 | Problem / Required Changes | `scripts/mcp_servers/dispatch.py` | Phase 3 | AC-2, AC-3 | `tests/mcp_servers/test_mcp_dispatch.py` | Explicit in issue |
| REQ-004 | Required Changes (snapshot at call start); `tool_audit.py:159/188` evidence | `scripts/shared/execution_snapshot.py`, `scripts/agent/tool_audit.py` | Phases 1, 3 | AC-4 | `tests/shared/test_execution_snapshot.py`, audit tests | Explicit in issue |
| REQ-005 | Required Changes (replay rules; owner replay decision) | `scripts/mcp_servers/dispatch.py` | Phase 3 | AC-3 | Replay policy integration tests | Explicit in issue + owner decision |
| REQ-006 | Required Changes (retry classification; owner classification decision) | `config/mcp_dedup.toml`, `scripts/shared/mcp_dedup.py` | Phases 1, 3 | AC-3 | Config-validation cases in `tests/shared/test_mcp_dedup.py` | Explicit in issue + owner decision |
| REQ-007 | Required Changes (schema via migration framework) | `scripts/db/schema_sql.py` | Phase 4 | AC-7 | dbmig001 harness | Explicit in issue |
| REQ-008 | Required Changes (interrupted replay; owner decision: new turn) | `scripts/agent/workflow/state_store.py`, `workflow_engine.py`, `llm_turn_runner.py` | Phase 5 | AC-5 | `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_llm_turn_runner.py` | Explicit in issue + owner decision |
| REQ-009 | Required Changes (retention; owner: configurable) | `scripts/shared/mcp_dedup.py`, `scripts/mcp_servers/dispatch.py` | Phase 3 | AC-6 | TTL purge tests | Explicit in issue + owner decision |
| REQ-010 | Constraints (existing anchors preserved) | `scripts/shared/http_transport.py`, `scripts/db/schema_sql.py` | Phases 2, 4 | AC-1, AC-7 | Regression suites | Derived from confirmed evidence |
| REQ-004 | Documentation Impact | `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` | Phase 6 | AC-4 | Docs checkers | Derived from confirmed evidence |
| REQ-002 | Documentation Impact | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Phase 6 | AC-2 | Docs checkers | Derived from confirmed evidence |