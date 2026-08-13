---
title: "Agent Operations and Observability - Validation and Troubleshooting (Part 2)"
category: agent
tags:
  - agent
  - operations
  - validation
  - troubleshooting
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_03_operations-and-observability-workflow-observability.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md
---

# エージェントの運用と可観測性

- 設定 → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## MCPサーバのリロードと再起動のセマンティクス

MCPサーバ定義（transport、url、startup_mode、call_timeout_sec、startup_timeout_sec、tool_names、auth_token、role、cmd、env）は再起動時点のスナップショットである。`/reload` は `[mcp_servers.*]` の変更を検出し、再起動が必要な変更として報告するが、稼働中のプロセスには一切適用しない。

`/mcp` / `/mcp status` は常に稼働中（再起動前）のサーバ設定を反映し、保留中の `/reload` の変更は反映しない。

MCP watchdog（バックグラウンドの自動ヘルスポーリング・自動再起動ループ）は削除済み。サブプロセスモードで失敗したサーバーは、次回の tool dispatch 時に `ensure_ready()` が *現在* の起動設定で再起動を試みるのみであり — これはヘルス駆動の復旧であって設定リロードではないため、保留中のMCPサーバ定義の変更も適用されない。

変更されたMCPサーバ定義が適用されるのは、エージェントの完全な再起動時のみである。

## `/context` の解釈

``` text
Context state:
  Messages        : 12
  Total chars     : 4,321
  Compress limit  : 8,000
  Remaining       : 3,679 chars until compression
  Compress count  : 1
  System prompt   : default
  Token estimate  : 1,080 (category-aware estimate)
  Token limit     : disabled
  Memory layer    : disabled
Budget breakdown:
  system        :    1,234 chars ( 38%)
   history       :    1,987 chars ( 62%)
```

- **Remaining:** `context_char_limit` までの残り距離 → 圧縮のトリガー
- **Token estimate:** カテゴリ別推定（テキスト: 4.0、ツール呼び出しJSON: 2.5、システムメッセージ: 3.5 の比率）を使用
- **Token limit:** `context_token_limit` が未設定の場合は `disabled`
- **Memory layer:** `use_memory_layer=True` の場合は `enabled (entries=N)`

**実装上の注意点:**
- `/context` の Token estimate値はカテゴリ別推定のまま変わらず、`/tokenize` の値が実際に使われるのは次ターンの履歴圧縮判定であり、`/context` の表示値ではない。
- カテゴリ別推定の比率定数（テキスト: 4.0、ツール呼び出しJSON: 2.5、システムメッセージ: 3.5）は `shared/token_estimation.py` の `RATIO_TEXT`/`RATIO_TOOL_CALL`/`RATIO_SYSTEM` を単一の正とする。`agent/services/context_view.py::_token_breakdown` はこれらをインポートして使用し、以前ローカルに重複定義していた同名の比率定数は廃止済み。
- `/context` の `Approval pending` はターン状態から算出される。一方、`/stats` の `Approval pending` はワークフロー状態を参照する。両フィールドは orchestrator と startup コマンドで常にペアでセット/クリアされているため実運用上の値は一致するが、参照しているフィールドはコマンドごとに異なる実装になっている。

## `/stats` の解釈

``` text
Turns: 5 | Tool calls: 12 | Errors: 1
LLM: retries=0, reconnects=0, HB timeouts=0, partials=0, parse_errors=0
Cache hits: 3 | Compress: 1 | Semantic cache hits: 0
Input tokens: 2,048 | Output tokens: 512
Latency (mean/max): llm=1.2s/2.1s, tools=0.3s/0.8s
```

- **Partial completions:** ストリーミング途中で中断されたLLM応答が記録される。詳細は `session_diagnostics`(`kind=partial_completion`)を確認すること。正式な部分完了モデルについては → [05_agent_03 §Partial-Completion Model](05_agent_03_01_turn-processing-flow-overview.md)
- **HB timeouts:** SSEハートビートタイムアウト(LLMの過負荷の可能性)
- **Cache hits:** ツール結果キャッシュのヒット数
- **Approval pending:** `ctx.workflow.approval_pending=True` の場合のみ表示される

**実装上の注意点:**
- 実際の `/stats` はキーバリュー形式で1項目1行、かつドキュメント記載より多くの項目を出力する。
- 条件付き行として、`stat_memory_consistency_failures` が真の場合のみ `Memory inconsist.`、メモリ埋め込みのサーキットブレーカーが開いている場合は `Memory embed: CIRCUIT OPEN [DEGRADED]`、rag_db_configured が真の場合は `Hint: Run /session rag-consistency for index integrity status` が追加表示される。
- `Latency (mean/max)` は `ctx.stats.stat_latency` の `"llm"` キーのサンプル配列のみを集計対象としており、ツール呼び出しの遅延行は出力されない。

## 関連資料

- [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md) — 起動とヘルスチェック
- [05_agent_10_02_operations-and-observability-audit-and-otel.md](05_agent_10_02_operations-and-observability-audit-and-otel.md) — 監査ログとOTel
- [05_agent_10_03_operations-and-observability-workflow-observability.md](05_agent_10_03_operations-and-observability-workflow-observability.md) — ワークフローの可観測性
- [05_agent_10_05_operations-and-observability-monitoring.md](05_agent_10_05_operations-and-observability-monitoring.md) — モニタリング
- [05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md](05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md) — RAG診断とメモリ
- [05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md](05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md) — 追加検証とトラブルシューティング
