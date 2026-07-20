---
title: "Shared Runtime and Execution - Tool Runtime"
category: shared
tags:
  - shared
  - runtime
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

## 4. `ToolExecutor` (`shared/tool_executor.py`, `shared/tool_executor_helpers.py`)

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
``` text
execute(tool_name, args)
  → キャッシュ参照: キャッシュキー "tool_name:json(args)" でTTLキャッシュ参照
      → ヒットかつ age < cache_ttl: LRU更新してヒット数を加算し即返す
  → 同時実行保護: 同一キーの同時実行はFutureを共有し、二重実行を防止
      → 例外発生時は共有Futureのすべての待機者へ例外を伝播させる (inflight.set_exception)
  → 基本実行:
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

## 4a. `ToolRegistry` / `route_resolver` / `tool_routing_validation` (ルーティングの正本)

**責務分離 (Explicit in code — module docstring):**
- `shared/runtime_tool_registry.py`: **最優先のルーティング権威**。McpToolDiscoveryService によりライブ `/v1/tools` discovery で構築され、`ToolExecutor.set_runtime_registry()` で接続される
- `shared/tool_registry.py`: **フォールバックのルーティング権威**。`tool_constants.py` の frozenset群がインポート時にこのレジストリへ登録される
- `shared/route_resolver.py`: `ToolRouteResolver` — ツール名→server_key解決。**RuntimeToolRegistry が最優先で解決され、見つからない場合に ToolRegistry にフォールバックする**
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

- `ToolDefinition.description` / `input_schema` は**予約フィールドで現状未使用** (デフォルトレジストリ初期化関数は設定しない)。LLM向けツールスキーマは各サーバーの `tools.py` の `TOOL_LIST` が正本
- デフォルト登録は `tool_constants.py` の `READ_TOOLS`/`WRITE_TOOLS`/`DELETE_TOOLS`/`RAG_TOOLS`/`CICD_TOOLS`/`MDQ_TOOLS`/`GIT_TOOLS`/`SHELL_TOOLS`/`GITHUB_TOOLS`/`WEB_SEARCH_TOOLS` を対応するserver_keyに登録する

```python
class ToolRouteResolver:
    def __init__(
        self,
        server_configs: dict[str, McpServerConfig],   # 後方互換のためだけに受理; 読み取られない
        *,
        runtime_registry: RuntimeToolRegistry | None = None,  # 最優先のルーティング権威
        discovery_map: dict[str, str] | None = None,   # 診断専用; resolve()には使われない
        warn_on_missing: bool = False,
        strict_mode: bool = False,
        known_tools: frozenset[str] | None = None,     # 現状どの本番呼び出しも渡していない
    ) -> None
    def resolve(self, tool_name: str) -> str   # RuntimeToolRegistry → ToolRegistry の順で解決; 未登録はValueError
```

**Current behavior (Explicit in code):**
- `server_configs` はコンストラクタで受け取るが一切読み取られず保存もされない (後方互換性のためだけの引数)
- `runtime_registry` が設定されている場合、`resolve()` で最初に RuntimeToolRegistry が検索される
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

## 4b. `LifecycleProtocol` (`shared/tool_lifecycle.py`)

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

token_counter
otel_tracer
git_helper
formatters
ToolExecutor
ToolRegistry
LifecycleProtocol
