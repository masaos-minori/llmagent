---
title: "Verification Methods"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_configuration_and_operations.md
source:
  - 04_mcp_06_configuration_and_operations.md
---

# Verification Methods

## Verification Methods

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

### HTTP status code behavior

- **HTTP 200**: Server is fully healthy (`status="ok"`, `ready=true`)
- **HTTP 503**: Server has dependency failures (`status="degraded"`, `ready=false`)

The watchdog inspects both the HTTP status code and the `restart_recommended` body field; restart is only attempted when `restart_recommended=true` or the server is unreachable. HTTP 503 with `restart_recommended=false` (e.g. missing credentials) logs a WARNING but does not restart.

```bash
# Check HTTP status code (not just body)
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8006/health   # 200 if healthy, 503 if degraded
```

### Health probe response examples

**Base response (healthy, all servers):**
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
HTTP 200 — fully healthy.

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
HTTP 503 — `sh` is not found in PATH. Watchdog logs WARNING but does NOT restart (`operator_action_required=true`).

**rag-pipeline-mcp (port 8010) — degraded:**
```json
{
  "status": "degraded",
  "ready": false,
  "liveness": true,
  "restart_recommended": false,
  "operator_action_required": true,
  "dependencies": {"embed_url": "not configured"},
  "details": {}
}
```
HTTP 503 — no embedding URL is set. Watchdog logs WARNING but does NOT restart (`operator_action_required=true`).

**github-mcp (port 8006) — degraded:**
```json
{
  "status": "degraded",
  "ready": false,
  "liveness": true,
  "restart_recommended": false,
  "operator_action_required": true,
  "dependencies": {"github_token": "not_set"},
  "details": {}
}
```
HTTP 503 — GitHub token is not set. Watchdog logs WARNING but does NOT restart (`operator_action_required=true`).

**mdq-mcp (port 8013) — degraded:**
```json
{
  "status": "degraded",
  "ready": false,
  "liveness": true,
  "restart_recommended": false,
  "operator_action_required": true,
  "dependencies": {"db_file": "not found: /opt/llm/db/mdq.sqlite"},
  "details": {"service": "mdq-mcp", "database": "/opt/llm/db/mdq.sqlite"}
}
```
HTTP 503 — database file not found. Watchdog logs WARNING but does NOT restart (`operator_action_required=true`).

**git-mcp (port 8014) — degraded:**
```json
{
  "status": "degraded",
  "ready": false,
  "liveness": true,
  "restart_recommended": false,
  "operator_action_required": true,
  "dependencies": {"git": "git not found in PATH"},
  "details": {}
}
```
HTTP 503 — git is not found in PATH. Watchdog logs WARNING but does NOT restart (`operator_action_required=true`).

### /v1/tools verification

```bash
curl -s http://127.0.0.1:8005/v1/tools | jq '.tools[].name'
```

### Agent REPL check

```
agent[:#N]> /mcp
```

Probes all HTTP servers. Expected: all show `OK` with tool list.

### Startup failure checkpoints

| Failure | Cause | Check |
|---|---|---|
| Server not started | Subprocess failed to start | Check stderr; verify port not in use |
| subprocess timeout | uvicorn fails to start | Check stderr; verify port not in use |
| Tool definition mismatch | Config out of sync | `/mcp` → tool count; compare with config |


---


## Related Documents

- [04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration-file-inventory.md)

## Keywords

configuration
