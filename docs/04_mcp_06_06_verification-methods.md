---
title: "Verification Methods"
area: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
  - 04_mcp_06_12_watchdog-configuration-monitoring.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# Verification Methods

## Health Probes

### Health probes

```bash
# Individual server health checks (all return 4-field nested format)
curl -s http://127.0.0.1:8004/health | jq   # web-search: base response only
curl -s http://127.0.0.1:8005/health | jq   # file-read: dependencies.filesystem
curl -s http://127.0.0.1:8006/health | jq   # github: dependencies.github_token
curl -s http://127.0.0.1:8007/health | jq   # file-write: dependencies.filesystem
curl -s http://127.0.0.1:8008/health | jq   # file-delete: dependencies.filesystem
curl -s http://127.0.0.1:8009/health | jq   # shell: dependencies.shell, details.sandbox_backend
curl -s http://127.0.0.1:8010/health | jq   # rag-pipeline: dependencies.embed_url
curl -s http://127.0.0.1:8012/health | jq   # cicd: dependencies.github_token
curl -s http://127.0.0.1:8013/health | jq   # mdq: details.service
curl -s http://127.0.0.1:8014/health | jq   # git: dependencies.git

# Base response shape: {"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}
```

### HTTP Status Code Behavior

- **HTTP 200**: Server is fully healthy (`status="ok"`, `ready=true`)
- **HTTP 503**: Server has dependency failures (`status="degraded"`, `ready=false`)

`/mcp status` (`McpStatusService.probe_all()`) reads both the HTTP status code and the `restart_recommended`/`operator_action_required` fields in the response body, reflecting them in the `health_reason` column. This is for display only and does not trigger automatic restarts (see [04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md), as the MCP watchdog was removed on 2026-07-16).

```bash
# Check HTTP status code (not just body)
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8006/health   # 200 if healthy, 503 if degraded
```

### Example Health Probe Responses

**Base Response (healthy, common to all servers):**
```json
{
  "status": "ok",
  "ready": true,
  "liveness": true,
  "restart_recommended": false,
  "operator_action_required": false,
  "dependencies": {},
  "details": {}
}
```
HTTP 200 — Fully healthy.

**shell-mcp (port 8009) — degraded:**
```json
{
  "status": "degraded",
  "ready": false,
  "liveness": true,
  "restart_recommended": false,
  "operator_action_required": true,
  "dependencies": {"shell": "sh not found in PATH"},
  "details": {"sandbox_backend": "firejail"}
}
```
HTTP 503 — `sh` not found in PATH. Reflected in `/mcp status`'s `health_reason` as `operator_action_required` (display only; no automatic restart occurs).

Other servers share the same `degraded` response shape (`status`/`ready`/`liveness`/`restart_recommended`/`operator_action_required`/`dependencies`/`details`), with only the content of `dependencies` representing server-specific unmet conditions. All return HTTP 503 and are reflected in `/mcp status`'s `health_reason` as `operator_action_required` (display only; no automatic restart occurs).

| Server (Port) | `dependencies` Example | Meaning |
|---|---|---|
| rag-pipeline-mcp (8010) | `{"embed_url": "not configured"}` | Embedding URL not configured |
| github-mcp (8006) | `{"github_token": "not_set"}` | GitHub token not set |
| mdq-mcp (8013) | `{"db_file": "not found: /opt/llm/db/mdq.sqlite"}` | Database file not found |
| git-mcp (8014) | `{"git": "git not found in PATH"}` | Git not found in PATH |

## Verification via /v1/tools

```bash
curl -s http://127.0.0.1:8005/v1/tools | jq '.tools[].name'
```

## Checking in Agent REPL

```text
agent[:#N]> /mcp
```

Probes all HTTP servers. Expected result: All show `OK` along with their tool lists.

### Troubleshooting Startup Failures

| Failure | Cause | How to Verify |
|---|---|---|
| Server fails to start | Subprocess startup failure | Check stderr; check if port is in use |
| Subprocess timeout | uvicorn startup failure | Check stderr; check if port is in use |
| Tool definition mismatch | Config sync missing | Run `/mcp` → check tool count vs config |

## Standalone Launch (dev/debug)

Each MCP server can be launched individually for local debugging via the unified launcher:

```bash
uv run python scripts/mcp_launcher.py <server_key>      # launch one server standalone
uv run python scripts/mcp_launcher.py --list             # list all discoverable server keys
uv run python scripts/mcp_launcher.py <server_key> --force # bypass the port-collision guard
```

**Why `mcp_servers`, not `mcp`**: the package was renamed from `scripts/mcp` to `scripts/mcp_servers` because the original name collided with the PyPI Model Context Protocol SDK (`mcp`), which is transitively installed via the `semgrep` dev dependency — this caused `ModuleNotFoundError: No module named 'mcp.audit'` when launching a server standalone in the dev venv.

The launcher guards against accidentally starting a server whose port is already bound (e.g., by the running agent) — use `--force` only when intentionally starting a duplicate instance.

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)
- [04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md)

## Keywords

configuration
