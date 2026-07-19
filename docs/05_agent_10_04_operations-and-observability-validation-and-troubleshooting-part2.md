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
  - 04_mcp_06_12_watchdog-configuration-monitoring.md
source:
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md
---

# エージェントの運用と可観測性

- 設定 → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## MCP Server Reload and Restart Semantics(MCPサーバのリロードと再起動のセマンティクス)

**注記:** MCPサーバ定義(`transport`、`url`、`startup_mode`、
`call_timeout_sec`、`startup_timeout_sec`、`tool_names`、
`auth_token`、`role`、`cmd`、`env`)は再起動時点のスナップショットである。`/reload`
は `[mcp_servers.*]` の変更を検出し、再起動が必要な変更として報告する
(`[RESTART] - mcp_servers/<server>.<field>`)が、稼働中のプロセスには一切適用しない。
`/mcp` / `/mcp status` は常に稼働中(再起動前)のサーバ設定を反映し、保留中の
`/reload` の変更は反映しない。MCP watchdog(バックグラウンドの自動ヘルスポーリング・
自動再起動ループ)は2026-07-16に削除された
([04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md)参照)。
サブプロセスモードで失敗したサーバーは、次回のtool dispatch時に `ensure_ready()`
(`agent/factory.py`)が*現在*の起動設定で再起動を試みるのみであり — これはヘルス駆動の
復旧であって設定リロードではないため、保留中のMCPサーバ定義の変更も適用されない。
変更されたMCPサーバ定義が適用されるのは、エージェントの完全な再起動時のみである。

**実装補足:** 上記のフィールド単位の差分検出に加え、`config/*.toml` に新規追加されたサーバは `mcp_servers/<server> (new server)`、削除されたサーバは `mcp_servers/<server> (removed server)` として `needs_restart` に計上される。いずれも `ctx.cfg.mcp.mcp_servers` を書き換えず比較のみを行う関数であり、この点は既存の「稼働中のプロセスには一切適用しない」という記述と整合する(根拠: Explicit in code)。

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

**実装補足:**

- 実際の `/context` 出力には上記の項目に加え、`Fallback trunc`、`System prompt`、`Git`(ブランチ@コミット。取得失敗時は `unavailable`)、`Approval pending`、および `Budget breakdown` の各カテゴリ行(`system`/`history`/`tool_messages`、文字数と割合)が表示される。`state.partial_completions > 0` の場合のみ `Partial compl` 行が追加される(根拠: Explicit in code)。
- **Token estimateの算出方法はドキュメント記載と異なる。** 履歴トークンカウント関数は `last_input_tokens` が無い場合、単純な `文字数 / 4` ではなく、テキスト(比率4.0)・ツール呼び出しJSON(比率2.5)・システムメッセージ(比率3.5)をカテゴリ別に按分するカテゴリ別推定を行う。さらに `/context` が使うコンテキスト状態収集関数は同期版 `count_tokens()` のみを呼び出しており、`/tokenize` エンドポイントを問い合わせる非同期版は使われない。そのため `tokenize_url` が設定されていても `/context` のToken estimate値自体はカテゴリ別推定のまま変わらず、ラベルが `/tokenize (next turn)` に変わるだけである。`/tokenize` の値が実際に使われるのは次ターンの履歴圧縮判定であり、`/context` の表示値ではない(根拠: Explicit in code)。
- **Approval pendingの判定元がコマンドごとに異なる。** `/context` の `Approval pending` はターン状態から算出される。一方、後述の `/stats` の `Approval pending` はワークフロー状態を参照する。両フィールドは orchestrator と startup、workflow コマンド で常にペアでセット/クリアされているため実運用上の値は一致するが、参照しているフィールドはコマンドごとに異なる実装になっている(根拠: Explicit in code)。

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

**実装補足:**

- 上記のサンプル出力は簡略化されたイメージであり、実際の `/stats` はキーバリュー形式で1項目1行、かつドキュメント記載より多くの項目を出力する。`Session ID`、`Turns`、`Tool calls`、`Tool errors`、`LLM retries`、`LLM reconnects`、`HB timeouts`、`Partial compl`(0件でも常に表示、`stat_partial_completions > 0` の場合のみ `(stored in session_diagnostics)` を付記)、`Parse errors`、`Cache hits`、`Compress`、`Fallback trunc`、`Sem. cache`、`Input tokens`/`Output tokens`(未取得時は `N/A`)、`Debug mode` が常に出力される(根拠: Explicit in code)。
- 条件付き行として、`stat_memory_consistency_failures` が真の場合のみ `Memory inconsist.`、メモリ埋め込みのサーキットブレーカーが開いている場合は `Memory embed: CIRCUIT OPEN [DEGRADED]`、そうでなくFTSフォールバック回数が1以上の場合は `Memory embed: fts_only x<N> [degraded]`、`rag_db_configured`(`db.config.build_db_config()` が例外なく成功するか)が真の場合は `Hint: Run /session rag-consistency for index integrity status` が追加表示される。これらはドキュメントのサンプルには含まれていない(根拠: Explicit in code)。
- `Latency (mean/max)` は `ctx.stats.stat_latency` の `"llm"` キーのサンプル配列のみを集計対象としており、ツール呼び出し(`tools=...`)の遅延行は出力されない。ドキュメントのサンプル出力にある `tools=0.3s/0.8s` に相当する行は現行実装には存在しない(根拠: Explicit in code)。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_10_01_operations-and-observability-startup-and-health.md`
- `05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `05_agent_10_03_operations-and-observability-workflow-observability.md`
- `05_agent_10_05_operations-and-observability-monitoring.md`
- `05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`
- `05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md`
- `04_mcp_06_12_watchdog-configuration-monitoring.md`

## Keywords

workflow startup validation
MCP server reload
/context
/stats
partial completion
troubleshooting
