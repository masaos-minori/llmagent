# 共有インフラ仕様

## 1. 目的

エージェント・MCP サーバー・RAG パイプライン・DB 層が共通利用するライブラリ群（設定読み込み・ログ・型定義・ツール定数・プラグインレジストリ・OTel トレーシング）を提供する。

---

## 2. スコープ

- **対象コンポーネント:** `shared/` 配下の全モジュール（config_loader、logger、types、tool_constants、route_resolver、mcp_config、tool_executor、plugin_registry、otel_tracer、token_counter、git_helper、formatters）
- **対象外:** MCP サーバー実装、RAG パイプライン、エージェント REPL、DB 層

---

## 3. 背景

`shared/` は他のすべてのモジュール（`agent/`・`mcp/`・`rag/`・`db/`）が依存する最下位層である。インポートレイヤー制約により、`shared/` から `agent/`・`mcp/`・`rag/`・`db/` へのインポートは禁止されている（`.importlinter` で強制）。

---

## 4. 前提条件

1. Python 3.13 以上。
2. 依存パッケージ: `orjson`, `httpx`, `pydantic`, `tomllib`（Python 3.11+ stdlib、設定読み込み）。
3. OTel（`opentelemetry-*`）は任意（`otel_enabled=false` の場合はスキップ）。
4. GitPython は任意（`git_helper.py` 使用時のみ）。
5. Sudachi は任意（`ChunkSplitter` の日本語処理時のみ）。

---

## 5. 制約

| 制約 | 内容 |
|---|---|
| インポート方向 | `shared/` → 外部ライブラリのみ。`agent/`・`mcp/`・`rag/`・`db/` へのインポート禁止 |
| JSON ライブラリ | stdlib `json` ではなく `orjson` を使用。`orjson.dumps()` は `bytes` を返すため `.decode()` が必要 |
| HTTP クライアント | `requests` ではなく `httpx` を使用（`httpx.AsyncClient` for async） |
| 設定ファイル | TOML 形式、`/opt/llm/config/` に配置（`_` プレフィックスのキーは除外） |
| ログ | 日本語のコメント・ログメッセージ禁止（英語のみ） |
| `# noqa`/`# type: ignore` | インラインの根拠コメントが必須（ルールコード明記） |

---

## 6. 機能要件

### 6.1 設定読み込み（shared/config_loader.py）
- TOML (`.toml`) および JSON (`.json`) ファイルの読み込みと辞書へのマージ
- 複数ファイルを順番に読み込み、後のファイルが前を上書き
- `_` プレフィックスのキーはドキュメント用メタデータとして除外
- 解析エラー時は `ValueError` を送出

### 6.2 ロギング（shared/logger.py）
- 名前付きロガー（`Logger(__name__, filepath)`）の構築
- FileHandler + StreamHandler の自動設定（propagate=False で重複防止）
- 構造化ログ（JSON Lines）オプション（`structured_log=True`）
- コンテキスト注入（`turn_id`・`session_id` 等）

### 6.3 型定義（shared/types.py）
- `LLMMessage(TypedDict)` — OpenAI 互換チャットメッセージ
- `RagConfig(Protocol)` — `RagPipeline` が要求するコンフィグインターフェース

### 6.4 ツール定数（shared/tool_constants.py）
- `READ_TOOLS`・`WRITE_TOOLS`・`DELETE_TOOLS`・`RAG_TOOLS`・`CICD_TOOLS`・`MDQ_TOOLS`・`GIT_TOOLS` — frozenset 型の静的ルーティングテーブル

### 6.5 プラグインレジストリ（shared/plugin_registry.py）
- `plugins/` ディレクトリからプラグインを動的ロード
- `register_tool(name, async_fn)` でプラグインツールを登録
- `get_tool(name)` でプラグインツールを取得（MCP より優先的に呼び出される）

### 6.6 OTel トレーシング（shared/otel_tracer.py）
- `build_tracer()` でプロセスローカルな `TracerProvider` を構築
- グローバル OTel への干渉なし（プライベートプロバイダー設計）
- `otel_enabled=false` の場合は NoOp スタブを返す

### 6.7 トークンカウンター（shared/token_counter.py）
- `/tokenize` エンドポイントで正確なトークン数を取得
- 未設定時は `chars / 4` のフォールバック推定

### 6.8 テキストフォーマッター（shared/formatters.py）
- `truncate(text, max_chars)` — 文字数制限と末尾省略記号
- `fmt_kvlog(event, **kwargs)` — key=value 形式のログ文字列生成
- `MAX_SNIPPET_CHARS` — スニペット表示の最大文字数定数

---

## 7. 入出力

### 7.1 ConfigLoader

```python
loader = ConfigLoader()
cfg = loader.load("agent.toml")            # 単一ファイル
cfg = loader.load("common.toml", "agent.toml")  # 複数マージ
cfg = loader.load_all()                    # 11ファイルのハードコード済みリストをマージ（common.toml は含まない）
```

### 7.2 Logger

```python
logger = Logger(__name__, "/opt/llm/logs/agent.log")
logger.info("message")
logger.warning("message")
logger.error("message")
logger.set_context(turn_id="T001", session_id=42)  # コンテキスト注入
```

### 7.3 ToolExecutor（主要入出力）

```python
result, is_error, x_request_id = await tool_executor.execute(
    tool_name="read_text_file",
    args={"path": "/opt/llm/docs/README.md"}
)
```

---

## 8. 処理フロー

### 8.1 設定読み込みフロー

```
ConfigLoader().load("agent.toml")
  → config/agent.toml (TOML または JSON) を読み込み
  → `_` プレフィックスのキーを除外
  → dict を返す（ファイル不存在/解析エラー時は ValueError）

ConfigLoader().load_all()
  → ハードコード済み11ファイル [llm, http, rag, context, tools, memory, otel, security, system_prompts, mcp_servers, tools_definitions] を順番にマージ
  → 存在しないファイルはスキップ（ValueError をキャッチして continue）
  → dict を返す（common.toml は含まない）
```

### 8.2 プラグインロードフロー

```
plugin_registry.load_plugins(plugin_dir)
  → plugins/ 配下の *.py を動的インポート
  → @register_tool('tool_name') デコレータで登録
  → ToolExecutor.execute() が MCP より先にプラグインをチェック
```

### 8.3 ToolExecutor 実行フロー

```
ToolExecutor.execute(tool_name, args)
  → plugin_registry.get_tool(tool_name) → プラグイン優先
  → キャッシュ確認（TTL 以内 → キャッシュ返却）
  → _raw_execute(tool_name, args)
      → ServerLifecycleManager.ensure_ready(server_key)
      → Semaphore 取得（concurrency_limits 設定時）
      → transport.call(tool_name, args)
  → キャッシュ保存（is_error=false 時のみ）
  → (result, is_error, x_request_id) を返す
```

---

## 9. データ仕様

### 9.1 LLMMessage（shared/types.py）

```python
class LLMMessage(TypedDict, total=False):
    role: str           # "user" | "assistant" | "tool" | "system"
    content: str | None
    tool_calls: list[dict]
    tool_call_id: str
    name: str
    importance: float   # message importance score for compression prioritization
    pinned: bool        # whether message should be preserved during compression
```

### 9.2 ツール定数（shared/tool_constants.py）

| 定数 | ツール名 |
|---|---|
| `READ_TOOLS` | list_directory, list_directory_with_sizes, directory_tree, read_text_file, read_media_file, read_multiple_files, search_files, grep_files, get_file_info（9 ツール） |
| `WRITE_TOOLS` | write_file, edit_file, create_directory, move_file（4 ツール） |
| `DELETE_TOOLS` | delete_file, delete_directory（2 ツール） |
| `RAG_TOOLS` | rag_run_pipeline, rag_debug_pipeline |
| `CICD_TOOLS` | GitHub Actions 関連 4 ツール |
| `MDQ_TOOLS` | search_docs, get_chunk, outline, index_paths, refresh_index, stats, grep_docs |
| `GIT_TOOLS` | git_status, git_log, git_diff, git_branch, git_show, git_add, git_commit, git_checkout, git_pull, git_push |

### 9.3 McpServerConfig（shared/mcp_config.py）

→ `docs/spec_mcp.md` 「9.1 McpServerConfig フィールド」を参照

---

## 10. 公開インターフェース仕様

### 10.1 ConfigLoader（shared/config_loader.py）

```python
class ConfigLoader:
    def load(*filenames: str) -> dict[str, Any]
    def load_all() -> dict[str, Any]  # ハードコード済み11ファイル [llm, http, rag, context, tools, memory, otel, security, system_prompts, mcp_servers, tools_definitions] をマージ（common.toml 除外）
```

### 10.2 Logger（shared/logger.py）

```python
class Logger:
    def __init__(name: str, filepath: str, *, structured_log: bool = False)
    def info(msg: str, *args, **kwargs) -> None
    def warning(msg: str, *args, **kwargs) -> None
    def error(msg: str, *args, **kwargs) -> None
    def set_context(**kwargs) -> None
```

### 10.3 plugin_registry（shared/plugin_registry.py）

```python
def load_plugins(plugin_dir: Path) -> int  # ロードしたプラグイン数
def register_tool(name: str) -> Callable   # デコレータ
def get_tool(name: str) -> Callable | None
def iter_commands() -> dict[str, tuple[Callable, bool]]  # 登録済みコマンドのスナップショット
```

### 10.4 TokenCounter（shared/token_counter.py）

```python
class TokenCounter:
    def __init__(tokenize_url: str = "")
    async def count(text: str) -> int  # トークン数（フォールバック: len(text) // 4）
```

### 10.5 build_tracer（shared/otel_tracer.py）

```python
def build_tracer(
    enabled: bool,
    service_name: str,
    otlp_endpoint: str = "",
) -> opentelemetry.trace.Tracer
```

### 10.6 git_helper（shared/git_helper.py）

```python
def get_repo_info() -> dict | None
# 戻り値: {"branch": str, "commit": str, "origin": str} または None（Git 未使用時）
```

---

## 11. エラーハンドリング

| エラー種別 | 対応 |
|---|---|
| `ConfigLoader` ファイル不存在 | `ValueError` を送出（原因をメッセージに含む） |
| TOML 解析エラー | `ValueError` を送出（原因をメッセージに含む） |
| `Logger` ファイル書き込みエラー | サイレントフォールバック（StreamHandler のみで継続） |
| プラグインロードエラー | ログに警告を出力してスキップ（他プラグインに影響しない） |
| `TokenCounter` 接続エラー | `chars / 4` のフォールバック推定を使用、警告を 1 回だけ出力 |
| `get_repo_info()` の例外 | `None` を返す（GitPython 未インストール・Git リポジトリ外を含む） |

---

## 12. 検証計画

| 検証項目 | ツール | 合格基準 |
|---|---|---|
| ユニットテスト | `uv run pytest tests/test_token_counter.py tests/test_route_resolver.py tests/test_mcp_config.py tests/test_tool_executor_routing.py` | 全パス |
| 型チェック | `uv run mypy scripts/shared/` | 新規エラーなし |
| アーキテクチャ境界 | `PYTHONPATH=scripts uv run lint-imports` | `shared/` から上位層への参照 0 |
| Lint | `uv run ruff check scripts/shared/` | 0 エラー |
| セキュリティ | `uv run bandit -r scripts/shared/` | HIGH 未対応なし |

---

## 13. 未解決事項・既知問題

| 項目 | 詳細 |
|---|---|
| `LLMMessage.role` 型 | `str` のまま。`Literal["user", "assistant", "tool", "system"]` への型強化が未実装 (`implementations/20260606-194710_shared_types.md` 参照) |
| `McpServerConfig.transport` 型 | `str` のまま。`Literal["http", "stdio"]` への型強化が未実装 |
| `token_counter._warned_unavailable` | モジュールグローバル変数。インスタンス変数への移動が未実装 (`implementations/20260606-194738_shared_global_state.md` 参照) |
| `ToolRouteResolver` fallback 警告 | 設定外のツールが静的フォールバックを使用する際の警告が未実装（`warn_on_fallback` オプション追加が必要） |
| `plugin_registry.load_plugins()` | ロード失敗詳細の機械可読なレポートが未実装（成功/失敗/理由の構造化返却が必要） |
| `git_helper.get_repo_info()` | `except Exception` で全例外を飲み込んで `None` を返す。理由コード付き結果型への変更が必要 |
