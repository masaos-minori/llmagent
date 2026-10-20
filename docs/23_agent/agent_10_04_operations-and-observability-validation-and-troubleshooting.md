---
title: "Agent Operations and Observability - Validation and Troubleshooting"
area: agent
tags:
  - agent
  - operations
  - validation
  - troubleshooting
related:
  - agent_00_document-guide.md
  - agent_10_01_operations-and-observability-startup-and-health.md
  - agent_10_02_operations-and-observability-audit-and-otel.md
  - agent_10_03_operations-and-observability-workflow-observability.md
  - agent_10_05_operations-and-observability-monitoring.md
  - agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
  - agent_03_03_turn-processing-flow-workflow-engine.md
  - agent_08_04_configuration-mcp-approval-obs.md
---

# Agent Operations and Observability

- Configuration → [agent_08_04_configuration-mcp-approval-obs.md](agent_08_04_configuration-mcp-approval-obs.md)

## Workflow Startup Verification

The agent unconditionally verifies the existence of workflow definition files before initializing the orchestrator. There are no settings to disable or degrade this check.

**Expected Path:** `config/workflows/default.json`

### Severity Mapping

The FATAL / WARNING / SKIPPED / OK semantics and the per-check severity rules (`tool_definitions`, `routing_drift`, `mcp_tool_discovery`, `mcp_auth`) are defined once in [Severity Mapping for Startup Verification](agent_10_01_operations-and-observability-startup-and-health.md#severity-mapping-for-startup-verification) in the startup and health document.

### SIGINT/SIGTERM Interruption During Startup Sequence

See [SIGINT/SIGTERM Interruption During Startup](agent_10_01_operations-and-observability-startup-and-health.md#sigintsigterm-interruption-during-startup) in the startup and health document.

### Resource Cleanup on Shutdown

See [Resource Cleanup on Shutdown](agent_10_01_operations-and-observability-startup-and-health.md#resource-cleanup-on-shutdown) in the startup and health document.

## Workflow Deployment Runbook

Workflows are **mandatory** deployment artifacts; there are no settings, environment variables, or deployment flags to disable or bypass them.

### Quick Verification Commands

```bash
# Directly validate workflow definition files (without starting services)
PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json

# Check workflow DB schema tables and versions
sqlite3 <workflow_db_path> ".tables"
sqlite3 <workflow_db_path> "SELECT * FROM workflow_schema_version ORDER BY applied_at DESC;"
```

### Common Failures and Responses

#### Missing `config/workflows/default.json`

**Symptom:** `deploy.sh` exits with `[FATAL] Missing required workflow definition: config/workflows/default.json`.

**Response:** Restore from version control and redeploy.

#### Workflow JSON Parsing Error

**Symptom:** `deploy.sh` or the validator CLI outputs `[FATAL] Invalid workflow definition ...: <JSON parse error>`.

**Response:** Fix the reported JSON syntax error and re-validate before redeploying.

#### Missing Required Stages

**Symptom:** The validator reports `required stages missing: <names>`.

**Response:** Include objects with `id` values for `plan`, `execute`, and `verify` in the workflow definition's `stages` array.

#### Invalid Retry Policy

**Symptom:** The validator reports `retry_policy.max_attempts must be >= 1` or `retry_policy.backoff_sec must be >= 0`.

**Response:** Fix the reported fields and re-validate.

#### Missing or Incomplete `workflow.sqlite`

**Symptom:** `init_db.sh` or `setup_services.sh` outputs `[FATAL] Workflow database schema is missing or incomplete.`

**Response:** Re-run the deployment scripts.

#### Schema Version Mismatch

**Symptom:** Agent startup or deployment scripts report `Workflow schema version mismatch: expected <X>, found <Y>`.

**Response:** Re-run the deployment scripts to apply migrations.

#### Workflow Definition Updates Require Restart

**Description:** Workflow definitions are validated and loaded only once during agent startup. They are NOT hot-reloadable — changes are not applied via `/reload`.

**Response:** After deploying a new definition, fully restart the agent process.

## MCP Server Reloading Semantics

MCP server definitions (transport, url, startup_mode, call_timeout_sec, startup_timeout_sec, tool_names, auth_token, role, cmd, env) are snapshots at the time of restart. `/reload` detects changes in `[mcp_servers.*]` and reports them as requiring a restart, but never applies them to running processes.

`/mcp` / `/mcp status` always reflects the currently running (pre-restart) server settings and does not reflect pending `/reload` changes.

There is no background health polling or automatic restart loop for MCP servers. If a server fails in subprocess mode, `ensure_ready()` will only attempt a restart with the *current* startup configuration during the next tool dispatch — because this is a health-driven recovery and not a configuration reload, pending changes to MCP server definitions are not applied.

Changed MCP server definitions are only applied during a full agent restart.

## Production Security Regression Suite

`tests/integration/test_production_security_regression.py` is the process/integration-level regression suite for Production-grade policy, MCP loopback-only exposure, and MCP authentication. It must prove that:

- a non-production mode is rejected and strict configuration validation runs through the real `ProductionConfigValidator`;
- MCP servers bind only to loopback (verified by real socket inspection) and a wildcard bind is rejected;
- a failed required MCP server aborts startup, a failed non-required one disables only its own tools, and disabled tools are excluded from LLM visibility;
- MCP Bearer authentication rejects missing/invalid tokens and the token is redacted in logs;
- the loopback-bound service is unreachable from outside the loopback interface.

### Platform-Capability Requirements and Manual Fallback

`test_external_unreachability_or_manual_fallback` uses `unshare --net`
network-namespace isolation when this environment grants that capability
(some CI/sandbox/container environments do not). When unavailable, the test
automatically falls back to a manual-equivalent check — binding a probe
socket to a non-loopback local interface address and confirming a
`ConnectionRefused`/timeout when attempting to reach the loopback-bound
service from it — and prints which path it took. If no non-loopback local
address is available to probe (e.g. a fully isolated sandbox whose hostname
itself resolves to loopback), the test reports `SKIPPED` with an explicit
reason rather than a false pass.

To manually verify loopback-only binding and external unreachability without
running the automated suite: start the MCP server in question, confirm
`socket.getsockname()` (or `ss -tlnp` / `netstat -tlnp` at the OS level)
reports a `127.0.0.1` bind address, then attempt a connection to that port
from a different host or network namespace and confirm it is refused or
times out.

## `/context` Interpretation

- **Remaining:** Distance to `context_char_limit` → trigger for compression.
- **Token estimate:** Uses category-aware estimation (per-category ratios defined in `shared/token_estimation.py`).
- **Token limit:** Set to `disabled` if `context_token_limit` is not configured.
- **Memory layer:** Set to `enabled (entries=N)` if `use_memory_layer=True`.

**Implementation Notes:**
- The `/context` token estimate is always the category-aware estimate; the value returned by `/tokenize` is used only for the next turn's history-compression decision, not for display.
- The estimation ratios have a single source, `shared/token_estimation.py`; `agent/services/context_view.py` defines no local ratio constants.

## `/stats` Interpretation

`/stats` reports turn, tool-call and error counts, LLM transport counters (reconnects, heartbeat timeouts, partial completions, parse errors), compression count, token totals and latency.

- **Partial completions:** LLM responses interrupted during streaming are recorded. See [agent_03 Partial-Completion Model](agent_03_03_turn-processing-flow-workflow-engine.md) for details.
- **HB timeouts:** SSE heartbeat timeouts (potential LLM overload).

**Implementation Notes:**
- `/stats` adds conditional lines for a memory consistency failure, an open memory embedding circuit (`[DEGRADED]`), and a hint to run `/session rag-consistency` when a RAG DB is configured.
- `Latency (mean/max)` aggregates only the `"llm"` samples of `ctx.stats.stat_latency`; tool-call latencies are not included.

## Keywords

- agent
- operations
- validation
- troubleshooting
