---
title: "Agent Documentation Guide"
category: agent
tags:
  - agent
  - documentation
  - guide
  - routing
  - file-index
related:
  - 05_agent_01_system-overview.md
  - 05_agent_02_runtime-architecture.md
  - 05_agent_05_llm-and-streaming.md
  - 05_agent_13_reference-api.md
  - 05_agent_90_inconsistencies_and_known_issues.md
---

# Agent Documentation Guide

再構成されたAgentドキュメントセットのエントリポイントである。
最初に本ファイルを読み、どの章を開くべきかを判断すること。

---

## Purpose of This Document Set

これらのファイルはLLM Agent REPLシステムを文書化するものである。LLM Agent REPLシステムとは、LLMのfunction
callingを用いてMCPツールサーバーと対話し、会話履歴を維持し、ターミナルに
回答を返すCLIツールである。これらのファイルが正式なリファレンスである(元のモノリシックなソース
ファイルは削除済み)。

---

## Recommended Reading Order (Human)

```
01 Overview → 02 Runtime Architecture → 03 Turn Processing Flow
  → 04 State/Persistence → 05 LLM/Streaming → 06 Tool Execution/Approval
  → 07 CLI/Commands → 08 Configuration → 09 Data Layer
  → 10 Operations/Observability → 11 Extension Points → 12 Memory → 13 Reference API
```

---

## AI Query Routing Table

| Question | File |
|---|---|
| エージェントとは何か、どのように動作するか | `05_agent_01` |
| 主要コンポーネント/依存関係は何か。関数シグネチャは | `05_agent_02` (runtime) / `05_agent_13` (signatures) |
| 1回のユーザーターンで何が起きるか | `05_agent_03` (§Overview; §LLM+Tool Loop; §Workflow Engine) |
| 履歴圧縮とは何か。永続化される状態とメモリ上の状態の違いは | `05_agent_04` |
| SSEストリーミング、リトライ、`LLMTransportError`とは | `05_agent_05` |
| ツールはどのように実行/承認されるか。`/plan`モードとは | `05_agent_06` (§Execution; §Approval) |
| スラッシュコマンドとその効果は。`/reload`のスコープは | `05_agent_07` (§Slash Commands; §Hot Reload) |
| 設定フィールド、デフォルト値、どのファイルが何を制御するか | `05_agent_08` (§Loading Agent Config; §LLM/RAG; §Tools/Memory; §MCP/Approval/Obs) |
| エージェントはどのSQLiteテーブルを使うか | `05_agent_09_data-layer-*.md` (session-db / access-patterns) |
| 起動、検証、トラブルシューティング、監査ログの読み方は | `05_agent_10_operations-and-observability-*.md` (startup-and-health / validation-and-troubleshooting / audit-and-otel) |
| プラグインコマンド、ツール、新しいMCPサーバーの追加方法は | `05_agent_11_extension-points-*.md` (plugin-command / tool-registration / registry-rules) |
| メモリレイヤー(注入、プルーニング)はどのように動作するか | `05_agent_12_memory-*.md` — **Implemented** (SQLite + JSONL + FTS5 + optional vectors) |
| クラスXはどこで定義され、呼び出し元は誰か | `05_agent_13` — runtime context → `05_agent_02` |

---

## Canonical Source Rules

削除済みの`05_ref-*` / `05_agent-impl-flow.md` / `05_agent-ops.md`ファイルは、上記の02〜13章に統合されている。既知の問題と未解決の論点: [05_agent_90_inconsistencies_and_known_issues.md](05_agent_90_inconsistencies_and_known_issues.md)。

---

## File Index

| Chapter | Files |
|---|---|
| 00 | [document-guide.md](05_agent_00_document-guide.md) — this file |
| 01 | [system-overview.md](05_agent_01_system-overview.md) — purpose, tool-calling model, component map |
| 02 | [runtime-architecture.md](05_agent_02_runtime-architecture.md) — dependency diagram, responsibilities |
| 03 turn processing | [overview](05_agent_03_01_turn-processing-flow-overview.md), [llm-tool-loop](05_agent_03_02_turn-processing-flow-llm-tool-loop.md), [workflow-engine](05_agent_03_03_turn-processing-flow-workflow-engine.md) |
| 04 state/persistence | [state-model](05_agent_04_01_state-and-persistence-state-model.md), [history-compression](05_agent_04_02_state-and-persistence-history-compression.md), [platform-databases](05_agent_04_03_state-and-persistence-platform-databases.md) |
| 05 | [llm-and-streaming.md](05_agent_05_llm-and-streaming.md) — LLMClient API, SSE, reconnect |
| 06 tool exec/approval | [execution](05_agent_06_01_tool-execution-and-approval-execution.md), [approval](05_agent_06_02_tool-execution-and-approval-approval.md), [concurrency-safety](05_agent_06_03_tool-execution-and-approval-concurrency-safety.md), [canonical](05_agent_06_04_tool-execution-and-approval-canonical.md) |
| 07 CLI/commands | [cli-reference](05_agent_07_01_cli-and-commands-cli-reference.md), [cliview](05_agent_07_02_cli-and-commands-cliview.md), [command-registry](05_agent_07_03_cli-and-commands-command-registry.md), [purpose](05_agent_07_04_cli-and-commands-purpose.md), [repl-io](05_agent_07_05_cli-and-commands-repl-io.md), [hot-reload](05_agent_07_06_cli-and-commands-hot-reload.md), [migration-notes](05_agent_07_07_cli-and-commands-migration-notes.md) |
| 07 slash commands | [session-mcp](05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md), [context-db](05_agent_07_09_cli-and-commands-slash-commands-context-db.md), [workflow-debug](05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md), [memory-other](05_agent_07_11_cli-and-commands-slash-commands-memory-other.md) |
| 08 configuration | [loading-agent-config](05_agent_08_01_configuration-loading-agent-config.md), [llm-rag](05_agent_08_02_configuration-llm-rag.md), [tools-memory](05_agent_08_03_configuration-tools-memory.md), [mcp-approval-obs](05_agent_08_04_configuration-mcp-approval-obs.md) |
| 09 data layer | [session-db](05_agent_09_01_data-layer-session-db.md), [access-patterns](05_agent_09_02_data-layer-access-patterns.md), [indexing-boundaries](05_agent_09_03_data-layer-indexing-boundaries.md) |
| 10 operations | [startup-and-health](05_agent_10_01_operations-and-observability-startup-and-health.md), [audit-and-otel](05_agent_10_02_operations-and-observability-audit-and-otel.md), [workflow-observability](05_agent_10_03_operations-and-observability-workflow-observability.md), [validation-and-troubleshooting](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md), [monitoring](05_agent_10_05_operations-and-observability-monitoring.md), [rag-diagnostics-and-memory](05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md) |
| 11 extension points | [plugin-command](05_agent_11_01_extension-points-plugin-command.md), [tool-registration](05_agent_11_02_extension-points-tool-registration.md), [registry-rules](05_agent_11_03_extension-points-registry-rules.md) |
| 12 memory | [overview-and-modes](05_agent_12_01_memory-overview-and-modes.md), [gate-data-model-search](05_agent_12_02_memory-gate-data-model-search.md), [module-ref-core-and-store](05_agent_12_03_memory-module-ref-core-and-store.md), [module-ref-retrieval-and-injection](05_agent_12_04_memory-module-ref-retrieval-and-injection.md), [module-ref-extraction-and-facade](05_agent_12_05_memory-module-ref-extraction-and-facade.md), [module-ref-ops-and-scoring](05_agent_12_06_memory-module-ref-ops-and-scoring.md) |
| 13 | [reference-api.md](05_agent_13_reference-api.md) — per-module API: role, callers, callees, config, failure |
| 90 | [inconsistencies_and_known_issues.md](05_agent_90_inconsistencies_and_known_issues.md) — known bugs, spec conflicts, open questions |

---

## Documentation Consistency Checklist

スキーマやコマンド参照を変更する際は、以下を確認すること: `05_agent_01_system-overview.md` の§Slash Commandsおよび`05_agent_07_cli-and-commands-*.md`が`scripts/agent/commands/registry.py`と一致していること(すべてのCommandDefにドキュメント項目があり、削除済みコマンドへの参照が残っていないこと)。`05_agent_09_data-layer-*.md`が`scripts/db/schema_sql.py`と`init_db.sh`と一致していること。診断関連のドキュメントが`session_diagnostics`のみを参照していること(削除済みの`diagnostics.jsonl`への参照が残っていないこと)。

---

## Known Limitations

古いモノリシックなソースファイル(`05_agent.md`、`05_ref-agent-*.md`など)は削除済みであり、本ドキュメントセットが正式なリファレンスである。メモリレイヤー(`agent/memory/`)は`05_agent_12_memory-*.md`で詳細に文書化され、`05_agent_02`の§Memory Servicesで概要が述べられている。

## Related Documents

- `05_agent_01_system-overview.md`
- `05_agent_02_runtime-architecture.md`
- `05_agent_05_llm-and-streaming.md`
- `05_agent_13_reference-api.md`
- `05_agent_90_inconsistencies_and_known_issues.md`

## Keywords

agent
documentation
guide
routing
file-index
