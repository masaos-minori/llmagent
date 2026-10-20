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
# Each probe presents that server's own Bearer token, taken from the environment variable referenced by auth_token in config/agent.toml
curl -s -H "Authorization: Bearer ${MCP_<SERVER_KEY>_AUTH_TOKEN}" http://127.0.0.1:<server_port>/health | jq
```

Base response shape: `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`. Server-specific unmet conditions appear in `dependencies` (for example `shell`, `github_token`, `embed_url`, `db_file`, `git`, `filesystem`) and server-specific state in `details`.

`/health` is authenticated like every other route: a server answers `401` to a probe without a matching Bearer header, which is an authentication failure, not an unhealthy server. This applies to every HTTP MCP server, including mdq-mcp. Real tokens must never be pasted into shell history or documents; export them from the environment.

### HTTP Status Code Behavior

- **HTTP 200**: Server is fully healthy (`status="ok"`, `ready=true`)
- **HTTP 503**: Server has dependency failures (`status="degraded"`, `ready=false`)

The mcp subcommand's `status` action (`McpStatusService.probe_all()`) reads both the HTTP status code and the `restart_recommended`/`operator_action_required` fields in the response body, reflecting them in the `health_reason` column. This is for display only and does not trigger automatic restarts (see [mcp_06_07_mcp-failure-diagnosis.md](mcp_06_07_mcp-failure-diagnosis.md) for manual recovery).

### Degraded responses

A degraded server returns HTTP 503 with `status="degraded"`, `ready=false`, and a server-specific unmet condition in `dependencies` (for example `{"shell": "sh not found in PATH"}` for shell-mcp). The mcp subcommand's `status` action reflects it in `health_reason` as `operator_action_required` (display only; no automatic restart occurs).

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

- Server fails to start or subprocess times out: check the per-server stderr log and whether the port is already in use.
- Tool definition mismatch: configuration was not synchronized; run `mcp` and compare the tool count with config.

## Standalone Launch (dev/debug)

Each MCP server can be launched individually for local debugging via the unified launcher:

```bash
uv run python scripts/mcp_launcher.py <server_key>   # see --list for server keys and --force for the port guard
```

**Why `mcp_servers`, not `mcp`**: the package is `scripts/mcp_servers`, not `scripts/mcp`, because the name `mcp` collides with the PyPI Model Context Protocol SDK (`mcp`), which is transitively installed via the `semgrep` dev dependency — a colliding name causes `ModuleNotFoundError: No module named 'mcp.audit'` when launching a server standalone in the dev venv.

The launcher guards against accidentally starting a server whose port is already bound (e.g., by the running agent) — use `--force` only when intentionally starting a duplicate instance.

---


## Keywords

- configuration
