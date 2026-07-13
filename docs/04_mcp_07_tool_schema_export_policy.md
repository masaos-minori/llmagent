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

### 実装上の補足 (Current behavior)

- `tests/test_mcp_tool_schema_exports.py` の `_TOOL_MODULES` に、全9モジュール(`shell`, `cicd`, `git`, `rag_pipeline`, `web_search`, `mdq`, `github`, `file.read_tools`, `file.write_tools`, `file.delete_tools`)が列挙されており、各モジュールが `TOOL_LIST` を空でないリストとしてエクスポートし、`_MCP_TOOLS` を持たないことを機械的に検証している。実装を確認した限り、`file.delete_tools` を含む全モジュールで `TOOL_LIST` への移行が完了している。(根拠: Explicit in code)
- `mdq/tools.py` のみ `TOOL_LIST` の要素型を `MCPToolSchema`(`TypedDict`、`status` および任意項目 `is_write`/`requires_serial` を含む)として明示しており、`mdq/server.py` では `mcp_tools = cast(list[dict[str, Any]], TOOL_LIST)` として `MCPServer.mcp_tools`(`list[dict[str, Any]]`)に代入している。他サーバーは `TOOL_LIST` の宣言時点で `list[dict[str, Any]]` または `list[dict]` 型であり、`cast` を要しない。(根拠: Explicit in code)
- 各サーバーの `server.py` は `tools.py` から `TOOL_LIST` をインポートし、`MCPServer` サブクラスの `mcp_tools` クラス属性に代入する。`MCPServer.list_tools()` はエージェント向けのツール名一覧を、`list_tools_with_server_key()` は `server_key` を付与したツール定義一覧を返し、後者は `/v1/tools` エンドポイントおよび起動時のツール検出で使用される(`scripts/mcp_servers/server.py`)。`file.read_tools` / `file.write_tools` / `file.delete_tools` の各 `server.py` は `list_tools_with_server_key()` を使わず、`/v1/tools` ハンドラ内で `TOOL_LIST` を直接 `server_key` 付きに変換している箇所がある(例: `scripts/mcp_servers/file/read_server.py`)。(根拠: Explicit in code)
- `shared/tool_registry.py` の `ToolDefinition.description` / `input_schema` フィールドは「将来利用のため予約」であり `_populate_default_registry()` では未設定と明記されている。LLM向けのツールスキーマ(description・inputSchema)はこのレジストリではなく各サーバーの `tools.py` の `TOOL_LIST` に由来する、という役割分担がコード内コメントで明示されている。本ドキュメントの記述と整合している。(根拠: Explicit in code)

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_03_02_tool-registry.md`

## Keywords

mcp
tool-schema
export
policy
