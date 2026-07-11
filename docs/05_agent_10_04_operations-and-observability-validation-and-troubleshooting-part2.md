---
title: "Agent Operations and Observability - Validation and Troubleshooting (Part 2)"
category: agent
tags:
  - agent
  - operations
  - startup-validation
  - mcp-reload
  - troubleshooting
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_03_operations-and-observability-workflow-observability.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md
---

# エージェントの運用と可観測性

- 設定 → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## MCP Server Reload and Restart Semantics(MCPサーバのリロードと再起動のセマンティクス)

**注記:** MCPサーバ定義(`transport`、`url`、`startup_mode`、
`healthcheck_mode`、`call_timeout_sec`、`startup_timeout_sec`、`tool_names`、
`auth_token`、`role`、`cmd`、`env`)は再起動時点のスナップショットである。`/reload`
は `[mcp_servers.*]` の変更を検出し、再起動が必要な変更として報告する
(`[RESTART] - mcp/<server>.<field>`)が、稼働中のプロセスには一切適用しない。
`/mcp` / `/mcp status` は常に稼働中(再起動前)のサーバ設定を反映し、保留中の
`/reload` の変更は反映しない。ウォッチドッグによる再起動(`watchdog_loop()`)は、
失敗したサブプロセスを*現在*の起動設定で再起動する — これはヘルス駆動の復旧であり、
設定リロードではないため、保留中のMCPサーバ定義の変更も適用されない。
変更されたMCPサーバ定義が適用されるのは、エージェントの完全な再起動時のみである。

**注記:** MCPサーバ定義(`transport`、`url`、`startup_mode`、
`healthcheck_mode`、`call_timeout_sec`、`startup_timeout_sec`、`tool_names`、
`auth_token`、`role`、`cmd`、`env`)は再起動時点のスナップショットである。`/reload`
は `[mcp_servers.*]` の変更を検出し、再起動が必要な変更として報告する
(`[RESTART] - mcp/<server>.<field>`)が、稼働中のプロセスには一切適用しない。
`/mcp` / `/mcp status` は常に稼働中(再起動前)のサーバ設定を反映し、保留中の
`/reload` の変更は反映しない。ウォッチドッグによる再起動(`watchdog_loop()`)は、
失敗したサブプロセスを*現在*の起動設定で再起動する — これはヘルス駆動の復旧であり、
設定リロードではないため、保留中のMCPサーバ定義の変更も適用されない。
変更されたMCPサーバ定義が適用されるのは、エージェントの完全な再起動時のみである。

---

## Interpreting `/context`(`/context` の解釈)

```
Context state:
  Messages        : 12
  Total chars     : 4,321
  Compress limit  : 8,000
  Remaining       : 3,679 chars until compression
  Compress count  : 1
  System prompt   : default
  System preview  : '...'
  Token estimate  : 1,080 (chars / 4)
  Token limit     : disabled
  Memory layer    : disabled
Budget breakdown:
  system        :    1,234 chars ( 38%)
   history       :    1,987 chars ( 62%)
```

- **Remaining:** `context_char_limit` までの残り距離 → 圧縮のトリガー
- **Token estimate:** `/tokenize` エンドポイントが設定されていない限り `文字数 / 4`
- **Token limit:** `context_token_limit` が未設定の場合は `disabled`。`context_token_limit` が設定されている場合は `200,000 tokens`(または設定値)を表示
- **Memory layer:** `use_memory_layer=True` の場合は `enabled (entries=N)`

---

## Interpreting `/stats`(`/stats` の解釈)

```
Turns: 5 | Tool calls: 12 | Errors: 1
LLM: retries=0, reconnects=0, HB timeouts=0, partials=0, parse_errors=0
Cache hits: 3 | Compress: 1 | Semantic cache hits: 0
Input tokens: 2,048 | Output tokens: 512
Latency (mean/max): llm=1.2s/2.1s, tools=0.3s/0.8s
```

- **Partial completions:** ストリーミング途中で中断されたLLM応答が記録される。詳細は `session_diagnostics`(`kind=partial_completion`)を確認すること。正式な部分完了モデルについては → [05_agent_03 §Partial-Completion Model](05_agent_03_01_turn-processing-flow-overview.md)
- **HB timeouts:** SSEハートビートタイムアウト(LLMの過負荷の可能性)
- **Cache hits:** ツール結果キャッシュのヒット数
- **Approval pending:** `Approval: PENDING — use /approve or /reject` の行は、`ctx.workflow.approval_pending=True` の場合のみ表示される。ワークフロータスクが `/approve` または `/reject` の入力を待機している場合に表示される。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_10_01_operations-and-observability-startup-and-health.md`
- `05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `05_agent_10_03_operations-and-observability-workflow-observability.md`
- `05_agent_10_05_operations-and-observability-monitoring.md`
- `05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`
- `05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md`

## Keywords

workflow startup validation
MCP server reload
/context
/stats
partial completion
troubleshooting
