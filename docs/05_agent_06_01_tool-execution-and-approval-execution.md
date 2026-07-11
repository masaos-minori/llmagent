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
source:
  - 05_agent_06_tool-execution-and-approval.md
---

# エージェントのツール実行と承認

- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- MCPルーティング → [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)

## 目的

`ToolExecutor`の挙動、並列実行と逐次実行、承認フロー、
プランモード、ツール実行結果の要約、キャッシュ、安全制御、`allowed_tools`を文書化する。

---

## ToolExecutor (`shared/tool_executor.py`)

`execute(tool_name, args) -> ToolCallResult`のディスパッチ優先順位:

```
1. Plugin tool (@register_tool)        — ローカルPython関数、MCPをバイパス
2. TTL cache                           — 期限切れでなければキャッシュ結果を返す
3. MCP server dispatch via internal method
     → ToolRouteResolver.resolve()     — tool_name → server_key (ルーティングの権威; 04_mcp_03 §Routing Source of Truth 参照)
     → McpServerHealthRegistry check  — UNAVAILABLEなサーバーをスキップ
     → LifecycleProtocol.ensure_ready() — 必要に応じてondemandサーバーを起動
     → HttpTransport — MCPサーバーへ送信
```

`ToolCallResult`はfrozenなdataclass: `(output: str, is_error: bool, request_id: str, server_key: str)`

---

## 並列実行と逐次実行

`execute_all_tool_calls()`は設定フラグに基づいてディスパッチする。設定リファレンス → [05_agent_08 §ToolConfig `use_tool_dag`](05_agent_08_01_configuration-loading-agent-config-part1.md)。

| Condition | Execution |
|---|---|
| `use_tool_dag=True`かつ`serial_tool_calls=False` | DAGスケジューリング |
| `serial_tool_calls=True` | 逐次 (全ツール) |
| `use_tool_dag=False`、副作用のあるツールが存在 | 逐次 (安全のためシリアル化) |
| `use_tool_dag=False`、副作用のあるツールなし | 並列 (`asyncio.gather()`) |

**本番運用上の注意:** `use_tool_dag=false`の設定はレガシー (非本番) 動作とみなされる。本番モードでは、この設定は`ProductionConfigValidator.validate()`による起動時検証でエラーとしてフラグされる。DAGスケジューラは独立した読み取りに対してリソーススコープ単位の並列性を提供しつつ、書き込みはリソーススコープごとにシリアル化する。

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
