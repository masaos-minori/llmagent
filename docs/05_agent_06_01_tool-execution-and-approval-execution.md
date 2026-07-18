---
title: "Agent Tool Execution and Approval - Execution"
category: agent
tags:
  - agent
  - tool-execution
  - toolexecutor
  - dag-scheduler
  - parallel-execution
related:
  - 05_agent_00_document-guide.md
  - 05_agent_06_02_tool-execution-and-approval-approval.md
  - 05_agent_06_03_tool-execution-and-approval-concurrency-safety.md
  - 05_agent_06_04_tool-execution-and-approval-canonical.md
---

# エージェントのツール実行と承認

- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- MCPルーティング → [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)
- GitHub変更操作の承認/gitops制御 → [05_agent_06_02_tool-execution-and-approval-approval.md](05_agent_06_02_tool-execution-and-approval-approval.md)

## 目的

`ToolExecutor`の挙動、並列実行と逐次実行、承認フロー、
プランモード、ツール実行結果の要約、キャッシュ、安全制御、`allowed_tools`を文書化する。

---

## ToolExecutor (`shared/tool_executor.py`)

`execute(tool_name, args) -> ToolCallResult`のディスパッチ優先順位:

```
1. TTL cache                           — 期限切れでなければキャッシュ結果を返す
2. MCP server dispatch via internal method
     → ToolRouteResolver.resolve()     — tool_name → server_key (ルーティングの権威; 04_mcp_03 §Routing Source of Truth 参照)
     → McpServerHealthRegistry check  — UNAVAILABLEなサーバーをスキップ
     → LifecycleProtocol.ensure_ready() — 必要に応じてondemandサーバーを起動
     → HttpTransport — MCPサーバーへ送信
```

`ToolCallResult`はfrozenなdataclass: `(output: str, is_error: bool, request_id: str, server_key: str)`

---

## 並列実行と逐次実行

`execute_all_tool_calls()`は`ctx.cfg.tool.serial_tool_calls`のみに基づいてディスパッチする。

| Condition | Execution |
|---|---|
| `serial_tool_calls=False` (デフォルト) | `_execute_with_dag()` — DAGスケジューリング |
| `serial_tool_calls=True` | `_execute_standard()` — 逐次/並列判定 (副作用のあるツールが1つでもあれば逐次、なければ`asyncio.gather()`で並列) |

> **Explicit in code:** `agent/tool_runner.py`の`execute_all_tool_calls()`は`if not ctx.cfg.tool.serial_tool_calls: _execute_with_dag(...) else: _execute_standard(...)`という2分岐のみで構成される。`use_tool_dag`という設定フィールドはコードベース全体 (`agent/config_dataclasses.py`含む) に存在しない。DAGスケジューリングは`serial_tool_calls=False`の場合に常時有効であり、「レガシー動作」への切替フラグは実装上存在しない。旧版ドキュメントにあった`use_tool_dag`および`ProductionConfigValidator`による`use_tool_dag=false`の起動時エラー化の記述は実装と一致しないため削除した。`ProductionConfigValidator.validate()` (`shared/production_config_validator.py`) が実際に検証するのは`tool_definitions_strict`/`routing_drift_strict`のstrictキー、`tool_safety_tiers`の登録漏れ・不明キー、および`allowed_tools=[]`のみである (詳細は[05_agent_06_03](05_agent_06_03_tool-execution-and-approval-concurrency-safety.md)参照)。

---

## DAG Tool Scheduler (`agent/tool_scheduler.py`)

`build_execution_groups(tool_calls, tool_meta)`はツール呼び出しを順序付きバッチにグルーピングする。

### ルール (優先順位順に適用)

1. **`requires_serial=True`** — ツールは単一要素のシリアルバリアを形成し、他のすべてのツールより前に単独で実行される
2. **同一の`resource_scope` + `is_write=True`** — 同じスコープを共有するツールはそのスコープのグループ内でシリアル化される
3. **`resource_scope`のない`is_write=True`** — `write_first`グループに入る (保守的に、読み取りより前に実行される)
4. **その他すべて** — 末尾の並列グループ

### `concurrent_groups`構造

`metadata.concurrent_groups: list[list[list[dict]]]` — バッチのリスト:
- 各**バッチ**は他のバッチに対して逐次実行される
- バッチ**内**のグループは`asyncio.gather()`により並行実行される
- `serial_barrier`ツール: それぞれ単独のバッチ
- `write_first`グループ: 専用の逐次バッチ
- すべての`resource_scope`グループ + 並列グループ: 共有の並行バッチ

例: `[write_file(scope=file), github_push(scope=github), read_text_file]` →
3つのグループを持つ1つの並行バッチとなり、すべて同時に実行される。

### `scheduling_mode`監査フィールド

`"dag_concurrent"` — 少なくとも1つのバッチで複数のグループが並行実行された。
`"dag_sequential"` — すべてのバッチが単一グループで実行された (バッチ内の並行性なし)。

### `execute_one_tool_call(ctx, tc, turn)`

1つのtool_call dictを解析、実行し、必要に応じて要約する。`(tc_id, name, args, full_text, is_error, llm_text)`を返す。

- `arguments` JSONを解析する; 不正なJSONの場合は`ToolArgumentsDecodeError`を発生させる
- `ctx.services_required.tools`がNoneの場合`ToolExecutorUnavailableError`を発生させる
- トランスポートエラーの場合: 失敗を`ctx.diagnostics`に保存する
- 要約が有効かつ結果が閾値を超える場合: `summarize_tool_result()`を呼び出す → `llm_text`
- それ以外: `tool_result_max_llm_chars`まで切り詰め + "\n... (truncated)"

### シリアル化統計

シリアル化統計はラウンドをまたいだシリアル化の影響を追跡する:

| Counter | Description |
|---|---|
| `total_events` | 全ラウンドを通じた累積シリアル化イベント数 |
| `total_tools_affected` | シリアル化の影響を受けた累積ツール数 |
| `tools_affected_last_round` | 直近のラウンドで影響を受けたツール数 (シリアル化がない場合は0にリセット) |

### 表示閾値

500文字を超える結果は、ログ上で全文の代わりに行数/文字数として表示される。

---

### シリアル化イベントスキーマ

各ラウンドは`round_exec`監査イベントを発行する:

| Field | Type | Description |
|---|---|---|
| `round_id` | string | このラウンドを識別するUUIDv4 |
| `tool_count` | int | ラウンド内のツール呼び出し数 |
| `mode` | string | `"parallel"`または`"serial"` |
| `has_side_effect` | bool | シリアル化イベントが発生した場合True |
| `trigger_tool` | string or null | シリアル化を引き起こした最初のツール |
| `elapsed_ms` | float | ラウンド全体の実時間 (ミリ秒) |
| `scheduling_mode` | string or null | DAGモード: `"dag_concurrent"`または`"dag_sequential"`; 標準モードではnull |
| `affected_tools` | list[string] | このラウンドで実行されたツール名一覧 |
| `serial_reason` | string or null | シリアル化理由 (例: `"side_effect"`。DAGモードでは`requires_serial`/`resource_scope_conflict`/`is_write_overlap`のいずれか) |
| `estimated_parallel_ms` | float or null | 標準モードでのみ設定。並列実行だった場合の推定所要時間 (各ツール実行時間の合計) |
| `source` | string | 固定値`"agent"` |
| `ts` | float | イベント発行時刻 (UNIX時間) |

> **Explicit in code:** `agent/tool_audit.py`の`write_round_exec()`が上記フィールドをすべて発行する。`agent/tool_runner.py`の`_execute_with_dag()`は`mode`フィールドに常に文字列`"parallel"`を設定する (DAG実行であることを示す固定値であり、バッチ内の逐次/並列の別は`scheduling_mode`側で表現される)。一方`_execute_standard()`の`mode`は実際の実行方式に応じて`"serial"`または`"parallel"`になる。同じ`mode`フィールドでも経路によって意味が異なる点に注意。

`elapsed_ms`を使ってシリアル化のオーバーヘッドを特定する。`has_side_effect=true`かつ
同等の並列ラウンドと比較して`elapsed_ms`が高いラウンドは、最適化の候補となる。

監査ログの検索:
```
grep round_exec /path/to/audit.log
```

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_06_02_tool-execution-and-approval-approval.md`
- `05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`
- `05_agent_06_04_tool-execution-and-approval-canonical.md`

## Keywords

ToolExecutor
parallel vs sequential execution
DAG tool scheduler
execute_one_tool_call
