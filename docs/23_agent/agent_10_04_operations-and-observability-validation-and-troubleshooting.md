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
---

# Agent Operations and Observability

- Configuration → [agent_08_04_configuration-mcp-approval-obs.md](agent_08_04_configuration-mcp-approval-obs.md)

## Workflow Startup Verification

The agent unconditionally verifies the existence of workflow definition files before initializing the orchestrator. There are no settings to disable or degrade this check.

**Expected Path:** `config/workflows/default.json`

### Severity Mapping

| Severity | Meaning | Behavior |
|---|---|---|
| FATAL | Condition preventing startup | Throws `RuntimeError` after all checks complete, aborting startup |
| WARNING | Check performed but problem detected | Continues startup, but requires operator attention |
| SKIPPED | Check could not be performed | Continues startup. Occurs when environment-dependent checks are unavailable |
| OK | Check performed successfully | Indicates normal state (Note: `security_audit` OK means "check completed", not necessarily "no problems found") |

**Important Notes:**
- `routing_drift_live` and `routing_safety_tiers` record no outcome during normal operation (silence means healthy).
- `tool_definitions` follows a unified severity scheme: FATAL when in strict mode (`tool_definitions_strict`), WARNING otherwise.
- `mcp_tool_discovery` failure for a required MCP server (`McpServerConfig.required`) is FATAL and aborts startup; for a non-required server it is WARNING and startup continues with that server's tools disabled (ADR-004).

### SIGINT/SIGTERM Interruption During Startup Sequence

See [SIGINT/SIGTERM Interruption During Startup](agent_10_01_operations-and-observability-startup-and-health.md#sigintsigterm-interruption-during-startup) in the startup and health document.

### Restoration of Pending Post-Execution Approval States

See [Restoration of Pending Post-Execution Approvals](agent_10_01_operations-and-observability-startup-and-health.md#restoration-of-pending-post-execution-approvals) in the startup and health document.

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

`tests/integration/test_production_security_regression.py` is a process/
integration-level regression suite proving Production-grade policy, MCP
loopback-only exposure, and MCP authentication. It covers:

- Production-only policy enforcement (`test_production_only_rejects_local_mode`)
- Strict configuration validation through the real `ProductionConfigValidator`
  (`test_strict_configuration_validation_via_real_startup`)
- MCP server loopback-socket binding, with real socket inspection
  (`test_mcp_server_socket_is_loopback_only`,
  `test_mcp_server_wildcard_bind_is_rejected`)
- Required-vs-optional MCP startup failure handling
  (`test_required_mcp_failure_aborts_startup`,
  `test_optional_mcp_failure_disables_only_that_tool`) and disabled-tool
  LLM-visibility exclusion (`test_disabled_tool_excluded_from_llm_visibility`)
- MCP Bearer-token authentication and log redaction
  (`test_mcp_auth_missing_invalid_valid_token`,
  `test_mcp_auth_token_redacted_in_logs`)
- External unreachability from outside the loopback interface
  (`test_external_unreachability_or_manual_fallback`)

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

``` text
Context state:
  Messages        : 12
  Total chars     : 4,321
  Compress limit  : 8,000
  Remaining       : 3,679 chars until compression
  Compress count  : 1
  System prompt   : default
  Token estimate  : 1,080 (category-aware estimate)
  Token limit     : disabled
  Memory layer    : disabled
Budget breakdown:
  system        :    1,234 chars ( 38%)
   history       :    1,987 chars ( 62%)
```

- **Remaining:** Distance to `context_char_limit` → trigger for compression.
- **Token estimate:** Uses category-aware estimation (ratios: Text: 4.0, Tool Call JSON: 2.5, System Message: 3.5).
- **Token limit:** Set to `disabled` if `context_token_limit` is not configured.
- **Memory layer:** Set to `enabled (entries=N)` if `use_memory_layer=True`.

**Implementation Notes:**
- The Token estimate in `/context` remains constant based on category-aware estimation; the actual value used by `/tokenize` is only used for history compression decisions in the next turn, not for display in `/context`.
- Category-aware estimation ratio constants (Text: 4.0, Tool Call JSON: 2.5, System Message: 3.5) use `RATIO_TEXT`/`RATIO_TOOL_CALL`/`RATIO_SYSTEM` from `shared/token_estimation.py` as the single source. `agent/services/context_view.py::_token_breakdown` imports and uses these and defines no local ratio constants.
- `/context`'s `Approval pending` is derived from turn state. Meanwhile, `/stats`'s `Approval pending` refers to workflow state. While both fields are always set/cleared in pairs by the orchestrator and startup commands, resulting in consistent operational values, they refer to different implementation fields.

## `/stats` Interpretation

``` text
Turns: 5 | Tool calls: 12 | Errors: 1
LLM: retries=0, reconnects=0, HB timeouts=0, partials=0, parse_errors=0
Compress: 1 | Semantic cache hits: 0
Input tokens: 2,048 | Output tokens: 512
Latency (mean/max): llm=1.2s/2.1s, tools=0.3s/0.8s
```

- **Partial completions:** LLM responses interrupted during streaming are recorded. See [agent_03 Partial-Completion Model](agent_03_03_turn-processing-flow-workflow-engine.md) for details.
- **HB timeouts:** SSE heartbeat timeouts (potential LLM overload).
- **Semantic cache hits:** Fixed counter field (`stat_semantic_cache_hits`) that is only reset and displayed; no code path increments it, so it is always 0. The RAG pipeline has no semantic cache. (Explicit in code — `scripts/agent/context.py`, `scripts/agent/commands/cmd_config_stats.py`)
- **Approval pending:** Displayed only if `ctx.workflow.approval_pending=True`.

**Implementation Notes:**
- Actual `/stats` output is key-value format with one item per line, and contains more items than documented here.
- Conditional lines are added: `Memory inconsist.` if `stat_memory_consistency_failures` is true; `Memory embed: CIRCUIT OPEN [DEGRADED]` if the memory embedding circuit breaker is open; and `Hint: Run /session rag-consistency for index integrity status` if `rag_db_configured` is true.
- `Latency (mean/max)` aggregates only the sample array of the `"llm"` key from `ctx.stats.stat_latency`; delay rows for tool calls are not included in this aggregation.

## Keywords

- agent
- operations
- validation
- troubleshooting
