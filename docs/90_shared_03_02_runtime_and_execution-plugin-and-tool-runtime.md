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
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md
  - 90_shared_03_04_runtime_and_execution-caching-and-reference.md
source:
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
---

# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 4. `plugin_registry` (`shared/plugin_registry.py`)

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
def register_command(name: str, prefix: bool = False) -> Callable
def get_command(name: str) -> tuple[Callable, bool] | None
def iter_commands() -> dict[str, tuple[Callable, bool]]
def iter_tools() -> dict[str, Callable[..., Any]]
def register_pipeline_stage(when: "post") -> Callable
def get_pipeline_post_stages() -> list[Callable]
async def run_pipeline_stages(hits, query, *, strict=False) -> list[Any]
```

**プラグイン読込フロー:**
```
plugin_registry.load_plugins(plugin_dir, known_tools=..., override_policy="reject", strict_mode=False)
  → plugins/*.py をアルファベット順にglob
  → 各ファイルをインポート
  → @register_* デコレータがインポート時に実行される
  → エラー時: WARNINGとして記録しプラグインをスキップ(fail-open);strict_mode=Trueなら最初のエラーで例外
  → 全読込後: ツール競合検証により既知のMCPセットから競合ツールを除去
  → ディレクトリが存在しない場合: 0を返す(エラーにしない)
```

**優先順位:** `@register_tool` ハンドラは `ToolExecutor.execute()` によってキャッシュ・MCPルーティングより**先に**チェックされる。
`@register_command` ハンドラは `CommandRegistry` によって組み込みコマンドの**後に**ディスパッチされる。

**戻り値の型:**

```python
@dataclass(frozen=True)
class PluginFailure:
    path: str          # plugin .py filename
    error: str         # exception message

@dataclass(frozen=True)
class PluginLoadResult:
    loaded_count: int
    failed: tuple[PluginFailure, ...]
    tool_conflicts_shadowed: int
    tool_conflicts_allowed: int
    command_shadows: int

class PluginLoadError(RuntimeError):
    pass

def get_last_load_result() -> PluginLoadResult | None
```

- `get_last_load_result()` は直近の `PluginLoadResult` を返す。初回ロード前は `None`。
- `PluginLoadError` は `strict_mode=True` かつ失敗またはMCP競合がある場合のみ発生する。
- `PluginFailure.error` には失敗したプラグインの例外メッセージ全文が入る。

**テスト分離:** リセット関数は全レジストリをクリアするもので、コマンド・ツール・パイプラインステージを登録するテストファイルでは
`pytest.fixture(autouse=True)` 内で必ず呼び出す必要がある。テスト以外のコードはこの関数を呼び出してはならない。

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
- `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`
- `90_shared_03_04_runtime_and_execution-caching-and-reference.md`

## Keywords

plugin_registry
token_counter
otel_tracer
git_helper
formatters
ToolExecutor
