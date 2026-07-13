---
title: "New MCP Server Addition Checklist"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# New MCP Server Addition Checklist

## 新規MCPサーバー追加チェックリスト

サーバーを追加する際:

- [ ] `scripts/mcp_servers/<name>/server.py`を作成する(`MCPServer`を継承し、`dispatch()`をオーバーライドする)
- [ ] `MCPServer`サブクラス内で`own_config_file = "<key>_mcp_server.toml"`を宣言する — `run_http()`が自動的に`ConfigLoader.restrict_to(own_config_file)`を呼び出す
- [ ] `config/<key>_mcp_server.toml`を作成し、**サーバーが必要とするすべての設定**を含める(DBパス・外部URL等を含む;`agent.toml`は参照しない)
- [ ] `config/agent.toml`の`[[tool_definitions]]`にツール定義を追加する
- [ ] ツールは`shared/tool_constants.py`のfrozensetに登録する(起動時に自動ルーティングされる);設定側の`tool_names`は任意のドリフト検証にのみ使われる
- [ ] `deploy/deploy.sh`のコピー対象リストに新規ファイルを追加する
- [ ] `deploy/setup_services.sh`に起動手順を追加する
- [ ] 新規ツールすべてについて`config/agent.toml`に`tool_safety_tiers`のエントリを追加する
- [ ] 新しいドキュメントが必要な場合は`routing.md`を更新する

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
