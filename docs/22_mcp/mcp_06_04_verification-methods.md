---
title: "Verification Methods"
area: mcp
tags:
  - mcp
  - configuration
related:
  - mcp_00_document-guide.md
  - mcp_06_01_configuration-file-inventory.md
  - mcp_06_07_mcp-failure-diagnosis.md
---

# Verification Methods

## Health Probes

### Health probes

```bash
# Individual server health checks (all return the nested format shown below)
# Each probe presents the server's own Bearer token, taken from the environment variable that `auth_token` in config/agent.toml references
curl -s -H "Authorization: Bearer ${MCP_WEB_SEARCH_AUTH_TOKEN}" http://127.0.0.1:<web_search_port>/health | jq   # web-search: details.provider, details.browser_provider (dependencies on repeated failures)
curl -s -H "Authorization: Bearer ${MCP_FILE_READ_AUTH_TOKEN}" http://127.0.0.1:<file_read_port>/health | jq   # file-read: dependencies.filesystem
curl -s -H "Authorization: Bearer ${MCP_GITHUB_AUTH_TOKEN}" http://127.0.0.1:<github_port>/health | jq   # github: dependencies.github_token
curl -s -H "Authorization: Bearer ${MCP_FILE_WRITE_AUTH_TOKEN}" http://127.0.0.1:<file_write_port>/health | jq   # file-write: dependencies.filesystem
curl -s -H "Authorization: Bearer ${MCP_FILE_DELETE_AUTH_TOKEN}" http://127.0.0.1:<file_delete_port>/health | jq   # file-delete: dependencies.filesystem
curl -s -H "Authorization: Bearer ${MCP_SHELL_AUTH_TOKEN}" http://127.0.0.1:<shell_port>/health | jq   # shell: dependencies.shell, details.sandbox_backend
curl -s -H "Authorization: Bearer ${MCP_RAG_PIPELINE_AUTH_TOKEN}" http://127.0.0.1:<rag_pipeline_port>/health | jq   # rag-pipeline: dependencies.embed_url
curl -s -H "Authorization: Bearer ${MCP_CICD_AUTH_TOKEN}" http://127.0.0.1:<cicd_port>/health | jq   # cicd: dependencies.github_token
curl -s -H "Authorization: Bearer ${MCP_MDQ_AUTH_TOKEN}" http://127.0.0.1:<mdq_port>/health | jq   # mdq: details.service
curl -s -H "Authorization: Bearer ${MCP_GIT_AUTH_TOKEN}" http://127.0.0.1:<git_port>/health | jq   # git: dependencies.git

# Base response shape: {"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}
```

`/health` is authenticated like every other route: a server that verifies the Bearer token answers `401` to a probe without the header, which is an authentication failure, not an unhealthy server. Two cases need no valid token: mdq-mcp does not verify Bearer tokens at the HTTP layer, and web-search admits `/health` from a loopback client without a token. Supplying the header on those probes is harmless. Real tokens must never be pasted into shell history or documents; export them from the environment.

### HTTP Status Code Behavior

- **HTTP 200**: Server is fully healthy (`status="ok"`, `ready=true`)
- **HTTP 503**: Server has dependency failures (`status="degraded"`, `ready=false`)

The mcp subcommand's `status` action (`McpStatusService.probe_all()`) reads both the HTTP status code and the `restart_recommended`/`operator_action_required` fields in the response body, reflecting them in the `health_reason` column. This is for display only and does not trigger automatic restarts (see [mcp_06_07_mcp-failure-diagnosis.md](mcp_06_07_mcp-failure-diagnosis.md) for manual recovery).

```bash
# Check HTTP status code (not just body)
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer ${MCP_GITHUB_AUTH_TOKEN}" http://127.0.0.1:<github_port>/health   # 200 if healthy, 503 if degraded
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

**shell-mcp — degraded:**
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
HTTP 503 — `sh` not found in PATH. Reflected in the mcp subcommand's `status` action's `health_reason` as `operator_action_required` (display only; no automatic restart occurs).

Other servers share the same `degraded` response shape (`status`/`ready`/`liveness`/`restart_recommended`/`operator_action_required`/`dependencies`/`details`), with only the content of `dependencies` representing server-specific unmet conditions. All return HTTP 503 and are reflected in the mcp subcommand's `status` action's `health_reason` as `operator_action_required` (display only; no automatic restart occurs).

| Server (Port) | `dependencies` Example | Meaning |
|---|---|---|
| rag-pipeline-mcp | `{"embed_url": "not configured"}` | Embedding URL not configured |
| github-mcp | `{"github_token": "not_set"}` | GitHub token not set |
| mdq-mcp | `{"db_file": "not found: <db_path>"}` | Database file not found |
| git-mcp | `{"git": "git not found in PATH"}` | Git not found in PATH |

## Verification via /v1/tools

```bash
curl -s http://127.0.0.1:<file_read_port>/v1/tools | jq '.tools[].name'
```

## Checking in Agent REPL

```text
> /mcp status
```

Probes all HTTP servers. Expected result: All show `OK` along with their tool lists.

### Troubleshooting Startup Failures

| Failure | Cause | How to Verify |
|---|---|---|
| Server fails to start | Subprocess startup failure | Check stderr; check if port is in use |
| Subprocess timeout | uvicorn startup failure | Check stderr; check if port is in use |
| Tool definition mismatch | Config sync missing | Run `mcp` → check tool count vs config |

## Standalone Launch (dev/debug)

Each MCP server can be launched individually for local debugging via the unified launcher:

```bash
uv run python scripts/mcp_launcher.py <server_key>      # launch one server standalone
uv run python scripts/mcp_launcher.py --list             # list all discoverable server keys
uv run python scripts/mcp_launcher.py <server_key> --force # bypass the port-collision guard
```

**Why `mcp_servers`, not `mcp`**: the package is `scripts/mcp_servers`, not `scripts/mcp`, because the name `mcp` collides with the PyPI Model Context Protocol SDK (`mcp`), which is transitively installed via the `semgrep` dev dependency — a colliding name causes `ModuleNotFoundError: No module named 'mcp.audit'` when launching a server standalone in the dev venv.

The launcher guards against accidentally starting a server whose port is already bound (e.g., by the running agent) — use `--force` only when intentionally starting a duplicate instance.

---


## Keywords

- configuration
