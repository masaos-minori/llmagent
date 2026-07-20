---
title: "Shared Runtime and Execution - Config and Logging"
category: shared
tags:
  - shared
  - runtime
  - config-loader
  - config-isolation
  - logger
related:
  - 90_shared_00_document-guide.md
  - 90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md
  - 90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md
source:
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
---

# 共有ランタイムと実行基盤

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 1. 目的

`shared/` におけるランタイム基盤とユーティリティを文書化する: 設定読み込み、ロギング、
トークンカウント、OTel トレーシング、git ヘルパー、フォーマッター、ToolExecutor、
および McpServerConfig。

---

## 2. `ConfigLoader` (`shared/config_loader.py`)

```python
class ConfigLoader:
    def __init__(self, config_dir: Path | None = None)
    def load(self, *filenames: str) -> dict[str, Any]
    def load_all(self, strict: bool = False) -> dict[str, Any]

    @classmethod
    def restrict_to(cls, *filenames: str) -> None
```

**`load(*filenames)`**
- 1 つ以上の TOML/JSON ファイルを順に読み込み、マージする
- 後のファイルが前のファイルを上書きする (トップレベルの単純な `dict.update`; ネストした dict のマージは行わない)
- `_` で始まるキーは除外される (ドキュメント用メタデータ)
- `ConfigMissingError` (ファイル未検出)、`ConfigParseError` (パースエラー)、`ConfigReadError` (I/O エラー) を発生させる — いずれも `ValueError` のサブクラス
- `restrict_to()` が呼ばれている場合、許可セットに含まれないファイル名を指定すると `ConfigPermissionError` を発生させる

**`load_all(strict=False)`**
- `agent.toml` のみを読み込む (`_BASE_CONFIG_FILES = ("agent.toml",)`)
- `strict=False` (デフォルト): 存在しないファイルは黙って無視される (`ConfigMissingError` を捕捉し debug ログを出して継続)
- `strict=True`: `_REQUIRED_CONFIG_FILES = frozenset(("agent.toml",))` に含まれるファイルが欠けている場合は `ConfigMissingError` を再送出する
- `dict` 値を持つキーは 1 階層だけ深くマージされる (`{**merged[key], **val}`) — 複数の MCP サーバー設定ファイルがそれぞれ `[mcp_servers.<key>]` セクションを持ち込んでも、先に読んだファイルのエントリを上書きせずに済む設計
- `restrict_to()` が呼ばれている場合、`agent.toml` が許可セットに含まれないと `ConfigPermissionError` を発生させる

**`restrict_to(*filenames)`** (クラスメソッド)
- プロセス起動時に一度呼び出し、そのプロセスが読み込むことを許可された設定ファイルを宣言する
- それ以降の `load()` や `load_all()` の呼び出しがこのセット外のファイルに触れると `ConfigPermissionError` を発生させる
- エージェントプロセスからは呼ばれない (無制限); MCP サーバー、crawler、ingester、chunk_splitter から呼ばれる
- テストは `restrict_to()` を呼ばないため、テストプロセスは無制限である

---

## 2a. プロセス分離方針 (Config Isolation Policy)

### 2a. Process separation policy (Config isolation policy)

### Process separation policy

### Config ownership

**各プロセスは自身の設定ファイルのみを読み込む。**

エージェント / 各 MCP サーバー / crawler / ingester / chunk_splitter はそれぞれ独立したプロセスとして動作する。設定ファイルは以下のルールに従う:

- 各プロセスは起動時に自身に対応する設定ファイル 1 つだけを `ConfigLoader().load("xxx.toml")` で読み込む
- 他プロセスの設定ファイルは読み込まない (`agent.toml` を含む)
- DB パス・外部サービス URL など複数プロセスが必要とする値は **共通ファイルを作らず、各プロセスの設定ファイルにそれぞれ記述する**
- `ConfigLoader.restrict_to(own_config_file)` をプロセス起動直後に呼ぶことでこのルールをランタイムでも強制する — 違反時は `ConfigPermissionError` が発生する

| プロセス | 設定ファイル | `restrict_to()` 呼び出し箇所 |
|---|---|---|
| agent | `config/agent.toml` | 呼ばない (制限なし) |
| rag-pipeline-mcp | `config/rag_pipeline_mcp_server.toml` | `MCPServer.run_http()` |
| cicd-mcp | `config/cicd_mcp_server.toml` | `MCPServer.run_http()` |
| file-delete-mcp | `config/file_delete_mcp_server.toml` | `MCPServer.run_http()` |
| file-read-mcp | `config/file_read_mcp_server.toml` | `MCPServer.run_http()` |
| file-write-mcp | `config/file_write_mcp_server.toml` | `MCPServer.run_http()` |
| git-mcp | `config/git_mcp_server.toml` | `MCPServer.run_http()` |
| github-mcp | `config/github_mcp_server.toml` | `MCPServer.run_http()` |
| mdq-mcp | `config/mdq_mcp_server.toml` | `MCPServer.run_http()` |
| shell-mcp | `config/shell_mcp_server.toml` | `MCPServer.run_http()` |
| web-search-mcp | `config/web_search_mcp_server.toml` | `MCPServer.run_http()` |
| crawler | `config/crawler.toml` | `if __name__ == "__main__"` |
| ingester | `config/ingester.toml` | `if __name__ == "__main__"` |
| chunk_splitter | `config/chunk_splitter.toml` | `if __name__ == "__main__"` |
| eventbus | `config/eventbus.toml` | (独自ローダー) |

**`MCPServer.own_config_file` クラス変数:**
`MCPServer` サブクラスは `own_config_file = "xxx_mcp_server.toml"` を宣言する。`run_http()` がこの値を使って `ConfigLoader.restrict_to(own_config_file)` を uvicorn 起動前に呼び出す。

**Config loading flow:**
```
ConfigLoader().load("agent.toml")
  → read /opt/llm/config/agent.toml (TOML)
  → remove keys prefixed with "_"
  → return dict  (ConfigMissingError on missing, ConfigParseError on parse error)

ConfigLoader().load_all()
  → iterate _BASE_CONFIG_FILES = ("agent.toml",)
  → skip missing files silently
  → merge into single dict
  → return dict

ConfigLoader.restrict_to("crawler.toml")  # called at process startup
ConfigLoader().load("agent.toml")         # → ConfigPermissionError
ConfigLoader().load_all()                 # → ConfigPermissionError (agent.toml not allowed)
```

---

## 2b. `RagConfigValidator` / `ProductionConfigValidator` (`shared/config_validator.py`, `shared/production_config_validator.py`)

```python
@dataclasses.dataclass
class ConfigValidationResult:  # config_validator.py
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool

class RagConfigValidator:
    def validate(self, cfg: dict[str, Any]) -> ConfigValidationResult
```

- RAG 設定のクロスファイル整合性を検証する。`cfg` は `agent.toml` 形式のネスト `{"rag": {...}}` と MCP モジュール設定のフラット `{...}` の両方を受け付ける (`"rag" in cfg` で判定)
- チェック内容: `embedding_dim` と `vec_dim` の不一致 (error) / `use_rrf=False` (warning) / `semantic_cache_threshold < 0.5` (warning) / `semantic_cache_max_size < 0` (error)

```python
@dataclass
class ConfigValidationResult:  # production_config_validator.py (別定義、同名だが別モジュール)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

class ProductionConfigValidator:
    def validate(
        self,
        config: Mapping[str, object],
        security_profile: SecurityProfile | str = "local",
        known_tools: set[str] | None = None,
    ) -> ConfigValidationResult
    def validate_unknown_tool_safety_tiers(self, unknown_keys: list[str]) -> ConfigValidationResult
```

- `security_profile == "production"` の場合のみ違反を error にする。それ以外 (local/development) は `[local/development]` 接頭辞付きの warning に降格される
- 検証項目:
  - `_REQUIRED_STRICT_KEYS = ("tool_definitions_strict", "routing_drift_strict")` が `False` (未設定含む)
  - `tool_safety_tiers` と `tool_registry.get_registry().get_all_tool_names()` の双方向差分 (登録済みツールで tier 未設定 / tier に未登録キー)
  - `allowed_tools == []` (空リストは「全ツール許可」を意味するため警告/エラー対象)
- `known_tools` 省略時は `shared.tool_registry.get_registry()` から動的取得を試み、例外時は当該チェックをスキップする (静かに空リスト扱い)

**Note (Explicit in code):** `config_validator.py` と `production_config_validator.py` はそれぞれ独立した `ConfigValidationResult` データクラスを定義しており、共通の型ではない。両者は責務が異なる (RAG 設定の整合性 vs 本番運用の厳格性) ため、混同しないこと。

---

## 3. `Logger` (`shared/logger.py`)

```python
class Logger:
    def __init__(self, name: str, log_file: str, *, structured_log: bool = False)
    def info(self, msg: str, *args, **kwargs) -> None
    def warning(self, msg: str, *args, **kwargs) -> None
    def error(self, msg: str, *args, **kwargs) -> None
    def set_context(self, **kwargs) -> None
    def clear_context(self) -> None
```

- コンストラクタ第2引数名は `log_file` (実装名。旧記載の `filepath` は誤り)
- `name` / `log_file` はいずれも非空文字列であることが必須で、違反時は `ValueError` を送出する (文字列検証関数)
- `FileHandler` + `StreamHandler` を自動設定する (`propagate=False` により重複を防止)
- 同一 `name` のロガーに既にハンドラが設定済みの場合、ロガー初期化処理は何もせず即座に return する (二重登録防止; 同名 `Logger` を複数回生成しても安全)
- `structured_log=True` → ログファイルは JSON Lines 形式になる (`_JsonFormatter`; フィールドは `ts`/`level`/`func`/`msg` に加え `turn_id`/`session_id`/`rag_query_id`/`workflow_id`/`task_id`/`exc` が値のあるもののみ出力される)
- コンテキスト注入: `set_context(turn_id="T001", session_id=42)` により、以降のすべてのログ行にフィールドが追加される。`_ContextFilter` は `contextvars.ContextVar` を使うため、同一ロガーを共有する並行 asyncio タスク間でコンテキストが混線しない
- ファイル書き込みエラー (`OSError`) → `shared.logger.fallback` ロガー経由で WARNING がログされ (stderr に表示される)、StreamHandler のみにフォールバックする; 例外は発生しない
- ログメッセージは**英語のみ**でなければならない (日本語不可) — `rules/coding.md` の規約

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`
- `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md`
- `90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md`

## Keywords

ConfigLoader
config isolation policy
RagConfigValidator
ProductionConfigValidator
Logger
runtime
