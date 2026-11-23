# Add an Agent-only call-state API, reconciliation contract, and secure result replay

## Goal
- Let the Agent recover the outcome of a side-effecting MCP call after response loss: query structured call state from the owning MCP server through an Agent-only control API, run tool-specific reconciliation behind a defined contract, and receive a complete result, a secure reference, a redacted preview, or explicit `replay_unavailable` evidence — without ever re-executing a completed side effect.

## Priority
High

## Scope
- **In-Scope**: Authenticated Agent-only call-state and reconcile control endpoints on every MCP server; a separate control authorization path; durable result metadata (content hash, byte size, result class, external reference, stable error code) in the dedup ledger; the reconciler contract (vocabulary, registration seam, evidence recording); the authoritative Agent-to-MCP call-state mapping and an Agent recovery service consulted during workflow stale-pending classification; per-server and Agent control-token configuration; documentation of the contract, result classes, and failure behavior.
- **Out-of-Scope**: Ledger ownership/lease/store-identity mechanics (mcpdl002, done); dispatcher dedup-gate integration (mcpai001); the logical call id and Agent approval/intent states (mcpdl001, done); retention and capacity monitoring for the new result fields (mcpdl005); end-to-end two-layer failure verification (mcpdl006); per-tool reconciler implementations (mcpai006, mcpci002, mcpai008, mcpai009); any change to an ADR decision or invariant (no approval record exists).
- **Dependencies**: Built on the completed mcpdl001 (logical call id, approval grant, intent states), mcpdl002 (owner-lease store, identity contract), and mcpdl003 (per-server `[dedup]` config) chains. Blocks mcpdl005 and mcpdl006. Related: mcpai006, mcpci002, mcpai008, mcpai009 implement tool-specific reconcilers on this contract.
  - **Depends on**: issues/done/20261120-115840_mcpdl001_approval-grant-intent.md | phase all | the logical call id (`X-Idempotency-Key` value), the `tool_call_state` row vocabulary, and the `classify_stale_pending` recovery seam this Plan consults and extends.
  - **Depends on**: issues/done/20261120-115841_mcpdl002_store-identity-continuity.md | phase all | the disposable store's fingerprint/identity refusal model and acquisition-state vocabulary that the new schema version and call-state reads ride on.
  - **Depends on**: plans/done/20261121-172154_mcpdl003_dedup-config-isolation.md | phase all | the per-server `[dedup]` table bootstrap in `MCPServer.run_http()` that the new `[control]` table wiring mirrors, and the post-split module layout (`mcp_dedup_schema.py` / `mcp_dedup_rows.py` / `mcp_dedup_ledger.py`) this Plan modifies.

## Background
Source: consolidated MCP deduplication two-layer defense backlog, Issue 4 (mcpdl004). The mcpdl001/mcpdl002/mcpdl003 chains landed the logical call id, the owner-lease disposable store, and per-server dedup config. What is missing is the read/recovery side: after a lost response the Agent has no way to ask the server what happened, and the store keeps only a 1000-character preview plus a hash for oversized results.

## Problem
After a network failure or Agent crash the Agent cannot know whether the side effect was applied; lease expiry proves only that the process stopped renewing ownership. Today no server exposes a call-state or reconciliation endpoint (verified by negative `rg` over `scripts/`), `RESULT_MAX_CHARS = 8000` / `RESULT_PREVIEW_CHARS = 1000` in `scripts/shared/mcp_dedup_schema.py:40-41` replace oversized results with a truncated sentinel, and re-executing to recover output is unsafe.

## Reason for Change
Recovery of side-effecting calls without duplication. State retrieval, reconciliation, and replay form one contract: separating them would let the Agent learn that a call completed with no safe way to read its result. The store-side groundwork (mcpdl001-003) is now merged, so this is the next link in the chain and the prerequisite for mcpdl005/mcpdl006.

## Implementation Intent
Add two control-plane endpoints per server (`GET /v1/call_state/{key}` and `POST /v1/call_state/{key}/reconcile`), attached once in `MCPServer.run_http()` and authenticated by a dedicated control Bearer token separate from the tool Bearer token. Enrich the dedup ledger at finalization with result metadata and a closed result-class vocabulary. Define the reconciler contract as shared vocabulary plus a registration seam; unregistered tools report `reconciliation_required` with operator review. On the Agent side, a recovery service maps MCP ledger state into the mcpdl001 Agent states and is consulted from stale-pending classification, never re-executing handlers. All control responses carry only structured evidence: never raw arguments, credentials, signed URLs, raw exceptions, or internal paths.

## Requirements
- `REQ-001`: Add the control endpoints `GET /v1/call_state/{key}` and `POST /v1/call_state/{key}/reconcile` returning logical call state, attempt number, dispatch/lease evidence, result availability class, a stable error code, and whether reconciliation is required — never raw arguments, credentials, signed URLs, raw exceptions, or internal paths.
- `REQ-002`: Authorize control operations with a dedicated control Bearer token (per-server `[control]` config, Agent `control_auth_token`): the tool token must not reach control paths, a missing/empty control token fails closed on control paths, and ordinary tool authorization is unchanged (ADR-017 INV-03 semantics preserved).
- `REQ-003`: At finalization store `result_sha256`, `result_size_bytes`, `result_class` (closed vocabulary `complete | secure_reference | redacted_preview | replay_unavailable`), `result_code`, and optional `external_ref`; apply redaction before preview creation; retention stays with `purge_expired`.
- `REQ-004`: Define the reconciler contract: closed outcome vocabulary, per-tool registration seam, reuse of completed evidence, never rerun an active/unknown/ambiguous call, multiple candidates or unverifiable outcome require operator review, and evidence plus decision are recorded in `call_attempt_history` without sensitive payloads.
- `REQ-005`: Own the authoritative MCP-ledger-state → Agent-state mapping (`completed`, `in_progress`, `outcome_unknown`, `reconciliation_required`, `failed`) and an Agent recovery service consulted during `classify_stale_pending`; a completed call is never re-executed and no path re-executes a handler to recover output.
- `REQ-006`: Bump the disposable store's schema shape and version; existing stores must fail the open-time fingerprint gate as `schema_mismatch` and be re-initialized by the operator (disposable-store policy, no in-place migration).
- `REQ-007`: Document the control operations, the reconciler contract, the result classes, and the failure behavior in the MCP endpoint/transport, MCP access-control, and active-database documents.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/shared/mcp_call_state_contract.py | New shared vocabulary: `RESULT_CLASSES`, `RECONCILE_OUTCOMES`, `CONTROL_ERROR_CODES`, reconciler Protocol, and the MCP-state → Agent-state mapping table | REQ-001/003/004/005 need one closed-vocabulary source readable by `shared`, `mcp_servers`, and `agent` without breaking the shared-is-leaf contract | REQ-001, REQ-003, REQ-004, REQ-005 | `scripts/shared/tool_metadata.py` precedent for closed vocabularies; `.importlinter` contract `shared-is-leaf` | tests/shared/test_mcp_call_state_contract.py | Verified |
| scripts/shared/mcp_dedup_schema.py | Add nullable result-metadata columns to `dedup_call_state` (`result_sha256`, `result_size_bytes`, `result_class`, `result_code`, `external_ref`); bump `_USER_VERSION` 1→2 (fingerprint moves automatically) | REQ-003/REQ-006: the ledger must retain replay-availability facts beyond the preview+hash sentinel | REQ-003, REQ-006 | `scripts/shared/mcp_dedup_schema.py:40-60` (`RESULT_MAX_CHARS = 8000`, DDL, `_USER_VERSION = 1`) | tests/shared/test_mcp_dedup.py, tests/shared/test_mcp_dedup_identity.py | Verified |
| scripts/shared/mcp_dedup_rows.py | Extend `DedupRow` with the metadata fields; classify the stored payload and fill the metadata in `prepare_completed_record`/`_cap_result` (hash, size, class) | REQ-003: classification happens once at store time, redaction before preview creation | REQ-003 | `scripts/shared/mcp_dedup_rows.py:89-103` (`prepare_completed_record` already computes `sha256` + `truncated`) | tests/shared/test_mcp_dedup.py | Verified |
| scripts/shared/mcp_dedup_ledger.py | Persist the metadata at `record_completed`; add a read-only `call_state_view(key)` returning the control-API projection (state, attempt, lease evidence, result class, error code, reconciliation flag) | REQ-001/REQ-003: the ledger owns the evidence the control endpoint projects | REQ-001, REQ-003 | `scripts/shared/mcp_dedup_ledger.py:246-279` (`record_completed`), `437-450` (`_fetch_locked`, `get_execution`) | tests/shared/test_mcp_dedup.py | Verified |
| scripts/shared/mcp_dedup.py | Re-export the new contract vocabularies and `call_state_view` through the facade | The facade is the consumer-facing surface; split modules are re-exported here | REQ-001, REQ-003 | `scripts/shared/mcp_dedup.py:77-99` (facade re-export block) | tests/shared/test_mcp_dedup.py | Verified |
| scripts/shared/mcp_config.py | Add `control_auth_token: str = ""` to `McpServerConfig` | REQ-002: the Agent must hold a per-server control token distinct from `auth_token` | REQ-002 | `scripts/shared/mcp_config.py:60-61` (`McpServerConfig` dataclass); `config/agent.toml:235-307` per-server `auth_token` entries | tests/shared tests for mcp_config | Verified |
| scripts/shared/http_transport.py | Add control-client methods `get_call_state(server, key)` and `request_reconcile(server, key)` sending the control Bearer token; surface control-path failures as typed results | REQ-001/REQ-005: the Agent needs the control round-trip over the same transport that owns the logical call id | REQ-001, REQ-005 | `scripts/shared/http_transport.py:189-216` (`X-Idempotency-Key` send), `270-291` (transport error taxonomy with `dispatch_stage`) | tests/shared/test_http_transport.py | Verified |
| scripts/mcp_servers/control_api.py | New module: FastAPI endpoint handlers for `GET /v1/call_state/{key}` and `POST /v1/call_state/{key}/reconcile`, control-token bearer check, reconciler registry lookup, operator-review responses | REQ-001/REQ-002/REQ-004: keeps `dispatch.py` (24,573 B, at the 24,576 B module-size gate) unmodified | REQ-001, REQ-002, REQ-004 | `scripts/mcp_servers/server.py:124-153` (`attach_auth_middleware` bearer pattern); `scripts/mcp_servers/dispatch.py` size 24573 B | tests/mcp_servers/test_call_state_api.py | Verified |
| scripts/mcp_servers/models.py | Add the control-response models (call-state view, reconcile result) with closed-vocabulary fields | REQ-001: response shape must exclude free-form payloads and enforce the closed vocabulary at the boundary | REQ-001 | `scripts/mcp_servers/models.py:24-56` (`CallToolRequest`/`CallToolResponse` incl. `dedup_state`); `ReconciliationPolicy` already imported | tests/mcp_servers/test_call_state_api.py | Verified |
| scripts/mcp_servers/server.py | In `run_http()`, load the server's own `[control]` table (mirroring the `[dedup]` bootstrap) and attach the control API via `control_api`'s wiring helper; fail closed (control paths 401/404) when unconfigured | REQ-002: single wiring point for all 10 servers; per-server config isolation is already enforced here | REQ-001, REQ-002 | `scripts/mcp_servers/server.py:357-378` (`[dedup]` bootstrap in `run_http`), `340-355` (config isolation) | tests/mcp_servers/test_mcp_server_base.py, tests/mcp_servers/test_call_state_api.py | Verified |
| scripts/agent/mcp_call_recovery.py | New Agent recovery service: given a logical call id and server key, query the control API, map MCP state through the shared mapping table, finalize the Agent `tool_call_state` row accordingly, and return the result class plus secure reference/preview when present; never re-execute | REQ-005 | mcpdl001 AC-6 semantics require recovery outside `tool_runner` (post-send failures stay `dispatched` there) | tests/agent/test_mcp_call_recovery.py | Verified |
| scripts/agent/workflow/tool_call_state_ops.py | Consult an optional call-state resolver before declaring `outcome_unknown` for stale `dispatched`/`response_received` rows; apply the mapped states (`completed`, `in_progress`, `reconciliation_required`, `outcome_unknown`) | REQ-005: authoritative mapping applied at the recovery decision point | REQ-005 | `scripts/agent/workflow/tool_call_state_ops.py:116-156` (stale classification to `outcome_unknown`) | tests/agent/test_mcp_call_recovery.py, existing tool_call_state tests | Verified |
| scripts/agent/workflow/workflow_engine.py | Wire the recovery service's resolver into stale-pending classification at startup recovery | REQ-005 | `scripts/agent/workflow/workflow_engine.py:167-195` (classified `outcome_unknown` list) | tests/agent/workflow tests (engine recovery) | Verified |
| config/agent.toml | Add `control_auth_token = "${ENV:MCP_<NAME>_CONTROL_TOKEN}"` to each of the 10 `[mcp_servers.*]` entries | REQ-002: Agent-side control credential provisioning | REQ-002 | `config/agent.toml:235-307` (`auth_token = "${ENV:MCP_*_AUTH_TOKEN}"` pattern) | tests/agent/test_http_lifecycle_env_allowlist_integration.py | Verified |
| config/shell_mcp_server.toml | Add `[control] auth_token = "${ENV:MCP_SHELL_CONTROL_TOKEN}"` | REQ-002: server-side control credential, mirrors the `[dedup]` table | REQ-002 | `grep -l "[dedup]" config/*.toml` includes it | tests/mcp_servers/test_call_state_api.py (config fixture) | Verified |
| config/git_mcp_server.toml | Add `[control]` table (env-substituted control token) | REQ-002 | REQ-002 | carries `[dedup]` | as above | Verified |
| config/github_mcp_server.toml | Add `[control]` table (env-substituted control token) | REQ-002 | REQ-002 | carries `[dedup]` | as above | Verified |
| config/cicd_mcp_server.toml | Add `[control]` table (env-substituted control token) | REQ-002 | REQ-002 | carries `[dedup]` | as above | Verified |
| config/file_read_mcp_server.toml | Add `[control]` table (env-substituted control token) | REQ-002 | REQ-002 | carries `[dedup]` | as above | Verified |
| config/file_write_mcp_server.toml | Add `[control]` table (env-substituted control token) | REQ-002 | REQ-002 | carries `[dedup]` | as above | Verified |
| config/file_delete_mcp_server.toml | Add `[control]` table (env-substituted control token) | REQ-002 | REQ-002 | carries `[dedup]` | as above | Verified |
| config/web_search_mcp_server.toml | Add `[control]` table (env-substituted control token) | REQ-002 | REQ-002 | carries `[dedup]` | as above | Verified |
| config/rag_pipeline_mcp_server.toml | Add `[control]` table (env-substituted control token) | REQ-002 | REQ-002 | carries `[dedup]` | as above | Verified |
| config/mdq_mcp_server.toml | Add `[control]` table (env-substituted control token) | REQ-002 | REQ-002 | carries `[dedup]` | as above | Verified |
| tests/shared/test_mcp_call_state_contract.py | New tests: closed vocabularies, mapping-table totality (every MCP state maps), reconciler Protocol defaults | REQ-004, REQ-005 | REQ-004, REQ-005 | N/A: new file | itself | Verified |
| tests/shared/test_mcp_dedup.py | Update the table/DDL pinning asserts and add result-metadata/classification tests | REQ-003/REQ-006 fallout: line 304 asserts the exact table set and schema facts | REQ-003, REQ-006 | `tests/shared/test_mcp_dedup.py:304` | itself | Verified |
| tests/shared/test_mcp_dedup_identity.py | Update `_STORE_TABLES`/schema-drift fixtures for the new columns and version stamp | REQ-006 | REQ-006 | `tests/shared/test_mcp_dedup_identity.py:34,213` | itself | Verified |
| tests/mcp_servers/test_mcp_dispatch.py | Update the raw `CREATE TABLE dedup_call_state (key TEXT PRIMARY KEY, status TEXT)` seed: the widened `SELECT` in `_fetch_locked` breaks against a two-column fixture | REQ-003/REQ-006 predictable fallout | REQ-003, REQ-006 | `tests/mcp_servers/test_mcp_dispatch.py:802` | itself | Verified |
| tests/mcp_servers/test_call_state_api.py | New tests: control endpoint authorization matrix (tool token rejected, control token accepted, empty token fail-closed), response shape (no raw args/paths), reconcile on live lease refuses, ambiguous outcome → operator review | REQ-001, REQ-002, REQ-004 | Issue AC "control operations are Agent-only", "sensitive data absent" | N/A: new file | itself | Verified |
| tests/agent/test_mcp_call_recovery.py | New tests: response-lost recovery maps `completed`/`in_progress`/`outcome_unknown`/`reconciliation_required`; completed call never re-executed; `replay_unavailable` does not rerun the handler; control-unavailable leaves `outcome_unknown` | REQ-005 | Issue AC "Agent can query MCP state", "completed and active calls are not re-executed" | N/A: new file | itself | Verified |
| docs/22_mcp/mcp_02_01_endpoints-and-transport.md | Document the two control endpoints, their response shape, and failure behavior | REQ-007 | REQ-007 | `docs/00_index.md:161` task mapping "MCP server implementation" | tests/tools/test_generate_reference_table.py drift check | Verified |
| docs/22_mcp/mcp_05_01_access-control-and-allowlists.md | Document the separate control authorization path and its fail-closed posture | REQ-007 | REQ-007 | `docs/00_index.md:167` task mapping "MCP security model" | as above | Verified |
| docs/41_db/db_08_active_databases.md | Update the dedup-store schema facts (new columns, version stamp, re-initialization policy) | REQ-007 | REQ-006, REQ-007 | `docs/41_db/db_08_active_databases.md:70-77` cites the DDL and row semantics | as above | Verified |

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
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/mcp_servers/dispatch.py | Dedup gate and `dedup_state` early-result flow: `not affected: no change needed — result metadata is written inside `record_completed`, and reconcile runs through the store, not the gate. Also `not affected` because the file is at the 24,576 B module-size gate | REQ-001, REQ-004 |
| scripts/agent/tool_runner.py | mcpdl001 AC-6: post-send failures deliberately leave the row `dispatched` and are never finalized here; the recovery hook must not move into this file | REQ-005 |
| scripts/agent/workflow/models.py | `TOOL_CALL_STATES` closed set the mapping targets must stay inside | REQ-005 |
| scripts/agent/workflow/state_store.py | `classify_stale_pending` persistence seam the resolver plugs into | REQ-005 |
| scripts/agent/context.py | `ToolCallRecorder` seam (`finalize_tool_call`) the recovery service uses | REQ-005 |
| scripts/agent/startup_validation.py | `auth_token` presence validation precedent; control tokens are optional by design (absent control config degrades recovery to `outcome_unknown`, it does not refuse startup) — read to confirm no change is required | REQ-002 |
| scripts/shared/mcp_dedup_config.py | `[dedup]` section validation precedent mirrored by `[control]` loading | REQ-002 |
| scripts/shared/tool_constants.py | Canonical side-effect tool set that bounds which calls the recovery path expects to find ledger rows for | REQ-005 |
| scripts/shared/execution_snapshot.py | `snapshot_json`/`snapshots_equal` contract consumed by the replay branch the result classes refine | REQ-003 |
| scripts/agent/http_lifecycle_health_checker.py | Bearer-header pattern for Agent-initiated server requests | REQ-002 |
| tools/check_db_separation.py | `not affected: no new table is added — the new fields are columns of the already-registered `dedup_call_state` (registry line 95) | REQ-006 |
| tools/generate_reference_table.py | `not affected at code level: reads `mcp_dedup_schema.py` DDL dynamically; its drift test forces the `docs/41_db/db_08_*` row update | REQ-007 |
| rules/persisted-schema-change.md | Planning checklist whose items this Plan's Design records | REQ-006 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-005): After response loss the Agent queries the owning server's call-state endpoint and finalizes the local `tool_call_state` row from the mapped MCP state.
- AC-2 (REQ-004, REQ-005): Completed and active calls are never re-executed; ambiguous outcomes (`pending` with expired lease, attempt exhaustion, multiple reconcile candidates) end in `reconciliation_required` or operator review.
- AC-3 (REQ-001, REQ-003): A caller can distinguish the four result classes — `complete`, `secure_reference`, `redacted_preview`, `replay_unavailable` — from the control response alone.
- AC-4 (REQ-002): Control operations are Agent-only: a tool Bearer token cannot read call state; an unconfigured or empty control token fails closed on control paths.
- AC-5 (REQ-001): Responses and ledger previews contain no raw arguments, credentials, signed URLs, raw exceptions, or internal paths (redaction precedes preview creation).
- AC-6 (REQ-006): A pre-existing store opened with the new code fails the fingerprint gate as `schema_mismatch` and is refused; a fresh store initializes at the new version.

## Tests
- Unit: result classification and metadata write paths (`complete` vs `redacted_preview`, hash/size correctness, redaction before preview) — REQ-003.
- Unit: mapping-table totality and closed vocabularies — REQ-004, REQ-005.
- Integration (`tests/mcp_servers/test_call_state_api.py`): authorization matrix (tool token rejected on control paths; control token accepted; empty token → 401 fail-closed), response-shape assertions, reconcile refusal on live lease, attempt-exhaustion refusal — REQ-001, REQ-002, REQ-004.
- Integration (`tests/agent/test_mcp_call_recovery.py`): workflow dispatch accepted but response lost; Git remote-update reconciliation evidence reuse; file deletion already completed; ambiguous external result → operator review; complete result and secure reference retrieval; `replay_unavailable` result does not rerun the handler — REQ-005, per the Issue's Testing Expectations.
- Regression: updated store-identity and dispatch fixtures — REQ-006.
- Toolchain: `uv run ruff check`, `uv run mypy scripts/`, `uv run pytest` (full suite), `uv run python tools/check_db_separation.py`, `uv run pytest tests/tools/` (reference-table drift), per `rules/toolchain.md`.

## Documentation Impact
Yes (REQ-007). Target docs named via `docs/00_index.md` "Document References by Task": "MCP server implementation" (endpoint/transport doc) and "MCP security model" (access-control doc); the disposable-store facts live in the active-databases document (`docs/41_db/db_08_active_databases.md`, schema-authority section). Content: the control operations, the reconciler contract, the result classes, and the failure behavior. ADR docs are not touched: this change adds a separate authorization path without altering ADR-017 or ADR-008 decisions (no maintainer approval record is being written or simulated).

## Assumptions
- The disposable dedup store keeps its ADR-008 posture: the schema fingerprint gate plus operator re-initialization is the upgrade mechanism; no in-place migration of existing stores is planned.
- Full results stay inside the disposable store; the `secure_reference` class reserves the field for external object ids that per-tool reconcilers (out-of-scope issues) will populate. At-rest encryption beyond file permissions is intentionally not introduced (no new dependency), because the store already holds same-sensitivity ledger payloads.
- Control tokens are provisioned per server through `${ENV:...}` substitution, mirroring `auth_token` in `config/agent.toml`; env-var naming `MCP_<NAME>_CONTROL_TOKEN` mirrors `MCP_<NAME>_AUTH_TOKEN`.
- Control configuration is optional: a server without `[control]` keeps the control paths closed, and Agent recovery degrades to the current `outcome_unknown` behavior.
- One control token per server (not per call): the control caller is the Agent process, and store rows are already keyed by the logical call id.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Operator runbook/timing for re-initializing the 10 production dedup stores after the fingerprint bump (stores refuse open until re-initialized) | Production store locations/ops cadence not inspected at planning time | Phase 4 documents the re-initialization step; stores are disposable and re-creatable (`first_initialization`) | False |
| UNK-02 | Final env-var names and provisioning path for the 10 `MCP_*_CONTROL_TOKEN` values on the deployment host | Deployment env provisioning is host-managed | Phase 2/3 config rows name the vars; `deploy.sh` unchanged (see Affected areas) | False |
| UNK-03 | Whether the Issue's behavior claims (duplicated Git pushes, workflow dispatches, deletions, merges after lost responses) actually occurred in production | Marked `Needs confirmation` in the Issue; no ledger forensics run | Not required for the contract; mcpdl006 verification exercises the fixed paths end to end | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/server.py | Control-API wiring in `run_http()` | All 10 MCP server processes | 11 | High (single maintainer >70%) | None: no new process; servers restart under existing lifecycle |
| scripts/mcp_servers/control_api.py | New endpoints per server | New attack surface on the loopback HTTP port | new | High | None |
| scripts/shared/mcp_dedup_schema.py | DDL + version bump | Every existing dedup store refuses open until re-initialized | 2 | High | None (store re-init is operator action, documented) |
| scripts/shared/mcp_dedup_ledger.py | Metadata writes + new read | Dispatcher finalization path of every side-effecting call | 1 | High | None |
| scripts/shared/http_transport.py | Control client methods | All Agent→MCP HTTP traffic module | 8 | High | None |
| scripts/agent/tool_runner.py | (reference) unchanged by design | — | 15 | High | None |
| scripts/agent/workflow/workflow_engine.py | Recovery wiring at startup | Workflow recovery on Agent restart | low | High | None |
| config/agent.toml + 10 server tomls | `[control]` / `control_auth_token` entries | Startup config validation | low | High | None: `deploy.sh` unchanged; operators export the new `MCP_*_CONTROL_TOKEN` env vars |

## Design
- **Control plane vs data plane**: the control endpoints live in a new `scripts/mcp_servers/control_api.py`, attached once from `MCPServer.run_http()`. `dispatch.py` (24,573 B) stays untouched to respect the 24,576 B module-size gate. Control paths are matched by exact prefix (`/v1/call_state/`), authenticated against a separate control Bearer with the same `hmac.compare_digest` pattern as `attach_auth_middleware`; an empty/unconfigured control token closes only the control paths (tool paths keep ADR-017 INV-03 fail-closed semantics unchanged).
- **Result ledger (REQ-003)**: five nullable columns on `dedup_call_state` — `result_sha256`, `result_size_bytes`, `result_class`, `result_code`, `external_ref`. No new table: `tools/check_db_separation.py`'s table registry and the three table-set-pinning tests stay valid (columns only). At `record_completed`, the payload classification is: serialized ≤ `RESULT_MAX_CHARS` → `complete`; oversized → existing truncated sentinel → `redacted_preview`; owner-finalized `failed` → `replay_unavailable` with `result_code = error_class`; `secure_reference` is written only when a `external_ref` is present (populated by future per-tool reconcilers). The sha256/size facts move from read-time sentinel re-derivation into stored columns, redaction staying upstream of preview creation.
- **Schema/version (REQ-006)** — persisted-schema-change checklist outcomes: item 1: version storage is the store's own `_USER_VERSION` (1→2) plus the canonical-DDL fingerprint; no other store moves. item 2: the DDL change moves the fingerprint, and the open-time classifier refuses the old store as `schema_mismatch` — this is the registered upgrade mechanism for this disposable store. items 3/4: no rebuild, no NOT NULL columns, all new columns nullable, so no backfill and no failing existing INSERT. item 5: N/A, this store has no migration registry. item 6: pinning tests are named as target rows (`test_mcp_dedup.py:304`, `test_mcp_dedup_identity.py:34`, `test_mcp_dispatch.py:802` raw-table seed). item 7: retained old rows are decided as "refuse the whole store and re-initialize" — the disposable-store policy, recorded here and in docs.
- **Reconciler contract (REQ-004)**: shared `Reconciler` Protocol plus `RECONCILE_OUTCOMES = {evidence_found, no_evidence, ambiguous, unverifiable}`. The reconcile endpoint looks up the tool's registered reconciler; none registered → the response is `reconciliation_required` + `operator_review` and the ledger row moves exactly as `reconcile_execution` already governs (expired lease → `interrupted`, live lease and attempt exhaustion refuse). The decision and a non-sensitive evidence digest are appended to `call_attempt_history` (reuse of the existing history table, no new DDL for audit).
- **Agent mapping (REQ-005)**: authoritative table (owned by `shared/mcp_call_state_contract.py`, verified end to end by mcpdl006): ledger `pending`+live lease → `in_progress`; `pending`+expired lease → `reconciliation_required`; `completed` → `completed` (result class reported separately); `failed` → `failed`; `interrupted` → `reconciliation_required`; unknown key / control unavailable → stay `outcome_unknown`. The resolver is consulted from `classify_stale_pending`, so mcpdl001 AC-6 (no finalize inside `tool_runner`) is preserved.
- **Security posture**: control responses project only structured fields (models enforce closed vocabularies); key existence lookup is by exact logical call id, so a caller can only read state for a call id it already legitimately holds — the control API cannot widen what ordinary tool authorization allows.

## Implementation steps
1. **Phase 1: Shared contract and store schema**
   - [ ] Define `RESULT_CLASSES`, `RECONCILE_OUTCOMES`, `CONTROL_ERROR_CODES`, reconciler Protocol, and the MCP→Agent mapping table (REQ-004, REQ-005; scripts/shared/mcp_call_state_contract.py) with its vocabulary tests (REQ-004; tests/shared/test_mcp_call_state_contract.py)
   - [ ] Add the nullable result-metadata columns and bump `_USER_VERSION` (REQ-003, REQ-006; scripts/shared/mcp_dedup_schema.py)
   - [ ] Classify payloads and fill metadata at store time (REQ-003; scripts/shared/mcp_dedup_rows.py); persist at finalization and add `call_state_view` read (REQ-001, REQ-003; scripts/shared/mcp_dedup_ledger.py); re-export via the facade (REQ-001; scripts/shared/mcp_dedup.py)
   - [ ] Update store fixtures/pins: metadata assertions (REQ-003; tests/shared/test_mcp_dedup.py), identity/version drift (REQ-006; tests/shared/test_mcp_dedup_identity.py), raw-table seed widening (REQ-006; tests/mcp_servers/test_mcp_dispatch.py)
2. **Phase 2: Server-side control API**
   - [ ] Control-response Pydantic models with closed vocabularies (REQ-001; scripts/mcp_servers/models.py)
   - [ ] Endpoint handlers, control-bearer check, reconciler-registry lookup, operator-review responses (REQ-001, REQ-002, REQ-004; scripts/mcp_servers/control_api.py) and wiring from `run_http()` with `[control]` config load, fail-closed when unconfigured (REQ-002; scripts/mcp_servers/server.py)
   - [ ] Add `[control]` tables to the 10 server configs (REQ-002; config/shell_mcp_server.toml, config/git_mcp_server.toml, config/github_mcp_server.toml, config/cicd_mcp_server.toml, config/file_read_mcp_server.toml, config/file_write_mcp_server.toml, config/file_delete_mcp_server.toml, config/web_search_mcp_server.toml, config/rag_pipeline_mcp_server.toml, config/mdq_mcp_server.toml)
   - [ ] Authorization matrix and response-shape tests (REQ-001, REQ-002, REQ-004; tests/mcp_servers/test_call_state_api.py)
3. **Phase 3: Agent control client and recovery**
   - [ ] `control_auth_token` on `McpServerConfig` (REQ-002; scripts/shared/mcp_config.py) and the 10 `control_auth_token` entries in config/agent.toml (REQ-002; config/agent.toml)
   - [ ] Control-client methods on the transport (REQ-001, REQ-005; scripts/shared/http_transport.py)
   - [ ] Recovery service mapping states and never re-executing (REQ-005; scripts/agent/mcp_call_recovery.py)
   - [ ] Resolver consulted at stale classification (REQ-005; scripts/agent/workflow/tool_call_state_ops.py) and wired at startup recovery (REQ-005; scripts/agent/workflow/workflow_engine.py)
   - [ ] Recovery integration tests incl. replay-unavailable-does-not-rerun (REQ-005; tests/agent/test_mcp_call_recovery.py)
4. **Phase 4: Documentation & verification**
   - [ ] Document endpoints/response shape/failure behavior (REQ-007; docs/22_mcp/mcp_02_01_endpoints-and-transport.md), control authorization posture (REQ-007; docs/22_mcp/mcp_05_01_access-control-and-allowlists.md), and store schema/re-init facts (REQ-006, REQ-007; docs/41_db/db_08_active_databases.md)
   - [ ] Deployment validation: run the full sequence in `rules/toolchain.md` — `uv run ruff check`, `uv run mypy scripts/`, `uv run pytest`, `uv run python tools/check_db_separation.py`, `uv run pytest tests/tools/` (reference-table drift after doc edits) — and confirm the fingerprint-refusal/re-init runbook from UNK-01 against a scratch store (REQ-006)

### Release units
N/A: no release unit — phases land sequentially; each phase passes validation alone (new columns are nullable, control paths are inert until Phase 2 wiring, Agent paths inert until Phase 3).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/mcp_dedup_* (schema/rows/ledger) | Unit + scratch-store integration | `uv run pytest tests/shared/test_mcp_dedup.py tests/shared/test_mcp_dedup_identity.py tests/shared/test_mcp_dedup_concurrency.py` | Metadata written at completion; old store refused as `schema_mismatch`; fresh store initializes |
| scripts/mcp_servers/control_api.py, server.py | Integration (TestClient) | `uv run pytest tests/mcp_servers/test_call_state_api.py tests/mcp_servers/test_mcp_server_base.py` | Authorization matrix passes; responses free of raw args/paths |
| scripts/agent/mcp_call_recovery.py + workflow_* | Integration | `uv run pytest tests/agent/test_mcp_call_recovery.py tests/agent/` | Lost-response recovery finalizes mapped states; no re-execution |
| scripts/mcp_servers/test_mcp_dispatch.py fixtures | Regression | `uv run pytest tests/mcp_servers/test_mcp_dispatch.py` | Widened seed passes against new SELECT shape |
| Whole repository | Lint/types/tests/gates | `uv run ruff check && uv run mypy scripts/ && uv run pytest && uv run python tools/check_db_separation.py && uv run pytest tests/tools/` | All green; reference-table drift cleared after doc updates |

## Risks
- **Risk**: The fingerprint bump makes every existing dedup store refuse to open until the operator re-initializes it, briefly disabling dedup replay on deployed servers → **Mitigation**: sequenced release (stop server, delete/rename the disposable store file, start server); documented in the Phase 4 runbook; stores are disposable by ADR-008 design.
- **Risk**: High churn on `tool_runner.py` (15), `server.py` (11), `http_transport.py` (8) raises conflict probability with parallel work → **Mitigation**: `tool_runner.py` is deliberately untouched; changes are additive methods/params; land this Plan's phases promptly.
- **Risk**: The control API widens the server attack surface (state disclosure by call id) → **Mitigation**: loopback-only binding, separate fail-closed control token, responses restricted to structured vocabulary, key lookups exact-match only (AC-4/AC-5 tests).
- **Risk**: `mcp_dedup_ledger.py` growth could approach the 24,576 B module-size gate → **Mitigation**: keep `call_state_view` projection thin (row-level SELECT + dict projection); if the gate trips, split the view into a new `shared/mcp_dedup_view.py` (recorded in the module-size-gate fallout check).
- **Risk**: Recovery mapping drifts from mcpdl001's vocabulary → **Mitigation**: the mapping table lives in shared code and tests assert totality against `TOOL_CALL_STATES` (tests/shared/test_mcp_call_state_contract.py).
- **Risk**: Control token config missing on a deployed server silently degrades recovery → **Mitigation**: fail-closed control paths plus a startup warning log naming the server (no ADR change); mcpdl006 verifies the enabled end-to-end path.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Shared contract and store schema | Pending | — | — | |
| 2 | Phase 2: Server-side control API | Pending | — | — | |
| 3 | Phase 3: Agent control client and recovery | Pending | — | — | |
| 4 | Phase 4: Documentation & verification | Pending | — | — | |

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
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261123-090353
- **Related target files**: scripts/shared/mcp_call_state_contract.py, scripts/shared/mcp_dedup_schema.py, scripts/shared/mcp_dedup_rows.py, scripts/shared/mcp_dedup_ledger.py, scripts/shared/mcp_dedup.py, scripts/shared/mcp_config.py, scripts/shared/http_transport.py, scripts/mcp_servers/control_api.py, scripts/mcp_servers/models.py, scripts/mcp_servers/server.py, scripts/agent/mcp_call_recovery.py, scripts/agent/workflow/tool_call_state_ops.py, scripts/agent/workflow/workflow_engine.py, config/agent.toml, config/shell_mcp_server.toml, config/git_mcp_server.toml, config/github_mcp_server.toml, config/cicd_mcp_server.toml, config/file_read_mcp_server.toml, config/file_write_mcp_server.toml, config/file_delete_mcp_server.toml, config/web_search_mcp_server.toml, config/rag_pipeline_mcp_server.toml, config/mdq_mcp_server.toml, tests/shared/test_mcp_call_state_contract.py, tests/shared/test_mcp_dedup.py, tests/shared/test_mcp_dedup_identity.py, tests/mcp_servers/test_mcp_dispatch.py, tests/mcp_servers/test_call_state_api.py, tests/agent/test_mcp_call_recovery.py, docs/22_mcp/mcp_02_01_endpoints-and-transport.md, docs/22_mcp/mcp_05_01_access-control-and-allowlists.md, docs/41_db/db_08_active_databases.md — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; `server.py:172` negative evidence (no control endpoint) | scripts/mcp_servers/control_api.py | 2 | AC-1, AC-3, AC-5 | test_call_state_api.py | Planned |
| REQ-001 | ledger evidence | scripts/shared/mcp_dedup_ledger.py | 1 | AC-1 | test_mcp_dedup.py | Planned |
| REQ-001 | facade surface | scripts/shared/mcp_dedup.py | 1 | AC-1 | test_mcp_dedup.py | Planned |
| REQ-001 | response shape | scripts/mcp_servers/models.py | 2 | AC-5 | test_call_state_api.py | Planned |
| REQ-001 | Agent round-trip | scripts/shared/http_transport.py | 3 | AC-1 | test_mcp_call_recovery.py | Planned |
| REQ-002 | Constraints "must not widen tool authorization"; `agent.toml:235-307` | scripts/mcp_servers/server.py | 2 | AC-4 | test_call_state_api.py | Planned |
| REQ-002 | server credential | config/shell_mcp_server.toml | 2 | AC-4 | test_call_state_api.py fixture | Planned |
| REQ-002 | server credential | config/git_mcp_server.toml | 2 | AC-4 | test_call_state_api.py fixture | Planned |
| REQ-002 | server credential | config/github_mcp_server.toml | 2 | AC-4 | test_call_state_api.py fixture | Planned |
| REQ-002 | server credential | config/cicd_mcp_server.toml | 2 | AC-4 | test_call_state_api.py fixture | Planned |
| REQ-002 | server credential | config/file_read_mcp_server.toml | 2 | AC-4 | test_call_state_api.py fixture | Planned |
| REQ-002 | server credential | config/file_write_mcp_server.toml | 2 | AC-4 | test_call_state_api.py fixture | Planned |
| REQ-002 | server credential | config/file_delete_mcp_server.toml | 2 | AC-4 | test_call_state_api.py fixture | Planned |
| REQ-002 | server credential | config/web_search_mcp_server.toml | 2 | AC-4 | test_call_state_api.py fixture | Planned |
| REQ-002 | server credential | config/rag_pipeline_mcp_server.toml | 2 | AC-4 | test_call_state_api.py fixture | Planned |
| REQ-002 | server credential | config/mdq_mcp_server.toml | 2 | AC-4 | test_call_state_api.py fixture | Planned |
| REQ-002 | Agent credential | config/agent.toml | 3 | AC-4 | env allowlist integration test | Planned |
| REQ-002 | Agent config model | scripts/shared/mcp_config.py | 3 | AC-4 | mcp_config tests | Planned |
| REQ-003 | `mcp_dedup_schema.py:40-41` preview+sentinel evidence | scripts/shared/mcp_dedup_schema.py | 1 | AC-3 | test_mcp_dedup.py | Planned |
| REQ-003 | classification point | scripts/shared/mcp_dedup_rows.py | 1 | AC-3, AC-5 | test_mcp_dedup.py | Planned |
| REQ-004 | Required Changes bullet 2 | scripts/shared/mcp_call_state_contract.py | 1 | AC-2 | test_mcp_call_state_contract.py | Planned |
| REQ-004 | registry lookup | scripts/mcp_servers/control_api.py | 2 | AC-2 | test_call_state_api.py | Planned |
| REQ-005 | Required Changes bullet 4; `tool_call_state_ops.py:116-156` | scripts/agent/workflow/tool_call_state_ops.py | 3 | AC-1, AC-2 | test_mcp_call_recovery.py | Planned |
| REQ-005 | recovery service | scripts/agent/mcp_call_recovery.py | 3 | AC-1, AC-2 | test_mcp_call_recovery.py | Planned |
| REQ-005 | mapping owner | scripts/shared/mcp_call_state_contract.py | 1 | AC-1, AC-2 | test_mcp_call_state_contract.py | Planned |
| REQ-005 | startup wiring | scripts/agent/workflow/workflow_engine.py | 3 | AC-1 | agent/workflow tests | Planned |
| REQ-006 | ADR-008 fingerprint gate | scripts/shared/mcp_dedup_schema.py | 1 | AC-6 | test_mcp_dedup_identity.py | Planned |
| REQ-006 | fixture fallout | tests/mcp_servers/test_mcp_dispatch.py | 1 | AC-6 | test_mcp_dispatch.py | Planned |
| REQ-006 | pin fallout | tests/shared/test_mcp_dedup.py | 1 | AC-6 | test_mcp_dedup.py | Planned |
| REQ-006 | pin fallout | tests/shared/test_mcp_dedup_identity.py | 1 | AC-6 | test_mcp_dedup_identity.py | Planned |
| REQ-007 | Documentation Impact | docs/22_mcp/mcp_02_01_endpoints-and-transport.md | 4 | AC-1, AC-3 | reference-table drift test | Planned |
| REQ-007 | Documentation Impact | docs/22_mcp/mcp_05_01_access-control-and-allowlists.md | 4 | AC-4 | reference-table drift test | Planned |
| REQ-007 | Documentation Impact | docs/41_db/db_08_active_databases.md | 4 | AC-6 | reference-table drift test | Planned |
| REQ-005 | new tests | tests/agent/test_mcp_call_recovery.py | 3 | AC-1, AC-2 | itself | Planned |
| REQ-001 | new tests | tests/mcp_servers/test_call_state_api.py | 2 | AC-4, AC-5 | itself | Planned |
| REQ-004 | new tests | tests/shared/test_mcp_call_state_contract.py | 1 | AC-2 | itself | Planned |
