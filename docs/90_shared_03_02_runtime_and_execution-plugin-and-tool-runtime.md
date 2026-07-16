---
title: "Shared Runtime and Execution - Plugin and Tool Runtime"
category: shared
tags:
  - shared
  - runtime
  - plugin-registry
  - token-counter
  - otel-tracer
  - git-helper
  - tool-executor
related:
  - 90_shared_00_document-guide.md
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md
  - 90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md
source:
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
---

# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 4. `plugin_registry` (`shared/plugin_registry.py` ほか)

**モジュール分割 (Explicit in code):** プラグイン基盤は単一ファイルではなく以下に分割されている。`shared/plugin_registry.py` は公開APIの窓口であり、実体は各モジュールに存在する。

| モジュール | 役割 |
|---|---|
| `shared/plugin_registry.py` | 公開デコレータ・アクセサ (`register_command`/`register_tool`/`register_pipeline_stage`/`get_tool`/`get_command` 等)。`load_plugins`/`get_last_load_result`/`_reset_for_testing` は `plugin_auto_discover` へのシンラッパー |
| `shared/plugin_registries.py` | モジュールレベルの内部状態 (`_commands`/`_tools`/`_pipeline_post`/`_current_loading_module`/`_builtin_command_names`) を保持するのみ |
| `shared/plugin_auto_discover.py` | `load_plugins()` の実体。ディレクトリglob・インポート・失敗収集・`PluginLoadResult` 組み立てを行う |
| `shared/plugin_conflicts.py` | `validate_tool_conflicts()` / `validate_command_conflicts()` — MCP既知ツール・組み込みコマンドとの名前衝突解決 |
| `shared/plugin_result.py` | `PluginFailure` / `PluginLoadResult` / `PluginLoadError` のデータクラス定義本体 (`plugin_registry.py` は再エクスポートのみ) |
| `shared/plugin_tool_invoker.py` | `PluginToolInvoker` — 登録済みプラグインツールの実行層 (`ToolExecutor.execute()` から呼ばれる) |

```python
def load_plugins(
    plugin_dir: str | Path,
    *,
    known_tools: frozenset[str] = frozenset(),
    override_policy: str = "reject",
    strict_mode: bool = False,
) -> PluginLoadResult
def register_tool(name: str) -> Callable          # decorator
def get_tool(name: str) -> Callable | None
def register_command(name: str, *, prefix: bool = False) -> Callable
def get_command(name: str) -> tuple[Callable, bool] | None
def iter_commands() -> dict[str, tuple[Callable, bool]]
def iter_tools() -> dict[str, Callable[..., Any]]
def register_pipeline_stage(*, when: str = "post") -> Callable
def get_pipeline_post_stages() -> list[PipelineHook]
async def run_pipeline_stages(hooks, hits, query, *, strict=False) -> list[RagHit]
def register_builtin_commands(names: frozenset[str]) -> None
```

**プラグイン読込フロー:**
```
plugin_registry.load_plugins(plugin_dir, known_tools=..., override_policy="reject", strict_mode=False)
  → plugins/*.py をアルファベット順にglob (plugin_auto_discover.load_plugins)
  → 各ファイルをインポート (importlib.util; import時に @register_* が実行される)
  → エラー時: WARNINGとして記録しプラグインをスキップ(fail-open); 例外種別は ImportError/SyntaxError/AttributeError/RuntimeError/ValueError のみ捕捉
  → 全読込後: plugin_conflicts.validate_tool_conflicts() / validate_command_conflicts() でMCP既知ツール・組み込みコマンドとの衝突を解決
  → strict_mode=True かつ (load失敗 or 衝突による拒否) がある場合のみ集約された PluginLoadError を送出
  → ディレクトリが存在しない場合: loaded_count=0 の PluginLoadResult を返す(エラーにしない)
```

**register_tool のコントラクト検証 (Explicit in code):** `register_tool()` はデコレータ適用時に以下を強制する。違反時は `ValueError` を送出する(プラグインロード失敗として捕捉される)。
- ハンドラは `inspect.iscoroutinefunction()` で判定される非同期関数でなければならない
- 戻り値の型アノテーションが必須で、`tuple[str, bool]` と厳密一致しなければならない (`typing.get_type_hints` で解決)

**優先順位:** `@register_tool` handlers are checked by `ToolExecutor.execute()` **before** `ToolRegistry` route resolution, the tool-result cache, the health gate, lifecycle `ensure_ready()`, and `HttpTransport` — a plugin tool never reaches any of these MCP-routing mechanisms.
`@register_command` ハンドラは `CommandRegistry` によって組み込みコマンドの**後に**ディスパッチされる。

**ツール衝突解決 (`plugin_conflicts.validate_tool_conflicts`):**
- `known_tools` が空なら何もしない (`(0, 0, [])`)
- `override_policy="allow"`: 衝突するプラグインツールをMCPツールの上に残し、`allowed_count` を加算
- `override_policy="reject"` (デフォルト): 衝突するプラグインツールを `_tools` から削除し、`shadowed_count` を加算。`strict_mode=True` の場合はさらに `strict_rejected` リストに名前を積む

**コマンド衝突解決 (`plugin_conflicts.validate_command_conflicts`):**
- `register_builtin_commands()` で登録済みの組み込みコマンド名と衝突するプラグインコマンドを `_commands` から削除する
- `strict_mode=True` の場合、拒否された名前は集約エラーメッセージに含まれる

**戻り値の型:**

```python
# shared/plugin_result.py — plugin_registry.py はこれを再エクスポートするのみ
@dataclass(frozen=True)
class PluginFailure:
    path: str          # plugin .py filename
    error: str         # exception message

@dataclass(frozen=True)
class PluginLoadResult:
    loaded_count: int
    failed: tuple[PluginFailure, ...]
    tool_conflicts_shadowed: int = 0
    tool_conflicts_allowed: int = 0
    command_shadows_rejected: int = 0  # commands rejected due to strict-mode conflict with a builtin

class PluginLoadError(RuntimeError):
    pass

def get_last_load_result() -> PluginLoadResult | None
```

- `get_last_load_result()` は直近の `PluginLoadResult` を返す。初回ロード前は `None`。
- `PluginLoadError` は `strict_mode=True` かつ失敗またはMCP競合がある場合のみ発生する。In `strict_mode=True`, **all** plugins are attempted first; a single aggregated `PluginLoadError` (naming every load failure, tool-conflict rejection, and command-conflict rejection together) is raised only after every plugin has had a chance to load — not on the first failure.
- `PluginFailure.error` には失敗したプラグインの例外メッセージ全文が入る。

**PluginToolInvoker (`shared/plugin_tool_invoker.py`):**
- `try_execute(tool_name, args)` はプラグインツールが未登録なら `None` を返す (呼び出し側は `ToolExecutor.execute()`)
- プラグイン関数が例外を送出した場合は `ToolCallResult(is_error=True, source="plugin", error_type="tool")` に変換し、例外を外へ伝播させない
- 戻り値の実行時バリデーション: `tuple` かつ長さ2であること、`output: str`、`is_error: bool` を再チェックする。登録時のアノテーション検査とは別に、実行時にも防御的に検証する二重チェック設計 — 契約違反時は `error_type="plugin_contract"` の `ToolCallResult` を返す

**テスト分離:** `_reset_for_testing()` (実体は `plugin_auto_discover._reset_for_testing`) は全レジストリをクリアするもので、コマンド・ツール・パイプラインステージを登録するテストファイルでは
`pytest.fixture(autouse=True)` 内で必ず呼び出す必要がある。テスト以外のコードはこの関数を呼び出してはならない。

---

## 4a. `ToolExecutor` (`shared/tool_executor.py`, `shared/tool_executor_helpers.py`)

```python
class ToolExecutor(ToolTransportInvoker):
    def __init__(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None
    def apply_config(self, *, cache_ttl: float | None = None) -> None
    async def execute(self, tool_name: str, args: dict[str, Any]) -> ToolCallResult
    def clear_cache(self) -> None
    def get_error_counters(self) -> dict[str, dict[str, int]]
```

**`execute()` の実行順序 (Explicit in code):**
```
execute(tool_name, args)
  → PluginToolInvoker.try_execute() でプラグインツールか判定
      → プラグインツールなら結果を即返す (キャッシュ・MCPルーティングを一切経由しない)
  → _execute_with_cache(): キャッシュキー "tool_name:json(args)" でTTLキャッシュ参照
      → ヒットかつ age < cache_ttl: LRU更新してヒット数を加算し即返す
  → _execute_with_stampede_protection(): 同一キーの同時実行はFutureを共有し、二重実行を防止
      → 例外発生時は共有Futureのすべての待機者へ例外を伝播させる (inflight.set_exception)
  → _raw_execute():
      1. startup_mode=none のサーバーはエラー即返却 (無効化されたサーバーは使用不可)
      2. ヘルスチェックゲート
      3. lifecycle.ensure_ready() (LifecycleProtocol注入時のみ)
      4. transport解決 (ToolRouteResolver.resolve() でserver_key特定)
      5. per-server-key Semaphoreを介してtransport実行
  → 成功結果のみキャッシュに格納・LRU evict (cache_max_size > 0の場合)
```

- `ToolExecutor` は `ToolTransportInvoker` を継承する (`shared/tool_transport_invoker.py`; §caching-and-reference-part2 参照)
- キャッシュは失敗結果を保存しない — `is_error=True` の結果はキャッシュされない
- `apply_config(cache_ttl=...)` はインスタンスを再作成せずにホットリロード可能な設定を更新する

**補助関数 (`shared/tool_executor_helpers.py`):**
```python
def is_side_effect(tool_name: str) -> bool
def format_transport_error(*, source, phase, kind, url, status_code, retryable, partial) -> TransportErrorInfo
def tool_hash_key(name: str, args: dict[str, object]) -> str
```
- `is_side_effect()`: `WRITE_TOOLS`/`DELETE_TOOLS`/`{"shell_run"}`/`GIT_WRITE_TOOLS`/`GITHUB_WRITE_TOOLS`/`GITHUB_DANGEROUS_TOOLS` のいずれかに属するツールを判定する。並列実行を直列実行へ自動降格させる判定に用いる
- `tool_hash_key()`: MD5ハッシュ (`usedforsecurity=False`) を返す。**キャッシュキーには使われない** — キャッシュキーは平文の `f"{name}:{json_dumps(args)}"` 文字列そのもの。`tool_hash_key()` は失敗呼び出しの追跡用途専用

---

## 4b. `ToolRegistry` / `route_resolver` / `tool_routing_validation` (ルーティングの正本)

**責務分離 (Explicit in code — module docstring):**
- `shared/tool_registry.py`: MCPツール所有権とルーティングの唯一の正本。`tool_constants.py` の frozenset群がインポート時にこのレジストリへ登録される
- `shared/route_resolver.py`: `ToolRouteResolver` — ツール名→server_key解決。**ルーティング判断の唯一の権威は `ToolRegistry` であり、config の `tool_names` はドリフト検証専用のメタデータであってルーティング入力ではない**
- `shared/tool_routing_validation.py`: config / live `/v1/tools` 応答とレジストリの整合性検証 (ドリフト検出専用。ルーティングには使わない)

```python
@dataclass(frozen=True)
class ToolDefinition:
    name: str
    server_key: str
    description: str = ""        # reserved for future use; not populated today
    input_schema: dict[str, object] = field(default_factory=dict)  # reserved; not populated today

class ToolRegistry:
    def register(self, definition: ToolDefinition) -> None            # 名前重複はValueError
    def get_server_for_tool(self, tool_name: str) -> str | None
    def get_tool_names(self, server_key: str) -> list[str]            # sorted済み、契約として保証
    def get_all_tool_names(self) -> frozenset[str]
    def get_servers(self) -> list[str]
    def validate_tool_names_match(self, server_key, config_tool_names) -> list[str]
    def validate_live_tools_match(self, server_key, live_tool_names) -> list[str]

def get_registry() -> ToolRegistry   # グローバルシングルトン。初回呼び出し時に tool_constants から自動登録
```

- `ToolDefinition.description` / `input_schema` は**予約フィールドで現状未使用** (`_populate_default_registry()` は設定しない)。LLM向けツールスキーマは各サーバーの `tools.py` の `TOOL_LIST` が正本
- デフォルト登録は `tool_constants.py` の `READ_TOOLS`/`WRITE_TOOLS`/`DELETE_TOOLS`/`RAG_TOOLS`/`CICD_TOOLS`/`MDQ_TOOLS`/`GIT_TOOLS`/`SHELL_TOOLS`/`GITHUB_TOOLS`/`WEB_SEARCH_TOOLS` を対応するserver_keyに登録する

```python
class ToolRouteResolver:
    def __init__(
        self,
        server_configs: dict[str, McpServerConfig],   # 後方互換のためだけに受理; 読み取られない
        *,
        discovery_map: dict[str, str] | None = None,   # 診断専用; resolve()には使われない
        warn_on_missing: bool = False,
        strict_mode: bool = False,
        known_tools: frozenset[str] | None = None,     # 現状どの本番呼び出しも渡していない
    ) -> None
    def resolve(self, tool_name: str) -> str   # ToolRegistry参照のみ; 未登録はValueError
```

**Current behavior (Explicit in code):**
- `server_configs` はコンストラクタで受け取るが一切読み取られず保存もされない (後方互換性のためだけの引数)
- `discovery_map` はルーティングカバレッジ診断という現状どこからも呼ばれない診断機能専用で、`resolve()` の判断には一切使われない
- `known_tools` を渡す本番呼び出しは `tool_executor.py` を含め存在しない (2026-07時点)。このため起動時カバレッジログ機能は実質的に到達しないコード

```python
def validate_routing_against_config(registry=None, server_configs=None) -> dict[str, list[str]]
def validate_routing_against_live(registry=None, live_tool_lists=None) -> dict[str, list[str]]
def validate_all_routing(server_configs=None, live_tool_lists=None) -> dict[str, list[str]]
def check_tool_safety_tiers(registry=None, tool_safety_tiers=None) -> list[str]
def check_unknown_tool_safety_tiers(registry=None, tool_safety_tiers=None) -> list[str]
```
- いずれも空dict/空listはドリフトなしを意味する
- `check_tool_safety_tiers` / `check_unknown_tool_safety_tiers` は `tool_safety_tiers` が空/未設定なら即座に空リストを返す (機能自体がオプトイン)

## 4c. `LifecycleProtocol` (`shared/tool_lifecycle.py`)

```python
@runtime_checkable
class LifecycleProtocol(Protocol):
    async def ensure_ready(self, server_key: str) -> None
```
- `ToolExecutor` に注入されるライフサイクル管理者の最小プロトコル。実装は `MCPServer` 側のライフサイクルマネージャ (詳細は MCP系ドキュメント参照)

---

## 5. `token_counter` (`shared/token_counter.py`)

```python
async def get_token_count(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
) -> tuple[int, bool]   # (token_count, is_exact)
```

**優先順位:**
1. `POST {tokenize_url}/tokenize` → 正確な数値(`is_exact=True`)
2. カテゴリ別の文字数→トークン数推定(text: 4.0、tool_calls: 2.5、system: 3.5) → 推定値(`is_exact=False`)

- 接続エラーは静かにフォールバックする。`_WarnOnce` インスタンスがプロセス生存期間中の重複警告を抑制する
- カテゴリ別推定は、旧来の `chars // 4` ヒューリスティックを置き換え、多言語テキストと構造化ツールペイロードでの精度を高めたもの
- トークン推定は `(total_tokens, breakdown: dict[str, int])` をカテゴリ別カウント付きで返す

---

## 6. `otel_tracer` (`shared/otel_tracer.py`)

```python
def build_tracer(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol
```

- `enabled=False` → NoOpスタブを返す(OTel初期化なし)
- `enabled=True`、`otlp_endpoint=""` → `ConsoleSpanExporter`(stdout/ログへ出力)
- `enabled=True`、`otlp_endpoint` 指定あり → OTLP HTTPエクスポーター
- **プライベート** `TracerProvider` を使用する — グローバルなOTelプロバイダには触れない

---

## 7. `git_helper` (`shared/git_helper.py`)

```python
def get_repo_info(path: str = ".") -> RepoInfoResult
# RepoInfoResult(success: bool, data: dict[str, str] | None, failure_reason: FailureReason | None)
# Returns: {"branch": str, "commit": str (8-char), "message": str, "author": str}
# Returns None on any error (GitPython not installed, not a git repo, etc.)
```

- `ImportError` は個別に捕捉される(GitPythonが未インストールの場合)
- Git操作は `git.exc.GitError`、`OSError`、`AttributeError`、`ValueError` を個別に捕捉する
- `except Exception` の catch-all は削除済み。各エラー種別はその原因とともにDEBUGレベルでログ記録される

- 戻り値の辞書に `"origin"` フィールドは含まれない
- `"commit"` は `HEAD.hexsha[:8]`(8文字のみ)

---

## 8. `formatters` (`shared/formatters.py`)

```python
def truncate(text: str, max_chars: int) -> str
def fmt_kvlog(op: str, **kwargs) -> str   # key=value log string; first param named "op"
def fmt_size(size: int) -> str           # "1.5 KB", "2.3 MB", etc.
def fmt_md_link(text: str, url: str) -> str   # "[text](url)"
MAX_SNIPPET_CHARS: int                   # max chars for snippet display
```

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_03_01_runtime_and_execution-config-and-logging.md`
- `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md`
- `90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md`

## Keywords

plugin_registry
token_counter
otel_tracer
git_helper
formatters
ToolExecutor
