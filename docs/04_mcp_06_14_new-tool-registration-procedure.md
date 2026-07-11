---
title: "New Tool Registration Procedure"
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

# New Tool Registration Procedure

## 新規ツール登録手順

**既存**のMCPサーバーに新しいツールを追加する場合:

| 手順 | 操作 | 必須か |
|---|---|---|
| 1 | `shared/tool_constants.py`内の該当するfrozensetにツール名を追加する(例: `READ_TOOLS`、`WRITE_TOOLS`、または新しい`<SERVER>_TOOLS` frozensetを作成して`get_all_mcp_tool_names()`に追加) | **[必須]** |
| 2 | レジストリはインポート時にこれらのfrozensetから自動的に構築される — レジストリの手動編集は不要 | (自動) |
| 3 | 所有元のMCPサーバー(`mcp/<name>/server.py`)に`dispatch()`ハンドラを実装する | **[必須]** |
| 4 | `/v1/tools`エンドポイントでツールを公開する(`server_key`フィールドを含むツール定義を返す) | **[推奨]** — 起動時のドリフト検証を有効化するが、ルーティングには影響しない |
| 5 | `config/tools_definitions.toml`にLLMスキーマを追加する(OpenAIのfunction-calling形式) | **[必須]** — LLMにツールを見せる場合 |
| 6 | 新しいツールについて`config/agent.toml`に`tool_safety_tiers`のエントリを追加する | **[必須]** — すべてのツールは安全性ティアを宣言する必要がある |
| 7 | `config/<key>_mcp_server.toml`の`[mcp_servers.<key>]`セクションの`tool_names`にツール名を追加する | **[任意]** — 起動時のドリフト検証のみを有効化する;ルーティングには不要 |

**注記**: すべてのツールはToolRegistryに明示的に登録する必要がある。プレフィックスベースのルーティングは存在しない。

### 検証

登録完了後:

```bash
uv run pytest tests/test_tool_constants.py tests/test_route_resolver.py -v
```

期待される結果: すべてのルーティングテストがパスする。`tool_definitions_strict = true`の場合、エージェントを再起動し、起動ログに未マッピングの警告なしで`"Routing: N/N tools mapped"`が表示されることを確認する。

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
