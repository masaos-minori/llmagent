---
title: "Agent Operations and Observability - Startup and Health"
area: agent
tags:
  - agent
  - operations
  - startup
  - health-probes
  - operational-verification
related:
  - agent_00_document-guide.md
  - agent_10_02_operations-and-observability-audit-and-otel.md
  - agent_10_03_operations-and-observability-workflow-observability.md
  - agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - agent_10_05_operations-and-observability-monitoring.md
  - agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
  - agent_09_01_data-layer-session-db.md
  - agent_09_02_data-layer-access-patterns.md
  - agent_08_04_configuration-mcp-approval-obs.md
---

# Agent Operations and Observability

- Configuration → [agent_08_04_configuration-mcp-approval-obs.md](agent_08_04_configuration-mcp-approval-obs.md)

## Purpose

Documents the agent startup procedure, operational verification, health checks, and resource cleanup during shutdown.

## Design Intent

The startup process is divided into three phases: server start, health check, and restoration of approval states. If an exception occurs in any phase, a rollback is triggered to ensure all started subprocesses are reliably terminated.

`StartupOrchestrator` centrally manages the entire startup sequence. If startup fails, it closes all resources via `shutdown_all()` and re-raises the original exception. Even if the rollback itself fails, the original exception is preserved (only a log is recorded).

SIGTERM/SIGINT signals can be fired even during the startup sequence. Using `asyncio.wait(FIRST_COMPLETED)`, these signals compete with delayed timers; if a shutdown event fires first, the delay is interrupted immediately.

## Responsibility Boundary

- **Scope**: The lifecycle from agent process startup to shutdown.
- **Out of Scope**: Implementation of MCP servers, RAG pipeline details, internal workings of LLM endpoints.
- **Owners**: `agent/startup.py` (`StartupOrchestrator`), `agent/repl.py` (`AgentREPL`).

## Key Constraints

- MCP server `/health` endpoints require the server's Bearer token. The startup readiness poll (`HttpServerLifecycleManager._health_poll_until_ready`), the post-startup verification (`McpServerStarter.verify_health`), the liveness re-check (`verify_running_async`) and the `/mcp` status probe send `Authorization: Bearer <auth_token>` built by `McpServerConfig.auth_headers()`; a missing or wrong token yields HTTP 401 and is treated as unhealthy.
- Workflow definition files must always be loaded at startup. If they are missing or invalid, startup fails. Direct execution fallback is not supported.
- Unreachable LLM/embedding health probes are treated as startup failure (FATAL).
- Embedding dimension mismatches are treated as startup failures to prevent vector search data corruption.
- During rolling upgrades for session startup, the new process's startup is verified before the old process is shut down; if issues arise, the old process is maintained.

## Operational Notes

### Severity Mapping for Startup Verification

| Severity | Meaning | Behavior |
|---|---|---|
| FATAL | Condition preventing startup | Throws `RuntimeError` after all checks complete, aborting startup |
| WARNING | Check performed but problem detected | Continues startup, but requires operator attention |
| SKIPPED | Check could not be performed | Continues startup. Occurs when environment-dependent checks are unavailable |
| OK | Check performed successfully | Indicates normal state (Note: `security_audit` OK means "check completed", not necessarily "no problems found") |

**Important Notes:**
- `routing_drift_live` and `routing_safety_tiers` record no outcome during normal operation (silence means healthy).
- `tool_definitions` follows a unified severity scheme: FATAL when in strict mode, WARNING otherwise (`security_profile` is always `PRODUCTION`, so it does not affect the severity).
- `mcp_tool_discovery` follows the ADR-004 rule: an unreachable or invalid required MCP server (`McpServerConfig.required`), a missing required tool, a duplicate tool name, or an unexpected discovery exception is FATAL and aborts startup; an unreachable or invalid non-required server is WARNING and startup continues with that server's tools disabled. Drift and tool-definition findings are FATAL only in strict mode. See [mcp_06_09](../22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md).
- `mcp_auth` ("1b. MCP authentication check", runs between the security audit and service-readiness checks): FATAL if any `[mcp_servers.*]` entry has an empty `auth_token`, listing every offending server key in one outcome. In practice this is unreachable via a real `McpServerConfig` — construction itself already rejects an empty `auth_token` (see [mcp_06_01](../22_mcp/mcp_06_01_configuration-file-inventory.md)) — so this check only fires for a `ctx` assembled some other way than the normal config-load path. `check_services()` does not short-circuit on an earlier FATAL: every check listed here always runs and reports independently; only the final aggregated `has_fatal` decides whether startup aborts.

### Restoration of Pending Post-Execution Approvals

If post-execution approvals from a previous session remain unresolved upon agent startup, they are restored from `workflow.sqlite` via `StateStore.find_latest_pending_approval()`. Only one such approval is tracked at a time, applying the latest record across all sessions.

If a restoration value is set while a `pending_approval_task_id` is already configured, a `WARNING` level log is emitted and the process does not abort. When the existing value differs from the recovered id, the existing value is preserved (the log reads "Keeping existing pending_approval_task_id X instead of overwriting with Y"). When the values are equal, the assignment is idempotent (the log reads "Overwriting pending_approval_task_id X with Y" but the value is unchanged). When the existing value is `None`, the recovered value is simply assigned (no overwrite log).

### Resource Cleanup on Shutdown

Resources are closed in the following order within a `finally` block:

1. WAL checkpoint (with PASSIVE → TRUNCATE fallback)
2. WAL backup (with path validation)
3. `lifecycle.shutdown_all()`
4. `http.aclose()`

Each step is independently guarded so that if one fails, others still execute. WAL backups are allowed only within paths matching `allowed_root`, and symlinks are resolved before validation.

### SIGINT/SIGTERM Interruption During Startup

If SIGINT/SIGTERM is received during the startup sequence, a `ShutdownInterrupted` exception is raised, triggering a rollback. The HTTP subprocess health polling loop is also immediately interrupted by the shutdown event.

### Secret Masking in MCP Subprocess Failure Reports

When an MCP subprocess fails to start, the tail of its stderr is included in the startup failure report, and a failed first start attempt is logged. Both pass through `agent/secrets_masker.py`, which replaces values written as `key=value` for key names such as `password`, `api_key`, `secret` and `token` (case-insensitive) with a masked form. Only that `key=value` form is recognized; other shapes (for example an `Authorization: Bearer ...` header) are not masked.

### Manual Recovery: workflow.sqlite / eventbus.sqlite

When `workflow.sqlite` or `eventbus.sqlite` becomes corrupted (e.g., disk failure, unexpected shutdown), `recover_corruption()` returns `action="no_recovery_allowed"` for both — ADR-008 INV-18 prohibits automatic restoration for these two domains. Recovery is an operator action. Prefer restoring from a rotation-archive backup (below); fall back to recreating empty databases (Step 6) only when no valid backup exists.

**Step 1 — Stop the agent process completely** (ensure no remaining subprocesses).

**Step 2 — Preserve the corrupted files for forensics:**
```bash
cp workflow.sqlite workflow.sqlite.corrupted
cp eventbus.sqlite eventbus.sqlite.corrupted
```

**Step 3 — Locate available backups.** `rotate_all_dbs()` (`scripts/db/rotation.py`) archives `workflow.sqlite`/`eventbus.sqlite` alongside `rag.sqlite`/`session.sqlite` via the SQLite online backup API, writing WAL-consistent copies to the configured archive directory (`sqlite_archive_dir` in `agent.toml`) named `{stem}_{YYYYMMDD_HHMMSS}{suffix}` in UTC (e.g. `workflow_20260901_063000.sqlite`):
```bash
ARCHIVE_DIR="${SQLITE_ARCHIVE_DIR:?set to the configured sqlite_archive_dir}"
ls -lt "$ARCHIVE_DIR"/workflow_[0-9]*_[0-9]*.sqlite 2>/dev/null
ls -lt "$ARCHIVE_DIR"/eventbus_[0-9]*_[0-9]*.sqlite 2>/dev/null
```
List is sorted newest-first (`-t`); if none are listed, skip to Step 6 (No backup available).

**Note on retention**: archives written by `rotate_all_dbs()`/`rotate_workflow_db()`/`rotate_eventbus_db()` have no automatic cleanup — they accumulate indefinitely in the archive directory unless an operator or external job removes them. This is distinct from `scripts/db/maintenance.py`'s `CorruptArchiveRetentionConfig` (`max_files`/`max_age_days`), which governs only the timestamped `*_corrupt_*` pre-restore safety copies `recover_corruption()` creates for `rag`/`session` — it does not apply to these workflow/eventbus rotation archives.

**Step 4 — Validate a candidate backup**, starting with the most recent and working backward until one passes:
```bash
sqlite3 "$ARCHIVE_DIR/workflow_<YYYYMMDD_HHMMSS>.sqlite" "PRAGMA integrity_check;"
sqlite3 "$ARCHIVE_DIR/eventbus_<YYYYMMDD_HHMMSS>.sqlite" "PRAGMA integrity_check;"
```
Each must print exactly `ok`. Reject and try the next-older archive otherwise.

**Step 5 — Apply the validated backup, then re-verify:**
```bash
cp "$ARCHIVE_DIR/workflow_<YYYYMMDD_HHMMSS>.sqlite" workflow.sqlite
cp "$ARCHIVE_DIR/eventbus_<YYYYMMDD_HHMMSS>.sqlite" eventbus.sqlite
sqlite3 workflow.sqlite "PRAGMA integrity_check;"
sqlite3 eventbus.sqlite "PRAGMA integrity_check;"
```
Both must print `ok` again post-copy before starting the agent. Data committed after the backup's timestamp is lost — this is expected; note the gap when escalating if it matters operationally.

**Step 6 — No valid backup available (all candidates missing or failing integrity check).** Fall back to recreating empty databases — this is a last resort, not the default path. `recover_corruption()` has no reinitialization path for these domains (it only returns `no_recovery_allowed`), so the empty state is produced by removing the corrupted files and running the schema creation functions of `scripts/db/create_schema.py` (Explicit in code — `scripts/db/recovery.py`, `scripts/db/create_schema.py`). The corrupted content is not re-imported; Step 2's `.corrupted` copies are the only remaining record of it.
```bash
rm -f workflow.sqlite workflow.sqlite-wal workflow.sqlite-shm
rm -f eventbus.sqlite eventbus.sqlite-wal eventbus.sqlite-shm
# From the deployment root, with PYTHONPATH set to the deployed scripts directory
uv run python -c 'from db.create_schema import create_workflow_schema, create_eventbus_schema; create_workflow_schema(); create_eventbus_schema()'
```
The recreated databases contain schema only: all workflow state (tasks, attempts, processed events, artifacts) including all pending approvals, and all events, consumer delivery state, and offsets are lost. If the data loss is significant, escalate before proceeding — the removal is irreversible apart from the Step 2 copies.

**Step 7 — Start the agent process again** and confirm normal startup (see Severity Mapping above).

## Known Limitations / Unresolved Issues

- The WAL checkpoint and backup timeouts at shutdown are fixed in `ResourceShutdownCoordinator.close_resources()` and are not configurable; a timeout is recorded as a shutdown error and logged (Explicit in code — `scripts/agent/resource_shutdown_coordinator.py`).
- A failure of the rollback `shutdown_all()` during startup failure is only logged; the original startup exception is re-raised and nothing is shown on the console for the rollback failure (Explicit in code — `scripts/agent/startup.py`).
- Secret masking of MCP subprocess output is incomplete (see Secret Masking in MCP Subprocess Failure Reports).

## Keywords

- agent
- operations
- startup
- health-probes
- operational-verification
