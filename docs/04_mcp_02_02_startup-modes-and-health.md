---
title: "MCP Startup Modes, Bearer Auth, Truncation, and Health Responses"
category: mcp
tags:
  - mcp
  - auth
  - health
  - startup
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_02_01_endpoints-and-transport.md
  - 04_mcp_02_03_audit-logging-and-errors.md
source:
  - 04_mcp_02_protocol_and_transport.md
---

# MCP プロトコルとトランスポート: 起動モード・認証・ヘルスチェック

## HTTP 起動モード

| 観点 | `persistent` モード | `subprocess` モード |
|---|---|---|
| プロセス管理 | 外部で管理（既存プロセス） | エージェント起動時に uvicorn を起動 |
| リクエスト形式 | `/v1/call_tool` への POST | `/v1/call_tool` への POST |
| 並行性 | uvicorn async | uvicorn async |
| セッション ID ヘッダー | `X-Session-Id` | `X-Session-Id` |
| ツール一覧チェック | `GET /v1/tools` | `GET /v1/tools` |
| ヘルスチェック | `GET /health` | 起動時に `/health` をポーリング |

---

### 標準的な `/health` レスポンスのセマンティクス

全 MCP サーバーの `/health` エンドポイントは、レスポンスフィールドについて一貫したセマンティクスに従う。

**`status`**: 完全に健全な場合は `"ok"`、依存関係の失敗が検出された場合は `"degraded"`。

**`ready`**: 依存関係の失敗がない場合は `true`、いずれかの依存関係が失敗している場合は `false`。

**`liveness`**: デフォルトでは `true`（基底クラス）; サブクラスはプロセスがリクエストを受け付けられない致命的な内部状態を示すためにオーバーライドできる。

**`restart_recommended`**: `true` は、プロセスを再起動することで障害が解決する可能性があることをウォッチドッグに伝える。`false` は再起動しても効果がないことを意味する（例: 認証情報の欠落はオペレーターの対応が必要）。

**`operator_action_required`**: 人間による対応が必要な場合（認証情報の欠落、バイナリの欠落など）に `true`。ウォッチドッグは WARNING をログに記録するが、これが `true` かつ `restart_recommended=false` の場合は再起動を行わない。

**`dependencies`**: 依存関係名 → エラーメッセージの Dict。健全な場合は空。

**`details`**: サーバー固有の補足情報（例: `sandbox_backend`, `service`）。該当しない場合は空の dict。

**HTTP ステータスコード**:
- `status="ok"` かつ `ready=true`（完全に健全）の場合は `200`
- `status="degraded"` または `ready=false`（依存関係の失敗）の場合は `503`

**依存関係の値**: 空でない依存関係の値（`"not configured"`, `"not_set"`, `"check failed"` など）はいずれも degraded 状態を構成する — 全ての依存関係が満たされるまでサーバーは健全ではない。これらの値は単なる情報提供ではなく、常に実際の欠落または失敗した依存関係を示す。

**ウォッチドッグの挙動**: ウォッチドッグ（`agent/repl_health.py`）は HTTP ステータスコードと `restart_recommended` の本文フィールドの両方を検査する。再起動は `restart_recommended` によって制御される。
- `reachable=False`（HTTP レスポンスなし）: 再起動を試みる（subprocess モード、max_restarts 制限内）
- `reachable=True` かつ `restart_recommended=true`: 上記と同様に再起動を試みる
- `reachable=True` かつ `restart_recommended=false`: 再起動なし; `operator_action_required=true` の場合は WARNING をログに記録

**健全なレスポンスの例**:
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

**degraded なレスポンスの例**（`operator_action_required=true` — 認証情報の欠落、再起動なし）:
```json
{
  "status": "degraded",
  "ready": false,
  "liveness": true,
  "restart_recommended": false,
  "operator_action_required": true,
  "dependencies": {
    "github_token": "not_set"
  },
  "details": {}
}
```

---

---

## Bearer 認証

`McpServerConfig.auth_token` が空でない場合:
- サーバー側: `attach_auth_middleware(app, token)` がミドルウェアを登録し、
  `Authorization: Bearer <token>` を検証する。不一致のリクエストは HTTP 401 を受け取る。
- クライアント側: `HttpTransport` が全ての POST に `Authorization: Bearer <token>` を注入する。
- `auth_token` が空の場合: 認証チェックはスキップされる; `X-Request-Id` の注入のみが有効。

---

## レスポンスの切り詰め

結果が 512 KB を超える場合:
```
[TRUNCATED: {total:,} bytes total, showing {actual_visible:,} bytes]
```

- `total_bytes` = 元のバイト数（切り詰め前）
- `actual_visible_bytes` = 実際に表示されるバイト数（切り詰め境界にマルチバイト UTF-8 文字がある場合、512 KB より少なくなることがある）
- `mcp_servers/server.py` のメタデータ付き切り詰めメソッドにより実装

**注記:** サフィックスは設定された上限ではなく、実際に表示されるバイト数（`actual_visible_bytes`）を示す。ASCII テキストの場合、これは 512 KB（524,288 バイト）と等しくなる。境界にマルチバイト文字を含む UTF-8 テキストの場合、わずかに少なくなることがある。

**重要:** HTTP レスポンスメタデータ内の `total_bytes` と `actual_visible_bytes` フィールドは、切り詰め後のテキストサイズではなく、元のディスパッチ出力サイズを表す。これにより、クライアントは切り詰め不要な短いレスポンスと、切り詰められた長いレスポンスを区別できる。

---

## サーバー固有のヘルスレスポンスフィールド

| サーバー | `/health` のオーバーライド |
|---|---|
| web-search-mcp | No overrides (returns `{"status":"ok","ready":true}`) |
| github-mcp | `dependencies.github_token` (`"not_set"`) |
| mdq-mcp | `details.service: "mdq-mcp"`, `details.document_count`, `details.chunk_count`, `details.fts_row_count`, `details.last_indexed`, `details.stale_document_count`; checks `documents`, `chunks`, `chunks_fts` tables and triggers `chunks_ai/ad/au`; stale detection via `documents.mtime_ns` (nanoseconds) |
| shell-mcp | `dependencies.shell` (`"sh not found in PATH"`/`"check failed"`); `details.sandbox_backend` (`"firejail"` or `"none"`) |
| file-read-mcp | `dependencies.filesystem` (`"/workspace is not a directory"`/`"check failed: <error>"`) |
| file-write-mcp | `dependencies.filesystem` (`"/workspace is not a directory"`/`"check failed: <error>"`) |
| file-delete-mcp | `dependencies.filesystem` (`"/workspace is not a directory"`/`"check failed: <error>"`) |
| rag-pipeline-mcp | `dependencies` (`embed_url: "not configured"` / `config: "check failed"`) |
| git-mcp | `dependencies.git` (`"git not found in PATH"`/`"check failed"`) |
| cicd-mcp | `dependencies` (`github_token: "not_set"` / `config: "check failed"`) |

---

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_02_01_endpoints-and-transport.md`
- `04_mcp_02_03_audit-logging-and-errors.md`

## Keywords

mcp
protocol
transport
auth
bearer
health
truncation
watchdog
repl_health
