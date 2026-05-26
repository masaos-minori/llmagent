# Split Log

## 設計方針（将来の分割作業でも有効）

### Context Loader Pattern

```
Task → Routing → Minimal Skills → Shared Rules → Execution
```

### 4 原則

| 原則 | 内容 |
|---|---|
| **routing** | 分割後、`routing.md` の "Docs → task mapping" にタスク種別→参照ファイルの対応を追記する |
| **dependency direction** | 新ファイル間の依存は単方向に保つ。循環インポート・循環参照を作らない |
| **minimal loading** | 1 タスクで読む必要があるファイルが最小になるよう責務境界を引く |
| **shared normalization** | 複数ファイルに重複する共通仕様・プロトコル定義は 1 ファイルに集約し、他からは参照のみとする |


## 現状サマリー

### docs/

| ファイル | 行数 | 状態 |
|---|---|---|
| `00_llm-implementation-guide.md` | 24L | index |
| `01_overview.md` | 339L | 変更なし |
| `02_deployment.md` | 239L | 変更なし |
| `03_ingestion-pipeline.md` | 385L | 変更なし（分割トリガー未達） |
| `04_mcp-servers.md` | 10L | index |
| `04_mcp-web-search.md` | 185L | 分割済 |
| `04_mcp-file.md` | 198L | 分割済 |
| `04_mcp-github.md` | 209L | 分割済 |
| `04_mcp-protocol.md` | 60L | 分割済 |
| `05_agent.md` | 344L | 分割済 |
| `05_agent-impl.md` | 319L | 分割済 |
| `06_common.md` | 10L | index |
| `06_ref-infra.md` | 307L | 分割済 |
| `06_ref-mcp.md` | 181L | 分割済 |
| `06_ref-rag.md` | 143L | 分割済 |
| `06_ref-agent.md` | 14L | index（分割完了） |
| `06_ref-agent-session.md` | — | 分割済（agent_session.py） |
| `06_ref-agent-repl.md` | — | 分割済（agent_repl.py） |
| `06_ref-agent-config.md` | — | 分割済（agent_config.py） |
| `06_ref-agent-context.md` | — | 分割済（agent_context.py） |
| `06_ref-agent-view.md` | — | 分割済（cli_view.py） |
| `06_ref-agent-commands.md` | — | 分割済（agent_commands.py + ミックスイン群） |
| `06_ref-agent-llm.md` | — | 分割済（llm_client.py） |
| `06_ref-agent-history.md` | — | 分割済（history_manager.py） |

### scripts/（分割対象のみ）

| ファイル | 行数 | 状態 |
|---|---|---|
| `agent_repl.py` | 540L | 分割済（残留コア） |
| `agent_repl_debug.py` | 116L | 分割済 |
| `agent_repl_health.py` | 169L | 分割済 |
| `agent_repl_tool_exec.py` | 186L | 分割済 |
| `github_mcp_server.py` | 1043L | 分割済（残留コア） |
| `github_mcp_models.py` | 414L | 分割済 |
| `github_mcp_service.py` | 770L | 分割済 |
| `fileop_mcp_server.py` | 726L | 分割済（残留コア） |
| `fileop_mcp_models.py` | 281L | 分割済 |
| `fileop_mcp_service.py` | 748L | 分割済 |
| `agent_commands.py` | 187L | 分割済（残留コア） |
| `agent_cmd_session.py` | 125L | 分割済 |
| `agent_cmd_mcp.py` | 176L | 分割済 |
| `agent_cmd_config.py` | 318L | 分割済 |
| `agent_cmd_context.py` | 260L | 分割済 |
| `agent_cmd_rag.py` | 253L | 分割済 |
| `agent_cmd_ingest.py` | 162L | 分割済 |
| `agent_rag.py` | 253L | 分割済（残留コア） |
| `rag_types.py` | 45L | 分割済 |
| `rag_repository.py` | 316L | 分割済 |
| `rag_llm.py` | 381L | 分割済 |

### order.txt 対象 — 全完了

| 対象 | 状態 |
|---|---|
| `scripts/github_mcp_server.py` 2098L | 完了 |
| `scripts/fileop_mcp_server.py` 1649L | 完了 |
| `scripts/agent_commands.py` 1286L | 完了 |
| `scripts/agent_rag.py` 954L | 完了 |
| `docs/06_ref-agent.md` 494L | 完了 |
