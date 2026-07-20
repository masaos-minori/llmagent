---
title: "Verification Methods"
category: mcp
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

## Verification Methods

### ヘルスプローブ

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

### HTTPステータスコードの挙動

- **HTTP 200**: サーバは完全に健全（`status="ok"`、`ready=true`）
- **HTTP 503**: サーバに依存関係の失敗がある（`status="degraded"`、`ready=false`）

`/mcp status`（`McpStatusService.probe_all()`）はHTTPステータスコードと、レスポンスbody内の `restart_recommended`/`operator_action_required` フィールドの両方を読み取り、`health_reason` 列に反映する。これは表示のみであり、自動的な再起動は行わない（MCP watchdogは2026-07-16に削除された。[04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md) を参照）。

```bash
# Check HTTP status code (not just body)
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8006/health   # 200 if healthy, 503 if degraded
```

### ヘルスプローブレスポンスの例

**ベースレスポンス（healthy、全サーバ共通）:**
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
HTTP 200 — 完全に健全。

**shell-mcp（port 8009）— degraded:**
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
HTTP 503 — PATH内に `sh` が見つからない。`/mcp status` の `health_reason` に `operator_action_required` として反映される（表示のみ；自動的な再起動は行われない）。

**rag-pipeline-mcp（port 8010）— degraded:**
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
HTTP 503 — embedding URLが設定されていない。`/mcp status` の `health_reason` に `operator_action_required` として反映される（表示のみ；自動的な再起動は行われない）。

**github-mcp（port 8006）— degraded:**
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
HTTP 503 — GitHubトークンが設定されていない。`/mcp status` の `health_reason` に `operator_action_required` として反映される（表示のみ；自動的な再起動は行われない）。

**mdq-mcp（port 8013）— degraded:**
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
HTTP 503 — databaseファイルが見つからない。`/mcp status` の `health_reason` に `operator_action_required` として反映される（表示のみ；自動的な再起動は行われない）。

**git-mcp（port 8014）— degraded:**
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
HTTP 503 — PATH内にgitが見つからない。`/mcp status` の `health_reason` に `operator_action_required` として反映される（表示のみ；自動的な再起動は行われない）。

### /v1/tools による検証

```bash
curl -s http://127.0.0.1:8005/v1/tools | jq '.tools[].name'
```

### Agent REPLでの確認

```
agent[:#N]> /mcp
```

全HTTPサーバをプローブする。期待される結果: すべてがtool一覧とともに `OK` を表示する。

### 起動失敗時のチェックポイント

| 失敗 | 原因 | 確認方法 |
|---|---|---|
| サーバが起動しない | subprocessの起動失敗 | stderrを確認；ポートが使用中でないか確認 |
| subprocessタイムアウト | uvicornの起動失敗 | stderrを確認；ポートが使用中でないか確認 |
| Tool定義の不一致 | configの同期漏れ | `/mcp` → tool数を確認し、configと比較 |

## Standalone launch (dev/debug)

Each MCP server can be launched individually for local debugging via the unified launcher:

```bash
uv run python scripts/mcp_launcher.py <server_key>      # launch one server standalone
uv run python scripts/mcp_launcher.py --list             # list all discoverable server keys
uv run python scripts/mcp_launcher.py <server_key> --force # bypass the port-collision guard
```

**Why `mcp_servers`, not `mcp`**: the package was renamed from `scripts/mcp` to
`scripts/mcp_servers` because the original name collided with the PyPI Model Context
Protocol SDK (`mcp`), which is transitively installed via the `semgrep` dev dependency —
this caused `ModuleNotFoundError: No module named 'mcp.audit'` when launching a server
standalone in the dev venv.

The launcher guards against accidentally starting a server whose port is already bound
(e.g., by the running agent) — use `--force` only when intentionally starting a
duplicate instance.

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)
- [04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md)

## Keywords

configuration
