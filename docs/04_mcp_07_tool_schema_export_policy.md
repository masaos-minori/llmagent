---
title: "MCP Tool Schema Export Policy"
category: mcp
tags:
  - mcp
  - tool-schema
  - export
  - policy
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_03_02_tool-registry.md
---

# MCPツールスキーマ エクスポート命名ポリシー

## 正規のエクスポート名: `TOOL_LIST`

すべてのMCPサーバーのツールスキーマモジュール(`mcp/<name>/tools.py`)は、正規のツールリストを`TOOL_LIST`としてエクスポートしなければならない。

関連: [04_mcp_03_02_tool-registry.md](04_mcp_03_02_tool-registry.md) — ToolRegistry の所有権・ルーティングの役割について説明している（本ドキュメントのスキーマエクスポートの役割とは異なる）。

### 根拠

- `TOOL_LIST`はプレフィックスのないパブリックな名前であり、これがメインのエクスポートであることを明確に示す。
- GitHub MCPは既に`TOOL_LIST`を正規名として使用している(`mcp/github/tools.py`を参照)。

### 移行履歴

すべてのMCPサーバーは`TOOL_LIST`への移行が完了している。移行は以下の順序で実施された。

1. **git** — `scripts/mcp_servers/git/tools.py`, `scripts/mcp_servers/git/server.py`
2. **mdq** — `scripts/mcp_servers/mdq/tools.py`, `scripts/mcp_servers/mdq/server.py`
3. **rag_pipeline** — `scripts/mcp_servers/rag_pipeline/tools.py`, `scripts/mcp_servers/rag_pipeline/server.py`
4. **shell** — `scripts/mcp_servers/shell/tools.py`, `scripts/mcp_servers/shell/server.py`
5. **cicd** — `scripts/mcp_servers/cicd/tools.py`, `scripts/mcp_servers/cicd/server.py`
6. **web_search** — `scripts/mcp_servers/web_search/tools.py`, `scripts/mcp_servers/web_search/server.py`
7. **file_read** — `scripts/mcp_servers/file/read_tools.py`, `scripts/mcp_servers/file/read_server.py`
8. **file_write** — `scripts/mcp_servers/file/write_tools.py`, `scripts/mcp_servers/file/write_server.py`
9. **file_delete** — `scripts/mcp_servers/file/delete_tools.py`, `scripts/mcp_servers/file/delete_server.py`

### 検証

すべての移行完了後:
- 実行: `pytest tests/test_<name>_mcp_service.py -v`
- 実行: `pytest tests/test_mcp_tool_schema_exports.py -v` — アクティブなすべてのMCPツールスキーマモジュールが、"name"キーを持つ辞書の空でないリストとしてTOOL_LISTをエクスポートしていること、およびレガシー名の_MCP_TOOLSを使用しているモジュールが存在しないことを検証する。

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_03_02_tool-registry.md`

## Keywords

mcp
tool-schema
export
policy
