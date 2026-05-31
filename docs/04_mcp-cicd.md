# CI/CD MCP サーバー仕様 (cicd-mcp)

## 1. 概要

GitHub Actions REST API をラップする MCP サーバー。ポート 8012 で起動する。

| 項目 | 値 |
|---|---|
| ポート | 8012 |
| OpenRC サービス名 | `cicd-mcp` |
| 設定ファイル | `config/cicd_mcp_server.toml` |
| 実装 | `mcp/cicd/server.py`, `mcp/cicd/service.py`, `mcp/cicd/models.py` |

## 2. 提供ツール

| ツール名 | 説明 | 安全ティア |
|---|---|---|
| `trigger_workflow` | workflow_dispatch イベントでワークフローをトリガー | `WRITE_DANGEROUS` |
| `get_workflow_runs` | ワークフローの実行履歴一覧を取得 (最大 50 件) | `READ_ONLY` |
| `get_workflow_status` | 指定 run_id のワークフロー実行状態を取得 | `READ_ONLY` |
| `get_workflow_logs` | 指定 run_id のジョブログを取得 (最大 5 ジョブ、256 KB 上限) | `READ_ONLY` |

## 3. アーキテクチャ

```
CiCdMCPServer (FastAPI)
  └── CiCdService          # allowlist ガード + Backend 委譲
        └── CiBackend      # typing.Protocol — GitLab CI 等を将来追加可能
              └── GitHubActionsBackend  # httpx ベース GitHub API クライアント
```

### CiBackend プロトコル

`typing.Protocol` として定義し、`CiCdService` は具体的な Backend クラスに依存しない。
将来 GitLab CI や Jenkins バックエンドを追加する場合は `CiBackend` を実装するだけでよい。

### GitHubActionsBackend

- `_token` フィールドは `__repr__` でマスクされる ("set" / "not set" のみ表示)
- `_auth_headers()` の戻り値をログに渡してはならない (トークン漏洩防止)
- `get_workflow_logs` は GitHub の 302 リダイレクト先 (presigned URL) まで `follow_redirects=True` で追跡する

## 4. セキュリティポリシー

### repo_allowlist (fail-closed)

`cicd_mcp_server.toml` の `repo_allowlist` が空リストの場合、全リポジトリへのアクセスを拒否する。

```toml
repo_allowlist = []   # IMPORTANT: empty = deny all (fail-closed)
```

- 非空の場合は、一覧に含まれるリポジトリのみ許可する (`"owner/repo"` 形式)
- allowlist に含まれないリポジトリへのリクエストは HTTP 403 を返す

### workflow_allowlist (fail-open)

`workflow_allowlist` が空リストの場合、全ワークフローを許可する (fail-open)。

```toml
workflow_allowlist = []   # empty = allow all workflows
```

## 5. 設定ファイル

`config/cicd_mcp_server.toml`:

```toml
repo_allowlist = []       # IMPORTANT: empty = deny all (fail-closed)
workflow_allowlist = []   # empty = allow all
max_log_size_kb = 256
auth_token = ""           # cicd-mcp 自体の Bearer トークン (空 = 認証無効)
github_token = ""         # GitHub Personal Access Token (conf.d/cicd-mcp で設定)
```

`github_token` は OpenRC の `conf.d/cicd-mcp` に `GITHUB_TOKEN=...` として記述し、
`init.d/cicd-mcp` がサービス起動時に読み込む。

## 6. ログ上限と切り捨て

`get_workflow_logs` は以下の制限を適用する。

- 取得ジョブ数: 最大 5 ジョブ (`_MAX_JOBS_FOR_LOGS = 5`)
- ログサイズ: 合計 `max_log_size_kb` KB (デフォルト 256 KB)
- 超過時: `[TRUNCATED: exceeded X KB limit]` のサフィックスを付与して返す
