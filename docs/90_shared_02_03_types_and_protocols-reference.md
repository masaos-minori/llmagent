---
title: "Shared Types and Protocols - Reference"
category: shared
tags:
  - shared
  - types
  - tool-constants
  - call-tool
  - protocol-vs-dataclass
related:
  - 90_shared_00_document-guide.md
  - 90_shared_02_01_types_and_protocols-core-types.md
  - 90_shared_02_02_types_and_protocols-tool-and-execution-dto.md
source:
  - 90_shared_02_01_types_and_protocols-core-types.md
---

# 共有の型とプロトコル

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 9a. `DbConfig` (`db/config.py`)

```python
@dataclass
class DbConfig:
    rag_db_path: str
    session_db_path: str
    workflow_db_path: str = "/opt/llm/db/workflow.sqlite"
    sqlite_vec_so: str = ""       # empty = vec extension not required
    sqlite_timeout: int = 30
    sqlite_busy_timeout_ms: int = 30000
    embedding_dims: int = 384
```

- `__post_init__` で検証される: 親ディレクトリが存在すること、timeout/embedding_dims が 1 以上であること
- `ConfigLoader().load("agent.toml")` 経由で `agent.toml` を読み込む `build_db_config()` によって構築される
- `SQLiteHelper`、`maintenance.py`、およびセッションファクトリのコードで使用される

---

## 10. ツール定数 (`shared/tool_constants.py`)

すべての定数は `frozenset[str]` である。`ToolRegistry` のシードデータとして、また `ToolExecutor` の副作用分類に使用される。READ/WRITE/DELETE/RAG/CICD/MDQ/GIT/SHELL/WEB_SEARCH のカテゴリごとに定義され、`shared/tool_executor.py` および `agent/tool_runner.py` からも参照される。(Explicit in code: `scripts/shared/tool_constants.py`)

---

## 11. `CallToolRequest` / `CallToolResponse` リファレンス

`mcp_servers/models.py` で定義されている (`shared/` ではない。`mcp_servers` パッケージは PyPI の Model Context Protocol SDK `mcp` との名前衝突を避けるため `mcp` から改称された)。これらは MCP サーバー内でのみ使用される Pydantic モデルであり、`shared/` レイヤーのコードは `mcp_servers/` からインポートしない。`shared/tool_executor.py` の `ToolCallResult` dataclass と混同しないこと。(Explicit in code: `scripts/mcp_servers/models.py`)

---

## 12. `Protocol`、`TypedDict`、`dataclass`、DTO の違い

| Kind | Examples | Mutability | `isinstance()` | Usage |
|---|---|---|---|---|
| `TypedDict` | `LLMMessage`, `ArtifactEvent` | Mutable dict | No (unless `@runtime_checkable`) | Data transport; duck-typed |
| `Protocol` | `RagConfig` | Depends on impl | Yes (if `@runtime_checkable`) | Structural contract; any object satisfying fields works |
| frozen `dataclass` | `LLMUsage`, `LLMResponse`, `ActionResult` | Immutable | Yes | Value objects; hashable |
| `dataclass` | `ShellPolicy`, `DbConfig` | Mutable | Yes | Configuration objects |
| Pydantic model | `CallToolRequest`, `CallToolResponse` | Mutable | Yes | MCP HTTP request/response validation |

**AI ガイダンス:** 関数が `RagConfig` を受け取る場合、必要なフィールドを持つオブジェクトであれば
(`SimpleNamespace` を含め) プロトコルを満たす。`AgentConfig` でなければならないと仮定しないこと。


