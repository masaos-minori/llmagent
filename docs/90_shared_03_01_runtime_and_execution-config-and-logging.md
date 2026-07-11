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
  - 90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md
  - 90_shared_03_04_runtime_and_execution-caching-and-reference.md
source:
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
---

# 共有ランタイムと実行基盤

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 1. 目的

`shared/` におけるランタイム基盤とユーティリティを文書化する: 設定読み込み、ロギング、
プラグインレジストリ、トークンカウント、OTel トレーシング、git ヘルパー、フォーマッター、ToolExecutor、
および McpServerConfig。

---

## 2. `ConfigLoader` (`shared/config_loader.py`)

```python
class ConfigLoader:
    def __init__(self, config_dir: Path | None = None)
    def load(self, *filenames: str) -> dict[str, Any]
    def load_all(self) -> dict[str, Any]

    @classmethod
    def restrict_to(cls, *filenames: str) -> None
```

**`load(*filenames)`**
- 1 つ以上の TOML/JSON ファイルを順に読み込み、マージする
- 後のファイルが前のファイルを上書きする
- `_` で始まるキーは除外される (ドキュメント用メタデータ)
- `ConfigMissingError` (ファイル未検出)、`ConfigParseError` (パースエラー)、`ConfigReadError` (I/O エラー) を発生させる — いずれも `ValueError` のサブクラス
- `restrict_to()` が呼ばれている場合、許可セットに含まれないファイル名を指定すると `ConfigPermissionError` を発生させる

**`load_all()`**
- `agent.toml` のみを読み込む (`_BASE_CONFIG_FILES = ("agent.toml",)`)
- 存在しないファイルは黙って無視される (`ConfigMissingError` を捕捉して継続)
- `restrict_to()` が呼ばれている場合、`agent.toml` が許可セットに含まれないと `ConfigPermissionError` を発生させる

**`restrict_to(*filenames)`** (クラスメソッド)
- プロセス起動時に一度呼び出し、そのプロセスが読み込むことを許可された設定ファイルを宣言する
- それ以降の `load()` や `load_all()` の呼び出しがこのセット外のファイルに触れると `ConfigPermissionError` を発生させる
- エージェントプロセスからは呼ばれない (無制限); MCP サーバー、crawler、ingester、chunk_splitter から呼ばれる
- テストは `restrict_to()` を呼ばないため、テストプロセスは無制限である

---

## 2a. プロセス分離方針 (Config Isolation Policy)

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

## 3. `Logger` (`shared/logger.py`)

```python
class Logger:
    def __init__(self, name: str, filepath: str, *, structured_log: bool = False)
    def info(self, msg: str, *args, **kwargs) -> None
    def warning(self, msg: str, *args, **kwargs) -> None
    def error(self, msg: str, *args, **kwargs) -> None
    def set_context(self, **kwargs) -> None
    def clear_context(self) -> None
```

- `FileHandler` + `StreamHandler` を自動設定する (`propagate=False` により重複を防止)
- `structured_log=True` → ログファイルは JSON Lines 形式になる
- コンテキスト注入: `set_context(turn_id="T001", session_id=42)` により、以降のすべてのログ行にフィールドが追加される
- ファイル書き込みエラー → `shared.logger.fallback` ロガー経由で WARNING がログされ (stderr に表示される)、StreamHandler のみにフォールバックする; 例外は発生しない
- ログメッセージは**英語のみ**でなければならない (日本語不可)

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md`
- `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`
- `90_shared_03_04_runtime_and_execution-caching-and-reference.md`

## Keywords

ConfigLoader
config isolation policy
Logger
runtime
