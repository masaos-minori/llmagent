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
| `get_workflow_runs` | ワークフローの実行履歴一覧を取得 (デフォルト 10 件、最大 50 件) | `READ_ONLY` |
| `get_workflow_status` | 指定 run_id のワークフロー実行状態を取得 | `READ_ONLY` |
| `get_workflow_logs` | 指定 run_id のジョブログを取得 (最大 5 ジョブ、256 KB 上限) | `READ_ONLY` |

### ツール引数仕様

**`trigger_workflow`**

| 引数 | 型 | デフォルト | 説明 |
|---|---|---|---|
| `repo` | `str` | 必須 | リポジトリスラグ (`owner/repo` 形式) |
| `workflow` | `str` | 必須 | ワークフローファイル名 (例: `ci.yml`) またはワークフロー ID |
| `ref` | `str` | `"main"` | ワークフローを実行するブランチ名、タグ、または SHA |
| `inputs` | `dict[str, str]` | `{}` | ワークフローへの入力パラメータ (キーと値のペア) |

**`get_workflow_runs`**

| 引数 | 型 | デフォルト | 説明 |
|---|---|---|---|
| `repo` | `str` | 必須 | リポジトリスラグ (`owner/repo` 形式) |
| `workflow` | `str` | 必須 | ワークフローファイル名またはワークフロー ID |
| `limit` | `int` | `10` | 返却する最大件数 (1〜50 の範囲) |

**`get_workflow_status`**

| 引数 | 型 | デフォルト | 説明 |
|---|---|---|---|
| `repo` | `str` | 必須 | リポジトリスラグ |
| `run_id` | `int` | 必須 | ワークフロー実行 ID (正の整数) |

**`get_workflow_logs`**

| 引数 | 型 | デフォルト | 説明 |
|---|---|---|---|
| `repo` | `str` | 必須 | リポジトリスラグ |
| `run_id` | `int` | 必須 | ワークフロー実行 ID (正の整数) |

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

---

## 7. クラス API

`CiCdMCPServer` は `MCPServer` を継承し、HTTP モード起動ロジックを提供する。`MCPServer` 共通 API は `docs/06_ref-mcp.md` §2 を参照。

| クラス属性 | 値 | 説明 |
|---|---|---|
| `server_name` | `"cicd-mcp"` | MCP `initialize` レスポンスのサーバ識別名 |
| `server_version` | `"1.0.0"` | バージョン文字列 |
| `http_port` | `8012` | HTTP モード待受ポート |
| `app_module` | `"mcp.cicd.server:app"` | uvicorn 起動ターゲット |
| `mcp_tools` | `_MCP_TOOLS` | `tools/list` に返すツール定義 (4 種) |

| メソッド | 説明 |
|---|---|
| `dispatch(name, args) -> tuple[str, bool]` | `_dispatch_cicd_tool(name, args)` に委譲する。`CiCdService.get_dispatch_table()` でツール名を解決し `(result_text, is_error)` を返す |

**サービスクラス**

`CiCdService` (`mcp/cicd/service.py`): `CiCdService(cfg: dict[str, Any], backend: CiBackend)` で初期化する。`repo_allowlist` / `workflow_allowlist` のガードチェックを行い `CiBackend` に委譲する。`_assert_allowed_repo()` は空リスト時に fail-closed で 403 を返す。`_assert_allowed_workflow()` は空リスト時に全ワークフローを許可 (fail-open)。`_parse_repo()` は `owner/repo` 形式の検証を行い、不正フォーマット時は 400 を返す。`get_dispatch_table()` でツール名 → ハンドラのディスパッチテーブルを返す。

`GitHubActionsBackend` (`mcp/cicd/service.py`): `GitHubActionsBackend(github_token, http: httpx.AsyncClient, max_log_size_kb)` で初期化する。httpx ベースの GitHub Actions REST API クライアント。`_token` は `__repr__` でマスクされ (`"set"` / `"not set"` のみ表示)、`_auth_headers()` の戻り値をいかなるロガーにも渡してはならない。ログ取得時は GitHub の 302 リダイレクト先まで `follow_redirects=True` で追跡する。

`_check_response()` の HTTP ステータスコード処理:

| ステータス | 処理 |
|---|---|
| 204 | `trigger_workflow` の成功 (レスポンスボディなし) |
| 404 | HTTPException(404) を raise |
| 422 | レスポンスの `message` フィールドを含む HTTPException(422) を raise |
| 401 / 403 | レート制限の場合 `X-RateLimit-Reset` を含む HTTPException(403)、それ以外は `message` を含む HTTPException(403) |
| その他非 2xx | HTTPException(502) を raise |

**HTTP エンドポイント `POST /v1/call_tool`**

```json
// リクエスト
{"name": "get_workflow_runs", "args": {"repo": "owner/repo", "workflow": "ci.yml", "limit": 5}}

// レスポンス
{"result": "{\"repo\": \"owner/repo\", \"workflow\": \"ci.yml\", \"runs\": [...]}", "is_error": false}
```
