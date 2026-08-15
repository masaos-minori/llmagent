---
title: "Failure Modes and Operational Readiness"
category: operations
tags:
  - failure-modes
  - readiness
  - degradation
  - operational
related:
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - 04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
source:
  - shared/mcp_health.py
  - agent/startup.py
---

# Failure Modes and Operational Readiness

## Section 1: Failure Mode Overview

### 8 Failure Categories

| Category | Description | Impact | Recovery |
|---|---|---|---|
| MCP Server Unavailable | MCP server health check fails | Capability unavailable | Automatic retry (subprocess), manual restart (persistent) |
| MCP Server Degraded | MCP server responds but with errors | Capability degraded | Operator intervention required |
| Workflow Schema Missing | Required tables not initialized | Agent startup fails | Run `bash deploy/init_db.sh` |
| Workflow Definition Invalid | JSON validation fails | Agent startup fails | Fix JSON per validation error |
| Embedding Service Down | embed-llm health check fails | RAG degraded to fts-only | Restart embed-llm service |
| Memory Layer Circuit Open | Embedding circuit breaker trips | Memory degraded | Wait for cooldown, then verify |
| Database Corruption | SQLite integrity violation | Data loss risk | Restore from backup |
| Network Partition | Internal service communication fails | Multiple capabilities affected | Verify network connectivity |

## Section 2: MCP Failure Behavior

### Per Startup Mode

| Startup Mode | Health Check | Failure Response | Recovery |
|---|---|---|---|
| `none` | None | Server treated as unavailable | Manual configuration change |
| `persistent` | `/health` endpoint | 503 on degraded, retry loop | Operator restarts external server |
| `subprocess` | Watchdog polling | Auto-restart (max attempts) | Manual if restart limit reached |

### Fail-Fast vs Fail-Open

| Security Profile | MCP Startup Failure | REPL Behavior |
|---|---|---|
| `production` | RuntimeError — aborts startup | No REPL started |
| `local` | Warning logged, continues | REPL starts normally |

## Section 3: Workflow Failure Behavior

### 6 Failure Scenarios

| Scenario | Symptom | Failing Component | Remediation |
|---|---|---|---|
| Missing workflow definition | `[FATAL] Missing required workflow definition` | deploy.sh | Add `config/workflows/default.json` |
| Invalid workflow JSON | `[FATAL] Invalid workflow definition ...` | deploy.sh | Fix JSON per validation error |
| Checksum mismatch | `[FATAL] Deployed workflow checksum does not match source` | deploy.sh | Re-run deploy.sh, check filesystem |
| Schema incomplete | `[FATAL] Workflow schema is missing or incomplete` | init_db.sh | Run `bash deploy/init_db.sh` |
| Schema version mismatch | `[FATAL] Workflow schema version mismatch` | setup_services.sh | Run `bash deploy/init_db.sh` |
| Stage execution failure | Task status stuck in pending | WorkflowEngine | Use `/approve` or `/reject` commands |

## Section 4: RAG Failure Behavior

### 6 Failure Scenarios

| Scenario | Symptom | Degraded State | Recovery |
|---|---|---|---|
| Embedding API down | HTTP 503 on `/embedding` | fts-only mode | Restart embed-llm |
| Embedding dimension mismatch | ValueError on insert | Chunk skipped, WARNING logged | Verify embedding_dims config |
| Vector store corruption | sqlite3.DatabaseError | RAG unavailable | Restore from backup |
| FTS index desync | `fts_gap != 0` in consistency check | Search results incomplete | Run `rag_consistency.py` |
| Orphan vector rows | `orphan_vec_count > 0` | Search returns stale results | Run `ingester.py --force` |
| Crawler timeout | Connection timeout on fetch | URL skipped, WARNING logged | Retry crawler execution |

### Degraded Behavior

When embedding is unavailable:
- Existing documents remain searchable via FTS
- New documents cannot be indexed
- `memory_embed_enabled` remains true but embeddings are not generated
- System logs WARNING on each failed embedding attempt

## Section 5: Memory Layer Failure Behavior

### 4 Activation Modes

| Mode | Condition | Behavior |
|---|---|---|
| disabled | `use_memory_layer=false` | No memory operations |
| fts-only | `embed_client.enabled=False` | FTS search only, no embeddings |
| degraded | `circuit_open=True` | Circuit breaker open, skip embedding |
| hybrid | Normal operation | Full embedding + vector search |

### Degraded Conditions

- `circuit_open=True`: More than `failure_threshold` consecutive failures
- `half_open_cooldown_sec` elapsed since last UNAVAILABLE state
- One request allowed through HALF_OPEN state to test recovery

## Section 6: Capability Readiness Model

### Four States

| State | Meaning | HTTP Status | Example |
|---|---|---|---|
| healthy | All dependencies operational | 200 | Normal operation |
| degraded | Some dependencies failing | 503 | One MCP server unavailable |
| unavailable | Critical dependency missing | 503 | Embedding service down |
| unknown | Cannot determine status | N/A | Health check timeout |

### Capability-Level Readiness

| Capability | Required Services | Optional Services | Degraded When | Unavailable When |
|---|---|---|---|---|
| Repository Operations | git-mcp | github-mcp | git-mcp degraded | git-mcp unavailable |
| File Operations | file-mcp | — | file-mcp degraded | file-mcp unavailable |
| Code Search | mdq-mcp | — | mdq-mcp degraded | mdq-mcp unavailable |
| Web Search | web-search-mcp | — | web-search-mcp degraded | web-search-mcp unavailable |
| CI/CD | cicd-mcp | — | cicd-mcp degraded | cicd-mcp unavailable |
| Shell Execution | shell-mcp | — | shell-mcp degraded | shell-mcp unavailable |
| Document Retrieval | rag-pipeline-mcp | embed-llm | embed-llm down | rag-pipeline-mcp unavailable |
| GitHub Operations | github-mcp | — | github-mcp degraded | github-mcp unavailable |
| Local Git | git-mcp | — | git-mcp degraded | git-mcp unavailable |
| Memory Search | embed-llm, rag-pipeline-mcp | — | embed-llm down | Both unavailable |

## Section 7: Operator-Facing Examples

### Concrete User-Facing Messages

**Scenario 1: MCP Server Unavailable**
```
WARNING [workflow] MCP server 'git-mcp' unavailable after 3 retries.
Repository operations will be unavailable until the server recovers.
```

**Scenario 2: Embedding Service Down**
```
WARNING RAG degraded: embedding service unavailable.
Existing documents remain searchable via FTS.
New documents will not be indexed until the service recovers.
```

**Scenario 3: Workflow Schema Missing**
```
[FATAL] Session schema missing. Run: bash deploy/init_db.sh to initialize the database.
```

**Scenario 4: Memory Circuit Breaker Trips**
```
WARNING Memory layer degraded: circuit breaker open.
Embedding will be skipped until cooldown expires.
```

**Scenario 5: Fail-Closed Allowlist Empty**
```
WARNING Security posture summary — fail-closed (deny when empty): command_allowlist, allowed_repo_paths; fail-open (allow when empty): tool.allowed_tools
```

## Related Documents

- [Fail-Open/Fail-Closed and Risk Tiers](04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md)
- [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook)
- [RAG Consistency Check](03_rag_05_2-execution-guide.md#26-rag-integrity-check)

## Keywords

failure-modes
readiness
degradation
operational
health
