---
title: "Agent Operations and Observability - Startup and Health"
category: agent
tags:
  - agent
  - operations
  - startup
  - health-probes
  - operational-verification
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_03_operations-and-observability-workflow-observability.md
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# Agent Operations and Observability

- Configuration → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

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

- Workflow definition files must always be loaded at startup. If they are missing or invalid, startup fails. No direct execution fallback is provided.
- In production mode, unreachable health probes are treated as startup failure (FATAL). In local mode, they only issue a warning and continue.
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
- `tool_definitions` do not cause FATAL errors even in strict mode — they are always downgraded to WARNING.
- Failure in `mcp_tool_discovery` is treated as FATAL regardless of whether it is production or local mode. Since tool discovery failure makes all session tool calls impossible, it is critical.

### Restoration of Pending Post-Execution Approvals

If post-execution approvals from a previous session remain unresolved upon agent startup, they are restored from `workflow.sqlite` via `StateStore.find_latest_pending_approval()`. Only one such approval is tracked at a time, applying the latest record across all sessions.

If a restoration value is set while a `pending_approval_task_id` is already configured, a `WARNING` level log is emitted, but the value is overwritten (the process does not abort).

### Resource Cleanup on Shutdown

Resources are closed in the following order within a `finally` block:

1. WAL checkpoint (with PASSIVE $\rightarrow$ TRUNCATE fallback)
2. WAL backup (with path validation)
3. `lifecycle.shutdown_all()`
4. `http.aclose()`

Each step is independently guarded so that if one fails, others still execute. WAL backups are allowed only within paths matching `allowed_root`, and symlinks are resolved before validation.

### SIGINT/SIGTERM Interruption During Startup

If SIGINT/SIGTERM is received during the startup sequence, a `ShutdownInterrupted` exception is raised, triggering a rollback. The HTTP subprocess health polling loop is also immediately interrupted by the shutdown event.

## Known Limitations / Unresolved Issues

- Some branches in `startup.py` have been tested, but their actual behavior in production environments has only been partially verified.
- The WAL checkpoint timeout (default 30 seconds) may need adjustment based on real-world load.
- Information regarding rollback failures is not displayed on the console screen; it can only be checked in the log files.

## Related Docs

- [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md) — Role of `session_diagnostics`
- [05_agent_09_02_data-layer-access-patterns.md](05_agent_09_02_data-layer-access-patterns.md) — DB access patterns
- [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md) — Configuration files
