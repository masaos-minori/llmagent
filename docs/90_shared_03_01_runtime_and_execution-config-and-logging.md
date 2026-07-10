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

# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 1. Purpose

Documents the runtime infrastructure and utilities in `shared/`: config loading, logging,
plugin registry, token counting, OTel tracing, git helper, formatters, ToolExecutor,
and McpServerConfig.

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
- Loads and merges one or more TOML/JSON files in order
- Later files override earlier files
- Keys prefixed with `_` are excluded (documentation metadata)
- Raises `ConfigMissingError` (file not found), `ConfigParseError` (parse error), or `ConfigReadError` (I/O error) — all subclass `ValueError`
- If `restrict_to()` has been called, raises `ConfigPermissionError` when a filename is not in the allowed set

**`load_all()`**
- Loads only `agent.toml` (`_BASE_CONFIG_FILES = ("agent.toml",)`)
- Missing files are silently skipped (catches `ConfigMissingError` and continues)
- If `restrict_to()` has been called, raises `ConfigPermissionError` when `agent.toml` is not in the allowed set

**`restrict_to(*filenames)`** (class method)
- Call once at process startup to declare the only config files this process is permitted to load
- Any subsequent `load()` or `load_all()` call that touches a file outside this set raises `ConfigPermissionError`
- Not called by the agent process (unrestricted); called by MCP servers, crawler, ingester, chunk_splitter
- Tests do not call `restrict_to()`, so test processes are unrestricted

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

- Configures `FileHandler` + `StreamHandler` automatically (`propagate=False` prevents duplication)
- `structured_log=True` → JSON Lines format for log file
- Context injection: `set_context(turn_id="T001", session_id=42)` adds fields to all subsequent log lines
- File write errors → WARNING logged via `shared.logger.fallback` logger (visible on stderr), then falls back to StreamHandler only; no exception raised
- Log messages must be in **English only** (no Japanese)

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
