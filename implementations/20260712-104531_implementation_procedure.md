# GitHub MCP サーバー循環インポート修正 — 実装手順書

## 1. Goal

GitHub MCP サーバーの起動失敗を修正する。`server.py` のモジュールレベルでの循環インポート（`server.py → server_file.py → server_common.py → server.py`）により `ImportError: cannot import name 'router' from 'mcp_servers.github.server_file'` が発生し、GitHub 関連ツールがすべて使えなくなる問題を解消する。

## 2. Scope

**In-Scope**:
- `/home/sugimoto/llmagent/scripts/mcp_servers/github/server.py` — モジュールレベルのルーターインポートを遅延インポートへ変更

**Out-of-Scope**:
- CICD MCP サーバーのエラー（`GITHUB_TOKEN` 未設定）— 別の原因であり本件と無関係
- `/opt/llm/scripts/mcp/github/` ディレクトリ — 空のディレクトリであり古い構成の残骸
- 他の MCP サーバーの循環参照チェック — GitHub に限定して対応。他は別途調査・対応

## 3. Requirements

### Functional Requirements
- GitHub MCP サーバーがエラーなく起動すること
- GitHub 関連ツール（create_branch, create_or_update_file, push_files, delete_file, create_issue, add_issue_comment, create_pull_request, update_pull_request, merge_pull_request など）が正常に動作すること

### Non-Functional Requirements
- 初回リクエスト時のオーバーヘッドは無視できる程度であること
- 既存のテスト（78件）が全てパスすること

### Assumptions
1. `server_common.py` は既に遅延インポートになっている（確認済み：`_get_service()`, `_info()` 関数内で `from mcp_servers.github.server import _service` / `logger` を遅延インポートしている）。修正不要。
2. `server_file.py` も既に遅延インポートになっている（確認済み：各エンドポイント関数内で `_get_service`, `_info` を遅延インポートしている）。修正不要。
3. 問題の原因は `server.py` のみ。モジュールレベルで `from mcp_servers.github.server_file import router as file_router` などルーターをインポートしており、これが `server_file.py → server_common.py → server.py` のループを生成する。

### Dependencies
- FastAPI（ルーター登録用）
- uv（仮想環境管理）

## 4. Architecture

### Main Components & Responsibility Boundaries

| コンポーネント | 責任 |
|---|---|
| `server.py` | アプリケーションの中心。ルーターの遅延インポート、ツールディスパッチ、MCP統合 |
| `server_repository.py` | リポジトリ操作ルーター（6エンドポイント） |
| `server_file.py` | ファイル操作ルーター（4エンドポイント） |
| `server_issues.py` | イシュー操作ルーター（5エンドポイント） |
| `server_pull_requests.py` | プルリクエストラウター（6エンドポイント） |
| `server_common.py` | ルーター共通ヘルパー（`_get_service()`, `_info()`） |

### Control Flow

```
クライアント → /v1/call_tool → _dispatch_github_tool() → GitHubService.get_dispatch_table() → ツール実行
```

### Concurrency Model

非同期（`asyncio`）。FastAPI + Starlette による非同期 HTTP サーバー。

### Dependency Graph

```
server.py ──→ models, service_dispatch, service_init, tools, audit, dispatch, health_response, MCPServer
server_common.py ──→ server.py (_get_service(), _info()) [遅延インポート]
server_repository.py ──→ server_common.py, models, service_dispatch [Depends経由]
server_file.py ──→ server_common.py, models, service_dispatch [Depends経由]
server_issues.py ──→ server_common.py, models, service_dispatch [Depends経由]
server_pull_requests.py ──→ server_common.py, models, service_dispatch [Depends経由]
```

**重要**: `server_common.py` から `server.py` への依存は、`_get_service()` および `_info()` 内の遅延インポートによってのみ行われるため、モジュールレベルでの循環インポートは発生しない。

## 5. Module Design

### Package Layout

```
scripts/mcp_servers/github/
├── server.py              # アプリケーション中心
├── server_repository.py   # リポジトリ操作ルーター
├── server_file.py         # ファイル操作ルーター
├── server_issues.py       # イシュー操作ルーター
├── server_pull_requests.py # プルリクエストラウター
├── server_common.py       # ルーター共通ヘルパー
├── models.py              # データモデル
├── service_dispatch.py    # サービスディスパッチ
├── service_init.py        # サービス初期化
├── tools.py               # ツール定義
└── exception_handlers.py  # 例外ハンドラ
```

### Module Responsibilities

| モジュール | 責任 |
|---|---|
| `server.py` | アプリケーションの中心。ルーターの遅延インポート、ツールディスパッチ、MCP統合 |
| `server_repository.py` | リポジトリ操作ルーター（6エンドポイント） |
| `server_file.py` | ファイル操作ルーター（4エンドポイント） |
| `server_issues.py` | イシュー操作ルーター（5エンドポイント） |
| `server_pull_requests.py` | プルリクエストラウター（6エンドポイント） |
| `server_common.py` | ルーター共通ヘルパー（`_get_service()`, `_info()`） |

### Dependency Direction

```
models → service_dispatch → server_repository/file/issues/pull_requests → server
```

**ゼロ循環インポートの保証**:
- `server.py` はルーターをモジュールレベルでインポートしない
- ルーターは `_include_routers()` 関数内で遅延インポートされる
- ルーターは `server_common.py` を `Depends` 経由で間接的に利用

## 6. Interface Design

### Public Functions

```python
def _include_routers() -> None:
    """ルーターを遅延インポートしてアプリに登録する。"""
    from mcp_servers.github.server_file import router as file_router
    from mcp_servers.github.server_issues import router as issues_router
    from mcp_servers.github.server_pull_requests import router as pr_router
    from mcp_servers.github.server_repository import router as repo_router
    app.include_router(repo_router)
    app.include_router(file_router)
    app.include_router(issues_router)
    app.include_router(pr_router)
```

### Dependency Injection

```python
@router.post("/get_file_contents", response_model=GetFileContentsResponse)
async def get_file_contents(
    req: GetFileContentsRequest,
    svc: GitHubService = Depends(_get_service),  # 遅延インポート経由
) -> GetFileContentsResponse:
    ...
```

## 7. Data Model & Serialization

既存の Pydantic モデル（`models.py`）を変更しない。データモデルの変更は本タスクの範囲外。

## 8. Error Handling & Resource Lifecycle

### Failure Modes

| フェイチャー | 検出方法 | 対応 | ログ | ユーザー可視性 |
|---|---|---|---|---|
| 循環インポート | ImportError | アボート | なし | エラーメッセージ |
| GITHUB_TOKEN 未設定 | `_GITHUB_TOKEN` が空 | フォールバック | なし | `/health` で表示 |

### Logging Pattern

```python
logger = logging.getLogger(__name__)
logger.error("descriptive_message key=value key2=%s", val)
```

## 9. Configuration

- `github_mcp_server.toml` — GitHub トークンなどの設定
- `GITHUB_TOKEN` 環境変数 — サービス初期化時に使用

## 10. Test Strategy

### Unit Tests

| ターゲット | テスト戦略 | ツール/コマンド | 期待結果 |
|---|---|---|---|
| `server.py` | ユニット — インポートテスト | `python -c "from mcp_servers.github.server import app; print('OK:', app.title)"` | `OK: github-mcp` が出力される |
| `server.py` | 統合 — サーバー起動 | `timeout 8 uv run --directory /opt/llm python /opt/llm/scripts/mcp_servers/github/server.py` | エラーなく起動・シャットダウン |
| `server.py` | 統合 — ヘルスエンドポイント | `curl http://localhost:8006/health` | HTTP 200 が返る |
| Agent | 統合 — エージェント再起動 | エージェントを再起動 | GitHub MCP サーバーが正常に起動する |
| GitHub tools | 統合 — ツール呼び出し | エージェントから GitHub ツールを呼び出し | ツールが正常に動作する |

### Edge Cases

- 初回リクエスト時の遅延インポートオーバーヘッド
- uv の環境変数の扱いの違いによる直接実行とサブプロセス実行の挙動差

## 11. Implementation Plan

### Phase 1: Preparation / Verification

- [ ] Step 1: `server_common.py` の修正を確認（既に遅延インポート済みであることを確認）
- [ ] Step 2: `server_file.py` の修正を確認（`Depends` 経由のため循環参照なしを確認）
- [ ] Step 3: `server.py` の現在の状態を確認（モジュールレベルのルーターインポートを確認）

### Phase 2: Core Logic Implementation

- [ ] Step 4: `server.py` のモジュールレベルのルーターインポート（`from mcp_servers.github.server_file import router as file_router` など）を削除
- [ ] Step 5: `server.py` の `app.include_router(...)` を関数内 `_include_routers()` へ移動し、必要な箇所で遅延インポートを行う

### Phase 3: Deployment & Verification

- [ ] Step 6: `server.py` のインポートテスト — `python -c "from mcp_servers.github.server import app; print('OK:', app.title)"` で `OK: github-mcp` が出力されることを確認
- [ ] Step 7: GitHub MCP サーバーの起動テスト — `timeout 8 uv run --directory /opt/llm python /opt/llm/scripts/mcp_servers/github/server.py` でエラーなく起動・シャットダウンすることを確認
- [ ] Step 8: エージェント経由での起動テスト — エージェントを再起動し、GitHub MCP サーバーが正常に起動することを確認
- [ ] Step 9: GitHub ツールの呼び出しテスト — エージェントから GitHub ツールを呼び出し、正常に動作することを確認

## 12. Risks / Open Questions

- **Risk**: 遅延インポートにより初回リクエスト時のオーバーヘッドが発生する → **Mitigation**: ルーターの登録は一度だけ（アプリ起動時）、Depends 経由での `_get_service` の呼び出しは毎リクエストだが、遅延インポートのオーバーヘッドは無視できる程度
- **Risk**: 他の MCP サーバーにも同様の循環参照がある → **Mitigation**: 全 MCP サーバー（git, cicd, shell, web_search, rag_pipeline）を同様に確認する必要がある
- **Risk**: uv の環境変数の扱いの違いにより、直接実行とサブプロセス実行で挙動が変わる → **Mitigation**: 修正後に両方のパターンでテストすることで確認
